"""Tasks 0.8, 0.9 and the numbers for gate 0.

For every site: change between consecutive years at levels 0, 3 and 6; the noise floor and the
candidate threshold from the stable sites; the share of cells above the threshold per year pair;
a rank correlation between embedding change and change measured independently in imagery; and one
figure per site.

Coarse levels are built here from level 0 as the renormalised mean of valid unit vectors. Task 0.7
(docs/phase0/pyramid.json) records how that compares with the supplier's stored levels.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score

from almanac.common.constants import YEARS
from almanac.io.reader import valid_mask
from almanac.quality.embedding import coarsen_mean, cosine_change, dequantize, renormalize

sys.path.insert(0, str(Path(__file__).parent))
from common import DOCS, FIGURES, IMAGERY, Site, load_sites

LEVELS = {0: 1, 3: 8, 6: 64}  # level -> coarsening factor from level 0
PERCENTILES = (50, 90, 95, 99, 99.9)
FIXED_THRESHOLDS = (0.02, 0.05, 0.10, 0.20, 0.30)
PAIRS = [(YEARS[i], YEARS[i + 1]) for i in range(len(YEARS) - 1)]

#: Year pairs in which the documented event falls, fixed from the written record and the imagery
#: before any change value was looked at (docs/phase0/sites.md).
EVENT_PAIRS = {
    "xiongan": [(2019, 2020), (2020, 2021), (2021, 2022)],
    "novo_progresso": [(2019, 2020), (2020, 2021), (2023, 2024)],
}


def site_changes(site: Site) -> tuple[dict[int, tuple[np.ndarray, np.ndarray]], np.ndarray]:
    """Change for consecutive years at each level, and half-resolution unit vectors for display.

    Returns ``{level: (delta [T-1, H, W], valid [T-1, H, W])}`` and ``[T, 64, 512, 512]``.
    Years are processed one at a time so that a block's nine years never sit decoded in memory.
    """
    deltas: dict[int, tuple[list[np.ndarray], list[np.ndarray]]] = {lv: ([], []) for lv in LEVELS}
    previous: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    display = []
    for year in YEARS:
        stored = np.load(site.block_path(year))
        valid = valid_mask(stored)
        emb = renormalize(dequantize(stored))
        display.append(emb[:, ::2, ::2].copy())
        for level, factor in LEVELS.items():
            e, v = (emb, valid) if factor == 1 else coarsen_mean(emb, valid, factor)
            if level in previous:
                pe, pv = previous[level]
                deltas[level][0].append(cosine_change(pe, e).astype(np.float32))
                deltas[level][1].append(pv & v)
            previous[level] = (e, v)
    return {lv: (np.stack(d), np.stack(v)) for lv, (d, v) in deltas.items()}, np.stack(display)


def imagery_change(site: Site, year_a: int, year_b: int, factor: int = 16) -> np.ndarray | None:
    """Independent change measure from Sentinel-2: mean absolute difference of brightness-normalised
    red, green, blue and near-infrared, averaged over ``factor`` x ``factor`` cells."""
    d = IMAGERY / site.name
    try:
        stacks = []
        for y in (year_a, year_b):
            rgb = np.load(d / f"{y}_rgb.npy").astype(np.float32)
            nir = np.load(d / f"{y}_nir.npy").astype(np.float32)[None]
            bands = np.concatenate([rgb, nir])
            bands = (bands - bands.mean(axis=(1, 2), keepdims=True)) / (
                bands.std(axis=(1, 2), keepdims=True) + 1e-6
            )
            stacks.append(bands)
    except FileNotFoundError:
        return None
    diff = np.abs(stacks[1] - stacks[0]).mean(axis=0)
    h, w = diff.shape
    return diff.reshape(h // factor, factor, w // factor, factor).mean(axis=(1, 3))


def false_colour(emb_tchw: np.ndarray) -> np.ndarray:
    """Project 64 dimensions onto the site's first three principal axes; ``[T, H, W, 3]`` in 0..1."""
    c = emb_tchw.shape[1]
    sample = emb_tchw[:, :, ::4, ::4].transpose(0, 2, 3, 1).reshape(-1, c)
    mean = sample.mean(axis=0)
    _, _, vt = np.linalg.svd(sample - mean, full_matrices=False)
    proj = np.einsum("tchw,kc->thwk", emb_tchw - mean[None, :, None, None], vt[:3])
    lo, hi = np.percentile(proj[:, ::4, ::4], [2, 98], axis=(0, 1, 2))
    return np.clip((proj - lo) / (hi - lo + 1e-9), 0, 1)


def figure(site: Site, display: np.ndarray, delta0: np.ndarray, tau0: float) -> Path:
    colour = false_colour(display)
    fig, axes = plt.subplots(len(YEARS), 3, figsize=(9.6, 3.05 * len(YEARS)), dpi=80)
    vmax = max(4 * tau0, 0.2)
    for i, year in enumerate(YEARS):
        ax_img, ax_emb, ax_delta = axes[i]
        rgb_path = IMAGERY / site.name / f"{year}_rgb.npy"
        if rgb_path.exists():
            meta = json.loads((IMAGERY / site.name / f"{year}.json").read_text())
            ax_img.imshow(np.load(rgb_path).transpose(1, 2, 0)[::2, ::2])
            ax_img.set_title(f"Sentinel-2, {meta['datetime'][:10]}", fontsize=9)
        else:
            ax_img.text(0.5, 0.5, "no usable scene", ha="center", va="center")
            ax_img.set_title(f"Sentinel-2, {year}", fontsize=9)
        ax_emb.imshow(colour[i])
        ax_emb.set_title(f"Embedding, false colour, {year}", fontsize=9)
        if i == 0:
            ax_delta.text(0.5, 0.5, "first year:\nno earlier year to compare", ha="center", va="center")
        else:
            im = ax_delta.imshow(delta0[i - 1][::2, ::2], cmap="magma", vmin=0, vmax=vmax)
            share = float((delta0[i - 1] > tau0).mean())
            ax_delta.set_title(
                f"Change {year - 1} to {year}; {share:.1%} of cells above threshold", fontsize=9
            )
            fig.colorbar(im, ax=ax_delta, fraction=0.046, pad=0.02)
        for ax in axes[i]:
            ax.set_xticks([])
            ax.set_yticks([])
    fig.suptitle(
        f"{site.name} ({site.type}) - block {site.block_id}, 10.24 km square, north up\n"
        f"Change threshold at 10 m: {tau0:.4f}. Contains modified Copernicus Sentinel data.",
        fontsize=10,
        y=0.997,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.985))
    path = FIGURES / f"{site.name}.jpg"
    fig.savefig(path, pil_kwargs={"quality": 82})
    plt.close(fig)
    return path


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    sites = load_sites(roles=("change", "stable"))
    deltas: dict[str, dict[int, tuple[np.ndarray, np.ndarray]]] = {}
    for site in sites:
        deltas[site.name], _ = site_changes(site)
        print(f"{site.name}: change computed", flush=True)

    stable = [s.name for s in sites if s.role == "stable"]
    result: dict = {
        "event_pairs": {k: [f"{a}-{b}" for a, b in v] for k, v in EVENT_PAIRS.items()},
        "years": list(YEARS),
        "pairs": [f"{a}-{b}" for a, b in PAIRS],
        "levels": {},
    }
    for level in LEVELS:
        per_site = {}
        for name in deltas:
            d, v = deltas[name][level]
            per_site[name] = {
                "cells_per_pair": int(v[0].size),
                "percentiles": {str(p): float(np.percentile(d[v], p)) for p in PERCENTILES},
                "percentiles_by_pair": {
                    f"{a}-{b}": {str(p): float(np.percentile(d[i][v[i]], p)) for p in (50, 99)}
                    for i, (a, b) in enumerate(PAIRS)
                },
            }
        thresholds = {
            "desert_only": float(
                np.percentile(deltas["tanezrouft"][level][0][deltas["tanezrouft"][level][1]], 99)
            ),
            "pooled_stable": float(
                np.percentile(np.concatenate([deltas[n][level][0][deltas[n][level][1]] for n in stable]), 99)
            ),
            "strictest_stable": max(per_site[n]["percentiles"]["99"] for n in stable),
        }
        shares = {}
        for tname, tau in thresholds.items():
            shares[tname] = {
                name: {
                    f"{a}-{b}": float((deltas[name][level][0][i][deltas[name][level][1][i]] > tau).mean())
                    for i, (a, b) in enumerate(PAIRS)
                }
                for name in deltas
            }
        result["levels"][f"L{level}"] = {
            "distributions": per_site,
            "thresholds": thresholds,
            "share_above_threshold": shares,
        }

    # Shares above fixed thresholds: shows where in the distribution the sites separate.
    result["share_above_fixed_threshold_L0"] = {
        str(t): {
            name: {
                f"{a}-{b}": float((deltas[name][0][0][i][deltas[name][0][1][i]] > t).mean())
                for i, (a, b) in enumerate(PAIRS)
            }
            for name in deltas
        }
        for t in FIXED_THRESHOLDS
    }

    # Independent check: does embedding change line up with change measured in imagery?
    # Both are averaged to 160 m. "Changed in imagery" is the top tenth of imagery change.
    alignment: dict = {}
    for site in sites:
        d0, v0 = deltas[site.name][0]
        rows = {}
        for i, (a, b) in enumerate(PAIRS):
            img = imagery_change(site, a, b)
            if img is None:
                continue
            f = 16
            dm = np.where(v0[i], d0[i], np.nan).reshape(1024 // f, f, 1024 // f, f)
            dm = np.nanmean(dm, axis=(1, 3))
            ok = np.isfinite(dm)
            label = img[ok] >= np.percentile(img[ok], 90)
            rows[f"{a}-{b}"] = {
                "spearman": float(spearmanr(dm[ok], img[ok]).statistic),
                "auc_top_decile": float(roc_auc_score(label, dm[ok])),
                "mean_delta_changed": float(dm[ok][label].mean()),
                "mean_delta_rest": float(dm[ok][~label].mean()),
            }
        alignment[site.name] = rows
    result["imagery_alignment_160m"] = alignment

    tau0 = result["levels"]["L0"]["thresholds"]["strictest_stable"]
    for site in sites:
        _, display = site_changes(site)
        print("figure:", figure(site, display, deltas[site.name][0][0], tau0), flush=True)
        del display

    (DOCS / "noise_floor.json").write_text(json.dumps(result, indent=2))
    for level, block in result["levels"].items():
        print(level, "thresholds", {k: round(v, 5) for k, v in block["thresholds"].items()})
        for name, row in block["share_above_threshold"]["strictest_stable"].items():
            print(f"  {name:16s}", " ".join(f"{v:6.3f}" for v in row.values()))
    for name, rows in alignment.items():
        print(f"  {name:16s} AUC", " ".join(f"{r['auc_top_decile']:.2f}" for r in rows.values()))


if __name__ == "__main__":
    main()
