"""Task 0.7: learn how the supplier's pyramid levels were made.

Reads stored levels 1, 2, 3 and 6 for one block-year and compares each with candidates built from
the level below (and from level 0): nearest neighbour at each of the four offsets, mean of stored
integers, mean of decoded values, and renormalised mean of decoded unit vectors.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

from almanac.common.constants import NODATA
from almanac.io.reader import TransferLog, read_block_at_level, valid_mask
from almanac.quality.embedding import dequantize, quantize, renormalize

sys.path.insert(0, str(Path(__file__).parent))
from common import DOCS, load_sites

SITE, YEAR = "xiongan", 2021


def groups(a_chw: np.ndarray, f: int) -> np.ndarray:
    c, h, w = a_chw.shape
    return a_chw.reshape(c, h // f, f, w // f, f)


def candidates(fine: np.ndarray, f: int) -> dict[str, np.ndarray]:
    g = groups(fine, f)
    out: dict[str, np.ndarray] = {}
    for dy in (0, f - 1):
        for dx in (0, f - 1):
            # dy indexes north-up rows; the raw file is bottom-up, so "first raw row" is dy = f-1
            out[f"nearest(row {dy}, col {dx})"] = g[:, :, dy, :, dx]
    out["mean of stored integers"] = np.rint(g.astype(np.float32).mean(axis=(2, 4))).astype(np.int8)
    dec = groups(dequantize(fine), f).mean(axis=(2, 4))
    out["mean of decoded values"] = quantize(dec)
    out["renormalised mean of decoded"] = quantize(renormalize(dec))
    return out


def compare(name: str, supplier: np.ndarray, fine: np.ndarray, f: int) -> list[dict]:
    ok = valid_mask(supplier)
    rows = []
    for label, cand in candidates(fine, f).items():
        diff = np.abs(supplier.astype(np.int16) - cand.astype(np.int16))[:, ok]
        rows.append(
            {
                "comparison": name,
                "candidate": label,
                "exact_share": float((diff == 0).mean()),
                "within_1_share": float((diff <= 1).mean()),
                "mean_abs_diff": float(diff.mean()),
            }
        )
    return rows


def main() -> None:
    site = next(s for s in load_sites() if s.name == SITE)
    level0 = np.load(site.block_path(YEAR))
    levels: dict[int, np.ndarray] = {0: level0}
    transfer = {}
    for level in (1, 2, 3, 6):
        with TransferLog() as log:
            levels[level] = read_block_at_level(site.urls[YEAR], site.block_row, site.block_col, level)
        transfer[level] = {"bytes": log.bytes, "requests": log.requests}
        print(
            f"L{level}: shape {levels[level].shape}, {log.bytes / 1e6:.2f} MB, {log.requests} requests",
            flush=True,
        )

    rows = []
    rows += compare("L1 from L0", levels[1], levels[0], 2)
    rows += compare("L2 from L1", levels[2], levels[1], 2)
    rows += compare("L3 from L2", levels[3], levels[2], 2)
    rows += compare("L3 from L0", levels[3], levels[0], 8)
    rows += compare("L6 from L3", levels[6], levels[3], 8)
    rows += compare("L6 from L0", levels[6], levels[0], 64)

    lengths = {}
    for level, arr in levels.items():
        ok = valid_mask(arr)
        ln = np.linalg.norm(dequantize(arr), axis=0)[ok]
        lengths[level] = {
            "p01": float(np.percentile(ln, 1)),
            "p50": float(np.median(ln)),
            "p99": float(np.percentile(ln, 99)),
            "nodata_share": float((arr == NODATA).any(axis=0).mean()),
        }

    result = {
        "site": site.name,
        "block_id": site.block_id,
        "year": YEAR,
        "transfer": transfer,
        "vector_length_by_level": lengths,
        "comparisons": rows,
    }
    (DOCS / "pyramid.json").write_text(json.dumps(result, indent=2))
    for r in rows:
        print(
            f"{r['comparison']:11s} {r['candidate']:30s} exact {r['exact_share']:.4f} "
            f"within1 {r['within_1_share']:.4f} mad {r['mean_abs_diff']:.3f}"
        )
    print(json.dumps(lengths, indent=1))


if __name__ == "__main__":
    main()
