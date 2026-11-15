"""Scoring rules for the occurrence task (blueprint 3.8), with optional per-cell weights.

Weights exist for the bootstrap: a tile drawn twice gives each of its cells weight 2. Every
ranking metric treats tied scores as one threshold, as scikit-learn does, so a constant forecast
scores the base rate and nothing better.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.ndimage import uniform_filter


@dataclass(frozen=True)
class Ranked:
    """Scores sorted once, descending, with the ends of each group of tied scores."""

    order: np.ndarray  # indices into the original arrays
    group_end: np.ndarray  # index (into the sorted arrays) of the last member of each tie group
    y: np.ndarray  # labels in sorted order, float64


def rank(y: np.ndarray, score: np.ndarray) -> Ranked:
    s = np.asarray(score, dtype=np.float64)
    if np.isnan(s).any():
        raise ValueError("scores contain NaN; fill them before ranking")
    order = np.argsort(-s, kind="stable")
    ss = s[order]
    group_end = np.flatnonzero(np.r_[ss[1:] != ss[:-1], True])
    return Ranked(order, group_end, np.asarray(y, dtype=np.float64)[order])


def average_precision_ranked(r: Ranked, w: np.ndarray | None = None) -> float:
    """AP = sum over thresholds of (recall step) x (precision), weights already in sorted order."""
    wy = r.y if w is None else w * r.y
    ww = np.ones_like(r.y) if w is None else w
    tp = np.cumsum(wy)[r.group_end]
    seen = np.cumsum(ww)[r.group_end]
    total = tp[-1]
    if total <= 0:
        return float("nan")
    precision = np.divide(tp, seen, out=np.zeros_like(tp), where=seen > 0)
    recall_step = np.diff(np.r_[0.0, tp]) / total
    return float(np.sum(recall_step * precision))


def average_precision(y: np.ndarray, score: np.ndarray, w: np.ndarray | None = None) -> float:
    r = rank(y, score)
    return average_precision_ranked(r, None if w is None else np.asarray(w, dtype=np.float64)[r.order])


def precision_at_top(r: Ranked, share: float, w: np.ndarray | None = None) -> float:
    """Precision in the top ``share`` of cells (cells have equal area at one level).

    A tie group that straddles the cut contributes in proportion to the part of it inside, which is
    the expected precision under random tie-breaking.
    """
    ww = np.ones_like(r.y) if w is None else w
    wy = r.y * ww
    cw = np.cumsum(ww)
    cy = np.cumsum(wy)
    budget = share * cw[-1]
    if budget <= 0:
        return float("nan")
    ends = r.group_end
    seen = cw[ends]
    hits = cy[ends]
    g = int(np.searchsorted(seen, budget, side="left"))  # first group reaching the budget
    prev_seen = seen[g - 1] if g > 0 else 0.0
    prev_hits = hits[g - 1] if g > 0 else 0.0
    group_w = seen[g] - prev_seen
    group_hits = hits[g] - prev_hits
    frac = (budget - prev_seen) / group_w if group_w > 0 else 0.0
    return float((prev_hits + frac * group_hits) / budget)


def brier(y: np.ndarray, p: np.ndarray, w: np.ndarray | None = None) -> float:
    return float(np.average((np.asarray(p, dtype=np.float64) - y) ** 2, weights=w))


def log_loss(y: np.ndarray, p: np.ndarray, w: np.ndarray | None = None, eps: float = 1e-6) -> float:
    q = np.clip(np.asarray(p, dtype=np.float64), eps, 1 - eps)
    return float(np.average(-(y * np.log(q) + (1 - y) * np.log(1 - q)), weights=w))


def calibration(y: np.ndarray, p: np.ndarray, bins: int = 10) -> dict[str, list[float] | float]:
    """Reliability curve in ``bins`` equal-mass bins, and expected calibration error."""
    p = np.asarray(p, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    order = np.argsort(p, kind="stable")
    parts = np.array_split(order, bins)
    mean_p, mean_y, sizes = [], [], []
    for part in parts:
        if part.size == 0:
            continue
        mean_p.append(float(p[part].mean()))
        mean_y.append(float(y[part].mean()))
        sizes.append(part.size)
    sz = np.array(sizes, dtype=np.float64)
    ece = float(np.sum(sz * np.abs(np.array(mean_p) - np.array(mean_y))) / sz.sum())
    return {"mean_forecast": mean_p, "observed_rate": mean_y, "ece": ece}


def fss_terms(forecast_hw: np.ndarray, observed_hw: np.ndarray, scale: int) -> tuple[float, float]:
    """Numerator and reference sums of the fractions skill score for one tile at one scale.

    Inputs are binary maps with ineligible cells set to 0. FSS = 1 - sum(num) / sum(ref) over tiles.
    """
    pf = uniform_filter(forecast_hw.astype(np.float64), size=scale, mode="constant")
    po = uniform_filter(observed_hw.astype(np.float64), size=scale, mode="constant")
    return float(np.sum((pf - po) ** 2)), float(np.sum(pf**2) + np.sum(po**2))
