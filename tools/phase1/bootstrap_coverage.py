"""How often does the tile bootstrap's 95% interval cover the population value? (task 1.10)

Usage: python tools/phase1/bootstrap_coverage.py

Synthetic tiles: each has an event rate drawn from Beta(1, 15); a cell's score is its tile's rate
plus noise plus a bump if the event happened. "Model" has a larger bump than "baseline". The
population value is computed on 6,000 tiles. Writes docs/phase1/bootstrap_coverage.json.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from almanac.evaluate.bootstrap import bootstrap_ap, interval, tile_draws
from almanac.evaluate.metrics import average_precision, rank

REPO = Path(__file__).resolve().parents[2]
CELLS, REPS, DRAWS = 200, 40, 300


def make(rng: np.random.Generator, n: int) -> tuple[np.ndarray, ...]:
    rate = rng.beta(1, 15, n)
    tile = np.repeat(np.arange(n), CELLS)
    y = rng.random(tile.size) < rate[tile]
    e = rng.normal(0, 0.05, tile.size)
    model = rate[tile] + e + 0.10 * y
    base = rate[tile] + e + 0.06 * y + rng.normal(0, 0.03, tile.size)
    return tile, y, model, base


def main() -> None:
    rng = np.random.default_rng(20261115)
    _, y, m, b = make(rng, 6000)
    true_ap = average_precision(y, m)
    true_rel = true_ap / average_precision(y, b) - 1
    out = {
        "cells_per_tile": CELLS,
        "reps": REPS,
        "draws": DRAWS,
        "true_ap": true_ap,
        "true_rel": true_rel,
        "by_tiles": {},
    }
    for n in (60, 240):
        hits = {"ap": 0, "rel": 0}
        high = {"ap": 0, "rel": 0}
        est = {"ap": [], "rel": []}
        for _ in range(REPS):
            tile, y, m, b = make(rng, n)
            aps = bootstrap_ap(
                {"m": rank(y, m), "b": rank(y, b)}, tile, tile_draws(n, DRAWS, int(rng.integers(1 << 30)))
            )
            for k, draws, truth, value in (
                ("ap", aps["m"], true_ap, average_precision(y, m)),
                (
                    "rel",
                    aps["m"] / aps["b"] - 1,
                    true_rel,
                    average_precision(y, m) / average_precision(y, b) - 1,
                ),
            ):
                lo, hi = interval(draws)
                hits[k] += lo <= truth <= hi
                high[k] += truth < lo
                est[k].append(value)
        out["by_tiles"][str(n)] = {
            k: {
                "coverage": hits[k] / REPS,
                "interval_entirely_above_truth": high[k] / REPS,
                "mean_estimate": float(np.mean(est[k])),
            }
            for k in hits
        }
        print(n, out["by_tiles"][str(n)], flush=True)
    (REPO / "docs" / "phase1" / "bootstrap_coverage.json").write_text(json.dumps(out, indent=2), newline="\n")


if __name__ == "__main__":
    main()
