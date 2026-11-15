"""Gate 1 check: do two baseline reports agree on every number?

Usage: python tools/phase1/compare_reports.py <report_a.json> <report_b.json>

Run metadata (commit, digests of files whose bytes may differ only in line endings, timings) is
ignored; every score, count and interval must match exactly. Exits 1 on any difference.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

IGNORED = {"git_commit", "git_tree_dirty", "config_sha256", "split_sha256", "threshold_sha256", "seconds"}


def diff(a: object, b: object, path: str, out: list[str]) -> None:
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k in IGNORED:
                continue
            if k not in a or k not in b:
                out.append(f"{path}.{k}: present in one report only")
            else:
                diff(a[k], b[k], f"{path}.{k}", out)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append(f"{path}: lengths {len(a)} and {len(b)}")
        for i, (x, y) in enumerate(zip(a, b, strict=False)):
            diff(x, y, f"{path}[{i}]", out)
    elif a != b:
        out.append(f"{path}: {a!r} != {b!r}")


def main() -> None:
    a = json.loads(Path(sys.argv[1]).read_text())
    b = json.loads(Path(sys.argv[2]).read_text())
    out: list[str] = []
    diff(a, b, "$", out)
    numbers = sum(1 for _ in _leaves(a))
    if out:
        print(f"{len(out)} differences", *out[:50], sep="\n")
        raise SystemExit(1)
    print(f"identical: {numbers} values compared, metadata ignored: {sorted(IGNORED)}")


def _leaves(x: object):
    if isinstance(x, dict):
        for k, v in x.items():
            if k not in IGNORED:
                yield from _leaves(v)
    elif isinstance(x, list):
        for v in x:
            yield from _leaves(v)
    else:
        yield x


if __name__ == "__main__":
    main()
