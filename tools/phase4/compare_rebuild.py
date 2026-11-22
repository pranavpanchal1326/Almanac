"""Task 4.6 (per ADR 0005): compare a rebuilt package with the sealed one.

Usage: python tools/phase4/compare_rebuild.py SEALED_DIR REBUILT_DIR [--out REPORT.json]

The rebuild is made from a fresh clone at the recorded commit, in a fresh environment, into an
empty folder (no manifest yet). This script then:

1. checks the sealed package against its manifest;
2. compares every file of the two packages: each layer byte for byte (and, if not identical, the
   largest absolute difference and how many cells differ);
3. reports which fields of ``forecast/meta.json`` differ. That file records when the forecast
   was built and how long it took, so it cannot match byte for byte; every other field must;
4. computes the digest the rebuild would have with the same manifest metadata, both as built and
   with the sealed ``forecast/meta.json`` in place of its own. The second must equal the sealed
   digest for the rebuild to pass.

Nothing is written into either package.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from almanac.registry.package import MANIFEST, _sha256, canonical, verify

VOLATILE = {"built", "seconds", "git_commit"}  # fields of forecast/meta.json that record the run


def files(root: Path) -> dict[str, Path]:
    return {
        p.relative_to(root).as_posix(): p
        for p in sorted(root.rglob("*"))
        if p.is_file() and p.name != MANIFEST
    }


def digest_of(entries: list[dict], meta: dict) -> str:
    return hashlib.sha256(canonical({"meta": meta, "files": entries})).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("sealed", type=Path)
    ap.add_argument("rebuilt", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    problems = verify(args.sealed)
    if problems:
        raise SystemExit(f"the sealed package does not match its manifest: {problems}")
    sealed_raw = (args.sealed / MANIFEST).read_bytes()
    manifest = json.loads(sealed_raw)
    sealed_digest = hashlib.sha256(sealed_raw).hexdigest()
    if (args.rebuilt / MANIFEST).exists():
        raise SystemExit("the rebuild already has a manifest; compare an unsealed rebuild")

    a, b = files(args.sealed), files(args.rebuilt)
    report: dict = {"sealed_digest": sealed_digest, "files": {}}
    ok = set(a) == set(b)
    if not ok:
        report["only_sealed"] = sorted(set(a) - set(b))
        report["only_rebuilt"] = sorted(set(b) - set(a))

    for name in sorted(set(a) & set(b)):
        same = a[name].read_bytes() == b[name].read_bytes()
        row: dict = {"identical": same}
        if name.endswith(".npy") and not same:
            x, y = np.load(a[name]), np.load(b[name])
            row["shape_equal"] = x.shape == y.shape
            if x.shape == y.shape:
                nan_same = bool((np.isnan(x) == np.isnan(y)).all())
                fin = np.isfinite(x) & np.isfinite(y)
                d = np.abs(x[fin].astype(np.float64) - y[fin])
                row |= {
                    "nan_pattern_equal": nan_same,
                    "max_abs_difference": float(d.max(initial=0)),
                    "cells_differing": int((d > 0).sum()),
                }
        if name == "forecast/meta.json" and not same:
            ma, mb = json.loads(a[name].read_text()), json.loads(b[name].read_text())
            diff = sorted(k for k in set(ma) | set(mb) if ma.get(k) != mb.get(k))
            row["fields_differing"] = diff
            row["sealed"] = {k: ma.get(k) for k in diff}
            row["rebuilt"] = {k: mb.get(k) for k in diff}
            same = set(diff) <= VOLATILE
            row["only_run_record_differs"] = same
        report["files"][name] = row
        ok &= same

    entries = [{"path": n, "size": p.stat().st_size, "sha256": _sha256(p)} for n, p in b.items()]
    report["rebuilt_digest_as_built"] = digest_of(entries, manifest["meta"])
    swapped = [
        {"path": e["path"], "size": a[e["path"]].stat().st_size, "sha256": _sha256(a[e["path"]])}
        if e["path"] == "forecast/meta.json"
        else e
        for e in entries
    ]
    report["rebuilt_digest_with_sealed_meta"] = digest_of(swapped, manifest["meta"])
    report["digest_matches"] = report["rebuilt_digest_with_sealed_meta"] == sealed_digest
    ok &= report["digest_matches"]
    report["pass"] = bool(ok)

    for name, row in report["files"].items():
        extra = (
            "" if row["identical"] else "  " + json.dumps({k: v for k, v in row.items() if k != "identical"})
        )
        print(f"{'same' if row['identical'] else 'DIFF'}  {name}{extra}")
    print(f"sealed digest                      {sealed_digest}")
    print(f"rebuilt, as built                  {report['rebuilt_digest_as_built']}")
    print(f"rebuilt, with the sealed meta.json {report['rebuilt_digest_with_sealed_meta']}")
    print("PASS" if ok else "FAIL")
    if args.out:
        args.out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
