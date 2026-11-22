Almanac issue 2027.01: the forecast of forest loss in the Amazon and Cerrado for **2026**, made from data up to 2025 and sealed on 22 November 2026, before any 2026 loss map exists. The formal lock (timestamps, two signatures, archive deposit) follows on 15 January 2027; the exam is graded when the 2026 Global Forest Change data are published.

**Scorecard:** https://pranavpanchal1326.github.io/Almanac/

## What is in the archive

`almanac-2027.01.tar` (458 MB, uncompressed) holds one folder, `almanac-2027.01/`:

| File | Contents |
|---|---|
| `forecast/M_A2_forest.npy` | **The headline forecast:** probability of forest loss in 2026, model M (A2), three-seed ensemble |
| `forecast/B5_A2_forest.npy` | The reference it is graded against: the same network without neighbours (B5, A2) |
| `baselines/B0..B4_forest.npy` | The simple baselines, locked beside it and graded on the same truth |
| `*_embedding.npy` | The same forecasts for the secondary task (embedding change) |
| `tiles.csv` | The 499 exam tiles, in layer order |
| `forecast/meta.json`, `baselines/reproduction_check.json` | Checkpoint, calibration and code hashes; the baselines' reproduction check |
| `manifest.json` | Every file's size and SHA-256, canonical JSON |

Each layer is float32 `[499, 128, 128]`: one 640 m cell per value, NaN where a cell is not forecast.

## Verify it

```
sha256sum almanac-2027.01.tar
tar -xf almanac-2027.01.tar
python tools/verify_issue.py almanac-2027.01 --digest bc834b2691f0f1c9fdee05a0c0fbae87958efe3a8d3e670aeff113f9b02b7949
```

- Archive SHA-256: `a6164cdae90a33fdb8360ba576b0f7d78715b18e6ffd7669b7902af906ade27f` (the archive is built reproducibly by `tools/phase4/archive_package.py`)
- **Package digest** (SHA-256 of `manifest.json`): `bc834b2691f0f1c9fdee05a0c0fbae87958efe3a8d3e670aeff113f9b02b7949`, committed to this repository in `docs/phase4/package_2027.01_manifest.json` on 22 November 2026

The verifier needs only Python and NumPy and imports nothing else from the repository. It prints `VERIFIED` or the checks that failed.

## What the forecast claims, and what it does not

The win condition was fixed before any model was trained: average precision at least 20% above the reference, the lower end of the 95% interval above 10%, and better on the test tiles and on the held-out region separately.

On the 2025 backtest, graded once, the model was **16.0% above the reference** (95% interval +10.7% to +22.3%), better on both parts. **That is not a win**, and the 20% bar for 2026 is unchanged. Its probabilities ran high on 2025, so read the map as a ranking of risk first. The 2025 test data were read twice, once by mistake, with no effect on any forecast. Full record: [ADR 0004](https://github.com/pranavpanchal1326/Almanac/blob/main/docs/adr/0004-gate-2.md), [label](https://github.com/pranavpanchal1326/Almanac/blob/main/docs/phase4/LABEL.md).

## Data

AlphaEarth Foundations Satellite Embedding dataset, produced by Google and Google DeepMind, used under CC-BY 4.0. Forest labels: Hansen, M. C. et al. 2013, Science 342: 850–853; Global Forest Change 2000–2025 v1.13, University of Maryland, under CC-BY 4.0. The forecast layers are derived from these data and carry their attribution. Code: Apache 2.0 (see `LICENSE` and `NOTICE`).
