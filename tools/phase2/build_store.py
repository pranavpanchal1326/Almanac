"""Task 2.1: write the memory-mapped training store for every tile of the split.

Usage: python tools/phase2/build_store.py configs/splits/amazon_cerrado_v1.csv

About 9.6 MB per tile (19 GB for 2,020 tiles) under D:/almanac-data/store_v1. Resumable: tiles
already written are skipped.
"""

from __future__ import annotations

import csv
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from almanac.model.store import load_rule, write_tile

_RULE = None


def _one(tile_id: str) -> str:
    global _RULE
    if _RULE is None:
        _RULE = load_rule()
    write_tile(tile_id, _RULE)
    return tile_id


def main() -> None:
    with Path(sys.argv[1]).open() as f:
        tiles = [r["tile_id"] for r in csv.DictReader(f)]
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=8) as pool:
        for n, _ in enumerate(pool.map(_one, tiles, chunksize=4), 1):
            if n % 200 == 0:
                print(f"{n}/{len(tiles)} tiles, {time.time() - t0:.0f}s", flush=True)
    print(f"done: {len(tiles)} tiles, {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
