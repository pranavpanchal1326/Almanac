"""Whole-tile prediction and scoring with the same cells and metrics as the baselines.

A tile is predicted with overlapping patches (the training patch size, stride half a patch). Each
cell takes its value from the window in which it lies furthest from an edge, so cells are seen
with neighbours on all sides wherever the tile allows, as in training.
"""

from __future__ import annotations

import numpy as np
import torch

from almanac.model.data import DataConfig, PatchSpec, make_example
from almanac.model.net import Forecaster
from almanac.model.store import SIDE, TileStore, embedding_eligible, forest_eligible, forest_event

KEYS = ("emb", "valid", "year_scalars", "static")


def _windows(patch: int) -> list[int]:
    stride = patch // 2
    starts = list(range(0, SIDE - patch + 1, stride))
    if starts[-1] != SIDE - patch:
        starts.append(SIDE - patch)
    return starts


def _centrality(patch: int) -> np.ndarray:
    i = np.arange(patch)
    d = np.minimum(i, patch - 1 - i)
    return np.minimum(d[:, None], d[None, :]).astype(np.float32)


@torch.no_grad()
def predict_tile(
    net: Forecaster, store: TileStore, target: int, cfg: DataConfig, device: str, batch: int = 16
) -> dict[str, np.ndarray]:
    """Logits ``[SIDE, SIDE]`` for the forest and change heads."""
    net.eval()
    p = cfg.patch
    starts = _windows(p)
    specs = [PatchSpec(0, target, r, c, 0, False, 0, -1) for r in starts for c in starts]
    best = np.full((SIDE, SIDE), -1.0, np.float32)
    out = {"forest": np.zeros((SIDE, SIDE), np.float32), "change": np.zeros((SIDE, SIDE), np.float32)}
    cent = _centrality(p)
    for i in range(0, len(specs), batch):
        chunk = specs[i : i + batch]
        exs = [make_example(store, s, cfg, truth=False) for s in chunk]  # inputs only
        b = {k: torch.from_numpy(np.stack([e[k] for e in exs])).to(device) for k in KEYS}
        with torch.autocast(device_type="cuda", dtype=torch.bfloat16, enabled=device == "cuda"):
            res = net(b)
        f = res["forest"].float().cpu().numpy()
        c = res["change"].float().cpu().numpy()
        for j, s in enumerate(chunk):
            rs, cs = slice(s.row, s.row + p), slice(s.col, s.col + p)
            take = cent > best[rs, cs]
            best[rs, cs] = np.where(take, cent, best[rs, cs])
            out["forest"][rs, cs] = np.where(take, f[j], out["forest"][rs, cs])
            out["change"][rs, cs] = np.where(take, c[j], out["change"][rs, cs])
    return out


def tile_scores(store: TileStore, logits: dict[str, np.ndarray], target: int, task: str):
    """Eligible cell indices (flat, as the baselines order them), truth, and logits."""
    aux = np.asarray(store.aux)
    if task == "forest":
        elig, truth, z = forest_eligible(aux, target), forest_event(aux, target), logits["forest"]
    else:
        from almanac.model.store import AUX

        elig = embedding_eligible(aux, target)
        truth = aux[AUX[f"emb_event_{target}"]] > 0
        z = logits["change"]
    rows = np.flatnonzero(elig.ravel())
    return rows, truth.ravel()[rows], z.ravel()[rows]
