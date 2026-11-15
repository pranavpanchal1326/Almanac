"""Facts about the supplier's dataset. Every value here was read from the data in Phase 0."""

from __future__ import annotations

MIRROR_S3 = "s3://us-west-2.opendata.source.coop/"
MIRROR_HTTPS = "https://data.source.coop/"
ANNUAL_PREFIX = "tge-labs/aef/v1/annual/"
INDEX_URL = MIRROR_HTTPS + ANNUAL_PREFIX + "aef_index.parquet"

#: Version of the supplier's dataset this code was checked against (blueprint section 4.1).
DATASET_VERSION = "aef-v1-annual/1.1"

ATTRIBUTION = (
    "The AlphaEarth Foundations Satellite Embedding dataset is produced by Google and Google DeepMind."
)

BANDS = 64
TILE = 8192  # cells per tile side at level 0
BLOCK = 1024  # cells per internal block side
BLOCKS_PER_SIDE = TILE // BLOCK
CELL_M = 10.0  # level-0 cell size in metres
NODATA = -128
YEARS: tuple[int, ...] = (2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025)
