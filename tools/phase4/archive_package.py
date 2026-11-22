"""Pack a sealed forecast package into one reproducible, uncompressed tar for release.

Usage: python tools/phase4/archive_package.py PACKAGE_DIR OUT_TAR [--name ROOT]

The tar holds exactly the package's files under one root folder, in sorted order, with fixed
metadata (mtime 0, uid/gid 0, mode 0644, no user names), so the same package always gives the
same archive bytes and the same SHA-256. It is not compressed: float32 probabilities barely
compress, and an uncompressed tar can be checked and extracted by any tool, including the
``tar`` built into Windows 10 and later. Before writing, the package must verify against its
manifest; nothing outside the manifest is packed.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import tarfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from almanac.registry.package import digest, verify


def info(name: str, size: int) -> tarfile.TarInfo:
    ti = tarfile.TarInfo(name)
    ti.size, ti.mtime, ti.mode = size, 0, 0o644
    ti.uid = ti.gid = 0
    ti.uname = ti.gname = ""
    return ti


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("package", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--name", default="almanac-2027.01")
    args = ap.parse_args()
    problems = verify(args.package)
    if problems:
        raise SystemExit(f"package does not verify: {problems}")
    files = ["manifest.json"] + [e["path"] for e in json.loads((args.package / "manifest.json").read_bytes())["files"]]
    with tarfile.open(args.out, "w", format=tarfile.PAX_FORMAT) as tar:
        for d in sorted({str(Path(f).parent.as_posix()) for f in files} - {"."}):
            ti = tarfile.TarInfo(f"{args.name}/{d}")
            ti.type, ti.mtime, ti.mode, ti.uid, ti.gid, ti.uname, ti.gname = tarfile.DIRTYPE, 0, 0o755, 0, 0, "", ""
            tar.addfile(ti)
        for f in sorted(files):
            data = (args.package / f).read_bytes()
            tar.addfile(info(f"{args.name}/{f}", len(data)), io.BytesIO(data))
    h = hashlib.sha256(args.out.read_bytes()).hexdigest()
    print(f"{args.out}: {args.out.stat().st_size:,} bytes, {len(files)} files")
    print(f"archive sha256 {h}")
    print(f"package digest {digest(args.package)}")


if __name__ == "__main__":
    main()
