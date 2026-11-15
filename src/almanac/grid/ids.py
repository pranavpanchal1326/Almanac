"""Tile and block identifiers, and the arithmetic between coordinates and blocks.

Phase 0 finding: the supplier's image id changes every year for the same footprint, so it cannot
name a tile across years. A tile is therefore named by its UTM zone and its south-west corner,
which are identical in every year of the index.

Block rows count from the north (row 0 is the northernmost), matching a north-up array.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from almanac.common.constants import BLOCK, BLOCKS_PER_SIDE, CELL_M, TILE

_TILE_RE = re.compile(r"^(\d{1,2}[NS])_E(\d+)_N(\d+)$")
_BLOCK_RE = re.compile(r"^(.+)_b(\d)_(\d)$")


@dataclass(frozen=True)
class TileRef:
    """One tile footprint: UTM zone plus south-west corner in metres."""

    utm_zone: str
    utm_west: int
    utm_south: int

    @property
    def tile_id(self) -> str:
        return f"{self.utm_zone}_E{self.utm_west}_N{self.utm_south}"

    @property
    def utm_north(self) -> int:
        return self.utm_south + int(TILE * CELL_M)

    @property
    def utm_east(self) -> int:
        return self.utm_west + int(TILE * CELL_M)

    @property
    def epsg(self) -> int:
        zone = int(self.utm_zone[:-1])
        return (32600 if self.utm_zone.endswith("N") else 32700) + zone


def parse_tile_id(tile_id: str) -> TileRef:
    m = _TILE_RE.match(tile_id)
    if not m:
        raise ValueError(f"not a tile id: {tile_id!r}")
    return TileRef(m.group(1), int(m.group(2)), int(m.group(3)))


def block_id(tile: TileRef, block_row: int, block_col: int) -> str:
    _check_block(block_row, block_col)
    return f"{tile.tile_id}_b{block_row}_{block_col}"


def parse_block_id(value: str) -> tuple[TileRef, int, int]:
    m = _BLOCK_RE.match(value)
    if not m:
        raise ValueError(f"not a block id: {value!r}")
    row, col = int(m.group(2)), int(m.group(3))
    _check_block(row, col)
    return parse_tile_id(m.group(1)), row, col


def block_for_utm(tile: TileRef, easting: float, northing: float) -> tuple[int, int]:
    """Block (row, col), north-up, of the tile that contains a UTM coordinate."""
    col = int((easting - tile.utm_west) // (BLOCK * CELL_M))
    row = int((tile.utm_north - northing) // (BLOCK * CELL_M))
    _check_block(row, col)
    return row, col


def block_bounds_utm(tile: TileRef, block_row: int, block_col: int) -> tuple[float, float, float, float]:
    """(west, south, east, north) of a block in the tile's UTM zone, metres."""
    _check_block(block_row, block_col)
    side = BLOCK * CELL_M
    west = tile.utm_west + block_col * side
    north = tile.utm_north - block_row * side
    return west, north - side, west + side, north


def _check_block(block_row: int, block_col: int) -> None:
    if not (0 <= block_row < BLOCKS_PER_SIDE and 0 <= block_col < BLOCKS_PER_SIDE):
        raise ValueError(f"block ({block_row}, {block_col}) outside 0..{BLOCKS_PER_SIDE - 1}")
