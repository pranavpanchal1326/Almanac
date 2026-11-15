"""Candidate rules for what counts as a change event in the embeddings (task 1.8).

ADR 0001 withdrew the single noise-floor threshold. The three candidates studied here are:

- ``global``: one threshold on ``delta`` for the whole region.
- ``class``: one threshold per land class, where classes are clusters of the embedding of the
  starting year. A cell changes if its change is unusual for its kind of land.
- ``history``: a cell changes if its change is unusual for that cell, measured as a robust
  z-score against the cell's own earlier year-to-year changes.

Every rule is calibrated the same way: its threshold is the ``q`` quantile of its score on cells
that the independent forest label calls stable, so all three flag the same share of stable land.
"""

from __future__ import annotations

import warnings

import numpy as np

#: Floor on the robust spread of a cell's history, so a cell with a perfectly flat past does not
#: turn rounding noise into an enormous z-score. Of the order of the 640 m noise floor.
HISTORY_SPREAD_FLOOR = 0.005
MAD_TO_SD = 1.4826


def history_z(delta: np.ndarray, min_history: int = 2) -> np.ndarray:
    """Robust z-score of each pair's change against the same cell's earlier pairs.

    ``delta`` is ``[P, H, W]`` with NaN for invalid pairs. Pair ``i`` is scored against pairs
    ``0..i-1`` only, so no later year is used. Cells with fewer than ``min_history`` valid earlier
    pairs get NaN.
    """
    p = delta.shape[0]
    out = np.full(delta.shape, np.nan, dtype=np.float32)
    for i in range(p):
        past = delta[:i]
        if i < min_history:
            continue
        n = np.sum(~np.isnan(past), axis=0)
        with np.errstate(all="ignore"), warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)  # all-NaN slices
            med = np.nanmedian(past, axis=0)
            mad = np.nanmedian(np.abs(past - med), axis=0)
        spread = np.maximum(MAD_TO_SD * mad, HISTORY_SPREAD_FLOOR)
        z = (delta[i] - med) / spread
        z[n < min_history] = np.nan
        out[i] = z
    return out


def quantile_threshold(score: np.ndarray, q: float) -> float:
    """The ``q`` quantile of the finite values of ``score``."""
    s = score[np.isfinite(score)]
    if s.size == 0:
        raise ValueError("no finite scores to set a threshold from")
    return float(np.quantile(s, q))


def class_thresholds(score: np.ndarray, classes: np.ndarray, n_classes: int, q: float) -> np.ndarray:
    """Per-class ``q`` quantile. A class with fewer than 100 values gets the pooled quantile."""
    pooled = quantile_threshold(score, q)
    out = np.full(n_classes, pooled, dtype=np.float64)
    ok = np.isfinite(score)
    for c in range(n_classes):
        s = score[ok & (classes == c)]
        if s.size >= 100:
            out[c] = float(np.quantile(s, q))
    return out
