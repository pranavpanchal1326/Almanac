# Phase 2 — Model: status

Started 2026-11-16. Question: does a learned model beat the best simple method (B4) on places and
years it has not seen? Rules: [pre-registration](../prereg/2027.01.md),
[amendment 2](../prereg/2027.01.amendment-2.md) (stable recipe; FreeTSA 2026-11-17 07:00:36 UTC, DigiCert 07:00:39 UTC, and Bitcoin block 976,246, mined 07:56:28 UTC; the proof's commitment matches that block's Merkle root) and
[amendment 1](../prereg/2027.01.amendment-1.md) (the model specification, timestamped before any
training: FreeTSA 2026-11-15 20:12:41 UTC, DigiCert 20:12:43 UTC, and Bitcoin block 976,013, mined 20:43:06 UTC; the proof's commitment matches that block's Merkle root).

| ID | Task | Status | Evidence |
|---|---|---|---|
| 2.1 | Training store, dataset and balanced sampler | Done | `src/almanac/model/`, `tests/unit/test_model.py` |
| 2.2 | Smoke test; memory and speed; batch and steps by the amendment's rules | Done | Below |
| 2.3 | B5 (no neighbours), scored on validation first | Amendment 1 run: peaked at 0.2816, then collapsed; finishing its steps. A2 run next | `D:/almanac-data/runs/stage_a_b5_s1` |
| 2.4 | Stage A: model M, two schedules, then three seeds | Held: recipe fixed by [amendment 2](../prereg/2027.01.amendment-2.md) | |
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
| B5, attempt 2 | 2026-11-15 21:29 | **Completed** 100,000 steps on 2026-11-17 10:27 UTC (536 minutes). Best validation 2024 forest-loss AP **0.2816 at step 30,000**, the kept checkpoint; then collapsed (0.08–0.20 from step 56,000; 0.1592 at step 100,000). Kept as a reference candidate (amendment 2, section 4). |
| B5 under A2 | 2026-11-17 10:33 | **Completed** 100,000 steps on 2026-11-18 06:57 UTC (641 minutes of training; paused overnight at step 56,000 and resumed from its saved state). No collapse: largest probe attention logit 20.4, lowest mean entropy 0.47. Best validation 2024 forest-loss AP **0.3423 at step 86,000** (embedding task 0.5060), the kept checkpoint; 0.2967 at step 100,000. Reference candidate (amendment 2, section 4). |
| Model M under A2, schedule (a) | 2026-11-18 06:57 | **Completed** 90,000 steps on 2026-11-18 17:47 UTC (647 minutes). No collapse: largest probe logit 13.2, lowest entropy 0.47. Best validation 2024 forest-loss AP **0.3202 at step 86,000** (embedding task 0.4716); 0.3031 at step 90,000. Below B5 under A2 at almost every check. |
| Model M under A2, schedule (b) | 2026-11-19 01:56 | First start on 2026-11-18 17:48 was stopped after 3 minutes, before its first check, for a shutdown, and restarted from step 0. On 2026-11-19 about 09:45 UTC, after the check at step 64,000, a backward pass failed with CUDA out of memory and the process hung without exiting; a web browser was also using the GPU. Found at 11:55 UTC, stopped, and resumed from the saved state at step 64,000 (resume is exact; no configuration change). The same failure followed the check at step 66,000; stopped at 12:24 UTC and resumed from step 66,000 under the supervision described below. **Completed** 90,000 steps on 2026-11-19 15:16 UTC with no further failure. Best validation 2024 forest-loss AP **0.2784 at step 62,000** (embedding task 0.4424); 0.2618 at step 90,000. No collapse, but attention much sharper than schedule (a): largest probe logit 62.8. |
| Model M under A2, schedule (a), seed 2 | 2026-11-19 15:17 | **Completed** 90,000 steps on 2026-11-20 01:37 UTC (617 minutes), no restarts. No collapse: largest probe logit 16.5, lowest entropy 0.47. Best validation 2024 forest-loss AP **0.3332 at step 86,000** (embedding task 0.5256); 0.2748 at step 90,000. |
| Model M under A2, schedule (a), seed 3 | 2026-11-20 01:37 | Stopped by hand at 02:58 UTC for a shutdown; resumed from step 10,000 at 11:02 UTC. At 16:07 UTC the laptop went into standby, which paused training; on waking at 16:27 the supervisor read the 20-minute gap as a hang and stopped the run, and the laptop then shut down. Resumed from the saved state at step 50,000 on 2026-11-21 (resume is exact). Running. |

Fixes after attempt 1: pinned memory only on GPU runs; training saves its full state at every
check and resumes from it (tested: a stopped and resumed run matches an uninterrupted one exactly);
`tools/phase2/run_stage_a.sh` runs B5 and then model M (schedules a and b) and can be rerun at any
time; no other GPU or memory-heavy job runs during training.

## Schedule choice for model M

By the rule of amendment 1 (best validation 2024 forest-loss AP; a tie within 0.002 goes to schedule a): schedule (a) 0.3202, schedule (b) 0.2784. The difference, 0.0418, is far beyond the tie margin, so **schedule (a), constant learning rate 1.1e-4, is chosen**. Seeds 2 and 3 use `configs/model/stage_a2_m_a_s2.json` and `_s3.json`, identical to `stage_a2_m_a.json` except for the seed and the name, and run under the same supervision.

## Supervision of training runs

Two out-of-memory failures in schedule (b), on 2026-11-19, came in the first backward pass after
a validation check, on a card shared with other programs. Each time the process printed the error
and then hung instead of exiting, so the queue could not notice it. Changes, none of which alters a
result (resuming is exact):

- `train.py` releases cached GPU memory after every check (`torch.cuda.empty_cache()`), so the
  next training step finds contiguous memory.
- `train.py` exits at once with status 75 on any error, instead of a normal interpreter exit that
  can hang while data-loader workers shut down; it touches a `heartbeat` file every 50 steps.
- `tools/phase2/run_stage_a.sh` supervises each run: on a failure, or no heartbeat for 15
  minutes, it stops the process tree and resumes from the last check, up to 6 times, logging each
  event to `D:/almanac-data/runs/queue.log`. Tested with stand-in runs that crash once, hang once
  and always fail, an injected error in `train.py`, and a dry run on the CPU.
- Standby (2026-11-20): `train.py` now asks Windows not to idle-sleep while it runs (a request
  held by the process, released when it exits; no power setting is changed), and the supervisor no
  longer counts time the machine was asleep as a stall: a poll that took far longer than its interval
  restarts the stall clock. Tested with a stand-in run and a simulated 131-second suspension.

## Measurements for amendment 2 (A2 networks)

Run on 2026-11-17 after B5 attempt 2 finished, with nothing else on the GPU
(`train.py <config> --smoke`):

| | Model M (A2) | B5 (A2) |
|---|---|---|
| Parameters | 3,916,354 | 3,601,474 |
| Overfit one batch, 250 steps: total loss | 0.851 → −0.290 | 1.465 → −0.275 |
| Batch 8: peak memory, step time | 5.01 GiB, 0.318 s | 4.33 GiB, 0.272 s |
| Batch 16 | out of memory | out of memory |
| Data loading | 2.7 ms per patch (CPU) | 1.8 ms per patch |

Rules of amendment 1, section 5, re-applied as amendment 2 requires: **batch 8** for both. Steps:
8 hours is 28,800 s; at 0.318 s that is 90,566 steps for model M, so **90,000** (largest multiple
of 2,000); at 0.272 s it is 105,882 for B5, so **100,000** (the cap). The step time grew by about 14% (0.278 s to 0.318 s for model M) with the per-head
query-key normalisation.

Configurations after the rules (SHA-256):

| File | SHA-256 |
|---|---|
| `configs/model/stage_a2_b5.json` | `424396210ba755a9b2e0ce1800bbcc1b5f18f07b2473e415ba56f335c98ba63c` |
| `configs/model/stage_a2_m_a.json` | `cbc284d1cf9886bb314639b1b235aae7e778b082decb5ed3026c31e4481fb5a1` |
| `configs/model/stage_a2_m_b.json` | `c12fa3e33be60326d52ee6b9735809dda1cecd2337e573891a528d670ad082ae` |
| `configs/model/stage_a2_m_a_s2.json` | `3ee12de21f0db73e984f932fcfbcbf73748e55189e447fdafe7b2ea6c14e5fb6` |
| `configs/model/stage_a2_m_a_s3.json` | `267abd3f6bb66010704b45c4d30e1ee05d393272d6a7e05e1c1e0e12b88a4267` |

## Diagnosis of the B5 collapse (amendment 1 run)

Validation 2024 forest-loss AP rose to 0.2816 at step 30,000, then fell to 0.08–0.20 by step
56,000. All three training-loss terms got worse together from step 30,000 (forest 0.110 → 0.150,
embedding change 0.046 → 0.081, embedding likelihood −3.41 → −2.02): an optimisation failure, not
overfitting.

`python tools/phase2/diagnose.py configs/model/stage_a_b5.json <step-30,000 checkpoint> <step-58,000
checkpoint>`, 24 training patches, averaged weights:

| Block | Max attention logit, step 30k → 58k | Mean entropy (max 1.79) | Rows >99% on one year |
|---|---|---|---|
| 0 | 1,557 → 3,299 | 0.53 → 0.33 | 0.32 → 0.54 |
| 1–3 | 16–75 → 27–81 | 1.06–1.50 → 1.17–1.27 | 0.00–0.02 → 0.08–0.11 |
| 4 | 5,448 → 8,597 | 0.20 → 0.47 | 0.69 → 0.40 |
| 5 | 142,830 → 272,815 | 0.01 → 0.02 | 0.99 → 0.96 |
| 6 | 195,781 → 250,631 | 0.01 → 0.00 | 0.98 → 0.99 |
| 7 | 66,191 → 101,361 | 0.01 → 0.09 | 0.99 → 0.74 |

Attention in the later blocks had collapsed onto single years with logits far beyond what bfloat16
represents precisely, and the projection weights kept growing (no weight decay). The embedding
head was ruled out: its predicted spread (median 0.024 → 0.063) never reached the 1e-4 floor, and
its standardised errors stayed near 0.7. Fix and rules: [amendment 2](../prereg/2027.01.amendment-2.md).

## The bar

B4 on validation 2024: forest-loss AP 0.2459. The win needs at least 20% more on the exam, plus the
lower interval bound above 10% and a gain on test tiles and held-out region separately.
