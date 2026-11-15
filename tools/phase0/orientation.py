"""Task 0.4: orientation (Q1) and georeference (Q2) checks on a coastline block.

Reference: a water mask from the Sentinel-2 near-infrared band, which is georeferenced
independently of the embeddings. Probe: a fixed linear direction in embedding space that
separates water from land.

Q1 passes when the probe agrees with the reference north-up and disagrees after a vertical flip.
Q2 passes when the best alignment between the two masks is within one cell of zero shift.
Also freezes a small fixture for the offline orientation test.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

from almanac.io.reader import read_block_via_vrt
from almanac.quality.embedding import dequantize, renormalize

sys.path.insert(0, str(Path(__file__).parent))
from common import DOCS, IMAGERY, REPO, load_sites

YEAR = 2021
STEP = 8  # decimation of the stored fixture
MAX_SHIFT = 6


def otsu(values: np.ndarray) -> float:
    hist, edges = np.histogram(values, bins=256)
    mids = (edges[:-1] + edges[1:]) / 2
    w0 = np.cumsum(hist)
    w1 = w0[-1] - w0
    m0 = np.cumsum(hist * mids) / np.maximum(w0, 1)
    m1 = (np.sum(hist * mids) - np.cumsum(hist * mids)) / np.maximum(w1, 1)
    return float(mids[np.argmax(w0 * w1 * (m0 - m1) ** 2)])


def agreement(a: np.ndarray, b: np.ndarray) -> float:
    return float((a == b).mean())


def shifted_agreement(probe: np.ndarray, ref: np.ndarray, dy: int, dx: int) -> float:
    """Agreement when the probe mask is moved by (dy, dx) cells, over the common interior."""
    m = MAX_SHIFT
    h, w = ref.shape
    return agreement(probe[m + dy : h - m + dy, m + dx : w - m + dx], ref[m : h - m, m : w - m])


def main() -> None:
    site = next(s for s in load_sites() if s.name == "alamein_coast")
    stored = np.load(site.block_path(YEAR))
    nir = np.load(IMAGERY / site.name / f"{YEAR}_nir.npy").astype(np.float32)
    scene = json.loads((IMAGERY / site.name / f"{YEAR}.json").read_text())
    ref_water = nir < otsu(nir)

    emb = renormalize(dequantize(stored))
    fit = np.zeros_like(ref_water)
    fit[4::16, 4::16] = True  # the probe is fitted on a sparse lattice and applied everywhere
    w = emb[:, fit & ref_water].mean(axis=1) - emb[:, fit & ~ref_water].mean(axis=1)
    scores = np.einsum("c,chw->hw", w, emb)
    b = float((scores[fit & ref_water].mean() + scores[fit & ~ref_water].mean()) / 2)
    probe_water = scores > b

    q1 = {
        "water_share_reference": float(ref_water.mean()),
        "water_share_north_half": float(ref_water[:512].mean()),
        "water_share_south_half": float(ref_water[512:].mean()),
        "agreement_north_up": agreement(probe_water, ref_water),
        "agreement_flipped_vertically": agreement(probe_water[::-1], ref_water),
        "agreement_flipped_horizontally": agreement(probe_water[:, ::-1], ref_water),
    }
    q1["pass"] = q1["agreement_north_up"] > 0.8 and q1["agreement_flipped_vertically"] < 0.5

    grid = {
        (dy, dx): shifted_agreement(probe_water, ref_water, dy, dx)
        for dy in range(-MAX_SHIFT, MAX_SHIFT + 1)
        for dx in range(-MAX_SHIFT, MAX_SHIFT + 1)
    }
    (best_dy, best_dx), best = max(grid.items(), key=lambda kv: kv[1])
    q2 = {
        "best_shift_rows": best_dy,
        "best_shift_cols": best_dx,
        "agreement_at_best": best,
        "agreement_at_zero": grid[(0, 0)],
        "pass": abs(best_dy) <= 1 and abs(best_dx) <= 1,
    }

    vrt_url = site.urls[YEAR].removesuffix(".tiff") + ".vrt"
    via_vrt = read_block_via_vrt(vrt_url, site.block_row, site.block_col)
    cross = {
        "raw_flipped_equals_sidecar": bool(np.array_equal(via_vrt, stored)),
        "unflipped_equals_sidecar": bool(np.array_equal(via_vrt, stored[:, ::-1, :])),
    }

    fixture = REPO / "tests" / "golden" / "orientation_coast.npz"
    np.savez_compressed(
        fixture,
        stored=stored[:, STEP // 2 :: STEP, STEP // 2 :: STEP],
        reference_water=ref_water[STEP // 2 :: STEP, STEP // 2 :: STEP],
        probe_w=w.astype(np.float32),
        probe_b=np.float32(b),
    )
    result = {
        "site": site.name,
        "block_id": site.block_id,
        "year": YEAR,
        "url": site.urls[YEAR],
        "reference_scene": scene,
        "Q1_orientation": q1,
        "Q2_georeference": q2,
        "sidecar_cross_check": cross,
        "fixture": str(fixture.relative_to(REPO)).replace("\\", "/"),
    }
    (DOCS / "orientation.json").write_text(json.dumps(result, indent=2))
    print(
        json.dumps(
            {k: result[k] for k in ("Q1_orientation", "Q2_georeference", "sidecar_cross_check")}, indent=1
        )
    )


if __name__ == "__main__":
    main()
