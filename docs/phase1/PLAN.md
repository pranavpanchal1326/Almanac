# Plan to the first lock: Amazon + Cerrado, forest loss

Proposed 2026-11-15, after ADR 0002. It replaces blueprint section 16.3 onward for now. The lock
date stays 15 January 2027.

## What is built before the lock

| # | Item | Blueprint tasks | Done when |
|---|---|---|---|
| 1 | Region data on disk: 640 m embeddings, nine years, 2,020 tiles | 1.1–1.3 | Store report shows every tile and year, gates pass |
| 2 | Forest-loss label per cell and year, from Global Forest Change v1.13 | 1.4 | Lost area from the label matches the source within 2% on sample tiles |
| 3 | Fair split in space and time, inside the region | 1.7 | No test tile touches a training tile; split file committed |
| 4 | Change threshold, redesigned | 1.8 | Rule chosen from the region's change statistics and compared with the forest label |
| 5 | Baselines B0–B4 and the evaluation harness | 1.9–1.11 | Baseline report regenerates from one command |
| 6 | Pre-registration, timestamped, before any model is trained | 1.13 | Public commit and timestamp exist |
| 7 | The model, compared with the baselines | Phase 2 | Gate 2 decision recorded |
| 8 | Forecast for 2026, locked | Phase 4 | Package digest published |
| 9 | Public write-up, misses included | — | Repository public |

## Two primary tasks, reported separately

- **Forest loss (label task).** For each 640 m cell with forest, will measurable loss happen next
  year? Truth is the independent yearly map. This is the headline, because the truth does not
  come from the embeddings.
- **Embedding change.** As in the blueprint, once item 4 gives a usable threshold. Secondary.

## Parked until after the lock

Built-up labels and drivers (1.5, 1.6 beyond what the baselines need), the 200 detail blocks
(1.12), second-source embeddings, fine-resolution levels, the interface, tiles, web app, reports,
accounts, pricing, cloud infrastructure, orchestration, security compliance and legal work.

## Blueprint sections this overrides

| Section | Change |
|---|---|
| 7.6, 8.1, 8.6 | No sampling: the whole region is kept at 640 m, about 8 GB |
| 8.2 | Tile ID is zone + south-west corner |
| 8.4, 3.9 | Splits are sub-regions of one region, not continents |
| 3.4 | Threshold rule withdrawn (ADR 0001) |
| 2.2, 22 | No global public layer at the first lock; the claim is regional |

## Risks specific to this plan

- A proximity baseline may be very hard to beat on a single clearing front.
- The 2025 layer may differ systematically from earlier years (seen at one site in Phase 0).
- One person, eight weeks. If time runs short, cut item 7 to one model size and keep items 5, 6
  and 8: a locked, graded baseline forecast is still a result.
