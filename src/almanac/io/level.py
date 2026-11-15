"""Read one whole coarse pyramid level of a supplier file in two range requests.

Measured in task 1.1: the file header and the directory of every level fit in the first 128 KiB,
and the 64 band planes of a coarse level lie in one short span near the start of the file. So a
level costs one request for the header and one for exactly the span that holds its planes.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np
import rasterio
from rasterio.io import MemoryFile

from almanac.common.constants import BANDS, TILE
from almanac.io.http import RangeClient

HEADER_BYTES = 131072
MIN_LEVEL = 5  # finer levels have more than one block per band; use the block reader for those


@dataclass(frozen=True)
class LevelRead:
    values_chw: np.ndarray  # stored int8, north-up
    url: str
    etag: str
    last_modified: str
    object_size: int
    bytes_fetched: int
    sha256: str


def read_level(client: RangeClient, tiff_url: str, level: int) -> LevelRead:
    """One pyramid level of a raw file, north-up, ``[64, 8192 >> level, 8192 >> level]`` int8."""
    if not MIN_LEVEL <= level <= 13:
        raise ValueError(f"level must be {MIN_LEVEL}..13")
    side = TILE >> level
    head = client.get_range(tiff_url, 0, HEADER_BYTES)
    start, end = _plane_span(head.data, level, tiff_url)
    end = min(end, head.total_size)
    buffer = bytearray(max(end, len(head.data)))
    buffer[: len(head.data)] = head.data
    fetched = len(head.data)
    if end > len(head.data):
        body_start = max(start, len(head.data))
        body = client.get_range(tiff_url, body_start, end)
        buffer[body_start : body_start + len(body.data)] = body.data
        fetched += len(body.data)
    with rasterio.Env(), MemoryFile(bytes(buffer)) as mem, mem.open(OVERVIEW_LEVEL=level - 1) as ds:
        if (ds.count, ds.width, ds.height) != (BANDS, side, side) or ds.dtypes[0] != "int8":
            raise ValueError(f"unexpected level-{level} layout in {tiff_url}")
        if ds.transform.e <= 0:
            raise ValueError(f"raw file is not bottom-up as expected: {tiff_url}")
        values = ds.read()
    values = np.ascontiguousarray(values[:, ::-1, :])
    return LevelRead(
        values_chw=values,
        url=tiff_url,
        etag=head.etag,
        last_modified=head.last_modified,
        object_size=head.total_size,
        bytes_fetched=fetched,
        sha256=hashlib.sha256(values.tobytes()).hexdigest(),
    )


def _plane_span(header: bytes, level: int, url: str) -> tuple[int, int]:
    """Byte span ``[start, end)`` covering all 64 planes of a level, from the file header."""
    offsets: list[int] = []
    ends: list[int] = []
    with rasterio.Env(), MemoryFile(header) as mem, mem.open() as ds:
        if ds.count != BANDS:
            raise ValueError(f"expected {BANDS} bands in {url}, found {ds.count}")
        for band in range(1, BANDS + 1):
            offset = ds.get_tag_item("BLOCK_OFFSET_0_0", "TIFF", bidx=band, ovr=level - 1)
            size = ds.get_tag_item("BLOCK_SIZE_0_0", "TIFF", bidx=band, ovr=level - 1)
            if offset is None or size is None:
                # A plane that holds no data is not stored at all; it reads back as no-data.
                continue
            offsets.append(int(offset))
            ends.append(int(offset) + int(size))
    if not offsets:
        return 0, 0
    return min(offsets), max(ends)
