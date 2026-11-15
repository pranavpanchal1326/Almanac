"""Spatial split of a region's tiles (task 1.7).

Tiles are grouped into super-blocks of ``block_deg`` x ``block_deg`` degrees by their centre. Each
super-block goes to train, validation or test by a seeded hash, so the assignment never depends
on the order of the input. One named sub-region is held out of training entirely. Any training
tile whose footprint touches a validation, test or held-out tile is set aside as a buffer, so no
scored tile shares an edge with a training tile.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass

from almanac.grid.ids import TileRef

Box = tuple[float, float, float, float]  # west, south, east, north in WGS 84

TRAIN, VALIDATION, TEST, HELD_OUT, BUFFER = "train", "validation", "test", "held_out", "buffer"


@dataclass(frozen=True)
class SplitConfig:
    seed: str
    block_deg: float
    train_share: float
    validation_share: float
    held_out_box: Box
    touch_margin_deg: float = 0.01  # footprints closer than this count as touching


def super_block(box: Box, block_deg: float) -> str:
    lon = (box[0] + box[2]) / 2
    lat = (box[1] + box[3]) / 2
    return f"{math.floor(lat / block_deg) * block_deg:+.0f}_{math.floor(lon / block_deg) * block_deg:+.0f}"


def _unit_hash(seed: str, key: str) -> float:
    digest = hashlib.sha256(f"{seed}:{key}".encode()).digest()
    return int.from_bytes(digest[:8], "big") / 2**64


def _centre_in(box: Box, region: Box) -> bool:
    lon, lat = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    return region[0] <= lon < region[2] and region[1] <= lat < region[3]


def boxes_touch(a: Box, b: Box, margin: float) -> bool:
    return a[0] <= b[2] + margin and b[0] <= a[2] + margin and a[1] <= b[3] + margin and b[1] <= a[3] + margin


def assign(footprints: dict[TileRef, Box], config: SplitConfig) -> dict[TileRef, tuple[str, str]]:
    """Map every tile to (super-block, split)."""
    first: dict[TileRef, tuple[str, str]] = {}
    for tile, box in footprints.items():
        block = super_block(box, config.block_deg)
        if _centre_in(box, config.held_out_box):
            split = HELD_OUT
        else:
            u = _unit_hash(config.seed, block)
            split = (
                TRAIN
                if u < config.train_share
                else VALIDATION
                if u < config.train_share + config.validation_share
                else TEST
            )
        first[tile] = (block, split)

    scored = [footprints[t] for t, (_, s) in first.items() if s != TRAIN]
    # Coarse grid index over scored boxes keeps the neighbour search cheap.
    cell = 2.0
    grid: dict[tuple[int, int], list[Box]] = {}
    for box in scored:
        for gx in range(math.floor(box[0] / cell) - 1, math.floor(box[2] / cell) + 2):
            for gy in range(math.floor(box[1] / cell) - 1, math.floor(box[3] / cell) + 2):
                grid.setdefault((gx, gy), []).append(box)

    out: dict[TileRef, tuple[str, str]] = {}
    for tile, (block, split) in first.items():
        if split == TRAIN:
            box = footprints[tile]
            key = (math.floor((box[0] + box[2]) / 2 / cell), math.floor((box[1] + box[3]) / 2 / cell))
            if any(boxes_touch(box, other, config.touch_margin_deg) for other in grid.get(key, [])):
                split = BUFFER
        out[tile] = (block, split)
    return out
