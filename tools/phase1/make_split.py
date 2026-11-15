"""Task 1.7: write the split file for a region from its committed configuration.

Usage: python tools/phase1/make_split.py configs/splits/amazon_cerrado_v1.json
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

from almanac.data.splits import BUFFER, TRAIN, SplitConfig, assign, boxes_touch
from almanac.io.index import tile_footprints

REPO = Path(__file__).resolve().parents[2]
INDEX = Path("D:/almanac-data/index/aef_index.parquet")


def main() -> None:
    cfg_path = Path(sys.argv[1])
    cfg = json.loads(cfg_path.read_text())
    b = json.loads((REPO / cfg["region"]).read_text())["bbox_wgs84"]
    h = cfg["held_out_box_wgs84"]
    footprints = tile_footprints(INDEX, (b["west"], b["south"], b["east"], b["north"]))
    config = SplitConfig(
        cfg["seed"],
        cfg["block_deg"],
        cfg["train_share"],
        cfg["validation_share"],
        (h["west"], h["south"], h["east"], h["north"]),
        cfg["touch_margin_deg"],
    )
    result = assign(footprints, config)

    train = [footprints[t] for t, (_, s) in result.items() if s == TRAIN]
    scored = [footprints[t] for t, (_, s) in result.items() if s not in (TRAIN, BUFFER)]
    touching = sum(any(boxes_touch(a, o, config.touch_margin_deg) for o in scored) for a in train)

    out = cfg_path.with_suffix(".csv")
    with out.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["tile_id", "super_block", "split"])
        for tile in sorted(result, key=lambda t: t.tile_id):
            w.writerow([tile.tile_id, *result[tile]])
    counts = Counter(s for _, s in result.values())
    blocks = Counter()
    for _block, split in set(result.values()):
        blocks[split] += 1
    report = {
        "split": cfg["name"],
        "tiles": len(result),
        "tiles_by_split": dict(sorted(counts.items())),
        "super_blocks_by_split": dict(sorted(blocks.items())),
        "training_tiles_touching_a_scored_tile": touching,
        "file": out.name,
    }
    cfg_path.with_name(cfg_path.stem + "_report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
