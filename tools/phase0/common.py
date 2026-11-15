"""Shared helpers for the Phase 0 scripts: paths, sites, block lookup."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from pyproj import Transformer

from almanac.common.constants import YEARS
from almanac.grid.ids import TileRef, block_bounds_utm, block_for_utm, block_id
from almanac.io.index import files_for_point

REPO = Path(__file__).resolve().parents[2]
DATA = Path("D:/almanac-data")
INDEX = DATA / "index" / "aef_index.parquet"
WORK = DATA / "work" / "phase0"
RAW = WORK / "blocks"
IMAGERY = WORK / "imagery"
DOCS = REPO / "docs" / "phase0"
FIGURES = DOCS / "figures"
SITES_FILE = REPO / "configs" / "phase0" / "sites.json"


@dataclass(frozen=True)
class Site:
    name: str
    role: str
    type: str
    lon: float
    lat: float
    imagery_months: tuple[int, ...]
    tile: TileRef
    block_row: int
    block_col: int
    urls: dict[int, str]  # year -> https address of the raw file

    @property
    def block_id(self) -> str:
        return block_id(self.tile, self.block_row, self.block_col)

    @property
    def bounds_utm(self) -> tuple[float, float, float, float]:
        return block_bounds_utm(self.tile, self.block_row, self.block_col)

    def block_path(self, year: int) -> Path:
        return RAW / self.name / f"{self.block_id}_{year}.npy"

    def load_years(self) -> np.ndarray:
        """Stored int8 values for all years, ``[T, 64, 1024, 1024]``."""
        return np.stack([np.load(self.block_path(y)) for y in YEARS])


def load_sites(roles: tuple[str, ...] | None = None) -> list[Site]:
    spec = json.loads(SITES_FILE.read_text())["sites"]
    sites: list[Site] = []
    for s in spec:
        if roles and s["role"] not in roles:
            continue
        rows = files_for_point(INDEX, s["lon"], s["lat"])
        chosen: Site | None = None
        for tile in sorted({r.tile for r in rows}, key=lambda t: t.tile_id):
            e, n = Transformer.from_crs(4326, tile.epsg, always_xy=True).transform(s["lon"], s["lat"])
            if tile.utm_west <= e < tile.utm_east and tile.utm_south <= n < tile.utm_north:
                row, col = block_for_utm(tile, e, n)
                urls = {r.year: r.url for r in rows if r.tile == tile}
                chosen = Site(
                    s["name"],
                    s["role"],
                    s["type"],
                    s["lon"],
                    s["lat"],
                    tuple(s["imagery_months"]),
                    tile,
                    row,
                    col,
                    urls,
                )
                break
        if chosen is None:
            raise LookupError(f"no tile contains site {s['name']}")
        sites.append(chosen)
    return sites
