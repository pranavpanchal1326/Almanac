"""Verify a locked Almanac forecast package. Needs only Python 3.10+ and NumPy.

Usage: python tools/verify_issue.py PACKAGE_DIR [--digest HEX]

Written to be read by a stranger: it imports nothing from this repository, so what it checks does
not depend on trusting the code that built the package. It checks:

1. the manifest is canonical JSON (sorted keys, no whitespace, UTF-8), as the format specifies;
2. every listed file exists with the listed size and SHA-256, and no file is unlisted;
3. the package digest (SHA-256 of the manifest's bytes) equals ``--digest``, the value published
   with the lock and in its timestamp proofs, when given;
4. every layer is a float32 ``.npy`` of shape ``[n_tiles, 128, 128]`` with values in [0, 1] or
   NaN, where ``n_tiles`` is the length of ``tiles.csv``;
5. ``tiles.csv`` is unique and sorted, and the headline and reference layers exist for both tasks
   and cover every cell the baselines cover.

It prints one line per check and exits 0 only if every check passes.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

SIDE = 128
FORECASTS = ("M_A2", "B5_A2")  # headline and reference of issue 2027.01 (ADR 0004)
BASELINES = ("B0", "B1", "B2", "B3", "B4")
TASKS = ("forest", "embedding")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


class Report:
    def __init__(self) -> None:
        self.failed = 0

    def check(self, ok: bool, what: str) -> bool:
        print(f"{'PASS' if ok else 'FAIL'}  {what}")
        self.failed += not ok
        return ok


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("package", type=Path)
    ap.add_argument("--digest", help="the published package digest (64 hex characters)")
    args = ap.parse_args()
    root, r = args.package, Report()

    raw = (root / "manifest.json").read_bytes()
    manifest = json.loads(raw)
    canon = json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    r.check(canon.encode("utf-8") == raw, "manifest is canonical JSON")
    digest = hashlib.sha256(raw).hexdigest()
    print(f"      package digest {digest}")
    if args.digest:
        r.check(digest == args.digest.strip().lower(), "digest equals the published digest")

    listed = {e["path"]: e for e in manifest["files"]}
    bad = [p for p, e in listed.items()
           if not (root / p).is_file() or (root / p).stat().st_size != e["size"]
           or sha256(root / p) != e["sha256"]]
    r.check(not bad, f"{len(listed)} files match their size and SHA-256" + (f"; bad: {bad}" if bad else ""))
    extra = [p.relative_to(root).as_posix() for p in root.rglob("*")
             if p.is_file() and p.name != "manifest.json" and p.relative_to(root).as_posix() not in listed]
    r.check(not extra, "no unlisted files" + (f"; found {extra}" if extra else ""))

    with (root / "tiles.csv").open(newline="") as f:
        tiles = [row["tile_id"] for row in csv.DictReader(f)]
    r.check(tiles == sorted(set(tiles)), f"tiles.csv: {len(tiles)} unique tiles in sorted order")

    layers = sorted(p for p in listed if p.endswith(".npy"))
    for p in layers:
        a = np.load(root / p, allow_pickle=False)
        fin = a[np.isfinite(a)]
        r.check(a.dtype == np.float32 and a.shape == (len(tiles), SIDE, SIDE)
                and bool(((fin >= 0) & (fin <= 1)).all()),
                f"{p}: float32 {a.shape}, {fin.size:,} cells in [0, 1]")

    for task in TASKS:
        need = [f"baselines/{b}_{task}.npy" for b in BASELINES] + [f"forecast/{m}_{task}.npy" for m in FORECASTS]
        missing = [p for p in need if p not in listed]
        if not r.check(not missing, f"{task}: headline, reference and baselines present"
                       + (f"; missing {missing}" if missing else "")):
            continue
        cover = np.isfinite(np.load(root / f"baselines/B4_{task}.npy"))
        for m in FORECASTS:
            gap = int((cover & ~np.isfinite(np.load(root / f"forecast/{m}_{task}.npy"))).sum())
            r.check(gap == 0, f"{task}: {m} covers all {int(cover.sum()):,} baseline cells")

    print("VERIFIED" if r.failed == 0 else f"NOT VERIFIED: {r.failed} check(s) failed")
    return 0 if r.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
