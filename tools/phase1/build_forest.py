"""Forest extent and forest loss per 640 m cell and year, for every tile of a split.

Usage: python tools/phase1/build_forest.py configs/splits/amazon_cerrado_v1.csv

Needs the source's "treecover2000" and "lossyear" tiles in D:/almanac-data/labels/gfc. Writes one
file per tile with, on the 640 m grid:
  forest_start  float16 [9, 128, 128]  share of the cell that is forest at the start of 2018..2026
  forest_lost   float16 [8, 128, 128]  share of the cell that was forest and is lost in 2018..2025
  land_share    float16 [128, 128]     copied from the forest-loss label

Forest: tree cover in 2000 of at least 30%, not lost in an earlier year. Gain is ignored.
"""

from __future__ import annotations

import csv
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from almanac.data.labels import FOREST_COVER_PCT, GFC_VERSION, forest_by_year, sample_source_on_tile
from almanac.grid.ids import TileRef, parse_tile_id

REPO = Path(__file__).resolve().parents[2]
DATA = Path("D:/almanac-data")
SOURCE = DATA / "labels" / "gfc"
LOSS = DATA / "labels" / "forest_loss"
OUT = DATA / "labels" / "forest"
LEVEL, SUB = 6, 20
START_YEARS = list(range(2018, 2027))


def out_path(tile: TileRef) -> Path:
    return OUT / f"L{LEVEL}" / tile.utm_zone / f"{tile.tile_id}.npz"


def build(tile_id: str) -> tuple[str, float]:
    tile = parse_tile_id(tile_id)
    path = out_path(tile)
    if path.exists():
        with np.load(path) as f:
            return tile_id, float(f["forest_start"][0].astype(np.float64).sum())
    loss = sample_source_on_tile(tile, LEVEL, SUB, SOURCE, "lossyear")
    cover = sample_source_on_tile(tile, LEVEL, SUB, SOURCE, "treecover2000")
    start, lost = forest_by_year(loss, cover, SUB, START_YEARS)
    with np.load(LOSS / f"L{LEVEL}" / tile.utm_zone / f"{tile.tile_id}.npz") as f:
        land = f["land_share"]
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".part")
    with tmp.open("wb") as f:
        np.savez_compressed(
            f,
            forest_start=start.astype(np.float16),
            forest_lost=lost[:-1].astype(np.float16),
            land_share=land,
            start_years=np.array(START_YEARS),
            lost_years=np.array(START_YEARS[:-1]),
            source=np.array(GFC_VERSION),
            cover_pct=np.array(FOREST_COVER_PCT),
        )
    tmp.replace(path)
    return tile_id, float(start[0].astype(np.float64).sum())


def main() -> None:
    split_csv = Path(sys.argv[1])
    with split_csv.open() as f:
        tiles = [r["tile_id"] for r in csv.DictReader(f)]
    done = 0
    forest_cells = 0.0
    with ProcessPoolExecutor(max_workers=12) as pool:
        for _, cells in pool.map(build, tiles, chunksize=4):
            done += 1
            forest_cells += cells
            if done % 100 == 0:
                print(f"{done}/{len(tiles)} tiles", flush=True)
    summary = {
        "source": GFC_VERSION,
        "cover_pct": FOREST_COVER_PCT,
        "tiles": len(tiles),
        "forest_ha_start_2018_all_tiles": round(forest_cells * 640 * 640 / 1e4),
        "note": "overlapping tiles of neighbouring UTM zones count some land twice",
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
