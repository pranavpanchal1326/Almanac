"""Examples for the occurrence task on one tile and one target year, using only what is known at
issue time (the end of the year before the target).

Two tasks, reported separately (docs/phase1/PLAN.md):

- ``forest``: cells with forest at the start of the target year; the event is forest loss of at
  least ``LOSS_EVENT`` of the cell in the target year (Global Forest Change, independent of the
  embeddings).
- ``embedding``: cells valid in both years; the event is the change rule of task 1.8 on the pair
  ending in the target year.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.ndimage import convolve, maximum_filter, uniform_filter

from almanac.common.constants import YEARS
from almanac.data.change_rules import history_z
from almanac.data.cube import TileCube

LOSS_EVENT = 0.025  # about 1 ha of a 41 ha cell (10 of 400 sample points)
FOREST_MIN = 0.10  # a cell counts as forest if at least 10% of it (about 4 ha) is forest
LAND_MIN = 0.5
CELL_M = 640.0
PROXIMITY_M = 5000.0
PROXIMITY_YEARS = 3
RADII = (3, 7, 19)  # neighbourhood windows in cells: about 2, 4.5 and 12 km across
TASKS = ("forest", "embedding")


@dataclass(frozen=True)
class ChangeRule:
    """The per-class rule chosen in task 1.8."""

    centres: np.ndarray  # [K, 64]
    class_tau: np.ndarray  # [K]

    def classes(self, emb_chw: np.ndarray) -> np.ndarray:
        x = emb_chw.reshape(64, -1).T
        d = (x * x).sum(1)[:, None] - 2 * x @ self.centres.T + (self.centres**2).sum(1)[None, :]
        return d.argmin(1).reshape(emb_chw.shape[1:])

    def events(self, cube: TileCube, end_year: int) -> np.ndarray:
        """Bool map of change events on the pair ending ``end_year``; False where invalid."""
        i = end_year - YEARS[1]
        delta = cube.delta[i]
        cls = self.classes(cube.embedding(end_year - 1))
        return np.nan_to_num(delta, nan=-1.0) > self.class_tau[cls]


def proximity_kernel(cell_m: float = CELL_M, radius_m: float = PROXIMITY_M) -> np.ndarray:
    """Weights ``1 - d / radius`` for cell centres closer than ``radius``, the own cell included."""
    r = int(radius_m // cell_m)
    yy, xx = np.mgrid[-r : r + 1, -r : r + 1]
    d = np.hypot(yy, xx) * cell_m
    return np.where(d < radius_m, 1 - d / radius_m, 0.0)


def proximity(events_khw: np.ndarray) -> np.ndarray:
    """B3: distance-weighted sum of recent events (or amounts) within 5 km, summed over years."""
    total = np.nansum(events_khw, axis=0) if events_khw.ndim == 3 else events_khw
    return convolve(np.nan_to_num(total), proximity_kernel(), mode="constant", cval=0.0)


def great_circle_next(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """B1: continue the movement from ``a`` to ``b`` on the sphere: ``2 (a.b) b - a``."""
    ab = np.einsum("chw,chw->hw", a, b)
    return 2 * ab[None] * b - a


def _nan_mean_filter(x: np.ndarray, size: int) -> np.ndarray:
    ok = np.isfinite(x)
    s = uniform_filter(np.where(ok, x, 0.0), size=size, mode="constant")
    n = uniform_filter(ok.astype(np.float64), size=size, mode="constant")
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(n > 0, s / n, np.nan)


def _nan_max_filter(x: np.ndarray, size: int) -> np.ndarray:
    m = maximum_filter(np.where(np.isfinite(x), x, -np.inf), size=size, mode="constant", cval=-np.inf)
    return np.where(np.isfinite(m), m, np.nan)


@dataclass
class TileExamples:
    rows: np.ndarray  # flat cell index of each example
    y: np.ndarray  # bool
    scores: dict[str, np.ndarray] = field(default_factory=dict)  # B0..B3 raw scores
    features: np.ndarray | None = None  # float32 [n, F] for B4
    feature_names: list[str] = field(default_factory=list)


def _layer(arr: np.ndarray, index: int) -> np.ndarray | None:
    return arr[index] if 0 <= index < arr.shape[0] else None


def tile_examples(
    cube: TileCube, target: int, task: str, rule: ChangeRule, with_features: bool = True
) -> TileExamples:
    if task not in TASKS:
        raise ValueError(task)
    assert cube.forest_start is not None and cube.forest_lost is not None
    side = cube.land.shape[0]
    issue = target - 1  # last year whose data may be used
    vi = YEARS.index(issue)
    lab = target - 2018  # label index of the target year

    # Eligibility and truth.
    elig = (cube.land >= LAND_MIN) & cube.valid[vi]
    if task == "forest":
        elig &= cube.forest_start[lab] >= FOREST_MIN
        truth = cube.forest_lost[lab] >= LOSS_EVENT
    else:
        elig &= cube.valid[YEARS.index(target)]
        truth = rule.events(cube, target)
    rows = np.flatnonzero(elig.ravel())
    ex = TileExamples(rows, truth.ravel()[rows])

    # Past change (pairs ending at or before the issue year).
    pair = issue - YEARS[1]
    d = [_layer(cube.delta, pair - k) for k in range(3)]
    d = [x if x is not None else np.full((side, side), np.nan, np.float32) for x in d]
    z1 = history_z(cube.delta[: pair + 1])[pair] if pair >= 0 else np.full((side, side), np.nan)

    # Past forest loss (label years up to the issue year).
    lost = [_layer(cube.forest_lost, issue - 2018 - k) for k in range(PROXIMITY_YEARS)]
    lost = [x if x is not None else np.full((side, side), np.nan, np.float32) for x in lost]
    recent_loss = np.nansum(np.stack(lost), axis=0)
    cum_loss = cube.loss_before + cube.loss[: max(issue - 2018 + 1, 0)].sum(axis=0)

    # Past embedding events (rule of task 1.8) for the embedding task's proximity baseline.
    ev = []
    for k in range(PROXIMITY_YEARS):
        end = issue - k
        if end >= YEARS[1]:
            ev.append(rule.events(cube, end).astype(np.float32))
    events_recent = np.sum(ev, axis=0) if ev else np.zeros((side, side), np.float32)

    # Baselines B0..B3.
    b = cube.embedding(issue)
    if vi >= 1:
        a = cube.embedding(issue - 1)
        pred = great_circle_next(a, b)
        pred /= np.maximum(np.linalg.norm(pred, axis=0, keepdims=True), 1e-6)
        b1 = 1.0 - np.einsum("chw,chw->hw", b, pred)
    else:
        b1 = np.full((side, side), np.nan)
    prox = proximity(recent_loss) if task == "forest" else proximity(events_recent)
    flat = {
        "B0": np.zeros(side * side),
        "B1": np.nan_to_num(b1, nan=0.0).ravel(),
        "B2": np.nan_to_num(d[0], nan=0.0).ravel(),
        "B3": prox.ravel(),
    }
    ex.scores = {k: v[rows].astype(np.float64) for k, v in flat.items()}
    if not with_features:
        return ex

    cols: dict[str, np.ndarray] = {}
    for k in range(3):
        cols[f"delta_{k + 1}"] = d[k]
    cols["z_1"] = z1
    for r in RADII:
        cols[f"delta_1_mean_{r}"] = _nan_mean_filter(d[0], r)
        cols[f"delta_1_max_{r}"] = _nan_max_filter(d[0], r)
    for k in range(3):
        cols[f"forest_lost_{k + 1}"] = lost[k]
    cols["loss_before_2018"] = cube.loss_before
    cols["loss_cumulative"] = cum_loss
    for r in RADII:
        cols[f"recent_loss_mean_{r}"] = uniform_filter(recent_loss, size=r, mode="constant")
        cols[f"recent_loss_max_{r}"] = maximum_filter(recent_loss, size=r, mode="constant")
        cols[f"events_mean_{r}"] = uniform_filter(events_recent, size=r, mode="constant")
    cols["proximity_loss"] = proximity(recent_loss)
    cols["proximity_events"] = proximity(events_recent)
    cols["forest_start"] = cube.forest_start[lab]
    cols["land"] = cube.land
    names = list(cols)
    feat = np.stack([np.asarray(cols[n], dtype=np.float32).ravel()[rows] for n in names], axis=1)
    emb = b.reshape(64, -1)[:, rows].T.astype(np.float32)
    ex.features = np.concatenate([feat, emb], axis=1)
    ex.feature_names = names + [f"emb_{i}" for i in range(64)]
    return ex
