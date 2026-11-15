# Phase 2 — Model: status

Started 2026-11-16. Question: does a learned model beat the best simple method (B4) on places and
years it has not seen? Rules: [pre-registration](../prereg/2027.01.md) and
[amendment 1](../prereg/2027.01.amendment-1.md) (the model specification, timestamped before any
training: FreeTSA 2026-11-15 20:12:41 UTC, DigiCert 20:12:43 UTC, OpenTimestamps pending).

| ID | Task | Status | Evidence |
|---|---|---|---|
| 2.1 | Training store, dataset and balanced sampler | Done | `src/almanac/model/`, `tests/unit/test_model.py` |
| 2.2 | Smoke test; memory and speed; batch and steps by the amendment's rules | Next | |
| 2.3 | B5 (no neighbours), scored on validation first | Not started | |
| 2.4 | Stage A: model M, two schedules, then three seeds | Not started | |
| 2.5 | Ablations on validation | Not started | |
| 2.6 | Calibration on validation 2024 | Not started | |
| 2.7 | Stage B: one evaluation on 2025, logged | Not started | |
| 2.8 | Independent reproduction of stage B | Not started | |
| 2.9 | Gate 2 review | Not started | |

## Training store (2.1)

2,020 tiles as memory-mapped arrays under `D:/almanac-data/store_v1` (about 20 GB), built by
`tools/phase2/build_store.py` in about 4 minutes. Labels are copied bit for bit; on two real
tiles, three years and both tasks, the eligible cells and events equal the baselines' exactly.

## The bar

B4 on validation 2024: forest-loss AP 0.2459. The win needs at least 20% more on the exam, plus the
lower interval bound above 10% and a gain on test tiles and held-out region separately.
