"""Live reads from the supplier. Run with ``pytest -m network``.

These detect a change on the supplier's side: layout, orientation handling in a new GDAL or
Rasterio, or reprocessed values.
"""

from pathlib import Path

import numpy as np
import pytest

from almanac.io.reader import TransferLog, read_block, read_block_via_vrt

pytestmark = [pytest.mark.network, pytest.mark.slow]

URL = "https://data.source.coop/tge-labs/aef/v1/annual/{path}"
FIXTURE = Path(__file__).parents[1] / "golden" / "orientation_coast.npz"
FIXTURE_URL_FILE = Path(__file__).parents[2] / "docs" / "phase0" / "orientation.json"


def _fixture_source() -> tuple[str, int, int]:
    import json

    from almanac.grid.ids import parse_block_id

    rec = json.loads(FIXTURE_URL_FILE.read_text())
    _tile, row, col = parse_block_id(rec["block_id"])
    return rec["url"], row, col


def test_block_read_shape_type_and_transfer() -> None:
    url, row, col = _fixture_source()
    with TransferLog() as log:
        values, valid = read_block(url, row, col)
    assert values.shape == (64, 1024, 1024) and values.dtype == np.int8
    assert valid.shape == (1024, 1024)
    assert 10e6 < log.bytes < 80e6, log.bytes
    with np.load(FIXTURE) as f:
        np.testing.assert_array_equal(values[:, 4::8, 4::8], f["stored"])


def test_reader_matches_the_suppliers_north_up_sidecar() -> None:
    url, row, col = _fixture_source()
    values, _ = read_block(url, row, col)
    via_vrt = read_block_via_vrt(url.removesuffix(".tiff") + ".vrt", row, col)
    np.testing.assert_array_equal(values, via_vrt)
    assert not np.array_equal(values[:, ::-1, :], via_vrt)


def test_two_request_level_read_matches_a_standard_read() -> None:
    import rasterio

    from almanac.io.http import RangeClient
    from almanac.io.level import read_level
    from almanac.io.reader import GDAL_ENV

    url, _row, _col = _fixture_source()
    with RangeClient(connections=2) as client:
        got = read_level(client, url, 6)
        assert client.stats.requests == 2
    assert got.values_chw.shape == (64, 128, 128) and got.values_chw.dtype == np.int8
    assert got.bytes_fetched < 1_500_000
    with rasterio.Env(**GDAL_ENV), rasterio.open(f"/vsicurl/{url}", OVERVIEW_LEVEL=5) as ds:
        reference = ds.read()[:, ::-1, :]
    np.testing.assert_array_equal(got.values_chw, reference)
