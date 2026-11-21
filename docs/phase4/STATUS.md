# Phase 4 — Lock: preparation

Started 2026-11-16, alongside Phase 2 training. The lock is on 15 January 2027 and does not move.
The baseline forecasts and the package were prepared first, so a baseline could be locked if no
model cleared the bar.

**Gate 2 decision (2026-11-21, [ADR 0004](../adr/0004-gate-2.md)):** outcome Partial. The headline
of issue 2027.01 is model M (A2), locked with the reference B5 (A2) and B0–B4 in one package; the
exam's win condition is unchanged. The public label is fixed in [LABEL.md](LABEL.md).

| ID | Task | Status | Evidence |
|---|---|---|---|
| 4.3 | Baseline forecasts for 2026, B0–B4, on the 499 exam tiles | Done | `D:/almanac-data/packages/2027.01/baselines/` (10 layers, float32) |
| 4.5 | Package format: layers, canonical manifest, package digest | Done | `src/almanac/registry/package.py`, `tests/unit/test_package.py` |
| — | Grader for the exam (win condition with the guard) | Done, tested against the report; reference corrected to B5 under amendment 2 (2026-11-21) | `tools/phase5/grade.py` |
| 4.2 | Model forecast for 2026 (M A2) and the reference's (B5 A2) | Next: frozen weights, inputs up to 2025, no refit | |
| — | Public label | Fixed 2026-11-21, before the forecast exists | [LABEL.md](LABEL.md) |
| 4.4, 4.6–4.11 | Grader tag, independent rebuild, lock, site, release, announcement | Not started | |

## Format

A layer is a plain `.npy` file, float32 `[499, 128, 128]`: probability of the event in 2026, NaN
where the cell is not eligible; tiles in the order of `tiles.csv`. Plain `.npy` is byte-for-byte
reproducible, so an independent rebuild gives the same package digest; zip-based `.npz` embeds
timestamps and would not. The manifest lists every file's size and SHA-256 in canonical JSON, and
the package digest is the SHA-256 of the manifest.

## Results so far

- **Refit reproduces the bar.** All ten refitted baselines (B0–B4, both tasks) score validation 2024
  exactly as the published baseline report does, to the last digit
  (`baselines/reproduction_check.json` in the package).
- **First grader test (float16 layers).** Grading the validation 2024 layers gave the same cells
  and events as the report (forest loss 1,531,430 cells and 101,177 events; embedding change
  2,008,425 and 87,155), so eligibility and truth are graded identically. AP differed by at most
  4.7e-5: float16 merged nearly equal scores into ties (B0 and B2, which have no near-ties, matched
  to the last digit). Layers are now float32.
- **Second grader test (float32 layers).** Same cells and events again; 7 of the 10 AP values
  equal the report's to the last digit and the other 3 differ by at most 6.7e-9, which is float32
  rounding of probabilities the report kept in float64. The grader scores a package as the
  baseline report scored the baselines.

- **Reference corrected (2026-11-21).** The grader compared the model with B4, the reference
  under the original pre-registration. Amendment 2, section 4 made the reference the best on
  validation among B1–B4 and both B5 runs, which is B5 under amendment 2. The reference is now a
  parameter (`--reference`), defaulting to `B5_A2`, whose layer sits in `forecast/` beside the
  model's; `--reference B4` grades as before. The exam package must therefore carry the reference's
  2026 forecast as well as the model's.

## Checks built in

- The baseline forecast tool refits B0–B4 exactly as the baseline report did and stops unless
  validation 2024 reproduces the report's AP to the last digit.
- The same models write validation 2024 layers; grading those must reproduce the baseline report,
  which tests the grader end to end.
- Forecast mode never reads the target year: forest-task cells are exactly those the report
  scores; embedding-task cells drop only the target-year validity condition, which the grader
  applies.
