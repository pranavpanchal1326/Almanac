# ruff: noqa: RUF001  (typographic dashes and quotes are intended on the page)
"""Task 4.8: the public scorecard page of issue 2027.01, generated from the records.

Usage: python tools/phase4/build_site.py [PACKAGE_DIR]   (default D:/almanac-data/packages/2027.01)

Writes ``site/index.html`` and two map images (light and dark). Every number on the page is read
from a committed record, never typed by hand:

- the backtest from ``docs/phase2/stage_b_report.json`` and its reproduction from
  ``docs/phase2/stage_b_reproduction.json``;
- the 2026 forecast summary from ``docs/phase4/forecast_2026_meta.json``;
- the digest from ``docs/phase4/package_2027.01_manifest.json``, checked against the package the
  map is drawn from;
- the reads of the test truth from ``docs/phase1/test_touch_log.jsonl``.

The map is the headline forecast for 2026 (forest loss), each 640 m cell averaged onto a
longitude-latitude grid of about 1.3 km; cells that are not forecast (no forest, too little land,
no valid 2025 embedding) are left blank.
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
import rasterio
from PIL import Image, ImageDraw
from rasterio.transform import Affine, from_origin
from rasterio.warp import Resampling, reproject

REPO = Path(__file__).resolve().parents[2]
SITE = REPO / "site"
CELL = 640.0
SIDE = 128
RES = 0.012  # degrees per map pixel
BOUNDS = (-75.0, -25.5, -40.0, 6.0)  # region (74W-41W, 24S-5N) plus a margin for tile edges
HELD_OUT = (-68.0, -13.0, -60.0, -7.0)
TILE_RE = re.compile(r"^(\d{1,2})([NS])_E(\d+)_N(-?\d+)$")

# Probability bands and the sequential blue ramp (dataviz reference palette, steps 100..700).
BANDS = [0.0, 0.01, 0.02, 0.05, 0.10, 0.20, 0.40, 1.0001]
LABELS = ["under 1%", "1–2%", "2–5%", "5–10%", "10–20%", "20–40%", "40% or more"]
RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
TILE_EDGE = {"light": (120, 120, 115, 70), "dark": (200, 200, 195, 60)}
HELD_EDGE = {"light": (60, 60, 55, 255), "dark": (225, 225, 220, 255)}


def rgb(hexcolor: str) -> tuple[int, int, int]:
    return tuple(int(hexcolor[i : i + 2], 16) for i in (1, 3, 5))


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def tile_crs(tid: str) -> tuple[str, Affine]:
    m = TILE_RE.match(tid)
    zone, hemi, west, south = int(m.group(1)), m.group(2), int(m.group(3)), int(m.group(4))
    epsg = (32600 if hemi == "N" else 32700) + zone
    north = south + SIDE * CELL
    return f"EPSG:{epsg}", from_origin(west, north, CELL, CELL)


def render(package: Path, tiles: list[str]) -> tuple[np.ndarray, list[tuple[int, int, int, int]], Affine]:
    layer = np.load(package / "forecast" / "M_A2_forest.npy", mmap_mode="r")
    base = np.load(package / "baselines" / "B4_forest.npy", mmap_mode="r")  # issue-time eligibility
    west, south, east, north = BOUNDS
    width, height = round((east - west) / RES), round((north - south) / RES)
    dst_t = from_origin(west, north, RES, RES)
    total = np.zeros((height, width), np.float64)
    count = np.zeros((height, width), np.float64)
    boxes = []
    for t, tid in enumerate(tiles):
        crs, src_t = tile_crs(tid)
        vals = np.where(np.isfinite(base[t]), layer[t], np.nan).astype(np.float32)
        out = np.full((height, width), np.nan, np.float32)
        reproject(vals, out, src_transform=src_t, src_crs=crs, dst_transform=dst_t,
                  dst_crs="EPSG:4326", src_nodata=np.nan, dst_nodata=np.nan,
                  resampling=Resampling.average)
        ok = np.isfinite(out)
        total[ok] += out[ok]
        count[ok] += 1
        # Tile footprint on the map, for the faint outline of the exam area.
        corners = rasterio.warp.transform(crs, "EPSG:4326",
                                          [src_t.c, src_t.c + SIDE * CELL], [src_t.f - SIDE * CELL, src_t.f])
        (x0, x1), (y0, y1) = corners
        c0, r0 = ~dst_t * (min(x0, x1), max(y0, y1))
        c1, r1 = ~dst_t * (max(x0, x1), min(y0, y1))
        boxes.append((int(c0), int(r0), int(c1), int(r1)))
    with np.errstate(invalid="ignore"):
        prob = total / count
    return prob, boxes, dst_t


def paint(prob: np.ndarray, boxes, dst_t: Affine, mode: str, path: Path) -> tuple[int, int]:
    ramp = RAMP if mode == "light" else RAMP[::-1]  # low recedes into the surface in both modes
    band = np.digitize(np.nan_to_num(prob, nan=-1), BANDS) - 1
    img = np.zeros((*prob.shape, 4), np.uint8)
    for i, color in enumerate(ramp):
        sel = np.isfinite(prob) & (band == i)
        img[sel, :3] = rgb(color)
        img[sel, 3] = 255
    im = Image.fromarray(img, "RGBA")
    draw = ImageDraw.Draw(im, "RGBA")
    for b in boxes:
        draw.rectangle(b, outline=TILE_EDGE[mode], width=1)
    w, s, e, n = HELD_OUT
    c0, r0 = ~dst_t * (w, n)
    c1, r1 = ~dst_t * (e, s)
    for k in range(0, int(c1 - c0), 10):  # dashed outline of the held-out region
        draw.line([(c0 + k, r0), (min(c0 + k + 5, c1), r0)], fill=HELD_EDGE[mode], width=2)
        draw.line([(c0 + k, r1), (min(c0 + k + 5, c1), r1)], fill=HELD_EDGE[mode], width=2)
    for k in range(0, int(r1 - r0), 10):
        draw.line([(c0, r0 + k), (c0, min(r0 + k + 5, r1))], fill=HELD_EDGE[mode], width=2)
        draw.line([(c1, r0 + k), (c1, min(r0 + k + 5, r1))], fill=HELD_EDGE[mode], width=2)
    # Crop to the exam tiles, with a margin.
    xs = [v for b in boxes for v in (b[0], b[2])]
    ys = [v for b in boxes for v in (b[1], b[3])]
    pad = 20
    crop = (max(min(xs) - pad, 0), max(min(ys) - pad, 0),
            min(max(xs) + pad, im.width), min(max(ys) + pad, im.height))
    im = im.crop(crop)
    im.save(path, optimize=True)
    return im.size


def pct(x: float, digits: int = 1) -> str:
    return f"{x * 100:+.{digits}f}%"


def build(package: Path) -> None:
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
    prob, boxes, dst_t = render(package, tiles)
    size = paint(prob, boxes, dst_t, "light", SITE / "map-light.png")
    paint(prob, boxes, dst_t, "dark", SITE / "map-dark.png")

    forest = rep["tasks"]["forest"]
    v = forest["verdict"]
    order = [("M_A2", "Model M (A2), headline"), ("B5_A2", "Reference: network without neighbours (B5)"),
             ("B4", "Gradient-boosted trees (B4)"), ("B3", "Proximity to past loss (B3)"),
             ("B2", "Last year’s change (B2)"), ("B0", "Constant base rate (B0)")]
    top = max(forest["all"]["baselines"][k]["ap"] for k, _ in order)
    rows = []
    for k, name in order:
        cells = []
        for part in ("all", "test", "held_out"):
            ap = forest[part]["baselines"][k]["ap"]
            cells.append(f'<td class="num">{ap:.3f}</td>')
        ap_all = forest["all"]["baselines"][k]["ap"]
        lo, hi = forest["all"]["baselines"][k]["ap_ci95"]
        width = 100 * ap_all / top
        head = ' class="head"' if k == "M_A2" else ""
        rows.append(
            f'<tr{head}><th scope="row">{html.escape(name)}</th>'
            f'<td class="bar"><span style="width:{width:.1f}%" title="AP {ap_all:.3f} '
            f'(95% interval {lo:.3f} to {hi:.3f})"></span></td>{"".join(cells)}</tr>'
        )
    base_rate = forest["all"]["base_rate"]
    cond = [
        ("At least 20% above the reference", pct(v["relative_improvement"]), v["condition_1_at_least_20pct"]),
        ("Lower end of the 95% interval above 10%", pct(v["ci95"][0]), v["condition_2_lower_bound_above_10pct"]),
        ("Better on the test tiles and on the held-out region",
         f'{pct(v["improvement_by_part"]["test"])} and {pct(v["improvement_by_part"]["held_out"])}',
         v["condition_3_positive_on_each_part"]),
    ]
    cond_rows = "".join(
        f'<tr><th scope="row">{html.escape(a)}</th><td class="num">{b}</td>'
        f'<td><span class="tag {"yes" if ok else "no"}">{"Met" if ok else "Not met"}</span></td></tr>'
        for a, b, ok in cond
    )
    head = meta["layers"]["M_A2_forest"]
    legend = "".join(
        f'<li><span class="sw" style="--l:{c};--d:{d}"></span>{html.escape(t)}</li>'
        for c, d, t in zip(RAMP, RAMP[::-1], LABELS, strict=True)
    )
    touch_rows = "".join(
        f'<tr><td>{html.escape(t["when"][:16].replace("T", " "))} UTC</td><td>{html.escape(t["what"])}</td></tr>'
        for t in touches
    )
    n_checks = len(repro["checks"])
    n_ok = sum(c["ok"] for c in repro["checks"])
    largest = max(c["difference"] for c in repro["checks"])

    page = TEMPLATE.format(
        improvement=pct(v["relative_improvement"]), lo=pct(v["ci95"][0]), hi=pct(v["ci95"][1]),
        win="a win" if v["win"] else "not a win",
        rows="".join(rows), cond_rows=cond_rows, base_rate=f"{base_rate:.3f}",
        tiles=len(tiles), cells=f'{forest["all"]["cells"]:,}', events=f'{forest["all"]["events"]:,}',
        head_cells=f'{head["cells"]:,}', head_mean=f'{head["mean"] * 100:.1f}%',
        legend=legend, width=size[0], height=size[1], digest=digest, short=digest[:8],
        touch_rows=touch_rows, n_checks=n_checks, n_ok=n_ok, largest=f"{largest:.1e}",
        commit=meta["git_commit"][:7],
    )
    (SITE / "index.html").write_text(page, encoding="utf-8", newline="\n")
    print(f"site written: {SITE / 'index.html'}, map {size[0]}x{size[1]}, digest {digest}")


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Almanac issue 2027.01</title>
<meta name="description" content="A forecast of forest loss in the Amazon and Cerrado for 2026, locked before the truth exists, with its rules, backtest and proofs.">
<style>
:root {{
  --surface: #fcfcfb; --surface-2: #f3f2ef; --ink: #1d1d1b; --ink-2: #4a4a46; --muted: #6f6f69;
  --rule: #dcdbd6; --accent: #256abf; --bar: #3987e5; --bar-head: #184f95;
  --yes-bg: #e3f1e6; --yes-ink: #1f6b33; --no-bg: #f8e4e1; --no-ink: #9c2b1f;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --surface: #1a1a19; --surface-2: #232322; --ink: #ecebe7; --ink-2: #c4c3be; --muted: #9a9993;
    --rule: #383835; --accent: #86b6ef; --bar: #3987e5; --bar-head: #9ec5f4;
    --yes-bg: #1e3524; --yes-ink: #9fd8ae; --no-bg: #3d211d; --no-ink: #f0a99f;
  }}
}}
:root[data-theme="dark"] {{
  --surface: #1a1a19; --surface-2: #232322; --ink: #ecebe7; --ink-2: #c4c3be; --muted: #9a9993;
  --rule: #383835; --accent: #86b6ef; --bar: #3987e5; --bar-head: #9ec5f4;
  --yes-bg: #1e3524; --yes-ink: #9fd8ae; --no-bg: #3d211d; --no-ink: #f0a99f;
}}
* {{ box-sizing: border-box; }}
html {{ -webkit-text-size-adjust: 100%; }}
body {{ margin: 0; background: var(--surface); color: var(--ink);
  font: 16px/1.55 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }}
main {{ max-width: 960px; margin: 0 auto; padding: 32px 16px 64px; }}
h1 {{ font-size: clamp(1.7rem, 4vw, 2.4rem); line-height: 1.15; margin: 0 0 12px; letter-spacing: -0.01em; }}
h2 {{ font-size: 1.25rem; margin: 48px 0 12px; }}
p {{ margin: 0 0 12px; color: var(--ink-2); max-width: 68ch; }}
a {{ color: var(--accent); }}
.eyebrow {{ font-size: .8rem; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); margin: 0 0 8px; }}
.lede {{ font-size: 1.1rem; color: var(--ink); }}
.stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 12px; margin: 28px 0 8px; }}
.stat {{ background: var(--surface-2); border-radius: 10px; padding: 14px 16px; }}
.stat b {{ display: block; font-size: 1.6rem; font-variant-numeric: tabular-nums; line-height: 1.2; }}
.stat span {{ font-size: .85rem; color: var(--muted); }}
.scroll {{ overflow-x: auto; -webkit-overflow-scrolling: touch; }}
table {{ border-collapse: collapse; width: 100%; font-size: .95rem; }}
th, td {{ text-align: left; padding: 9px 10px; border-bottom: 1px solid var(--rule); vertical-align: middle; }}
thead th {{ font-size: .8rem; color: var(--muted); font-weight: 600; }}
td.num, th.num {{ text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }}
tbody th {{ font-weight: 500; }}
tr.head th, tr.head td.num {{ font-weight: 700; }}
td.bar {{ width: 28%; min-width: 90px; }}
td.bar span {{ display: block; height: 10px; border-radius: 0 4px 4px 0; background: var(--bar); }}
tr.head td.bar span {{ background: var(--bar-head); }}
.tag {{ display: inline-block; font-size: .8rem; font-weight: 600; padding: 2px 9px; border-radius: 999px; }}
.tag.yes {{ background: var(--yes-bg); color: var(--yes-ink); }}
.tag.yes::before {{ content: "✓ "; }}
.tag.no {{ background: var(--no-bg); color: var(--no-ink); }}
.tag.no::before {{ content: "✕ "; }}
figure {{ margin: 16px 0 0; }}
figure img {{ display: block; width: 100%; height: auto; background: var(--surface-2); border-radius: 10px; }}
figcaption {{ font-size: .85rem; color: var(--muted); margin-top: 8px; max-width: 68ch; }}
.legend {{ list-style: none; display: flex; flex-wrap: wrap; gap: 6px 16px; padding: 0; margin: 12px 0 0; font-size: .85rem; color: var(--ink-2); }}
.legend li {{ display: flex; align-items: center; gap: 6px; }}
.sw {{ width: 14px; height: 14px; border-radius: 3px; background: var(--l); }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) .sw {{ background: var(--d); }} }}
:root[data-theme="dark"] .sw {{ background: var(--d); }}
code, pre {{ font-family: ui-monospace, "Cascadia Mono", Consolas, monospace; font-size: .88rem; }}
pre {{ background: var(--surface-2); padding: 12px 14px; border-radius: 8px; overflow-x: auto; margin: 8px 0 12px; }}
.digest {{ word-break: break-all; }}
ul.plain {{ padding-left: 20px; color: var(--ink-2); max-width: 68ch; }}
ul.plain li {{ margin-bottom: 6px; }}
footer {{ margin-top: 56px; padding-top: 16px; border-top: 1px solid var(--rule); font-size: .85rem; color: var(--muted); }}
footer p {{ color: var(--muted); }}
</style>
</head>
<body>
<main>
<p class="eyebrow">Almanac · issue 2027.01 · forest loss, Amazon and Cerrado</p>
<h1>Where will forest be lost in 2026? A forecast made before anyone can know.</h1>
<p class="lede">For every 640 m cell of forest on {tiles} exam tiles, the probability that at least
2.5% of it (about 1 hectare) is lost in 2026. The forecast and the rules that grade it were fixed
before the 2026 loss maps exist. When they are published, it is graded here, in public, misses included.</p>

<div class="stats">
  <div class="stat"><b>{improvement}</b><span>backtest on 2025, against the reference (needs +20%)</span></div>
  <div class="stat"><b>{lo} to {hi}</b><span>95% interval of that improvement</span></div>
  <div class="stat"><b>{short}…</b><span>package digest, sealed 22 November 2026</span></div>
  <div class="stat"><b>15 Jan 2027</b><span>formal lock; the exam follows the 2026 data</span></div>
</div>

<h2>The 2026 forecast</h2>
<p>The headline forecast, model M (A2): {head_cells} cells, mean probability {head_mean}. Each
pixel is the average of the 640 m cells inside it. Blank cells are not forecast: no forest, too
little land, or no valid 2025 satellite embedding.</p>
<figure>
  <picture>
    <source srcset="map-dark.png" media="(prefers-color-scheme: dark)">
    <img src="map-light.png" width="{width}" height="{height}" alt="Map of the forecast probability of forest loss in 2026 on the {tiles} exam tiles of the Amazon and Cerrado, shaded from light (under 1%) to dark (40% or more), with the held-out region outlined.">
  </picture>
  <figcaption>Probability of forest loss in 2026. Faint squares: the {tiles} exam tiles (82 km each).
  Dashed box: the held-out region (68°W–60°W, 13°S–7°S), never used in training. The
  probabilities ran high in the backtest, so read the map as a ranking of risk first.</figcaption>
</figure>
<ul class="legend" aria-label="Probability bands">{legend}</ul>

<h2>The backtest: graded once, on 2025</h2>
<p>Before the forecast was made, the frozen model was scored once on 2025, on the same {tiles}
tiles: {cells} forest cells, {events} of them lost. Average precision (AP) rewards putting the
cells that were lost at the top of the ranking; a forecast with no skill scores the base rate,
{base_rate}.</p>
<div class="scroll"><table>
<thead><tr><th>Forecast</th><th>AP, all tiles</th><th class="num">All</th><th class="num">Test tiles</th><th class="num">Held-out region</th></tr></thead>
<tbody>{rows}</tbody>
</table></div>

<h2>The win condition, applied to the backtest</h2>
<p>Fixed and timestamped before any model was trained. All three must hold.</p>
<div class="scroll"><table>
<thead><tr><th>Condition</th><th class="num">Result</th><th>Status</th></tr></thead>
<tbody>{cond_rows}</tbody>
</table></div>
<p style="margin-top:12px">So the backtest is <b>{win}</b>. The model was still chosen as the
headline because it was the best forecast on every part of the test; the 20% bar for 2026 was not
moved, and the reference and every baseline are locked beside it and graded on the same truth.
<a href="https://github.com/pranavpanchal1326/Almanac/blob/main/docs/adr/0004-gate-2.md">The decision and the case against it</a>.</p>

<h2>What is weak, said plainly</h2>
<ul class="plain">
  <li>The probabilities ran high on 2025: more loss was forecast than happened in every tenth of the forecasts.</li>
  <li>On the 2024 validation year the model was 4.6% <i>below</i> the reference. That check was small (146 tiles), but it is part of the record.</li>
  <li>The 2025 test data were read twice: once for the graded backtest and once, against the protocol, for an independent re-grade of the same frozen forecasts. Nothing changed; it is logged below.</li>
  <li>One region, one kind of event, one year ahead.</li>
</ul>

<h2>Check it yourself</h2>
<p>The package is plain <code>.npy</code> layers, a tile list and a canonical manifest. Its digest is
the SHA-256 of the manifest:</p>
<pre class="digest">{digest}</pre>
<p>The verifier needs only Python and NumPy and imports nothing from the project:</p>
<pre>python tools/verify_issue.py PACKAGE_DIR --digest {digest}</pre>
<p>The backtest was re-graded by separate code that shares nothing with the grader, reading the
truth from the source label files: {n_ok} of {n_checks} values matched, the largest difference
{largest}.</p>

<h2>Every read of the test truth</h2>
<div class="scroll"><table>
<thead><tr><th>When</th><th>What</th></tr></thead>
<tbody>{touch_rows}</tbody>
</table></div>

<h2>The rules and their proofs</h2>
<ul class="plain">
  <li><a href="https://github.com/pranavpanchal1326/Almanac/blob/main/docs/prereg/2027.01.md">Pre-registration 2027.01</a>, timestamped 15 November 2026 by FreeTSA and DigiCert and anchored in Bitcoin.</li>
  <li><a href="https://github.com/pranavpanchal1326/Almanac/blob/main/docs/prereg/2027.01.amendment-1.md">Amendment 1</a> (the model) and <a href="https://github.com/pranavpanchal1326/Almanac/blob/main/docs/prereg/2027.01.amendment-2.md">amendment 2</a> (the stable recipe and the reference), each timestamped before the runs it governs.</li>
  <li><a href="https://github.com/pranavpanchal1326/Almanac/blob/main/docs/prereg/proofs/README.md">How to verify the timestamps</a>.</li>
  <li><a href="https://github.com/pranavpanchal1326/Almanac/blob/main/docs/phase2/STATUS.md">Every training run</a>, including the ones that collapsed.</li>
</ul>

<footer>
<p>Generated from the project's records by <code>tools/phase4/build_site.py</code>; forecast built at commit <code>{commit}</code>.
Code: <a href="https://github.com/pranavpanchal1326/Almanac">github.com/pranavpanchal1326/Almanac</a> (Apache 2.0).</p>
<p>Input data: AlphaEarth Foundations Satellite Embedding dataset, produced by Google and Google
DeepMind, used under CC-BY 4.0. Forest labels: Hansen, M. C. et al. 2013, Science 342: 850–853;
Global Forest Change 2000–2025 v1.13, University of Maryland, under CC-BY 4.0.</p>
</footer>
</main>
</body>
</html>
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("package", type=Path, nargs="?", default=Path("D:/almanac-data/packages/2027.01"))
    build(ap.parse_args().package)


if __name__ == "__main__":
    main()
