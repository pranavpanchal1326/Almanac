# Phase 4 — Lock: preparation

Started 2026-11-16, alongside Phase 2 training. The lock is on 15 January 2027 and does not move.
If no model clears the bar, the plan locks B4's forecast instead (blueprint 16.4, "Fail"), so the
baseline forecasts and the package are prepared first.

| ID | Task | Status | Evidence |
|---|---|---|---|
| 4.3 | Baseline forecasts for 2026, B0–B4, on the 499 exam tiles | Running | `tools/phase4/forecast_baselines.py` |
| 4.5 | Package format: layers, canonical manifest, package digest | Done | `src/almanac/registry/package.py`, `tests/unit/test_package.py` |
| — | Grader for the exam (win condition with the guard) | Written; test pending | `tools/phase5/grade.py` |
| 4.2 | Model forecast for 2026 | After Phase 2 | |
| 4.4, 4.6–4.11 | Grader tag, independent rebuild, lock, site, release, announcement | Not started | |

## Format

A layer is a plain `.npy` file, float16 `[499, 128, 128]`: probability of the event in 2026, NaN
where the cell is not eligible; tiles in the order of `tiles.csv`. Plain `.npy` is byte-for-byte
reproducible, so an independent rebuild gives the same package digest; zip-based `.npz` embeds
timestamps and would not. The manifest lists every file's size and SHA-256 in canonical JSON, and
the package digest is the SHA-256 of the manifest.

## Checks built in

- The baseline forecast tool refits B0–B4 exactly as the baseline report did and stops unless
  validation 2024 reproduces the report's AP to the last digit.
- The same models write validation 2024 layers; grading those must reproduce the baseline report,
  which tests the grader end to end.
- Forecast mode never reads the target year: forest-task cells are exactly those the report
  scores; embedding-task cells drop only the target-year validity condition, which the grader
  applies.
