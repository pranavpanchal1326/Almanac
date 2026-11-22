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
| 4.2 | Model forecast for 2026 (M A2) and the reference's (B5 A2) | Done 2026-11-22: frozen weights, inputs up to 2025, no refit; bit-exact on a repeat | [2026 forecasts](#the-2026-forecasts-task-42), `tools/phase4/forecast_exam.py` |
| — | Public label | Fixed 2026-11-21, before the forecast existed | [LABEL.md](LABEL.md) |
| — | Package sealed; stand-alone verifier | Done 2026-11-22: digest `bc834b26…7949`, `VERIFIED` | [manifest](package_2027.01_manifest.json), `tools/verify_issue.py` |
| 4.8 | Scorecard page, first version | Live 2026-11-22 at https://pranavpanchal1326.github.io/Almanac/ (GitHub Pages; the served files equal the repository's byte for byte). Fifth version the same day, "Blue Marble": the Earth from orbit with its blue limb, descending on the Amazon; risk in one validated blue ramp brightening to ice-white on slate land with near-black water, so blue means risk alone; IBM Plex Sans, Sans Condensed and Mono; a product layout with clear actions and a key-figures strip, numbered section headers, the framed map with coordinate margins, the backtest ruler, ruled tables, method cards and the seal; all motion stops for reduced motion | `site/index.html`, `tools/phase4/build_site.py`, `.github/workflows/pages.yml` |
| 4.9 | Public release of the sealed package | Published 2026-11-22 as a pre-release, tag `issue-2027.01-sealed`, asset `almanac-2027.01.tar` (SHA-256 `a6164cda…`); the public copy downloaded back and verified against digest `bc834b26` | [release](https://github.com/pranavpanchal1326/Almanac/releases/tag/issue-2027.01-sealed), `tools/phase4/archive_package.py`, [notes](RELEASE_2027.01.md) |
| — | Package digest timestamped | Done 2026-11-22: FreeTSA 08:24:35 and DigiCert 08:24:37 UTC (RFC 3161, both verified), OpenTimestamps pending Bitcoin | [proofs](proofs/README.md) |
| — | One maintainer: second-person rules replaced | Decided 2026-11-22 | [ADR 0005](../adr/0005-single-maintainer.md) |
| 4.6 | Rebuild (per ADR 0005: clean-environment rebuild by the maintainer) | Not started | |
| 4.7 | Lock (per ADR 0005: single maintainer, external witnesses) | 15 January 2027 | |
| 3.10 | Leakage review by an outsider | Open: kit ready 2026-11-22 (self-check passes, 20 of 20); a reviewer is being sought | [kit](../review/LEAKAGE_REVIEW.md), ADR 0005 |
| 4.4, 4.10, 4.11 | Grader tag, announcement, retrospective | Not started | |

## The 2026 forecasts (task 4.2)

Built 2026-11-22 in 24 minutes by `tools/phase4/forecast_exam.py` at commit `831c482`. It calls the
stage B prediction and calibration code with target 2026, so the forecast is made by the same
path that was backtested. Before writing, it checked the four frozen checkpoints and the
calibration file against the stage B record (all equal). Record: [forecast_2026_meta.json](forecast_2026_meta.json).

| Layer | Cells forecast | Mean probability | 99th percentile |
|---|---|---|---|
| `M_A2_forest` (headline) | 4,795,484 | 0.0641 | 0.319 |
| `B5_A2_forest` (reference) | 4,795,484 | 0.0400 | 0.372 |
| `M_A2_embedding` | 6,056,182 | 0.0158 | 0.287 |
| `B5_A2_embedding` | 6,056,182 | 0.0180 | 0.328 |

- **Coverage:** both forecasts cover every cell the baselines forecast, for both tasks.
- **Repeatability:** five tiles predicted a second time gave identical values (largest difference
  0.0, model seed 1 and reference), so an independent rebuild on the same hardware and software
  should give the same digest.
- **The headline's mean, 6.4%,** is above the 2025 base rate of forest-loss cells on these
  tiles (4.0%), which matches the backtest finding that its probabilities run high; the
  label says so. Nothing is recalibrated.

**Sealed 2026-11-22.** Package `D:/almanac-data/packages/2027.01` (437 MB: 14 layers, `tiles.csv`,
both meta files), digest
`bc834b2691f0f1c9fdee05a0c0fbae87958efe3a8d3e670aeff113f9b02b7949`, the SHA-256 of
[package_2027.01_manifest.json](package_2027.01_manifest.json). `tools/verify_issue.py` prints
`VERIFIED` for it and for a second copy on another drive. Committing the manifest publishes the
digest now, seven weeks before the formal lock and before any 2026 truth exists; the lock on
15 January adds the timestamps, signatures and archive deposit.

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
