"""Minimal reader for the supplier's files.

The raw files are stored bottom-up (row 0 is the southern edge). This reader opens the raw file,
reads whole internal blocks, and flips rows so every array it returns is north-up. Task 0.4
confirmed that the result is identical, value for value, to a read through the supplier's
north-up ``.vrt`` sidecar. Reading the raw file is preferred because the read stays aligned to
the file's 1024-cell blocks and avoids the warper.
"""

from __future__ import annotations

import logging
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import rasterio
from rasterio.windows import Window

from almanac.common.constants import BANDS, BLOCK, BLOCKS_PER_SIDE, NODATA, TILE

GDAL_ENV: dict[str, Any] = {
    "GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR",
    "CPL_VSIL_CURL_ALLOWED_EXTENSIONS": ".tiff,.vrt",
    "GDAL_HTTP_MULTIRANGE": "YES",
    "GDAL_HTTP_MERGE_CONSECUTIVE_RANGES": "YES",
    "GDAL_HTTP_MAX_RETRY": "5",
    "GDAL_HTTP_RETRY_DELAY": "2",
    "GDAL_HTTP_TIMEOUT": "120",
    "VSI_CACHE": "TRUE",
    # The sidecar points at the S3 address of the raw file; the bucket is public.
    "AWS_NO_SIGN_REQUEST": "YES",
    "AWS_REGION": "us-west-2",
    "CPL_DEBUG": "ON",  # needed for transfer accounting; messages go to the rasterio logger
}

DEFAULT_WORKERS = 8
MAX_WORKERS = 16  # blueprint section 7.5: at most 16 concurrent connections

_RANGE_RE = re.compile(r"Downloading (\d+)-(\d+)")


@dataclass
class TransferLog(logging.Handler):
    """Counts range requests and bytes from GDAL's debug messages."""

    requests: int = 0
    bytes: int = 0
    _logger: logging.Logger = field(default_factory=lambda: logging.getLogger("rasterio"))

    def __post_init__(self) -> None:
        super().__init__(level=logging.DEBUG)

    def emit(self, record: logging.LogRecord) -> None:
        m = _RANGE_RE.search(record.getMessage())
        if m:
            self.requests += 1
            self.bytes += int(m.group(2)) - int(m.group(1)) + 1

    def __enter__(self) -> TransferLog:
        self._previous_level = self._logger.level
        self._logger.setLevel(logging.DEBUG)
        self._previous_propagate = self._logger.propagate
        self._logger.propagate = False
        self._logger.addHandler(self)
        return self

    def __exit__(self, *exc: object) -> None:
        self._logger.removeHandler(self)
        self._logger.setLevel(self._previous_level)
        self._logger.propagate = self._previous_propagate


def _open(url: str, **kwargs: Any) -> rasterio.DatasetReader:
    path = url if "://" not in url else f"/vsicurl/{url}"
    return rasterio.open(path, **kwargs)


def _window(col_off: int, row_off: int, side: int) -> Window:
    return Window.from_slices((row_off, row_off + side), (col_off, col_off + side))


def _check_layout(ds: rasterio.DatasetReader, url: str) -> None:
    if (ds.count, ds.width, ds.height) != (BANDS, TILE, TILE) or ds.dtypes[0] != "int8":
        raise ValueError(f"unexpected layout in {url}: {ds.count} bands, {ds.width}x{ds.height}")
    if ds.transform.e <= 0:
        raise ValueError(f"raw file is not bottom-up as expected: {url}")


def read_block(
    tiff_url: str, block_row: int, block_col: int, workers: int = DEFAULT_WORKERS
) -> tuple[np.ndarray, np.ndarray]:
    """One level-0 block, north-up.

    ``block_row`` counts from the north. Returns stored values, int8 ``[64, 1024, 1024]``, and a
    validity mask, bool ``[1024, 1024]``, true where no band holds the no-data value.

    Each band is a separate range request and the mirror answers each in a second or more, so
    bands are read over ``workers`` connections at once. The cap keeps us a polite client.
    """
    if not (0 <= block_row < BLOCKS_PER_SIDE and 0 <= block_col < BLOCKS_PER_SIDE):
        raise ValueError(f"block ({block_row}, {block_col}) outside 0..{BLOCKS_PER_SIDE - 1}")
    if not 1 <= workers <= MAX_WORKERS:
        raise ValueError(f"workers must be 1..{MAX_WORKERS}")
    raw_row = BLOCKS_PER_SIDE - 1 - block_row
    window = _window(block_col * BLOCK, raw_row * BLOCK, BLOCK)

    def read_bands(indexes: list[int]) -> np.ndarray:
        with rasterio.Env(**GDAL_ENV), _open(tiff_url) as ds:
            _check_layout(ds, tiff_url)
            return ds.read(indexes, window=window)

    groups = [list(map(int, g)) for g in np.array_split(np.arange(1, BANDS + 1), workers)]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        parts = list(pool.map(read_bands, groups))
    values = np.ascontiguousarray(np.concatenate(parts)[:, ::-1, :])
    return values, valid_mask(values)


def read_block_via_vrt(vrt_url: str, block_row: int, block_col: int) -> np.ndarray:
    """The same block through the supplier's north-up sidecar. Used only to cross-check."""
    window = _window(block_col * BLOCK, block_row * BLOCK, BLOCK)
    with rasterio.Env(**GDAL_ENV), _open(vrt_url) as ds:
        return ds.read(window=window)


def read_block_at_level(tiff_url: str, block_row: int, block_col: int, level: int) -> np.ndarray:
    """The part of a stored pyramid level that covers one level-0 block, north-up.

    Level 1 is the first stored overview. The result has side ``1024 >> level``.
    """
    if not 1 <= level <= 10:
        raise ValueError("level must be 1..10; use read_block for level 0")
    side = BLOCK >> level
    raw_row = BLOCKS_PER_SIDE - 1 - block_row
    window = _window(block_col * side, raw_row * side, side)
    with rasterio.Env(**GDAL_ENV), _open(tiff_url, OVERVIEW_LEVEL=level - 1) as ds:
        values = ds.read(window=window)
    return np.ascontiguousarray(values[:, ::-1, :])


def valid_mask(values_chw: np.ndarray) -> np.ndarray:
    """True where every band of a cell holds data."""
    return (values_chw != NODATA).all(axis=0)
