"""Check a regional download: coverage, quality numbers and size, from the files on disk.

Usage: python tools/phase1/store_report.py configs/regions/amazon_cerrado.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

from almanac.common.constants import YEARS
from almanac.data.stream import embedding_path, load_summary, summary_path
from almanac.io.index import tiles_with_years

REPO = Path(__file__).resolve().parents[2]
DATA = Path("D:/almanac-data")
LEVEL = 6


def main() -> None:
    region = json.loads(Path(sys.argv[1]).read_text())
    b = region["bbox_wgs84"]
    work = tiles_with_years(
        DATA / "index" / "aef_index.parquet", None, (b["west"], b["south"], b["east"], b["north"])
    )
    done = missing = incomplete = files = 0
    fetched = emb_bytes = sum_bytes = 0
    per_year = dict.fromkeys(YEARS, 0)
    valid_share, length_out_of_band, shape_errors = [], 0, []
    for tile, urls in work:
        s_path = summary_path(DATA / "summaries", LEVEL, tile)
        e_path = embedding_path(DATA / "embeddings", LEVEL, tile)
        if not (s_path.exists() and e_path.exists()):
            missing += 1
            continue
        done += 1
        s = load_summary(s_path)
        sum_bytes += s_path.stat().st_size
        emb_bytes += e_path.stat().st_size
        present = s["present"]
        incomplete += int(present.sum() < len(YEARS))
        for year, rec in s["meta"]["lineage"].items():
            per_year[int(year)] += 1
            fetched += rec["bytes_fetched"]
            files += 1
        valid_share.append(float(1.0 - s["nodata_share"][present].mean()))
        q = s["length_q"][present]
        q = q[np.isfinite(q).all(axis=1)]
        length_out_of_band += int(((q[:, 0] < 0.98) | (q[:, 2] > 1.02)).sum())
        with np.load(e_path) as f:
            if f["stored"].shape != (len(urls), 64, 128, 128) or f["stored"].dtype != np.int8:
                shape_errors.append(tile.tile_id)
    result = {
        "region": region["name"],
        "level": LEVEL,
        "tiles_in_region": len(work),
        "tiles_on_disk": done,
        "tiles_missing": missing,
        "tiles_lacking_a_year": incomplete,
        "files_read": files,
        "tiles_per_year": per_year,
        "transfer_gb": round(fetched / 1e9, 2),
        "embeddings_gb": round(emb_bytes / 1e9, 2),
        "summaries_gb": round(sum_bytes / 1e9, 3),
        "mean_share_of_cells_with_data": round(float(np.mean(valid_share)), 4) if valid_share else None,
        "tile_years_with_vector_length_outside_0.98_1.02": length_out_of_band,
        "tiles_with_wrong_shape": shape_errors,
    }
    out = REPO / "docs" / "phase1" / f"store_{region['name']}.json"
    out.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
