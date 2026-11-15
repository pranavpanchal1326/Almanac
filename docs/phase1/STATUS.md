# Phase 1 — Scoreboard: status

Started 2026-11-15. Calendar weeks: 23 Nov–6 Dec. Gate 1 on 6 December.

| ID | Task | Status |
|---|---|---|
| 1.1 | Streaming reader for L6 with resume and a concurrency cap | **Done**, trialled on 150 tiles |
| 1.2 | Commit the patch-selection rule, run the pass over the planet | Not started; needs a go-ahead (below) |
| 1.3–1.13 | Store, labels, drivers, splits, threshold, baselines, harness, report, pre-registration | Not started |

## Task 1.1: what was built

- `almanac stream level --out <folder> [--zone 50N] [--limit N] [--workers 12]` reads the 640 m
  level of every tile for all nine years and writes one summary file per tile. Nothing else is
  kept.
- `almanac stream coverage --out <folder>` reports tiles visited per year and bytes.
- **Two requests per file.** The header and every level's directory fit in the first 128 KiB, and
  the 64 planes of the 640 m level lie in one span that ends within 1.2 MB of the start of the
  file. The reader fetches the header, then exactly that span. The result equals a standard read,
  value for value (live test). This answers open questions 4 and 6: there is no need to go
  through the sidecar file for coarse levels, and the planes of a level are stored together.
- **Resume.** A summary is written whole or not at all. A second run skips every tile that has
  one. Tested by killing a synthetic supplier part-way and re-running: nothing lost, nothing read
  twice.
- **Concurrency cap.** One client object holds a semaphore; more than 16 connections is refused
  at construction. The trial peaked at 12 in flight.

### What a summary holds

One file per tile, about 53 KB: the change between each pair of consecutive years for every cell
(one byte per cell, square-root scale), validity per year, no-data share, vector-length
percentiles, and the address, entity tag, date, size and content digest of every file read.

The blueprint asked for change counts per patch above the threshold. The whole change field is
kept instead, because the threshold rule is open (ADR 0001). Any rule can then be tried in task 1.8
without streaming the planet again.

## Trial: 150 tiles of zone 50N, nine years

| Measure | Value |
|---|---|
| Files read | 1,350 |
| Time | 296 s at 12 connections: about 1,830 tiles an hour |
| Transfer | 735 MB: 4.9 MB per tile, 544 KB per file |
| Requests | 2,700, of which 118 (4%) needed a retry |
| Failures | 0 |
| Summaries on disk | 8 MB: 53 KB per tile |
| Re-run | 150 skipped, 0 requests |
| Share of cells with data | 57% (the rest is sea) |

### Projection to the planet

| Measure | Projection for 34,266 tiles | Blueprint acceptance |
|---|---|---|
| Time | about 19 hours | "a night" |
| Transfer | about 170 GB | planned 130 GB |
| Requests | about 605,000 | — |
| Disk | about 1.8 GB | under 2 GB |

These scale one zone's first 150 tiles to the world. Zones with more land will cost more per
tile, so treat the transfer and disk figures as rough. The 4% retry rate says the mirror is
already pushing back at 12 connections; going to 16 is unlikely to help.

### First look at change at 640 m (one zone, not the world)

Over all cells with data in the 150 tiles: median change 0.025, 99th percentile 0.25. The share of
cells above a fixed threshold of 0.2 swings from 0.1% to 4.6% between year pairs. A fixed global
threshold would therefore make "how much changed" depend mostly on which year pair it is. This
supports setting the threshold relative to each year pair, each cell's own history, or both.

## Decision needed before task 1.2

The store of kept patches (task 1.3) needs the selection rule, the rule needs the threshold, and
the threshold needs the planet's change statistics. So the planet has to be read twice:

1. **Summary pass**: about 19 hours and 170 GB of transfer. It can start now; it does not depend
   on any open decision.
2. **Selection pass**, after task 1.8 fixes the threshold and the rule is committed: about the
   same again, keeping the embeddings of the chosen patches.

The alternative is one pass with a provisional threshold, then re-reading if the threshold
changes. Given what Phase 0 found about the threshold, two passes is the safer plan. It doubles
the transfer on a free mirror, so the pass should run once, at night, at 12 connections or fewer.
