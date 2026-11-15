"""Forecast packages (blueprint 11.2-11.3): layers, manifest and package digest.

A layer is one ``.npy`` file, float16 ``[n_tiles, 128, 128]``: the probability of the event in
each cell, NaN where the cell is not eligible. Tiles are in the order of ``tiles.csv``. Plain
``.npy`` is used because it is byte-deterministic: two independent builds from the same inputs
give the same digest. (Zip-based ``.npz`` embeds timestamps and would not.)

The manifest lists every file with its size and SHA-256, sorted by path, written as canonical
JSON (sorted keys, no insignificant whitespace, UTF-8). The package digest is the SHA-256 of the
manifest's bytes.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

SIDE = 128
MANIFEST = "manifest.json"


def write_layer(path: Path, probs: np.ndarray) -> None:
    if probs.ndim != 3 or probs.shape[1:] != (SIDE, SIDE):
        raise ValueError(f"layer must be [n, {SIDE}, {SIDE}], got {probs.shape}")
    finite = probs[np.isfinite(probs)]
    if finite.size and (finite.min() < 0 or finite.max() > 1):
        raise ValueError("probabilities outside [0, 1]")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".part")
    with tmp.open("wb") as f:
        np.save(f, probs.astype(np.float16), allow_pickle=False)
    tmp.replace(path)


def write_tiles(path: Path, tiles: list[str]) -> None:
    if tiles != sorted(tiles) or len(set(tiles)) != len(tiles):
        raise ValueError("tiles must be unique and sorted")
    path.write_text("tile_id\n" + "".join(f"{t}\n" for t in tiles), encoding="utf-8", newline="\n")


def canonical(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_manifest(root: Path, meta: dict) -> str:
    """Write ``manifest.json`` for every file under ``root``; return the package digest."""
    files = sorted(p for p in root.rglob("*") if p.is_file() and p.name != MANIFEST)
    entries = [
        {"path": p.relative_to(root).as_posix(), "size": p.stat().st_size, "sha256": _sha256(p)}
        for p in files
    ]
    data = canonical({"meta": meta, "files": entries})
    (root / MANIFEST).write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def verify(root: Path) -> list[str]:
    """Problems found when checking a package against its manifest (empty when it is intact)."""
    manifest = json.loads((root / MANIFEST).read_bytes())
    problems = []
    listed = {e["path"] for e in manifest["files"]}
    for e in manifest["files"]:
        p = root / e["path"]
        if not p.is_file():
            problems.append(f"missing {e['path']}")
        elif p.stat().st_size != e["size"] or _sha256(p) != e["sha256"]:
            problems.append(f"changed {e['path']}")
    for p in root.rglob("*"):
        if p.is_file() and p.name != MANIFEST and p.relative_to(root).as_posix() not in listed:
            problems.append(f"unlisted {p.relative_to(root).as_posix()}")
    if canonical(manifest) != (root / MANIFEST).read_bytes():
        problems.append("manifest is not canonical")
    return problems


def digest(root: Path) -> str:
    return hashlib.sha256((root / MANIFEST).read_bytes()).hexdigest()
