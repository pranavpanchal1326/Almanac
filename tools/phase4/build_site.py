# ruff: noqa: RUF001  (typographic dashes and quotes are intended on the page)
"""Task 4.8: the public scorecard page of issue 2027.01, generated from the records.

Usage: python tools/phase4/build_site.py [PACKAGE_DIR]   (default D:/almanac-data/packages/2027.01)

Writes into ``site/``:

- ``index.html``: the page. Every number is read from a committed record, never typed by hand:
  the backtest from ``docs/phase2/stage_b_report.json``, its reproduction from
  ``docs/phase2/stage_b_reproduction.json``, the 2026 forecast summary from
  ``docs/phase4/forecast_2026_meta.json``, the digest from
  ``docs/phase4/package_2027.01_manifest.json`` and the reads of the test truth from
  ``docs/phase1/test_touch_log.jsonl``;
- ``map-data.png``: the headline 2026 forecast on a longitude-latitude grid of 0.015° (about
  1.7 km). Red channel: the mean probability of the 640 m cells in the pixel, as
  ``round(255 * sqrt(p))``; green: its risk band (0 = lowest half of cells … 5 = top 1%), 255 where
  nothing is forecast. The page draws the map from it in the viewer's colour theme and reads it
  for the hover value;
- ``map-land.png``: the land share of every 640 m cell of the 2,020 region tiles (static, from the
  Global Forest Change data mask), drawn under the forecast as the base map;
- ``og.png``: a 1200 x 630 preview for links shared on social sites and the README.

Risk bands are ranks of the 640 m cells of the headline forecast, not fixed probabilities: the
backtest showed its probabilities run high, so the page shows where risk is highest relative to
everywhere else, and states each band's probability range beside it.

The map is drawn only from a package whose manifest equals the committed one.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
from pathlib import Path

import numpy as np
import rasterio.warp
from PIL import Image, ImageDraw, ImageFont
from rasterio.transform import Affine, from_origin
from rasterio.warp import Resampling, reproject

REPO = Path(__file__).resolve().parents[2]
SITE = REPO / "site"
DATA = Path("D:/almanac-data")
CELL, SIDE = 640.0, 128
RES = 0.015
BOUNDS = (-74.5, -24.5, -40.5, 5.5)  # the region (74W-41W, 24S-5N) with a half-degree margin
HELD_OUT = (-68.0, -13.0, -60.0, -7.0)
TILE_RE = re.compile(r"^(\d{1,2})([NS])_E(\d+)_N(-?\d+)$")
GITHUB = "https://github.com/pranavpanchal1326/Almanac"
SITE_URL = "https://pranavpanchal1326.github.io/Almanac/"
RELEASE = f"{GITHUB}/releases/tag/issue-2027.01-sealed"

# Risk bands: cut points as percentiles of the headline forecast over its forecast cells.
CUTS = [50, 75, 90, 95, 99]
BAND_NAMES = ["Lowest half", "Top 50%", "Top 25%", "Top 10%", "Top 5%", "Top 1%"]
# One-hue orange ramps (dataviz validate_palette.js: monotone lightness, visible steps, one hue, in
# both modes). This is a sequential map, so the lowest band is allowed to recede toward the
# background, as the palette's sequential rule permits: low risk should not look alarming.
RAMP_LIGHT = ["#f8dccb", "#f3b48e", "#ea8452", "#d65a22", "#a33e15", "#5e1f07"]
RAMP_DARK = ["#4a2516", "#7d3517", "#b44a1c", "#e2652c", "#f59b6c", "#fdd5bd"]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def tile_geo(tid: str) -> tuple[str, Affine]:
    m = TILE_RE.match(tid)
    zone, hemi, west, south = int(m.group(1)), m.group(2), int(m.group(3)), int(m.group(4))
    epsg = (32600 if hemi == "N" else 32700) + zone
    return f"EPSG:{epsg}", from_origin(west, south + SIDE * CELL, CELL, CELL)


def grid() -> tuple[int, int, Affine]:
    w, s, e, n = BOUNDS
    return round((e - w) / RES), round((n - s) / RES), from_origin(w, n, RES, RES)


def warp(values: np.ndarray, tid: str, width: int, height: int, dst: Affine) -> np.ndarray:
    crs, src = tile_geo(tid)
    out = np.full((height, width), np.nan, np.float32)
    reproject(values.astype(np.float32), out, src_transform=src, src_crs=crs, dst_transform=dst,
              dst_crs="EPSG:4326", src_nodata=np.nan, dst_nodata=np.nan, resampling=Resampling.average)
    return out


def box(tid: str, dst: Affine) -> list[float]:
    crs, src = tile_geo(tid)
    xs, ys = rasterio.warp.transform(crs, "EPSG:4326", [src.c, src.c + SIDE * CELL], [src.f - SIDE * CELL, src.f])
    c0, r0 = ~dst * (min(xs), max(ys))
    c1, r1 = ~dst * (max(xs), min(ys))
    return [round(c0, 1), round(r0, 1), round(c1 - c0, 1), round(r1 - r0, 1)]


def land_map(width: int, height: int, dst: Affine) -> np.ndarray:
    with (REPO / "configs/splits/amazon_cerrado_v1.csv").open() as f:
        region = [r["tile_id"] for r in csv.DictReader(f)]
    total = np.zeros((height, width))
    count = np.zeros((height, width))
    for tid in region:
        with np.load(DATA / "labels/forest_loss/L6" / tid.split("_", 1)[0] / f"{tid}.npz") as f:
            land = f["land_share"].astype(np.float32)  # static: Global Forest Change data mask
        out = warp(land, tid, width, height, dst)
        ok = np.isfinite(out)
        total[ok] += out[ok]
        count[ok] += 1
    with np.errstate(invalid="ignore"):
        share = total / count
    return np.where(np.isfinite(share), share, 0.0)


def forecast_map(package: Path, tiles: list[str], width: int, height: int, dst: Affine):
    layer = np.load(package / "forecast/M_A2_forest.npy", mmap_mode="r")
    elig = np.load(package / "baselines/B4_forest.npy", mmap_mode="r")  # issue-time eligibility
    cells = []
    total = np.zeros((height, width))
    count = np.zeros((height, width))
    for t, tid in enumerate(tiles):
        ok_cells = np.isfinite(elig[t])
        vals = np.where(ok_cells, layer[t], np.nan)
        cells.append(np.asarray(layer[t])[ok_cells])
        out = warp(vals, tid, width, height, dst)
        ok = np.isfinite(out)
        total[ok] += out[ok]
        count[ok] += 1
    cuts = np.percentile(np.concatenate(cells).astype(np.float64), CUTS)
    with np.errstate(invalid="ignore"):
        prob = total / count
    return prob, cuts, [box(t, dst) for t in tiles]


def encode(prob: np.ndarray, land: np.ndarray, cuts: np.ndarray) -> None:
    fin = np.isfinite(prob)
    band = np.where(fin, np.digitize(np.nan_to_num(prob), cuts), 255).astype(np.uint8)
    red = np.where(fin, np.round(255 * np.sqrt(np.clip(np.nan_to_num(prob), 0, 1))), 0).astype(np.uint8)
    rgb = np.stack([red, band, np.zeros_like(red)], axis=-1)
    Image.fromarray(rgb, "RGB").save(SITE / "map-data.png", optimize=True)
    Image.fromarray(np.round(255 * np.clip(land, 0, 1)).astype(np.uint8), "L").save(SITE / "map-land.png", optimize=True)


def font(size: int, bold: bool = False):
    for name in (["segoeuib.ttf", "DejaVuSans-Bold.ttf"] if bold else ["segoeui.ttf", "DejaVuSans.ttf"]):
        for root in (Path("C:/Windows/Fonts"), Path("/usr/share/fonts/truetype/dejavu")):
            if (root / name).exists():
                return ImageFont.truetype(str(root / name), size)
    return ImageFont.load_default()


def og_image(prob: np.ndarray, land: np.ndarray, cuts: np.ndarray, headline: str, sub: str) -> None:
    w, h = 1200, 630
    bg, landc, ink, muted = (252, 252, 251), (226, 224, 218), (29, 29, 27), (95, 95, 90)
    rgb = np.full((*prob.shape, 3), bg, np.uint8)
    a = np.clip(land, 0, 1)[..., None]
    rgb = (rgb * (1 - a) + np.array(landc) * a).astype(np.uint8)
    fin = np.isfinite(prob)
    band = np.digitize(np.nan_to_num(prob), cuts)
    for i, c in enumerate(RAMP_LIGHT):
        sel = fin & (band == i)
        rgb[sel] = [int(c[k : k + 2], 16) for k in (1, 3, 5)]
    m = Image.fromarray(rgb)
    m.thumbnail((480, 560))
    img = Image.new("RGB", (w, h), bg)
    img.paste(m, (w - m.width - 20, (h - m.height) // 2))
    d = ImageDraw.Draw(img)
    d.text((56, 64), "ALMANAC · ISSUE 2027.01", font=font(22, True), fill=muted)
    y = 112
    for line in headline.split("\n"):
        d.text((56, y), line, font=font(46, True), fill=ink)
        y += 58
    y += 18
    for line in sub.split("\n"):
        d.text((56, y), line, font=font(26), fill=muted)
        y += 36
    for i, c in enumerate(RAMP_LIGHT):
        d.rectangle([56 + i * 44, h - 92, 56 + i * 44 + 40, h - 78], fill=c)
    d.text((56, h - 70), "Forest-loss risk in 2026, lowest half → top 1%", font=font(20), fill=muted)
    img.save(SITE / "og.png", optimize=True)


def pct(x: float, digits: int = 1) -> str:
    return f"{x * 100:+.{digits}f}%"


def band_range(i: int, cuts: np.ndarray) -> str:
    lo = 0.0 if i == 0 else cuts[i - 1]
    if i == len(cuts):
        return f"probability {lo * 100:.0f}% or more"
    return f"{lo * 100:.1f}–{cuts[i] * 100:.1f}%"


CACHE = DATA / "work" / "site_map_cache.json"  # map geometry for --page-only; not published


def build(package: Path, page_only: bool = False) -> None:
    rep = read_json(REPO / "docs/phase2/stage_b_report.json")
    repro = read_json(REPO / "docs/phase2/stage_b_reproduction.json")
    meta = read_json(REPO / "docs/phase4/forecast_2026_meta.json")
    manifest_path = REPO / "docs/phase4/package_2027.01_manifest.json"
    digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    if (package / "manifest.json").read_bytes() != manifest_path.read_bytes():
        raise SystemExit("the package's manifest differs from the committed one; not drawing a map from it")
    touches = [json.loads(x) for x in (REPO / "docs/phase1/test_touch_log.jsonl").read_text().splitlines() if x.strip()]
    with (package / "tiles.csv").open() as f:
        tiles = [r["tile_id"] for r in csv.DictReader(f)]

    SITE.mkdir(exist_ok=True)
    width, height, dst = grid()
    if page_only:  # re-render the HTML only, from the map geometry of the last full build of this package
        cache = read_json(CACHE)
        if cache["digest"] != digest:
            raise SystemExit("the cached map is from another package; run a full build")
        cuts, boxes = np.array(cache["cuts"]), cache["boxes"]
    else:
        land = land_map(width, height, dst)
        prob, cuts, boxes = forecast_map(package, tiles, width, height, dst)
        encode(prob, land, cuts)
        og_image(prob, land, cuts,
                 "Where will forest be lost\nin 2026? A forecast made\nbefore anyone can know.",
                 f"Amazon and Cerrado · {len(tiles)} exam tiles\nSealed 22 Nov 2026 · digest {digest[:8]}\n"
                 "Graded in public, misses included")
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps({"digest": digest, "cuts": [float(c) for c in cuts], "boxes": boxes}))

    forest = rep["tasks"]["forest"]
    v = forest["verdict"]
    head = meta["layers"]["M_A2_forest"]

    order = [("M_A2", "Model M (A2)", "The headline: a network over five years of satellite embeddings and each cell’s neighbourhood"),
             ("B5_A2", "Reference B5 (A2)", "The same network without the neighbourhood: the bar to beat"),
             ("B4", "Gradient-boosted trees (B4)", "Past loss nearby, at three radii, plus the embeddings"),
             ("B3", "Proximity (B3)", "Distance-weighted forest loss of the last three years"),
             ("B2", "Last year’s change (B2)", "How much each cell’s embedding changed last year"),
             ("B0", "Constant (B0)", "The base rate everywhere: no skill")]
    top = max(forest["all"]["baselines"][k]["ap_ci95"][1] for k, _, _ in order)  # bars and intervals share a scale
    rows = []
    for k, name, what in order:
        b = forest["all"]["baselines"][k]
        lo, hi = b["ap_ci95"]
        nums = "".join(f'<td class="num">{forest[p]["baselines"][k]["ap"]:.3f}</td>' for p in ("all", "test", "held_out"))
        cls = ' class="head"' if k == "M_A2" else ""
        rows.append(
            f'<tr{cls}><th scope="row"><span class="fname">{html.escape(name)}</span>'
            f'<span class="fwhat">{html.escape(what)}</span></th>'
            f'<td class="bar"><span class="track" title="AP {b["ap"]:.3f}, 95% interval {lo:.3f} to {hi:.3f}">'
            f'<span class="fill" style="width:{100 * b["ap"] / top:.1f}%"></span>'
            f'<span class="ci" style="left:{100 * lo / top:.1f}%;width:{100 * (hi - lo) / top:.1f}%"></span></span></td>'
            f"{nums}</tr>"
        )
    cond = [
        ("At least 20% above the reference", pct(v["relative_improvement"]), v["condition_1_at_least_20pct"]),
        ("Lower end of the 95% interval above 10%", pct(v["ci95"][0]), v["condition_2_lower_bound_above_10pct"]),
        ("Better on the test tiles and on the held-out region, separately",
         f'{pct(v["improvement_by_part"]["test"])} · {pct(v["improvement_by_part"]["held_out"])}',
         v["condition_3_positive_on_each_part"]),
    ]
    cond_rows = "".join(
        f'<tr><th scope="row">{html.escape(a)}</th><td class="num">{b}</td>'
        f'<td><span class="tag {"yes" if ok else "no"}">{"Met" if ok else "Not met"}</span></td></tr>'
        for a, b, ok in cond
    )
    touch_rows = "".join(
        f'<tr><td class="nowrap">{html.escape(t["when"][:10])}</td><td>{html.escape(t["what"])}</td></tr>' for t in touches
    )
    n_checks, n_ok = len(repro["checks"]), sum(c["ok"] for c in repro["checks"])
    largest = max(c["difference"] for c in repro["checks"])
    rel = {k: forest["all"]["baselines"][k]["reliability"] for k in ("M_A2", "B4")}

    mapjson = {
        "bounds": BOUNDS, "res": RES, "width": width, "height": height,
        "tiles": boxes, "heldOut": HELD_OUT,
        "cuts": [float(c) for c in cuts], "bands": BAND_NAMES,
        "light": RAMP_LIGHT, "dark": RAMP_DARK,
    }
    bands_html = "".join(
        f'<li><span class="sw" style="--l:{RAMP_LIGHT[i]};--d:{RAMP_DARK[i]}"></span>'
        f"<span><b>{BAND_NAMES[i]}</b> {band_range(i, cuts)}</span></li>"
        for i in reversed(range(len(BAND_NAMES)))
    )
    tokens = {
        "IMPROVEMENT": pct(v["relative_improvement"]), "LO": pct(v["ci95"][0]), "HI": pct(v["ci95"][1]),
        "WIN": "a win" if v["win"] else "not a win",
        "ROWS": "".join(rows), "COND_ROWS": cond_rows, "BASE_RATE": f'{forest["all"]["base_rate"]:.3f}',
        "TILES": str(len(tiles)), "CELLS": f'{forest["all"]["cells"]:,}', "EVENTS": f'{forest["all"]["events"]:,}',
        "HEAD_CELLS": f'{head["cells"]:,}', "TOP1": f"{cuts[-1] * 100:.0f}%", "DIGEST": digest, "SHORT": digest[:8],
        "TOUCH_ROWS": touch_rows, "N_CHECKS": str(n_checks), "N_OK": str(n_ok), "LARGEST": f"{largest:.1e}",
        "COMMIT": meta["git_commit"][:7], "BANDS": bands_html,
        "MAPJSON": json.dumps(mapjson, separators=(",", ":")),
        "RELJSON": json.dumps(rel, separators=(",", ":")),
        "GITHUB": GITHUB, "SITE_URL": SITE_URL, "RELEASE": RELEASE, "N_TOUCH": str(len(touches)),
    }
    page = Path(__file__).with_name("site_template.html").read_text(encoding="utf-8")
    for k, val in tokens.items():
        page = page.replace(f"%%{k}%%", val)
    if "%%" in page:
        i = page.index("%%")
        raise SystemExit(f"unfilled token near: {page[i - 40 : i + 40]!r}")
    (SITE / "index.html").write_text(page, encoding="utf-8", newline="\n")
    print(f"site written: {SITE / 'index.html'}; map {width}x{height}; top 1% from p = {cuts[-1]:.3f}; digest {digest}")




def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("package", type=Path, nargs="?", default=Path("D:/almanac-data/packages/2027.01"))
    ap.add_argument("--page-only", action="store_true", help="re-render index.html from the cached map geometry")
    args = ap.parse_args()
    build(args.package, args.page_only)


if __name__ == "__main__":
    main()
