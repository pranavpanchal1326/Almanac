from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from almanac.data.labels import (
    cumulative_loss_share,
    gfc_tile_name,
    gfc_tiles_for_bounds,
    loss_share_by_year,
    sample_source_on_tile,
)
from almanac.grid.ids import TileRef


def test_source_tile_names() -> None:
    assert gfc_tile_name("lossyear", 0, -60) == "Hansen_GFC-2025-v1.13_lossyear_00N_060W.tif"
    assert gfc_tile_name("lossyear", -10, -60).endswith("_10S_060W.tif")
    assert gfc_tile_name("datamask", 10, 100).endswith("_10N_100E.tif")


def test_tiles_for_bounds_follow_top_left_naming() -> None:
    inside = gfc_tiles_for_bounds("lossyear", -55.9, -7.5, -55.1, -7.0)
    assert inside == [gfc_tile_name("lossyear", 0, -60)]
    across = gfc_tiles_for_bounds("lossyear", -60.2, -0.3, -59.8, 0.3)
    assert {n[-12:-4] for n in across} == {"10N_070W", "10N_060W", "00N_070W", "00N_060W"}


def test_loss_share_counts_each_year_once() -> None:
    fine = np.zeros((4, 4), dtype=np.uint8)
    fine[0, 0] = 18  # 2018
    fine[0, 1] = 18
    fine[1, 0] = 20  # 2020
    fine[2:, 2:] = 5  # 2005, all of the last coarse cell
    share = loss_share_by_year(fine, sub=2, years=[2018, 2019, 2020])
    assert share.shape == (3, 2, 2)
    np.testing.assert_allclose(share[:, 0, 0], [0.5, 0.0, 0.25])
    assert share[:, 1, 1].sum() == 0
    np.testing.assert_allclose(cumulative_loss_share(fine, 2, 2017), [[0, 0], [0, 1]])
    np.testing.assert_allclose(cumulative_loss_share(fine, 2, 2020), [[0.75, 0], [0, 1]])
    with pytest.raises(ValueError):
        loss_share_by_year(fine, sub=2, years=[1999])


def test_sampling_places_loss_at_the_right_cell_north_up(tmp_path: Path) -> None:
    # A synthetic 10-degree source tile at coarse resolution with one marked spot.
    tile = TileRef("21S", 581920, 9180800)  # near 7 S, 55.7 W
    res = 0.01
    data = np.zeros((1000, 1000), dtype=np.uint8)
    lon, lat = -55.80, -7.10  # inside the tile
    data[int((0 - lat) / res), int((lon + 60) / res)] = 22
    path = tmp_path / gfc_tile_name("lossyear", 0, -60)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=1000,
        height=1000,
        count=1,
        dtype="uint8",
        crs="EPSG:4326",
        transform=from_origin(-60, 0, res, res),
    ) as dst:
        dst.write(data, 1)

    fine = sample_source_on_tile(tile, level=6, sub=4, source_dir=tmp_path)
    assert fine.shape == (512, 512)
    rows, cols = np.nonzero(fine == 22)
    assert rows.size > 0

    from pyproj import Transformer

    e, n = Transformer.from_crs(4326, tile.epsg, always_xy=True).transform(lon + res / 2, lat - res / 2)
    step = 160.0
    assert abs(cols.mean() - (e - tile.utm_west) / step) < 4
    assert abs(rows.mean() - (tile.utm_north - n) / step) < 4  # row 0 is the northern edge


def test_missing_source_tile_is_an_error(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        sample_source_on_tile(TileRef("21S", 581920, 9180800), 6, 4, tmp_path)
