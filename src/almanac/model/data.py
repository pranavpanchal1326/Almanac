"""Task 2.1: patches for training and the balanced, seeded sampler.

An example is one tile, one target year ``Y`` and one square patch. Inputs use only what is known
at issue time (end of ``Y - 1``): embeddings of the last ``K`` years up to ``Y - 1``, forest loss
in those years, forest at the start of ``Y``, land share and loss before 2018. Targets are forest
loss in ``Y`` (primary), the embedding change event ending in ``Y``, and the embedding of ``Y``.

Sampling (blueprint 15.6): a share ``positive_share`` of each draw comes from patches with at least
one forest-loss event in the target year; the rest is uniform over patches with any eligible
forest cell. Everything is drawn from a generator seeded by ``(seed, epoch)``, so a given seed and
epoch always yield the same examples in the same order.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from almanac.common.constants import YEARS
from almanac.model.store import (
    AUX,
    SIDE,
    TileStore,
    embedding_eligible,
    forest_eligible,
    forest_event,
)

N_YEAR_SCALARS = 3  # forest lost that year, any loss that year, whether that year's label exists
N_STATIC = 4  # forest at the start of Y, land share, loss before 2018, cumulative loss to Y - 1


@dataclass(frozen=True)
class DataConfig:
    patch: int = 32
    history: int = 5  # K
    grid_stride: int = 16  # candidate patch origins
    jitter: int = 8  # random shift of a patch origin, in cells
    positive_share: float = 0.5
    truncate_prob: float = 0.5  # chance of hiding a random number of the earliest years
    mask_year_prob: float = 0.15  # chance of hiding one random year
    augment: bool = True  # flips and quarter turns


@dataclass(frozen=True)
class PatchSpec:
    tile: int
    target: int
    row: int
    col: int
    rot: int  # quarter turns
    flip: bool
    hide_first: int  # earliest years hidden
    hide_one: int  # index of one hidden year, or -1


@dataclass
class PatchIndex:
    """Candidate patches per tile and target year, with counts used by the sampler."""

    tiles: list[str]
    tile: np.ndarray = field(default_factory=lambda: np.empty(0, np.int32))
    target: np.ndarray = field(default_factory=lambda: np.empty(0, np.int16))
    row: np.ndarray = field(default_factory=lambda: np.empty(0, np.int16))
    col: np.ndarray = field(default_factory=lambda: np.empty(0, np.int16))
    eligible: np.ndarray = field(default_factory=lambda: np.empty(0, np.int32))
    events: np.ndarray = field(default_factory=lambda: np.empty(0, np.int32))

    @classmethod
    def build(cls, tiles: list[str], targets: list[int], cfg: DataConfig, root=None) -> PatchIndex:
        cols: dict[str, list[int]] = {k: [] for k in ("tile", "target", "row", "col", "eligible", "events")}
        origins = range(0, SIDE - cfg.patch + 1, cfg.grid_stride)
        for t, tid in enumerate(tiles):
            store = TileStore.open(tid) if root is None else TileStore.open(tid, root)
            aux = np.asarray(store.aux)
            for y in targets:
                elig = forest_eligible(aux, y)
                ev = forest_event(aux, y) & elig
                for r in origins:
                    for c in origins:
                        n = int(elig[r : r + cfg.patch, c : c + cfg.patch].sum())
                        if n == 0:
                            continue
                        cols["tile"].append(t)
                        cols["target"].append(y)
                        cols["row"].append(r)
                        cols["col"].append(c)
                        cols["eligible"].append(n)
                        cols["events"].append(int(ev[r : r + cfg.patch, c : c + cfg.patch].sum()))
        idx = cls(tiles)
        idx.tile = np.array(cols["tile"], np.int32)
        idx.target = np.array(cols["target"], np.int16)
        idx.row = np.array(cols["row"], np.int16)
        idx.col = np.array(cols["col"], np.int16)
        idx.eligible = np.array(cols["eligible"], np.int32)
        idx.events = np.array(cols["events"], np.int32)
        return idx


class BalancedSampler:
    """Draws ``PatchSpec``s; the same ``(seed, epoch)`` always gives the same list."""

    def __init__(self, index: PatchIndex, cfg: DataConfig, seed: int):
        self.index = index
        self.cfg = cfg
        self.seed = seed
        self.positive = np.flatnonzero(index.events > 0)
        self.uniform = np.arange(index.tile.size)
        if self.positive.size == 0:
            raise ValueError("no patch with a forest-loss event")

    def draw(self, n: int, epoch: int) -> list[PatchSpec]:
        cfg = self.cfg
        rng = np.random.default_rng([self.seed, epoch])
        n_pos = round(n * cfg.positive_share)
        picks = np.concatenate([rng.choice(self.positive, n_pos), rng.choice(self.uniform, n - n_pos)])
        rng.shuffle(picks)
        out = []
        hi = SIDE - cfg.patch
        for i in picks:
            r = int(np.clip(self.index.row[i] + rng.integers(-cfg.jitter, cfg.jitter + 1), 0, hi))
            c = int(np.clip(self.index.col[i] + rng.integers(-cfg.jitter, cfg.jitter + 1), 0, hi))
            hide_first = int(rng.integers(0, cfg.history)) if rng.random() < cfg.truncate_prob else 0
            hide_one = int(rng.integers(0, cfg.history)) if rng.random() < cfg.mask_year_prob else -1
            out.append(
                PatchSpec(
                    tile=int(self.index.tile[i]),
                    target=int(self.index.target[i]),
                    row=r,
                    col=c,
                    rot=int(rng.integers(0, 4)) if cfg.augment else 0,
                    flip=bool(rng.integers(0, 2)) if cfg.augment else False,
                    hide_first=hide_first,
                    hide_one=hide_one,
                )
            )
        return out


def history_years(target: int, k: int) -> list[int]:
    """The ``k`` years before ``target``, oldest first; years before 2017 are kept as placeholders."""
    return list(range(target - k, target))


def make_example(
    store: TileStore, spec: PatchSpec, cfg: DataConfig, truth: bool = True
) -> dict[str, np.ndarray]:
    """Arrays for one patch. Spatial arrays end in ``[P, P]``; nothing from ``spec.target`` or later
    enters an input. With ``truth=False`` the target year's labels are not read at all (forecasts
    and stage B), and only the inputs are returned."""
    p, k = cfg.patch, cfg.history
    rs, cs = slice(spec.row, spec.row + p), slice(spec.col, spec.col + p)
    aux = np.asarray(store.aux[:, rs, cs], dtype=np.float32)
    emb = np.full((k, 64, p, p), -128, dtype=np.int8)
    valid = np.zeros((k, p, p), dtype=bool)
    scal = np.zeros((k, N_YEAR_SCALARS, p, p), dtype=np.float32)
    present = np.zeros(k, dtype=bool)
    for j, year in enumerate(history_years(spec.target, k)):
        if year < YEARS[0] or j < spec.hide_first or j == spec.hide_one:
            continue
        v = aux[AUX[f"valid_{year}"]] > 0
        if not v.any():
            continue
        emb[j] = store.emb[YEARS.index(year), :, rs, cs]
        valid[j] = v
        present[j] = True
        if year >= 2018:
            scal[j, 0] = aux[AUX[f"forest_lost_{year}"]]
            scal[j, 1] = aux[AUX[f"loss_{year}"]]
            scal[j, 2] = 1.0
    cum = aux[AUX["loss_before_2018"]].copy()
    for year in range(2018, spec.target):
        cum += aux[AUX[f"loss_{year}"]]
    static = np.stack(
        [aux[AUX[f"forest_start_{spec.target}"]], aux[AUX["land"]], aux[AUX["loss_before_2018"]], cum]
    ).astype(np.float32)

    if not truth:
        ex = {"emb": emb, "valid": valid, "year_scalars": scal, "static": static}
        if spec.rot or spec.flip:
            ex = {key: _orient(val, spec.rot, spec.flip) for key, val in ex.items()}
        ex["present"] = present
        return ex

    full_aux = aux  # already cropped
    y_forest = forest_event(full_aux, spec.target).astype(np.float32)
    m_forest = forest_eligible(full_aux, spec.target)
    y_change = full_aux[AUX[f"emb_event_{spec.target}"]].astype(np.float32)
    m_change = embedding_eligible(full_aux, spec.target)
    y_emb = np.asarray(store.emb[YEARS.index(spec.target), :, rs, cs]) if spec.target in YEARS else None
    if y_emb is None:
        y_emb = np.full((64, p, p), -128, dtype=np.int8)
    m_emb = (y_emb != -128).all(axis=0)

    ex = {
        "emb": emb,
        "valid": valid,
        "year_scalars": scal,
        "static": static,
        "y_forest": y_forest,
        "m_forest": m_forest,
        "y_change": y_change,
        "m_change": m_change,
        "y_emb": y_emb,
        "m_emb": m_emb,
    }
    if spec.rot or spec.flip:
        ex = {key: _orient(val, spec.rot, spec.flip) for key, val in ex.items()}
    ex["present"] = present
    return ex


def _orient(a: np.ndarray, rot: int, flip: bool) -> np.ndarray:
    a = np.rot90(a, rot, axes=(-2, -1))
    if flip:
        a = a[..., ::-1]
    return np.ascontiguousarray(a)
