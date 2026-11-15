# Phase 1 — Scoreboard: status

Updated 2026-11-15. Scope is the Amazon + Cerrado region ([ADR 0002](../adr/0002-regional-start.md));
the plan to the lock is in [PLAN.md](PLAN.md). Gate 1 on 6 December.

| ID | Task | Status | Evidence |
|---|---|---|---|
| 1.1 | Streaming reader with resume and a concurrency cap | Done | Tests; trial below |
| 1.2–1.3 | Region data on disk | Done | [store_amazon_cerrado.json](store_amazon_cerrado.json) |
| 1.4 | Forest-loss label at 640 m | Done | [labels_forest_amazon_cerrado.json](labels_forest_amazon_cerrado.json) |
| 1.7 | Split | Done, fixed by the pre-registration | `configs/splits/amazon_cerrado_v1.*` |
| 1.8 | Change threshold, redesigned | Done | [THRESHOLD.md](THRESHOLD.md) |
| 1.9–1.11 | Baselines, evaluation harness, baseline report | Done | [baseline_report.md](baseline_report.md) |
| 1.13 | Pre-registration | Accepted 2026-11-15, timestamped | [2027.01.md](../prereg/2027.01.md), [proofs](../prereg/proofs/README.md) |
| 1.5, 1.6, 1.12 | Built-up label, drivers, detail blocks | Parked | PLAN.md |

## Region store (1.2–1.3)

| Measure | Value |
|---|---|
| Tiles on disk | 2,020 of 2,020 |
| Files read | 18,099 |
| Tiles lacking at least one year | 23 (2017–2020 and 2022 are the incomplete years) |
| Transfer | 12.5 GB, in 28,152 requests after the client fix, 1 retry, 0 failures |
| Embeddings on disk | 10.1 GB (`D:\almanac-data\embeddings`), stored values as read |
| Summaries on disk | 0.14 GB |
| Cells with data | 81% (the rest is sea or outside coverage) |
| Tile-years with vector length outside [0.98, 1.02] | 0 |
| Files with the wrong shape or type | 0 |

The first run used HTTP/2 and lost 27 tiles to protocol errors raised when one connection was
shared between threads. The client now uses HTTP/1.1 with connection reuse and retries every
transport error. The re-run completed every tile.

Not checked: gate Q8 (re-reading entity tags) and gate Q9 (duplicates). Tiles of neighbouring UTM
zones overlap, so some ground is held twice; anything that sums area over tiles must allow for it.

## Forest-loss label (1.4)

Source: Global Forest Change v1.13, loss year and data mask, CC-BY 4.0 (licence read from the
producer's page). Each 640 m cell is sampled at 20 × 20 points, 32 m apart.

Per tile: share of each cell lost in each year 2018–2025, share lost 2001–2017, and share of land.

| Check | Result | Target |
|---|---|---|
| Lost area from the label ÷ lost area counted on the 30 m source, 25 random tiles, all years | 1.001 | within 2% |
| Same, worst single year | 1.0021 | within 2% |

Lost area by year over all tiles (million hectares; overlapping tiles counted twice, so compare
years, not absolute size):

| 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| 4.99 | 5.30 | 5.46 | 5.34 | 5.84 | 5.70 | **8.55** | 5.47 |

2024 is about 1.5 times a normal year, consistent with that year's drought and fires. Any fold
that tests on 2024 faces a year unlike its training years, and fire loss is not the same event as
clearing. The blueprint's check against published country totals was not done; it needs country
boundaries, which are not in the project yet.

## Split (1.7)

Super-blocks of 2° × 2° assigned by a seeded hash, 70 / 10 / 20. The south-west Amazon
(68°W–60°W, 13°S–7°S) is held out of training entirely. Training tiles that touch a scored tile
are set aside.

| Split | Tiles | Super-blocks |
|---|---|---|
| Train | 800 | 165 |
| Buffer (unused) | 575 | — |
| Validation | 146 | 21 |
| Test | 379 | 49 |
| Held-out region | 120 | 16 |

No training tile touches a validation, test or held-out tile. The buffer costs 28% of the tiles;
that is the price of the no-shared-edge rule with blocks this small. The split is a proposal until
it is fixed in the pre-registration: the seed, the block size and the held-out box can still change,
but not after any model has been scored.

## Task 1.1 trial, for the record

150 tiles of zone 50N: two requests per file, 4.9 MB per tile, about 1,830 tiles an hour, and a
re-run that skipped everything. Scaled to the planet: about 19 hours and 170 GB. Not run; see
ADR 0002.

## Forest extent (added for 1.9)

Forest at the start of a year: share of a cell's 400 sample points with tree cover in 2000 of at
least 30% (Global Forest Change treecover2000, downloaded 2026-11-15, 16 rasters, checksums in
`D:/almanac-data/labels/gfc/SHA256SUMS`) and no earlier loss. Not checked against published
forest area.

## Change threshold (1.8)

Per-class rule chosen; it catches 13% of forest-loss cells at a 1% false-alarm rate on stable land,
against 7% for one regional threshold. Embedding change is a weak detector of forest loss at
640 m, and its rate drifts upward 2020–2025. Details in [THRESHOLD.md](THRESHOLD.md).

## Baselines (1.9–1.11)

Forest-loss task, average precision (base rate in brackets):

| Set | B0 | B2 last change | B3 proximity | B4 trees |
|---|---|---|---|---|
| Validation 2024 | (0.066) | 0.089 | 0.200 | **0.246** |
| Validation 2023 | (0.035) | 0.065 | 0.129 | **0.216** |
| Test 2025 | (0.035) | 0.063 | 0.160 | **0.315** |
| Held-out region 2025 | (0.051) | 0.214 | 0.283 | **0.549** |

B1 scores as B2 (identical change score, as derived). B4 is the reference for the win condition.
The report was generated twice, from two commits, and every one of its numbers matched
(`tools/phase1/compare_reports.py`). Both runs read the 2025 test truth and are logged in
[test_touch_log.jsonl](test_touch_log.jsonl).

The tile bootstrap undercovers AP when few tiles carry the signal
([bootstrap_coverage.json](bootstrap_coverage.json)); the pre-registration adds a guard for it.

## Gate 1

Decision record: [ADR 0003](../adr/0003-gate-1.md), accepted 2026-11-16. Passes on every condition
but the public commit; no model is trained until `ed2cf4f` is public.

| Condition | State |
|---|---|
| Baseline report reproduces | Yes: two runs, identical |
| Split committed | Yes |
| Threshold committed | Yes |
| Pre-registration timestamped | Yes: FreeTSA and DigiCert RFC 3161 tokens (2026-11-15 19:05 UTC), OpenTimestamps pending; [record](../prereg/2027.01.record.md) |
| Public commit | **No.** The repository has no public remote yet |

## Next

1. Publish the repository (or at least the pre-registration commit) so the commit is public.
2. Upgrade the OpenTimestamps proof once Bitcoin confirms it (`ots upgrade`).
3. Phase 2: specify the model in section 10 of the pre-registration before training it.
