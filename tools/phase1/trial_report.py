"""Task 1.1 trial: what did a partial streaming pass cost, and what does the planet cost at that rate?

Reads the per-tile summaries written so far and the supplier index. Prints and saves transfer and
storage per tile, a projection to all tiles, and the pooled distribution of year-to-year change at
this level (a first look for task 1.8; one zone is not the world).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

from almanac.data.stream import INVALID_CODE, decode_delta, load_summary
from almanac.io.index import footprint_summary

REPO = Path(__file__).resolve().parents[2]
INDEX = Path("D:/almanac-data/index/aef_index.parquet")
SUMMARIES = Path("D:/almanac-data/summaries")
LEVEL = 6
THRESHOLDS = (0.0124, 0.02, 0.05, 0.10, 0.20)


def main() -> None:
    paths = sorted((SUMMARIES / f"L{LEVEL}").glob("*/*.npz"))
    if not paths:
        sys.exit("no summaries found")
    fetched, on_disk, files, land_share = [], [], 0, []
    hist = np.zeros(256, dtype=np.int64)
    per_pair_valid = np.zeros(8, dtype=np.int64)
    per_pair_above = np.zeros((len(THRESHOLDS), 8), dtype=np.int64)
    for path in paths:
        s = load_summary(path)
        lineage = s["meta"]["lineage"]
        files += len(lineage)
        fetched.append(sum(r["bytes_fetched"] for r in lineage.values()))
        on_disk.append(path.stat().st_size)
        land_share.append(float(1.0 - s["nodata_share"][s["present"]].mean()))
        codes = s["delta_code"]
        hist += np.bincount(codes.ravel(), minlength=256)
        for i in range(codes.shape[0]):
            delta, ok = decode_delta(codes[i])
            per_pair_valid[i] += int(ok.sum())
            for k, t in enumerate(THRESHOLDS):
                per_pair_above[k, i] += int((delta[ok] > t).sum())

    fetched_a, disk_a, land_a = np.array(fetched), np.array(on_disk), np.array(land_share)
    totals = footprint_summary(INDEX)
    scale = totals["footprints"] / len(paths)
    valid_codes = hist[:INVALID_CODE]
    cdf = np.cumsum(valid_codes) / max(valid_codes.sum(), 1)
    quantile = {str(q): float((np.searchsorted(cdf, q / 100) / 254.0) ** 2) for q in (50, 90, 95, 99, 99.9)}
    result = {
        "level": LEVEL,
        "tiles": len(paths),
        "files_read": files,
        "mean_valid_share": float(land_a.mean()),
        "transfer_mb_per_tile": float(fetched_a.mean() / 1e6),
        "transfer_kb_per_file": float(fetched_a.sum() / files / 1e3),
        "summary_kb_per_tile": float(disk_a.mean() / 1e3),
        "projection_all_tiles": {
            "tiles": totals["footprints"],
            "files": totals["files"],
            "requests": totals["files"] * 2,
            "transfer_gb": float(fetched_a.mean() * totals["footprints"] / 1e9),
            "summaries_gb": float(disk_a.sum() * scale / 1e9),
            "caveat": "scaled from the tiles read so far; other zones have other shares of land",
        },
        "change_quantiles_all_valid_cells": quantile,
        "share_above_threshold_by_pair": {
            str(t): [float(a / max(v, 1)) for a, v in zip(per_pair_above[k], per_pair_valid, strict=True)]
            for k, t in enumerate(THRESHOLDS)
        },
    }
    out = REPO / "docs" / "phase1" / "stream_trial.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
