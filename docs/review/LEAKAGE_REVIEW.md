# Leakage review kit, issue 2027.01

**For:** someone who did not build the model and is comfortable reading Python and thinking about
train and test splits. **Time:** about two hours. **Data needed:** none. Everything here runs
from a clean clone.

**Why it matters.** A forecast can look better than it is if anything from the future, or from
the places it is graded on, leaks into what it learned or what it was given. The builder is the
worst person to look for that, because they know how it is supposed to work. Almanac is built by
one maintainer ([ADR 0005](../adr/0005-single-maintainer.md)), so this review is the one check
that needs you.

**What you are asked to do:** run one script, answer the questions below with *yes*, *no* or
*unsure*, note anything that worries you, and submit the result as a GitHub issue using the
*Leakage review* template. A finding against the project is as welcome as a clean bill: both are
published.

---

## Part A: the automated checks (10 minutes)

```bash
git clone https://github.com/pranavpanchal1326/Almanac && cd Almanac
uv sync
uv run python tools/review/leakage_selfcheck.py
```

It checks, from committed files only:

1. the split, threshold and data manifest match the digests fixed in the pre-registration;
2. every tile is in one split, and no training tile touches a scored tile;
3. every training configuration stops at target year 2023, and the training script refuses later years;
4. calibration was fitted on the 146 validation tiles of 2024 only;
5. every read of the 2025 test truth is logged, and stage B read it once;
6. the 2026 forecast used the frozen weights recorded before it;
7. the leakage tests on synthetic data pass: changing anything from the target year onward
   changes no input.

Add `--extra train` to `uv sync` (a larger download, PyTorch) to include the two model-input
tests; without it the script says it skipped them. It must end with `ALL PASS`. **Q-A.** Did it? Paste the output into your report.

---

## Part B: the questions only a person can answer (about 90 minutes)

Read the code at each location and answer. Line numbers are as of the sealed forecast.

### B1. Space: can an exam tile leak into training?

- The split assigns 2° super-blocks to train, buffer, validation, test and held-out; training tiles
  that touch a scored tile become buffer. [`src/almanac/data/splits.py`](../../src/almanac/data/splits.py),
  [`tools/phase1/make_split.py`](../../tools/phase1/make_split.py), report in
  [`configs/splits/amazon_cerrado_v1_report.json`](../../configs/splits/amazon_cerrado_v1_report.json).
- The model reads 32-cell patches inside one tile (each tile is stored and read on its own:
  [`src/almanac/model/store.py`](../../src/almanac/model/store.py)), so a training patch cannot
  contain cells of another tile.

**Q-B1.** Can any input to a training example contain cells of a validation, test or held-out
tile? Is the touching rule (shared edge or corner, with a margin) enough for 82 km tiles and a
neighbourhood of 32 cells?

### B2. Time: can the target year leak into the inputs?

- [`src/almanac/model/data.py:141-185`](../../src/almanac/model/data.py): `history_years` gives
  the five years before the target; `make_example` reads embeddings and loss labels only for those
  years, and with `truth=False` (used for every forecast) reads no target-year label at all.
- One static input is `forest_start_{target}`: forest at the *start* of the target year. Check in
  [`src/almanac/data/labels.py`](../../src/almanac/data/labels.py) that it depends only on loss up
  to the year before (test: `tests/unit/test_labels.py::test_forest_by_year_tracks_standing_forest`).
- The baselines' features: [`src/almanac/baselines/features.py:100-130`](../../src/almanac/baselines/features.py),
  where `issue = target - 1` is the last year used.

**Q-B2.** Does any input for target year *Y* depend on data from *Y* or later? Pay special
attention to `forest_start_{target}`, the cumulative-loss input, and eligibility.

### B3. Choosing on the test: was the test year used to make any choice?

- Model and schedule choice, early stopping and calibration all use validation 2024:
  [`tools/phase2/train.py`](../../tools/phase2/train.py), [`tools/phase2/ensemble.py`](../../tools/phase2/ensemble.py),
  [Phase 2 status](../phase2/STATUS.md).
- The reference was chosen on validation 2024 before the backtest
  ([amendment 2, section 4](../prereg/2027.01.amendment-2.md)).
- Every read of the 2025 truth: [`docs/phase1/test_touch_log.jsonl`](../phase1/test_touch_log.jsonl).
  The fourth read, a re-grade after stage B, is disclosed as against the protocol in
  [ADR 0004](../adr/0004-gate-2.md).

**Q-B3.** Could any setting, checkpoint, map or decision have been influenced by 2025 truth? Did
the re-grade after stage B change anything that went into the 2026 forecast?

### B4. The forecast itself: is it the frozen model, unchanged?

- [`tools/phase4/forecast_exam.py`](../../tools/phase4/forecast_exam.py) refuses to run unless
  the checkpoints and maps match the stage B record, and calls the stage B code with target 2026.
- The package digest has been public since 22 Nov 2026 and is timestamped
  ([proofs](../phase4/proofs/README.md)).

**Q-B4.** Is there any path by which the 2026 layers could differ from what the frozen model and
fixed maps produce?

### B5. Limits the project states: do you accept them?

- **Inputs and labels share satellites.** AlphaEarth embeddings fuse several sensors, including
  Landsat; the Global Forest Change labels come from Landsat. Clearing visible in the embedding of
  year *Y−1* is legitimate history, but a reviewer should say whether this makes the task easier
  than it looks.
- **Possible shift in the 2025 embedding layer.** Phase 0 noted a possible systematic difference
  in the 2025 layer ([report](../phase0/REPORT.md)); 2025 is an input year for the 2026 forecast.
- **No drivers.** The forecast uses no roads, prices or policy data, so there is no "valid as of"
  date to check; confirm that nothing else enters the model.

**Q-B5.** Do you see any other source of leakage, or a reason the backtest would overstate skill?

---

## Part C: your verdict

Choose one: **No leakage found** · **Concerns, none disqualifying** · **Leakage found**.

Submit it as a GitHub issue with the *Leakage review* template, or by pull request adding
`docs/review/<your-name>-2027.01.md`. Your report is published as written, and ADR 0005 and the
forecast label are updated to say the review happened and what it found.
