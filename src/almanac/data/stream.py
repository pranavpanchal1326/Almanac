"""Task 1.1: stream a coarse level of every tile once, keep only summaries.

For each tile the pass reads the level for every year, runs the per-tile quality numbers, computes
change between consecutive years, and writes one small summary file. The embeddings themselves are
discarded. A summary is written atomically, so an interrupted run resumes by skipping the tiles
whose summary exists.

The summary keeps the full change field (one byte per cell and year pair) rather than counts above
a threshold, because the threshold rule is still open (ADR 0001): any rule can be tried later
without streaming the planet again.
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from almanac.common.constants import DATASET_VERSION, YEARS
from almanac.grid.ids import TileRef
from almanac.io.level import LevelRead
from almanac.io.reader import valid_mask
from almanac.quality.embedding import cosine_change, dequantize, renormalize

INVALID_CODE = 255
_CODE_MAX = 254.0

#: Reads one level of one file. Injected so tests can run without a network.
Fetch = Callable[[str], LevelRead]


def encode_delta(delta_hw: np.ndarray, valid_hw: np.ndarray) -> np.ndarray:
    """Change in [0, 2] -> one byte: ``round(254 * sqrt(min(delta, 1)))``; 255 marks invalid cells.

    The square root spends the codes where they are needed: the step is about 0.001 at a change of
    0.015 and about 0.004 at 0.2.
    """
    code = np.rint(_CODE_MAX * np.sqrt(np.clip(delta_hw, 0.0, 1.0))).astype(np.uint8)
    code[~valid_hw] = INVALID_CODE
    return code


def decode_delta(code_hw: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Inverse of :func:`encode_delta`: change (float32, NaN where invalid) and validity."""
    valid = code_hw != INVALID_CODE
    delta = (code_hw.astype(np.float32) / _CODE_MAX) ** 2
    return np.where(valid, delta, np.nan).astype(np.float32), valid


def summary_path(out_dir: Path, level: int, tile: TileRef) -> Path:
    return out_dir / f"L{level}" / tile.utm_zone / f"{tile.tile_id}.npz"


def summarise_tile(tile: TileRef, level: int, reads: dict[int, LevelRead]) -> dict[str, Any]:
    """Arrays of one tile summary. ``reads`` maps year to the level read for that year."""
    if not reads:
        raise ValueError(f"no years to read for tile {tile.tile_id}")
    side = next(iter(reads.values())).values_chw.shape[-1]
    n_years = len(YEARS)
    present = np.array([y in reads for y in YEARS])
    valid = np.zeros((n_years, side, side), dtype=bool)
    nodata_share = np.ones(n_years, dtype=np.float32)
    length_q = np.full((n_years, 3), np.nan, dtype=np.float32)  # 1st, 50th, 99th percentile
    codes = np.full((n_years - 1, side, side), INVALID_CODE, dtype=np.uint8)
    previous: tuple[np.ndarray, np.ndarray] | None = None
    for i, year in enumerate(YEARS):
        if year not in reads:
            previous = None
            continue
        stored = reads[year].values_chw
        valid[i] = valid_mask(stored)
        nodata_share[i] = 1.0 - valid[i].mean()
        decoded = dequantize(stored)
        if valid[i].any():
            length_q[i] = np.percentile(np.linalg.norm(decoded, axis=0)[valid[i]], [1, 50, 99])
        emb = renormalize(decoded)
        if previous is not None:
            codes[i - 1] = encode_delta(cosine_change(previous[0], emb), previous[1] & valid[i])
        previous = (emb, valid[i])
    lineage = {
        str(year): {
            "url": r.url,
            "etag": r.etag,
            "last_modified": r.last_modified,
            "object_size": r.object_size,
            "bytes_fetched": r.bytes_fetched,
            "sha256": r.sha256,
        }
        for year, r in sorted(reads.items())
    }
    meta = {
        "tile_id": tile.tile_id,
        "level": level,
        "dataset_version": DATASET_VERSION,
        "years": list(YEARS),
        "lineage": lineage,
    }
    return {
        "delta_code": codes,
        "valid_bits": np.packbits(valid.reshape(n_years, -1), axis=1),
        "present": present,
        "nodata_share": nodata_share,
        "length_q": length_q,
        "meta": np.array(json.dumps(meta)),
    }


def process_tile(tile: TileRef, urls: dict[int, str], level: int, out_dir: Path, fetch: Fetch) -> int:
    """Read, summarise and write one tile. Returns bytes fetched."""
    reads = {year: fetch(url) for year, url in sorted(urls.items()) if year in YEARS}
    arrays = summarise_tile(tile, level, reads)
    path = summary_path(out_dir, level, tile)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.part")
    with tmp.open("wb") as f:
        np.savez_compressed(f, **arrays)
    tmp.replace(path)  # atomic: a summary either exists whole or not at all
    return sum(r.bytes_fetched for r in reads.values())


@dataclass
class StreamReport:
    tiles_total: int = 0
    tiles_skipped: int = 0
    tiles_done: int = 0
    tiles_failed: int = 0
    bytes_fetched: int = 0
    seconds: float = 0.0


def run_stream(
    work: Iterable[tuple[TileRef, dict[int, str]]],
    level: int,
    out_dir: Path,
    fetch: Fetch,
    workers: int,
    progress: Callable[[StreamReport], None] | None = None,
) -> StreamReport:
    """Process every tile that has no summary yet. Failures are logged and left for the next run."""
    report = StreamReport()
    started = time.time()
    todo: list[tuple[TileRef, dict[int, str]]] = []
    for tile, urls in work:
        report.tiles_total += 1
        if summary_path(out_dir, level, tile).exists():
            report.tiles_skipped += 1
        else:
            todo.append((tile, urls))
    errors_path = out_dir / f"L{level}" / "errors.jsonl"
    pool = ThreadPoolExecutor(max_workers=workers)
    try:
        futures = {pool.submit(process_tile, t, u, level, out_dir, fetch): t for t, u in todo}
        for future in as_completed(futures):
            tile = futures[future]
            try:
                report.bytes_fetched += future.result()
                report.tiles_done += 1
            except Exception as exc:
                report.tiles_failed += 1
                errors_path.parent.mkdir(parents=True, exist_ok=True)
                with errors_path.open("a") as f:
                    f.write(json.dumps({"tile_id": tile.tile_id, "error": repr(exc)[:500]}) + "\n")
            report.seconds = time.time() - started
            if progress and (report.tiles_done + report.tiles_failed) % 25 == 0:
                progress(report)
    finally:
        pool.shutdown(wait=True, cancel_futures=True)
    report.seconds = time.time() - started
    return report


def load_summary(path: Path) -> dict[str, Any]:
    """A tile summary with the packed fields opened up."""
    with np.load(path) as f:
        meta = json.loads(str(f["meta"]))
        codes = f["delta_code"]
        side = codes.shape[-1]
        n_years = len(meta["years"])
        valid = np.unpackbits(f["valid_bits"], axis=1)[:, : side * side].reshape(n_years, side, side)
        return {
            "meta": meta,
            "delta_code": codes,
            "valid": valid.astype(bool),
            "present": f["present"],
            "nodata_share": f["nodata_share"],
            "length_q": f["length_q"],
        }


def coverage(out_dir: Path, level: int) -> dict[str, Any]:
    """Tiles visited per year, bytes fetched and bytes on disk, from the summaries present."""
    per_year = dict.fromkeys(YEARS, 0)
    tiles = fetched = on_disk = 0
    for path in sorted((out_dir / f"L{level}").glob("*/*.npz")):
        with np.load(path) as f:
            meta = json.loads(str(f["meta"]))
        tiles += 1
        on_disk += path.stat().st_size
        for year, rec in meta["lineage"].items():
            per_year[int(year)] += 1
            fetched += rec["bytes_fetched"]
    return {"tiles": tiles, "tiles_per_year": per_year, "bytes_fetched": fetched, "bytes_on_disk": on_disk}
