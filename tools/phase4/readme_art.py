"""Art for the README, drawn from the same records as the scorecard page.

Usage: python tools/phase4/readme_art.py   (after tools/phase4/build_site.py)

Writes into ``docs/media/``:

- ``forecast.gif``: the headline 2026 forecast lighting up band by band, from the safest half to
  the top 1%, then a slow glow on the brightest bands; drawn from ``site/map-data.png`` and
  ``site/map-land.png`` with the page's blue ramp;
- ``backtest.png``: every forecast's average precision on the 2025 backtest with its 95% interval,
  read from ``docs/phase2/stage_b_report.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from build_site import BAND_NAMES, RAMP, font

OUT = REPO / "docs" / "media"
SPACE, LAND, WATER = np.array([5, 11, 22]), np.array([27, 35, 49]), np.array([7, 14, 27])
INK, MUTED, SKY = (232, 238, 247), (127, 144, 168), (108, 196, 240)
WIDTH = 760


def rgb(h: str) -> np.ndarray:
    return np.array([int(h[i : i + 2], 16) for i in (1, 3, 5)], float)


def forecast_gif() -> None:
    data = np.asarray(Image.open(REPO / "site" / "map-data.png").convert("RGB"))
    land = np.asarray(Image.open(REPO / "site" / "map-land.png").convert("L")).astype(float) / 255
    band = data[..., 1]
    a = land[..., None]
    base = np.where((land > 0)[..., None], WATER * (1 - a) + LAND * a, SPACE).astype(float)
    h = round(data.shape[0] * WIDTH / data.shape[1])
    small = lambda arr: np.asarray(Image.fromarray(arr.astype(np.uint8)).resize((WIDTH, h), Image.LANCZOS)).astype(float)  # noqa: E731
    base_s = small(base)
    layers = [small(np.where((band == i)[..., None], rgb(c), base)) for i, c in enumerate(RAMP)]
    masks = [np.asarray(Image.fromarray(((band == i) * 255).astype(np.uint8)).resize((WIDTH, h), Image.BOX)).astype(float)[..., None] / 255
             for i in range(len(RAMP))]
    hot = np.zeros((*band.shape, 3), np.uint8)
    for i in (4, 5):
        hot[band == i] = rgb(RAMP[i]).astype(np.uint8)
    glow = np.asarray(Image.fromarray(hot).resize((WIDTH, h), Image.BOX).filter(ImageFilter.GaussianBlur(4))).astype(float)

    pad, foot = 22, 64
    canvas_h = h + pad * 2 + foot
    frames, durations = [], []

    def frame(alphas: list[float], g: float) -> Image.Image:
        img = base_s.copy()
        for i, al in enumerate(alphas):
            if al > 0:
                img = img * (1 - masks[i] * al) + layers[i] * masks[i] * al
        img = np.clip(img + glow * g, 0, 255)
        out = Image.new("RGB", (WIDTH + pad * 2, canvas_h), tuple(SPACE))
        out.paste(Image.fromarray(img.astype(np.uint8)), (pad, pad))
        d = ImageDraw.Draw(out)
        d.rectangle([pad - 1, pad - 1, pad + WIDTH, pad + h], outline=(40, 56, 80))
        y = pad + h + 18
        x = pad
        for i, c in enumerate(RAMP):
            on = alphas[i] if i < len(alphas) else 1
            col = tuple(int(v) for v in (rgb(c) * on + SPACE * (1 - on)))
            d.rectangle([x + i * 40, y, x + i * 40 + 36, y + 8], fill=col)
        d.text((x + 6 * 40 + 10, y - 6), "Risk of forest loss in 2026 · lowest half → top 1%", font=font(15), fill=MUTED)
        lit = sum(1 for al in alphas if al >= 1)
        label = BAND_NAMES[min(lit, len(BAND_NAMES)) - 1] if lit else ""
        d.text((x, y + 18), "ALMANAC · ISSUE 2027.01 · AMAZON & CERRADO", font=font(13, True), fill=SKY)
        if label:
            d.text((pad + WIDTH, y + 18), f"lighting: {label.lower()}" if lit < len(RAMP) else "sealed 22 Nov 2026",
                   font=font(13), fill=INK, anchor="ra")
        return out

    steps = 5
    for i in range(len(RAMP)):
        for s in range(1, steps + 1):
            al = [1.0] * i + [s / steps] + [0.0] * (len(RAMP) - i - 1)
            frames.append(frame(al, 0))
            durations.append(70)
        durations[-1] = 260
    for g in list(np.linspace(0, 1, 8)) + list(np.linspace(1, .35, 8)) + list(np.linspace(.35, 1, 8)):
        frames.append(frame([1.0] * len(RAMP), float(g)))
        durations.append(90)
    durations[-1] = 2600
    pal = frames[-1].quantize(colors=255, method=Image.Quantize.MEDIANCUT)
    q = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    OUT.mkdir(parents=True, exist_ok=True)
    q[0].save(OUT / "forecast.gif", save_all=True, append_images=q[1:], duration=durations, loop=0, optimize=True, disposal=1)


def backtest_png() -> None:
    rep = json.loads((REPO / "docs/phase2/stage_b_report.json").read_text(encoding="utf-8"))["tasks"]["forest"]
    order = [("M_A2", "Model M (A2)"), ("B5_A2", "Reference B5 (A2)"), ("B4", "Gradient-boosted trees (B4)"),
             ("B3", "Proximity to past loss (B3)"), ("B2", "Last year's change (B2)"), ("B0", "Constant base rate (B0)")]
    W, row, top, left, right = 1200, 64, 96, 330, 120
    H = top + row * len(order) + 74
    img = Image.new("RGB", (W, H), tuple(SPACE))
    d = ImageDraw.Draw(img)
    d.text((40, 30), "Forest-loss average precision, 2025 backtest · all 499 exam tiles", font=font(24, True), fill=INK)
    d.text((40, 62), "Bars: average precision · whiskers: 95% paired tile-bootstrap interval", font=font(16), fill=MUTED)
    vmax = 0.55
    X = lambda v: left + v / vmax * (W - left - right)  # noqa: E731
    for t in np.arange(0, vmax + 1e-9, 0.1):
        d.line([X(t), top - 6, X(t), top + row * len(order)], fill=(22, 34, 52))
        d.text((X(t), top + row * len(order) + 10), f"{t:.1f}", font=font(14), fill=MUTED, anchor="ma")
    for r, (k, name) in enumerate(order):
        b = rep["all"]["baselines"][k]
        y = top + r * row + row // 2
        me = k == "M_A2"
        d.text((40, y), name, font=font(18, me), fill=SKY if me else INK, anchor="lm")
        col = (108, 196, 240) if me else ((84, 104, 134) if k == "B5_A2" else (52, 68, 92))
        d.rounded_rectangle([X(0), y - 9, X(b["ap"]), y + 9], radius=4, fill=col)
        lo, hi = b["ap_ci95"]
        d.line([X(lo), y, X(hi), y], fill=(180, 194, 214), width=2)
        for v in (lo, hi):
            d.line([X(v), y - 8, X(v), y + 8], fill=(180, 194, 214), width=2)
        d.text((X(hi) + 14, y), f"{b['ap']:.3f}", font=font(18, me), fill=INK, anchor="lm")
    v = rep["verdict"]
    d.text((40, H - 34), f"Model vs reference: {v['relative_improvement'] * 100:+.1f}% "
           f"(95% interval {v['ci95'][0] * 100:+.1f}% to {v['ci95'][1] * 100:+.1f}%) · the pre-registered bar is +20% · not a win",
           font=font(16), fill=(240, 196, 112))
    img.save(OUT / "backtest.png", optimize=True)


if __name__ == "__main__":
    forecast_gif()
    backtest_png()
    for p in sorted(OUT.iterdir()):
        print(p.name, f"{p.stat().st_size / 1e6:.2f} MB")
