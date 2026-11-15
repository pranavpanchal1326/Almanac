"""Paired block bootstrap over tiles (blueprint 3.10) and the win condition.

Each draw resamples tiles with replacement; a cell's weight is the number of times its tile was
drawn. Every forecast is scored on the same draws, so differences between forecasts are paired.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np

from almanac.evaluate.metrics import Ranked, average_precision_ranked

DRAWS = 2000
WIN_RELATIVE = 0.20  # at least 20% better than the reference
WIN_LOWER = 0.10  # with the lower end of the 95% interval above 10%


def tile_draws(n_tiles: int, draws: int, seed: int) -> np.ndarray:
    """``[draws, n_tiles]`` counts: how many times each tile is drawn in each replicate."""
    rng = np.random.default_rng(seed)
    out = np.empty((draws, n_tiles), dtype=np.float64)
    for d in range(draws):
        out[d] = np.bincount(rng.integers(0, n_tiles, n_tiles), minlength=n_tiles)
    return out


def bootstrap_ap(
    ranked: dict[str, Ranked], tile_index: np.ndarray, counts: np.ndarray
) -> dict[str, np.ndarray]:
    """AP of every forecast on every draw. ``tile_index`` maps each cell to its tile number."""
    out = {name: np.empty(counts.shape[0]) for name in ranked}
    sorted_tiles = {name: tile_index[r.order] for name, r in ranked.items()}
    for d in range(counts.shape[0]):
        for name, r in ranked.items():
            out[name][d] = average_precision_ranked(r, counts[d][sorted_tiles[name]])
    return out


def bootstrap_stat(
    stat: Callable[[np.ndarray], float], tile_index: np.ndarray, counts: np.ndarray
) -> np.ndarray:
    """Any statistic of cell weights, on every draw."""
    return np.array([stat(counts[d][tile_index]) for d in range(counts.shape[0])])


def interval(values: np.ndarray, level: float = 0.95) -> tuple[float, float]:
    a = (1 - level) / 2
    v = values[np.isfinite(values)]
    return float(np.quantile(v, a)), float(np.quantile(v, 1 - a))


def win_verdict(model: float, reference: float, rel_draws: np.ndarray) -> dict[str, float | bool]:
    """Win condition: relative AP improvement >= 20% and its 95% lower bound > 10%."""
    rel = model / reference - 1
    lo, hi = interval(rel_draws)
    return {
        "relative_improvement": rel,
        "ci_low": lo,
        "ci_high": hi,
        "win": bool(rel >= WIN_RELATIVE and lo > WIN_LOWER),
    }
