"""Write the file that gets timestamped: SHA-256 of everything issue 2027.01 depends on.

Usage: python tools/prereg/bundle.py 2027.01

Run on a clean tree, at the commit that holds the pre-registration and the baseline report. Writes
docs/prereg/<issue>.code-commit.txt (the commit id) and docs/prereg/<issue>.bundle.sha256 in
sha256sum format, paths relative to the repository root, so `sha256sum -c` checks it from a
clean checkout. Data files are covered through the data manifest's digest.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EVIDENCE = [
    "BLUEPRINT.md",
    "docs/phase1/PLAN.md",
    "docs/phase1/THRESHOLD.md",
    "docs/phase1/threshold_study.json",
    "docs/phase1/bootstrap_coverage.json",
    "docs/phase1/baseline_report.json",
    "docs/phase1/baseline_report.md",
    "docs/phase1/labels_forest_amazon_cerrado.json",
    "docs/phase1/store_amazon_cerrado.json",
    "docs/adr/0001-gate-0.md",
    "docs/adr/0002-regional-start.md",
    ".gitattributes",
    "pyproject.toml",
    "uv.lock",
]


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, cwd=REPO, check=True).stdout


def main() -> None:
    issue = sys.argv[1]
    if git("status", "--porcelain", "--untracked-files=no").strip():
        raise SystemExit("tree has uncommitted changes to tracked files; commit first")
    commit = git("rev-parse", "HEAD").strip()
    prereg = f"docs/prereg/{issue}.md"
    tracked = set(git("ls-files", "-z").split("\0"))
    if prereg not in tracked:
        raise SystemExit(f"{prereg} is not committed")
    commit_file = REPO / "docs" / "prereg" / f"{issue}.code-commit.txt"
    commit_file.write_text(f"{commit}\n", newline="\n")
    code = sorted(p for p in tracked if p.startswith(("src/", "tools/", "tests/", "configs/")) and p)
    paths = [prereg, commit_file.relative_to(REPO).as_posix(), *EVIDENCE, *code]
    missing = [p for p in paths if not (REPO / p).is_file()]
    if missing:
        raise SystemExit(f"missing: {missing}")
    lines = [f"{hashlib.sha256((REPO / p).read_bytes()).hexdigest()}  {p}" for p in paths]
    out = REPO / "docs" / "prereg" / f"{issue}.bundle.sha256"
    out.write_text("\n".join(lines) + "\n", newline="\n")
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    print(f"commit {commit}\n{len(lines)} files\nbundle sha256 {digest}")


if __name__ == "__main__":
    main()
