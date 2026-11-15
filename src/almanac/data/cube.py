"""Everything known about one tile at 640 m, loaded from the region store.

Index conventions (all arrays north-up, ``side`` x ``side`` cells):

- ``YEARS`` = 2017..2025: embeddings and validity, index ``t - 2017``.
- Change pairs: ``delta[i]`` is the change from ``YEARS[i]`` to ``YEARS[i + 1]``, so ``delta[i]``
  ends in year ``2018 + i``.
- Label years 2018..2025: ``loss[i]``, ``forest_lost[i]`` are for year ``2018 + i``;
  ``forest_start[i]`` is forest at the start of ``2018 + i`` (2018..2026, nine values).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from almanac.common.constants import YEARS
from almanac.data.stream import decode_delta, embedding_path, load_summary, summary_path
from almanac.grid.ids import TileRef, parse_tile_id
from almanac.quality.embedding import dequantize, renormalize

DATA = Path("D:/almanac-data")
LEVEL = 6
LABEL_YEARS: tuple[int, ...] = tuple(range(2018, 2026))


@dataclass
class TileCube:
    tile: TileRef
    valid: np.ndarray  # bool [9, H, W]
    delta: np.ndarray  # float32 [8, H, W], NaN where either year is invalid
    loss: np.ndarray  # float32 [8, H, W], share of the cell lost in 2018..2025 (any tree cover)
    loss_before: np.ndarray  # float32 [H, W], share lost 2001..2017
    land: np.ndarray  # float32 [H, W]
    forest_start: np.ndarray | None = None  # float32 [9, H, W], 2018..2026
    forest_lost: np.ndarray | None = None  # float32 [8, H, W], 2018..2025
    stored: np.ndarray | None = None  # int8 [9, 64, H, W]; years missing from the store are NODATA

    def embedding(self, year: int) -> np.ndarray:
        """Unit-length float32 ``[64, H, W]`` for one year. Invalid cells hold garbage; mask them."""
        if self.stored is None:
            raise ValueError("cube loaded without embeddings")
        return renormalize(dequantize(self.stored[YEARS.index(year)]))


def load_cube(tile_id: str, *, embeddings: bool = False, forest: bool = True, data: Path = DATA) -> TileCube:
    tile = parse_tile_id(tile_id)
    s = load_summary(summary_path(data / "summaries", LEVEL, tile))
    delta, _ = decode_delta(s["delta_code"])
    with np.load(data / "labels" / "forest_loss" / f"L{LEVEL}" / tile.utm_zone / f"{tile_id}.npz") as f:
        loss = f["loss_share"].astype(np.float32)
        loss_before = f["loss_before"].astype(np.float32)
        land = f["land_share"].astype(np.float32)
    cube = TileCube(tile, s["valid"], delta, loss, loss_before, land)
    if forest:
        with np.load(data / "labels" / "forest" / f"L{LEVEL}" / tile.utm_zone / f"{tile_id}.npz") as f:
            cube.forest_start = f["forest_start"].astype(np.float32)
            cube.forest_lost = f["forest_lost"].astype(np.float32)
    if embeddings:
        with np.load(embedding_path(data / "embeddings", LEVEL, tile)) as f:
            stored, years = f["stored"], [int(y) for y in f["years"]]
        full = np.full((len(YEARS), *stored.shape[1:]), -128, dtype=np.int8)
        for i, y in enumerate(years):
            full[YEARS.index(y)] = stored[i]
        cube.stored = full
    return cube
