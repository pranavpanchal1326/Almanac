# Phase 2 — Model: status

Started 2026-11-16. Question: does a learned model beat the best simple method (B4) on places and
years it has not seen? Rules: [pre-registration](../prereg/2027.01.md) and
[amendment 1](../prereg/2027.01.amendment-1.md) (the model specification, timestamped before any
training: FreeTSA 2026-11-15 20:12:41 UTC, DigiCert 20:12:43 UTC, and Bitcoin block 976,013, mined 20:43:06 UTC; the proof's commitment matches that block's Merkle root).

| ID | Task | Status | Evidence |
|---|---|---|---|
| 2.1 | Training store, dataset and balanced sampler | Done | `src/almanac/model/`, `tests/unit/test_model.py` |
| 2.2 | Smoke test; memory and speed; batch and steps by the amendment's rules | Done | Below |
| 2.3 | B5 (no neighbours), scored on validation first | Running (attempt 2) | `D:/almanac-data/runs/stage_a_b5_s1` |
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

## Smoke test and measurements (2.2)

`python tools/phase2/train.py <config> --smoke`, RTX 5060 Laptop GPU (8 GiB), bfloat16.

| | Model M | B5 (no spatial mixing) |
|---|---|---|
| Parameters | 3,914,818 | 3,599,938 |
| Overfit one batch of 8, 300 steps: forest loss | 0.529 → 0.044 | learns (total 1.04 → −0.29) |
| Batch 8: peak memory, step time | 4.29 GiB, 0.278 s | 3.60 GiB, 0.230 s |
| Batch 16 | out of memory | out of memory |
| Data loading | 1.3 ms per patch (CPU) | same |
| Validation pass (146 tiles, both tasks) | about 1.4 min | less |

Rules of amendment 1, section 5, applied: batch 16 does not fit under 6.4 GiB, so **batch 8**;
8 hours at the measured step time is over 100,000 steps for both, so **100,000 steps** (the cap).
The blueprint's estimate of 3–5 GB for M at batch 16 was too low by about half.

Configurations after the rules (SHA-256):

| File | SHA-256 |
|---|---|
| `configs/model/stage_a_b5.json` | `d6bcd5854baf2bf769f2625d83d352429c2886827aa1e666d9fbb7e2e8707456` |
| `configs/model/stage_a_m_a.json` | `65a6703b40afa6acae5dadaf2d3cdcbecb445bf61968755c3b7a32d91a1cc438` |
| `configs/model/stage_a_m_b.json` | `f69f0a01d27ec93c77921c3ba7fb6b8d59154e2c4944c9a780e2faf01f6a44b2` |

Expected wall time per run: about 8 hours of steps plus about 70 minutes of validation; five runs
(B5, M with two schedules, two more seeds) about 45 hours on this laptop.

On Windows the GPU driver spills to system memory instead of failing when a batch does not fit,
which is silently about 50 times slower; the training script caps the allocator at 95% of the card
so an oversized batch fails at once.

## Run log

| Run | Started (UTC) | Outcome |
|---|---|---|
| B5, attempt 1 | 2026-11-15 20:31 | **Crashed** after step 6,000, before the next check (GPU out of memory). A test job started alongside it on the CPU created a CUDA context through pinned memory and took GPU memory B5 needed. Validation 2024 forest-loss AP at steps 2,000 / 4,000 / 6,000: 0.2414 / 0.2479 / 0.2394. Kept in `D:/almanac-data/runs/failed/`. |
| B5, attempt 2 | 2026-11-15 21:29 | Running, from step 0, with the same configuration and seed. |

Fixes after attempt 1: pinned memory only on GPU runs; training saves its full state at every
check and resumes from it (tested: a stopped and resumed run matches an uninterrupted one exactly);
`tools/phase2/run_stage_a.sh` runs B5 and then model M (schedules a and b) and can be rerun at any
time; no other GPU or memory-heavy job runs during training.

## The bar

B4 on validation 2024: forest-loss AP 0.2459. The win needs at least 20% more on the exam, plus the
lower interval bound above 10% and a gain on test tiles and held-out region separately.
