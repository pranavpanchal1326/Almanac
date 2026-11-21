# Phase 2 — Model: status

Started 2026-11-16. Question: does a learned model beat the reference (the best simple method on
validation; see [The bar](#the-bar)) on places and years it has not seen? Rules: [pre-registration](../prereg/2027.01.md),
[amendment 2](../prereg/2027.01.amendment-2.md) (stable recipe; FreeTSA 2026-11-17 07:00:36 UTC, DigiCert 07:00:39 UTC, and Bitcoin block 976,246, mined 07:56:28 UTC; the proof's commitment matches that block's Merkle root) and
[amendment 1](../prereg/2027.01.amendment-1.md) (the model specification, timestamped before any
training: FreeTSA 2026-11-15 20:12:41 UTC, DigiCert 20:12:43 UTC, and Bitcoin block 976,013, mined 20:43:06 UTC; the proof's commitment matches that block's Merkle root).

| ID | Task | Status | Evidence |
|---|---|---|---|
| 2.1 | Training store, dataset and balanced sampler | Done | `src/almanac/model/`, `tests/unit/test_model.py` |
| 2.2 | Smoke test; memory and speed; batch and steps by the amendment's rules | Done | Below |
| 2.3 | B5 (no neighbours), scored on validation first | Done: amendment 1 run 0.2816 (then collapsed); amendment 2 run **0.3423**, the reference | [Run log](#run-log) |
| 2.4 | Stage A: model M, two schedules, then three seeds | Done under [amendment 2](../prereg/2027.01.amendment-2.md): schedule (a) chosen; seeds 0.3202, 0.3332, 0.3040 | [Three seeds](#model-m-under-amendment-2-three-seeds) |
| 2.5 | Ablations on validation | Not started | |
| 2.6 | Calibration on validation 2024 | Done: ensemble AP 0.3266 | [Calibration](#calibration-and-the-three-seed-ensemble-validation), `tools/phase2/ensemble.py` |
| 2.7 | Stage B: one evaluation on 2025, logged | Done 2026-11-21: model +16.0% over the reference (95% interval +10.7% to +22.3%); **win condition not met** (needs 20%) | [Stage B result](#stage-b-result-2025-the-single-logged-touch), `docs/phase2/stage_b_report.md` |
| 2.8 | Independent reproduction of stage B | Done 2026-11-21 by independent code: 64 of 64 checks within tolerance (largest difference 4.3e-16); a re-grade by a second person is still open | [Reproduction](#stage-b-reproduction-task-28), `docs/phase2/stage_b_reproduction.md` |
| 2.9 | Gate 2 review | Prepared 2026-11-21 (ADR 0004, proposed): recommends locking the model as the headline, labelled as missing the 20% margin; **decision pending the owner** | [ADR 0004](../adr/0004-gate-2.md) |

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
| Model M under A2, schedule (a), seed 3 | 2026-11-20 01:37 | Stopped by hand at 02:58 UTC for a shutdown; resumed from step 10,000 at 11:02 UTC. At 16:07 UTC the laptop went into standby, which paused training; on waking at 16:27 the supervisor read the 20-minute gap as a hang and stopped the run, and the laptop then shut down. Resumed from the saved state at step 50,000 on 2026-11-21 (resume is exact). After the check at step 58,000 (04:57 UTC) a backward pass failed with CUDA out of memory and the process hung on exit; the supervisor stopped it after 15 minutes and resumed from step 58,000. Stopped by hand right after the check at step 60,000 to load the retry described below, and resumed from step 60,000. At about step 82,800 (08:24 UTC) a backward pass failed with a cuDNN execution error and the process hung inside the GPU driver; the supervisor stopped it after 15 minutes and resumed from step 82,000. **Completed** 90,000 steps on 2026-11-21 09:39 UTC (656 minutes of training). No collapse: largest probe logit 16.5, lowest entropy 0.46. Best validation 2024 forest-loss AP **0.3040 at step 80,000** (embedding task 0.4742); 0.2707 at step 90,000. |

Fixes after attempt 1: pinned memory only on GPU runs; training saves its full state at every
check and resumes from it (tested: a stopped and resumed run matches an uninterrupted one exactly);
`tools/phase2/run_stage_a.sh` runs B5 and then model M (schedules a and b) and can be rerun at any
time; no other training or test job runs during training. (Everyday programs that use the GPU,
such as a web browser, did share the card later; see the supervision section.)

## Schedule choice for model M

By the rule of amendment 1 (best validation 2024 forest-loss AP; a tie within 0.002 goes to schedule a): schedule (a) 0.3202, schedule (b) 0.2784. The difference, 0.0418, is far beyond the tie margin, so **schedule (a), constant learning rate 1.1e-4, is chosen**. Seeds 2 and 3 use `configs/model/stage_a2_m_a_s2.json` and `_s3.json`, identical to `stage_a2_m_a.json` except for the seed and the name, and run under the same supervision.

## Model M under amendment 2: three seeds

| Seed | Best validation 2024 forest-loss AP | At step | Embedding task AP | Largest probe logit |
|---|---|---|---|---|
| 1 | 0.3202 | 86,000 | 0.4716 | 13.2 |
| 2 | 0.3332 | 86,000 | 0.5256 | 16.5 |
| 3 | 0.3040 | 80,000 | 0.4742 | 16.5 |
| Mean (sample s.d.) | **0.3191 (0.0146)** | | | |

B5 under amendment 2, the best reference candidate on validation, reached 0.3423 with one seed. Every seed of model M is below it, the best by 0.0091 and the mean by 0.0232. On validation the spatial context of model M has not yet shown a gain over B5, which sees each place alone. This is a validation result only; the test comparison is the one the pre-registration grades.

## Calibration and the three-seed ensemble (validation)

`tools/phase2/ensemble.py` follows amendment 1, section 7. Each seed's kept weights predict all 146 validation tiles for 2024 (1,531,430 eligible cells, 101,177 forest-loss events, base rate 0.066); its AP is recomputed and checked against the value logged when the checkpoint was kept (all three match to five decimals); its probabilities are mapped by isotonic regression fitted on its own validation predictions; the forecast is the mean of the three mapped probabilities. The maps and scores are in `docs/phase2/ensemble_m_a/` (`calibration.json` SHA-256 `19e03140016e58b825030f4d94b06ece88159f462283827e560c07b18802f455`). The test truth was not read.

| Forecast | AP | Brier | Log loss | ECE |
|---|---|---|---|---|
| Seed 1, raw / calibrated | 0.3201 / 0.3177 | 0.0534 / 0.0512 | 0.1925 / 0.1776 | 0.0218 / 0.0002 |
| Seed 2, raw / calibrated | 0.3332 / 0.3308 | 0.0524 / 0.0509 | 0.1925 / 0.1778 | 0.0238 / 0.0003 |
| Seed 3, raw / calibrated | 0.3040 / 0.3015 | 0.0541 / 0.0520 | 0.1970 / 0.1809 | 0.0243 / 0.0008 |
| **Ensemble (mean of calibrated)** | **0.3266** | 0.0512 | 0.1775 | 0.0015 |

Findings:

- The ensemble's validation AP, 0.3266, is above the mean of the single seeds (0.3191) and below B5 under amendment 2 (0.3423, one seed), the reference. On validation the model does not reach the reference, let alone the 20% margin the win condition requires on the exam.
- Amendment 1 says AP is unchanged by the isotonic map. That is true of the ranking but not exactly of AP as scored: the map is a step function, so it merges nearby scores into ties, and tied scores count as one threshold. Calibration lowers each seed's AP by about 0.0024. The rule is not changed; the forecast stays as fixed, and this is reported.
- The calibration scores are in-sample (each map is fitted on the cells it is scored on), so the low ECE here says little; stage B gives out-of-sample values.

## Stage B: tool and dry run

`tools/phase2/stage_b.py` makes stage B a rehearsal of the exam one year early: the same package
format as the locked forecast, the same grader (`tools/phase5/grade.py`) and win condition, target
2025 on the 499 exam tiles.

- `build` writes the package and reads no truth of the target year: baselines B0–B4 from the
  saved phase 4 models, used only after they score validation 2024 exactly as the baseline report
  does; the model `M_A2` (forest loss: the mean of the three seeds' isotonic-mapped probabilities,
  as amendment 1 fixes; embedding change, secondary: the mean of the seeds' probabilities, since no
  calibration is defined for it); and the reference `B5_A2`, with its probabilities as they were
  when it was chosen (not recalibrated, so the comparison does not favour the model). The model's
  inputs are built with `make_example(..., truth=False)`, which does not read the target year's
  labels at all (tested: the inputs are identical).
- `grade` is the single touch. It refuses without `--confirm-single-touch`, refuses if a stage B
  touch is already logged, refuses a package that changed since it was built or was built for the
  dry run, then scores both tasks on all exam tiles, the test tiles and the held-out region,
  applies the win condition against `B5_A2`, writes `docs/phase2/stage_b_report.{json,md}` and
  appends the touch to `docs/phase1/test_touch_log.jsonl`. Guards tested in
  `tests/unit/test_stage_b.py`.

**Dry run** (validation 2024, 146 tiles; no test data; nothing logged): built in 14 minutes, graded
in 45. Every known value is reproduced:

| Check | Dry run | Known value |
|---|---|---|
| B0–B4, both tasks (10 values) | equal to 7–8 decimals | baseline report, validation 2024 |
| `M_A2`, forest loss | 0.32660007 | 0.32660007 (`ensemble.py`) |
| `B5_A2`, forest loss | 0.34226808 | 0.34227 (training log) |

Dry verdict, for the record (validation, so it grades nothing): `M_A2` against `B5_A2`, −4.6%
(95% interval −12.6% to +11.0%); no condition met. On the secondary embedding-change task the
model leads: `M_A2` 0.5103, `B5_A2` 0.5060, B4 0.3471.

Expected time for the real run: about 40 minutes to build and 2–3 hours to grade (3.2 times the
validation cells).

## Stage B result (2025, the single logged touch)

Built 2026-11-21 from commit `fc0d158` in 41 minutes (package `D:/almanac-data/packages/stage_b_2025`,
digest `5e995faff2132247f4534aff7bfe8b2587290d8774040d4d39b837114ccb029e`; every baseline reproduced
validation 2024 before use); graded once in 2 h 28 min, the touch logged at 15:23 UTC in
`docs/phase1/test_touch_log.jsonl` with the package digest and the report's SHA-256 (`a2bebf41…`,
which matches the committed `stage_b_report.json`). The package verified unchanged after grading.
Full tables: [stage_b_report.md](stage_b_report.md).

**Win condition (forest loss, 499 exam tiles, against `B5_A2`):**

| Condition | Result | Met |
|---|---|---|
| Improvement at least 20% | +16.0% | No |
| Lower end of the 95% interval above 10% | +10.7% (interval +10.7% to +22.3%) | Yes |
| Positive on the test tiles and on the held-out region | +14.4% and +15.7% | Yes |
| **Win** | | **No** |

| Forest-loss AP, 2025 | All (499) | Test (379) | Held-out (120) |
|---|---|---|---|
| `M_A2` (model, three-seed ensemble) | **0.4683** | **0.3605** | **0.6725** |
| `B5_A2` (reference) | 0.4036 | 0.3152 | 0.5815 |
| B4 (trees) | 0.3862 | 0.3151 | 0.5485 |

What this says, without softening either way:

- The model is the best forecast on the exam for forest loss, on both parts, and the gain over the
  reference is clearly above zero; but it falls short of the 20% margin fixed before training, so by
  the pre-registered rule it **does not win**.
- The order flipped from validation: there the ensemble was 4.6% below the reference, on 2025 it is
  16.0% above. Validation is 146 tiles and one year, so its estimate was noisy (the dry interval
  ran from −12.6% to +11.0%); the reference was also chosen as the best of six on validation, which
  favours it there.
- Calibration is the model's weak point: ECE 0.0288 against B4's 0.0031, and B4 has the best Brier
  score (0.02994 against 0.03046) and log loss. The isotonic maps fitted on 2024 do not carry over
  to 2025 well; the ranking does.
- Secondary task (embedding change): model 0.4951, reference 0.4708, B4 0.4896; a small lead,
  positive on both parts.

**What follows is not decided here.** Amendment 2, section 5 says the best baseline's forecast is
locked if the A2 runs do not beat the reference. The model beats the reference but does not meet
the win condition; which reading applies is for the Gate 2 review (task 2.9), against the
amendment's text, with no new amendment (section 5 rules one out).

## Stage B reproduction (task 2.8)

`tools/phase2/reproduce_stage_b.py` re-grades the stage B package without any of the code that
graded it: it imports nothing from `almanac`, `stage_b.py` or `grade.py`; it takes truth and
eligibility from the source label stores and the stream summaries' validity bits (stage B read
the training store, a copy of them), following the pre-registration's section 3 text; it scores
AP with scikit-learn, and the bootstrap with its own weighted routine, checked against
scikit-learn on weighted draws. It first checks the package against the logged digest and the
stage B report against its logged SHA-256. Tolerances were fixed in the code before the run:
counts exact, every value within 1e-9.

Run once on 2026-11-21 (commit `c231ee9`, 7 minutes), logged in `docs/phase1/test_touch_log.jsonl`
as a read of the 2025 test truth:

| What was compared | Checks | Largest difference |
|---|---|---|
| Cells and events, all, test and held-out | 6 | 0 (exact) |
| Forest-loss AP of all 7 forecasts, three parts | 21 | 5.6e-17 |
| Brier score of all 7 forecasts, three parts | 21 | 0 (exact) |
| Improvement over the reference, all and each part | 3 | 2.2e-16 |
| Bootstrap intervals (improvement; AP of model and reference) | 6 | 4.3e-16 |
| Weighted AP routine against scikit-learn, 3 draws × 2 forecasts | 6 | 5.6e-17 |
| Win verdict | 1 | equal (no win) |

**Deviation.** Amendment 1, section 8 forbids any run that reads the 2025 test truth other than
the single stage B evaluation; this reproduction read it a second time. It scored the same frozen
package (digest checked first), changed nothing and found nothing new, and it is logged; it is
disclosed in [ADR 0004](../adr/0004-gate-2.md). No further run reads the 2025 test truth for issue
2027.01; the second person's check will rebuild the package instead.

The stage B result stands as graded: **+16.0% (95% interval +10.7% to +22.3%), no win.** Full
table: [stage_b_reproduction.md](stage_b_reproduction.md). The blueprint (task 2.8) asks for a
second person; this reproduction is by separate code from the same team, so a second person's
re-grade is still open, and the tool is written so that anyone with the package and the label
stores can run it.

## Frozen weights

The kept checkpoints (`best.pt`, averaged weights) that stage B and the forecast use. They live in
`D:/almanac-data/runs/<run>/`, with a second, hash-checked copy on another drive.

| Run | Role | Step | SHA-256 |
|---|---|---|---|
| `stage_a2_b5_s1` | Reference (B5 under amendment 2) | 86,000 | `bcfd6cd4b72077e968576cea19eb0e62e3d31383386a3ea3104f74deb109cdb6` |
| `stage_a2_m_a_s1` | Model M, seed 1 | 86,000 | `0aced0fdfdf8b8cf091f636d49f448ff8897d6967866048be2a0a7388b769117` |
| `stage_a2_m_a_s2` | Model M, seed 2 | 86,000 | `7c7e5bd345c811ab3a9aa8d3dbc14297bd175ddb2aae55139ff307a2b78e0bad` |
| `stage_a2_m_a_s3` | Model M, seed 3 | 80,000 | `3437866de8705e0b18f800cdaae6a6e353596c9f99a7d67f436cc74bc4ca834d` |

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
- Out of memory (2026-11-21, a third time, again in the first backward pass after a check): the
  card is shared with a web browser and a desktop app whose GPU memory varies, and training needs
  5.9 of its 8.2 GB (the data-loader workers hold none). A training step that runs out of GPU memory
  is now retried on the same batch with the random state it started from, after freeing the cache
  and waiting 20 s, up to 6 times; no weight has changed at that point, so the result is the same as
  if nothing had failed (tested: identical gradients after two injected failures). If the retries run
  out, the process ends through `TerminateProcess`, which cannot hang in the driver as a normal exit
  did, so the supervisor restarts it within seconds.
- Hung exit (2026-11-21, after a cuDNN execution error at step about 82,800): the process printed the
  error and then stayed alive even through `TerminateProcess`, held by a call stuck in the GPU driver,
  until the 15-minute stall limit. `train.py` now writes a `failed` marker before it exits, and the
  supervisor stops a process that has written it but is still alive 10 s later, from outside. Tested
  with a stand-in run that reports a failure and hangs: stopped in 14 s and resumed to completion.
  Errors other than running out of memory are not retried in the process, since they can leave the
  GPU context unusable; they restart from the last check.

These recovery paths are covered by `tests/unit/test_training_robustness.py`: the step retry
(identical gradients, GPU), the exit code, and the supervisor with stand-in runs that crash once,
always fail, report a failure and hang, stop beating, or are suspended together with the
supervisor (the supervisor tests are marked `slow`).

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

The reference is the best validation 2024 forest-loss AP among B1–B4, B5 under amendment 1 and B5
under amendment 2 ([amendment 2, section 4](../prereg/2027.01.amendment-2.md)):

| Candidate | Validation 2024 forest-loss AP |
|---|---|
| B4 (gradient-boosted trees) | 0.2459 |
| B5 under amendment 1 (kept checkpoint) | 0.2816 |
| **B5 under amendment 2** | **0.3423**, the reference |

The win needs the model's AP on the exam to be at least 20% above the reference's, the lower end of
the 95% interval of that improvement above 10%, and a gain on the test tiles and on the held-out
region separately (pre-registration, section 4). On validation the model's ensemble, 0.3266, is
4.6% below the reference. Amendment 2, section 5 fixes what follows if the A2 runs do not beat the
reference: the result is reported as it is and the best baseline's forecast is locked (blueprint
16.4). That decision belongs to the Gate 2 review. Stage B (2025): the model is 16.0% above the
reference, short of the 20% margin; see [Stage B result](#stage-b-result-2025-the-single-logged-touch).
