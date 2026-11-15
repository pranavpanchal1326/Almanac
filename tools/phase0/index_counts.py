"""Task 0.2: count the supplier index and write the table that replaces section 7's estimates."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

from almanac.io.index import counts_per_year, counts_per_zone, footprint_summary

sys.path.insert(0, str(Path(__file__).parent))
from common import DOCS, INDEX


def main() -> None:
    per_year = counts_per_year(INDEX)
    summary = footprint_summary(INDEX)
    zones = counts_per_zone(INDEX, per_year[-1][0])
    digest = hashlib.sha256(INDEX.read_bytes()).hexdigest()
    lines = [
        "# Supplier index counts (task 0.2)",
        "",
        f"Index file: `aef_index.parquet`, {INDEX.stat().st_size:,} bytes, sha256 `{digest}`.",
        "",
        f"- Files: **{summary['files']:,}** across {summary['years']} years.",
        f"- Distinct tile footprints (zone + south-west corner): **{summary['footprints']:,}**.",
        f"- Footprints present in all {summary['years']} years: **{summary['complete_footprints']:,}**.",
        "",
        "| Year | Files | UTM zones |",
        "|---|---|---|",
        *[f"| {y} | {n:,} | {z} |" for y, n, z in per_year],
        "",
        f"## Files per UTM zone, {per_year[-1][0]}",
        "",
        "| Zone | Files | Zone | Files | Zone | Files | Zone | Files |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for i in range(0, len(zones), 4):
        row = zones[i : i + 4]
        cells = " | ".join(f"{z} | {n:,}" for z, n in row)
        lines.append(f"| {cells} |" + " | |" * (4 - len(row)))
    (DOCS / "index_counts.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:22]))


if __name__ == "__main__":
    main()
