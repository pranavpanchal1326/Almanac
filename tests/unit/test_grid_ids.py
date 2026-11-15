import pytest

from almanac.grid.ids import (
    TileRef,
    block_bounds_utm,
    block_for_utm,
    block_id,
    parse_block_id,
    parse_tile_id,
)

TILE = TileRef("10N", 500000, 5079040)


def test_tile_id_round_trip() -> None:
    assert TILE.tile_id == "10N_E500000_N5079040"
    assert parse_tile_id(TILE.tile_id) == TILE
    assert TILE.epsg == 32610
    assert TileRef("21S", 581920, 9180800).epsg == 32721
    assert TILE.utm_north == 5160960  # matches the supplier's sidecar origin for this tile


def test_block_id_round_trip() -> None:
    assert parse_block_id(block_id(TILE, 2, 7)) == (TILE, 2, 7)
    with pytest.raises(ValueError):
        block_id(TILE, 8, 0)
    with pytest.raises(ValueError):
        parse_tile_id("nonsense")


def test_block_rows_count_from_the_north() -> None:
    assert block_for_utm(TILE, 500005, 5160955) == (0, 0)  # north-west corner cell
    assert block_for_utm(TILE, 581915, 5079045) == (7, 7)  # south-east corner cell
    west, south, east, north = block_bounds_utm(TILE, 0, 0)
    assert (west, north) == (500000, 5160960)
    assert (east - west, north - south) == (10240, 10240)


def test_point_outside_tile_is_rejected() -> None:
    with pytest.raises(ValueError):
        block_for_utm(TILE, 499990, 5100000)
