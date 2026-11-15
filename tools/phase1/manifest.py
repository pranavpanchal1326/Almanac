"""Content digests of every data file the first exam depends on, for the pre-registration.

Usage: python tools/phase1/manifest.py configs/splits/amazon_cerrado_v1.csv

Writes configs/manifests/amazon_cerrado_v1.sha256 (one line per file, sha256sum format, paths
relative to D:/almanac-data) and prints the digest of that file, which the pre-registration cites.
"""

from __future__ import annotations

import csv
import hashlib
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DATA = Path("D:/almanac-data")
STORES = ("embeddings/L6", "summaries/L6", "labels/forest_loss/L6", "labels/forest/L6")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    split = Path(sys.argv[1])
    with split.open() as f:
        tiles = [r["tile_id"] for r in csv.DictReader(f)]
    paths = []
    for store in STORES:
        for t in tiles:
            p = DATA / store / t.split("_")[0] / f"{t}.npz"
            if not p.exists():
                raise FileNotFoundError(p)
            paths.append(p)
    paths += sorted((DATA / "labels" / "gfc").glob("*.tif"))
    with ThreadPoolExecutor(8) as pool:
        digests = list(pool.map(sha, paths))
    lines = [f"{d}  {p.relative_to(DATA).as_posix()}" for d, p in zip(digests, paths, strict=True)]
    out = REPO / "configs" / "manifests" / f"{split.stem}.sha256"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", newline="\n")
    print(f"{len(lines)} files; manifest sha256 {hashlib.sha256(out.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()
