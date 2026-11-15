"""Task 1.4: forest-loss label for every downloaded tile of a region, and a check of its totals.

Usage: python tools/phase1/build_labels.py configs/regions/amazon_cerrado.json

Writes one file per tile with, on the 640 m grid:
  loss_share   float16 [8, 128, 128]  share of the cell lost in each year 2018..2025
  loss_before  float16 [128, 128]     share lost 2001..2017
  land_share   float16 [128, 128]     share of the cell mapped as land in the source's data mask

Check: for a sample of tiles, lost area per year from the label is compared with lost area counted
directly on the source grid inside the tile's footprint, using each source cell's true area.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from pyproj import Geod, Transformer
from rasterio.windows import from_bounds

from almanac.data.labels import (
    GFC_FIRST_YEAR,
    GFC_VERSION,
    cumulative_loss_share,
    gfc_tiles_for_bounds,
    loss_share_by_year,
    sample_source_on_tile,
)
from almanac.data.stream import summary_path
from almanac.grid.ids import TileRef
from almanac.io.index import tiles_with_years

REPO = Path(__file__).resolve().parents[2]
DATA = Path("D:/almanac-data")
SOURCE = DATA / "labels" / "gfc"
OUT = DATA / "labels" / "forest_loss"
LEVEL, SUB = 6, 20
LABEL_YEARS = list(range(2018, 2026))
CELL_AREA_HA = 640.0 * 640.0 / 1e4


def label_path(tile: TileRef) -> Path:
    return OUT / f"L{LEVEL}" / tile.utm_zone / f"{tile.tile_id}.npz"


def build(tile: TileRef) -> None:
    fine = sample_source_on_tile(tile, LEVEL, SUB, SOURCE, "lossyear")
    mask = sample_source_on_tile(tile, LEVEL, SUB, SOURCE, "datamask")
    side = fine.shape[0] // SUB
    land = (mask == 1).reshape(side, SUB, side, SUB).mean(axis=(1, 3))
    path = label_path(tile)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".part")
    with tmp.open("wb") as f:
        np.savez_compressed(
            f,
            loss_share=loss_share_by_year(fine, SUB, LABEL_YEARS).astype(np.float16),
            loss_before=cumulative_loss_share(fine, SUB, LABEL_YEARS[0] - 1).astype(np.float16),
            land_share=land.astype(np.float16),
            years=np.array(LABEL_YEARS),
            source=np.array(GFC_VERSION),
        )
    tmp.replace(path)


def direct_loss_ha(tile: TileRef) -> np.ndarray:
    """Lost hectares per label year, counted on the source grid inside the tile's footprint."""
    to_utm = Transformer.from_crs(4326, tile.epsg, always_xy=True)
    to_geo = Transformer.from_crs(tile.epsg, 4326, always_xy=True)
    xs = np.linspace(tile.utm_west, tile.utm_east, 41)
    ys = np.linspace(tile.utm_south, tile.utm_north, 41)
    edge_x = np.concatenate([xs, xs, np.full(41, xs[0]), np.full(41, xs[-1])])
    edge_y = np.concatenate([np.full(41, ys[0]), np.full(41, ys[-1]), ys, ys])
    lon, lat = to_geo.transform(edge_x, edge_y)
    west, east, south, north = lon.min(), lon.max(), lat.min(), lat.max()
    geod = Geod(ellps="WGS84")
    total = np.zeros(len(LABEL_YEARS))
    for name in gfc_tiles_for_bounds("lossyear", west, south, east, north):
        with rasterio.open(SOURCE / name) as src:
            b = src.bounds
            w, s, e, n = max(west, b.left), max(south, b.bottom), min(east, b.right), min(north, b.top)
            if w >= e or s >= n:
                continue
            win = from_bounds(w, s, e, n, src.transform).round_offsets().round_lengths()
            data = src.read(1, window=win)
            t = src.window_transform(win)
        rows, cols = np.nonzero(data >= LABEL_YEARS[0] - GFC_FIRST_YEAR + 1)
        if rows.size == 0:
            continue
        plon = t.c + (cols + 0.5) * t.a
        plat = t.f + (rows + 0.5) * t.e
        x, y = to_utm.transform(plon, plat)
        inside = (x >= tile.utm_west) & (x < tile.utm_east) & (y >= tile.utm_south) & (y < tile.utm_north)
        # True area of a source cell at each latitude, from the ellipsoid.
        lat_unique = np.unique(plat[inside])
        area = {}
        for la in lat_unique:
            a, _ = geod.polygon_area_perimeter(
                [0, t.a, t.a, 0], [la - t.e / 2, la - t.e / 2, la + t.e / 2, la + t.e / 2]
            )
            area[la] = abs(a) / 1e4
        cell_ha = np.array([area[la] for la in plat[inside]])
        values = data[rows[inside], cols[inside]]
        for i, year in enumerate(LABEL_YEARS):
            total[i] += cell_ha[values == year - GFC_FIRST_YEAR + 1].sum()
    return total


def main() -> None:
    region = json.loads(Path(sys.argv[1]).read_text())
    b = region["bbox_wgs84"]
    work = tiles_with_years(
        DATA / "index" / "aef_index.parquet", None, (b["west"], b["south"], b["east"], b["north"])
    )
    tiles = [t for t, _ in work if summary_path(DATA / "summaries", LEVEL, t).exists()]
    built = 0
    for i, tile in enumerate(tiles):
        if not label_path(tile).exists():
            build(tile)
            built += 1
        if (i + 1) % 100 == 0:
            print(f"{i + 1}/{len(tiles)} tiles", flush=True)

    # Regional totals and the check on a sample of tiles.
    regional = np.zeros(len(LABEL_YEARS))
    for tile in tiles:
        with np.load(label_path(tile)) as f:
            regional += f["loss_share"].astype(np.float64).sum(axis=(1, 2)) * CELL_AREA_HA
    rng = np.random.default_rng(20261115)
    sample = [tiles[i] for i in sorted(rng.choice(len(tiles), size=min(25, len(tiles)), replace=False))]
    from_label = np.zeros(len(LABEL_YEARS))
    from_source = np.zeros(len(LABEL_YEARS))
    for tile in sample:
        with np.load(label_path(tile)) as f:
            from_label += f["loss_share"].astype(np.float64).sum(axis=(1, 2)) * CELL_AREA_HA
        from_source += direct_loss_ha(tile)
    ratio = from_label / np.maximum(from_source, 1e-9)
    result = {
        "region": region["name"],
        "source": GFC_VERSION,
        "level": LEVEL,
        "sub_samples_per_side": SUB,
        "tiles_labelled": len(tiles),
        "tiles_built_this_run": built,
        "years": LABEL_YEARS,
        "loss_ha_by_year_all_tiles": [round(float(v)) for v in regional],
        "note_on_totals": "tiles of neighbouring UTM zones overlap, so the all-tile total counts some land twice",
        "check_sample_tiles": len(sample),
        "check_loss_ha_from_label": [round(float(v)) for v in from_label],
        "check_loss_ha_counted_on_source": [round(float(v)) for v in from_source],
        "check_ratio_by_year": [round(float(v), 4) for v in ratio],
        "check_ratio_all_years": round(float(from_label.sum() / max(from_source.sum(), 1e-9)), 4),
    }
    out = REPO / "docs" / "phase1" / f"labels_forest_{region['name']}.json"
    out.write_text(json.dumps(result, indent=2), newline="\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
