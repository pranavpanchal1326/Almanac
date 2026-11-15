"""Task 0.6: download one level-0 block for every year at each site, and run gates Q3-Q6.

Writes each block as a north-up int8 array and a manifest line with the object's address, entity
tag, bytes transferred, content digest and quality numbers. Safe to re-run; finished blocks are
skipped.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np

from almanac.common.constants import DATASET_VERSION, YEARS
from almanac.io.reader import TransferLog, read_block
from almanac.quality.embedding import dequantize, length_report

sys.path.insert(0, str(Path(__file__).parent))
from common import RAW, WORK, Site, load_sites

MANIFEST = WORK / "manifest.jsonl"


def object_head(url: str) -> dict[str, str]:
    req = urllib.request.Request(url, method="HEAD")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return {
            "etag": resp.headers.get("ETag", "").strip('"'),
            "last_modified": resp.headers.get("Last-Modified", ""),
            "content_length": resp.headers.get("Content-Length", ""),
        }


def fetch_one(site: Site, year: int) -> dict | None:
    path = site.block_path(year)
    if path.exists():
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    url = site.urls[year]
    last: Exception | None = None
    for attempt in range(3):
        try:
            started = time.time()
            with TransferLog() as log:
                values, valid = read_block(url, site.block_row, site.block_col)
            seconds = time.time() - started
            break
        except Exception as exc:  # bounded retry on a supplier read
            last = exc
            time.sleep(5 * (attempt + 1))
    else:
        raise RuntimeError(f"read failed for {site.name} {year} at {url}") from last
    if values.shape != (64, 1024, 1024) or values.dtype != np.int8:
        raise ValueError(f"bad block shape {values.shape} {values.dtype} for {site.name} {year}")
    np.save(path, values)
    lengths = length_report(dequantize(values), valid)
    return {
        "site": site.name,
        "block_id": site.block_id,
        "year": year,
        "url": url,
        "dataset_version": DATASET_VERSION,
        **object_head(url),
        "requests": log.requests,
        "bytes_transferred": log.bytes,
        "seconds": round(seconds, 1),
        "sha256": hashlib.sha256(values.tobytes()).hexdigest(),
        "nodata_share": float(1.0 - valid.mean()),
        "length": lengths,
    }


def main() -> None:
    names = set(sys.argv[1:])
    RAW.mkdir(parents=True, exist_ok=True)
    for site in load_sites():
        if names and site.name not in names:
            continue
        years = YEARS if site.role != "orientation" else (2021,)
        missing = [y for y in years if y not in site.urls]
        if missing:
            print(f"{site.name}: Q6 FAIL, years missing from the index: {missing}", flush=True)
        for year in years:
            if year not in site.urls:
                continue
            rec = fetch_one(site, year)
            if rec is None:
                continue
            with MANIFEST.open("a") as f:
                f.write(json.dumps(rec) + "\n")
            print(
                f"{site.name} {year}: {rec['bytes_transferred'] / 1e6:.1f} MB in {rec['seconds']} s, "
                f"{rec['requests']} requests, no-data {rec['nodata_share']:.4f}, "
                f"length in band {rec['length']['in_band']:.4f}",
                flush=True,
            )


if __name__ == "__main__":
    main()
