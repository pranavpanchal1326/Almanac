"""Forest-loss label on the tile grid (task 1.4).

Source: Global Forest Change v1.13 "lossyear" (Hansen/UMD/Google/USGS/NASA, CC-BY 4.0): 30 m
cells in geographic coordinates, value 0 for no loss and 1..25 for the year of loss, 2001..2025.

For one tile the source is sampled, nearest neighbour, onto a grid of ``sub`` x ``sub`` points
inside every coarse cell of the tile. The label is the share of those points lost in each year.
With a 640 m cell and ``sub`` = 20 the points are 32 m apart, close to the source's own spacing.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.vrt import WarpedVRT
from rasterio.warp import transform_bounds

from almanac.common.constants import CELL_M, TILE
from almanac.grid.ids import TileRef

GFC_VERSION = "GFC-2025-v1.13"
GFC_FIRST_YEAR = 2001  # value 1 in the source
GFC_LAST_YEAR = 2025


def gfc_tile_name(layer: str, lat_top: int, lon_left: int) -> str:
    """File name of the 10-degree source tile whose top-left corner is (lat_top, lon_left)."""
    lat = f"{abs(lat_top):02d}{'N' if lat_top >= 0 else 'S'}"
    lon = f"{abs(lon_left):03d}{'E' if lon_left >= 0 else 'W'}"
    return f"Hansen_{GFC_VERSION}_{layer}_{lat}_{lon}.tif"


def gfc_tiles_for_bounds(layer: str, west: float, south: float, east: float, north: float) -> list[str]:
    """Names of the source tiles that overlap a WGS 84 box."""
    names = []
    lat_top = int(np.ceil(north / 10.0) * 10)
    while lat_top > south:
        lon_left = int(np.floor(west / 10.0) * 10)
        while lon_left < east:
            names.append(gfc_tile_name(layer, lat_top, lon_left))
            lon_left += 10
        lat_top -= 10
    return names


def sample_source_on_tile(
    tile: TileRef, level: int, sub: int, source_dir: Path, layer: str = "lossyear"
) -> np.ndarray:
    """Source values on the tile's fine sampling grid, north-up, uint8 ``[side*sub, side*sub]``.

    Points outside every source tile on disk read as 0. A missing source file that should cover
    the tile is an error.
    """
    side = TILE >> level
    step = CELL_M * (1 << level) / sub
    n = side * sub
    crs = CRS.from_epsg(tile.epsg)
    transform = from_origin(tile.utm_west, tile.utm_north, step, step)
    bounds = transform_bounds(
        crs, CRS.from_epsg(4326), tile.utm_west, tile.utm_south, tile.utm_east, tile.utm_north, densify_pts=21
    )
    out = np.zeros((n, n), dtype=np.uint8)
    for name in gfc_tiles_for_bounds(layer, *bounds):
        path = source_dir / name
        if not path.exists():
            raise FileNotFoundError(f"label source tile missing for {tile.tile_id}: {path}")
        with (
            rasterio.open(path) as src,
            WarpedVRT(
                src,
                crs=crs,
                transform=transform,
                width=n,
                height=n,
                resampling=Resampling.nearest,
                src_nodata=None,
                nodata=None,
            ) as vrt,
        ):
            # Outside a source tile the warp leaves 0, so the maximum merges neighbouring tiles.
            np.maximum(out, vrt.read(1), out=out)
    return out


def loss_share_by_year(lossyear_fine: np.ndarray, sub: int, years: Sequence[int]) -> np.ndarray:
    """Share of each coarse cell lost in each year: float32 ``[len(years), side, side]``."""
    n = lossyear_fine.shape[0]
    if lossyear_fine.shape != (n, n) or n % sub:
        raise ValueError("fine grid must be square with a side that is a multiple of sub")
    side = n // sub
    blocks = lossyear_fine.reshape(side, sub, side, sub)
    out = np.empty((len(years), side, side), dtype=np.float32)
    for i, year in enumerate(years):
        if not GFC_FIRST_YEAR <= year <= GFC_LAST_YEAR:
            raise ValueError(f"year {year} outside the source's range")
        out[i] = (blocks == year - GFC_FIRST_YEAR + 1).mean(axis=(1, 3))
    return out


#: Tree cover in 2000 at or above this percentage makes a source point forest (the producer's and
#: Global Forest Watch's usual definition).
FOREST_COVER_PCT = 30


def forest_by_year(
    lossyear_fine: np.ndarray,
    cover_fine: np.ndarray,
    sub: int,
    years: Sequence[int],
    cover_pct: int = FOREST_COVER_PCT,
) -> tuple[np.ndarray, np.ndarray]:
    """Forest at the start of each year and forest lost during it, as shares of each coarse cell.

    A source point is forest at the start of year ``Y`` if its tree cover in 2000 was at least
    ``cover_pct`` and it had not been lost in any year before ``Y``. Gain is ignored, as the source
    does not date it. Returns two float32 arrays ``[len(years), side, side]``: ``start`` and
    ``lost`` (points that were forest at the start of ``Y`` and are lost in ``Y``).
    """
    n = lossyear_fine.shape[0]
    if lossyear_fine.shape != (n, n) or cover_fine.shape != (n, n) or n % sub:
        raise ValueError("fine grids must be square, equal, with a side that is a multiple of sub")
    side = n // sub
    forest2000 = cover_fine >= cover_pct
    start = np.empty((len(years), side, side), dtype=np.float32)
    lost = np.empty((len(years), side, side), dtype=np.float32)
    for i, year in enumerate(years):
        if not GFC_FIRST_YEAR <= year <= GFC_LAST_YEAR + 1:
            raise ValueError(f"year {year} outside the source's range")
        code = year - GFC_FIRST_YEAR + 1
        standing = forest2000 & ((lossyear_fine == 0) | (lossyear_fine >= code))
        start[i] = standing.reshape(side, sub, side, sub).mean(axis=(1, 3))
        lost[i] = (standing & (lossyear_fine == code)).reshape(side, sub, side, sub).mean(axis=(1, 3))
    return start, lost


def cumulative_loss_share(lossyear_fine: np.ndarray, sub: int, through_year: int) -> np.ndarray:
    """Share of each coarse cell lost in any year from 2001 through ``through_year``."""
    n = lossyear_fine.shape[0]
    side = n // sub
    code = through_year - GFC_FIRST_YEAR + 1
    lost = (lossyear_fine >= 1) & (lossyear_fine <= code)
    return lost.reshape(side, sub, side, sub).mean(axis=(1, 3)).astype(np.float32)
