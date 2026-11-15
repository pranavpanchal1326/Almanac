# Task 1.8 — What counts as an embedding change event

Run 2026-11-15 on the 800 training tiles only. Command:
`uv run python tools/phase1/threshold_study.py configs/splits/amazon_cerrado_v1.csv`.
Numbers: [threshold_study.json](threshold_study.json). Record: `configs/thresholds/amazon_cerrado_v1.json`.

## Question

ADR 0001 withdrew the noise-floor threshold: at 640 m it flags most managed land every year. Which
of the three candidates should replace it: one regional threshold, a threshold per land class, or a
threshold per cell from its own history?

## Method

- Change `δ` = `1 − e(t)·e(t+1)` at 640 m, 64.6 million land cell-pairs, pairs ending 2020–2025.
- Land classes: k-means with 12 clusters on the starting year's embedding (453,774 sampled
  training cells, 2017–2022). No outside land-cover map is used.
- History rule: robust z-score of `δ` against the same cell's earlier pairs (median and 1.4826 ×
  median absolute deviation, floor 0.005, at least two earlier pairs).
- "Label-stable" cell: at least half land, no forest loss in the source in the end year, the year
  before or the year after.
- Each rule is calibrated so it flags 1% of label-stable cells in the fit years (pairs ending
  2020–2023), then evaluated on 2020–2025.
- Decision rule, written into the script before the run: highest recall of forest-loss cells
  (≥ 2.5% of the cell lost in the end year) at that common false-alarm rate, unless its flag rate
  across land classes varies more than twice as much as the runner-up's.

## Result

| Rule | Flag rate, stable land | Recall of loss cells | Recall of large loss (≥ 20%) | Share of flags on loss cells | Flag rate max ÷ min over classes | AP of the score vs loss (base 0.025) |
|---|---|---|---|---|---|---|
| One threshold, `δ` > 0.126 | 1.1% | 7.0% | 24.8% | 13.6% | 8,878 | 0.066 |
| **Per class** | 1.3% | **13.1%** | **38.3%** | 20.6% | **2.4** | **0.096** |
| Per-cell history, z > 9.35 | 0.9% | 9.7% | 35.0% | 21.7% | 1,142 | 0.088 |
| Phase 0 noise floor, `δ` > 0.0124 | 60.3% | 91.8% | 99.5% | 5.6% | 6.7 | — |
| Fixed `δ` > 0.2 | 0.3% | 2.6% | 10.2% | 17.4% | 21,111 | — |

**Chosen: the per-class rule.** It has the highest recall and the flattest rate across land classes;
it was not a close call. The per-class thresholds range from 0.022 to 0.254: what is a large
change for one kind of land is ordinary for another. With one threshold, three classes almost never
fire (rates of 0.0–0.04%) and two fire 5–6% of the time, which is the failure ADR 0001 predicted.

## What this does not settle

1. **Embedding change is a weak detector of forest loss at 640 m.** At a 1% false-alarm rate the
   chosen rule catches 13% of cells that lost at least 1 ha and 38% of cells that lost a fifth or
   more. Most forest loss in a 41 ha cell is too small a share of the cell to move its annual
   embedding much. This is why the forest-loss task, graded on the independent label, is the
   headline and embedding change is secondary.
2. **The flag rate drifts upward over time.** On stable land the per-class rule flags 0.4% (2020),
   0.9%, 1.2%, 1.3% (2023), then 2.0% (2024) and 1.9% (2025). The single-threshold rule shows the
   same rise. Either the embeddings of later years differ more from each other, or land use
   changes more; this study cannot tell. A forecast of embedding change for 2026 inherits it, so
   the base rate in the exam year is uncertain by about a factor of two.
3. **2024 and 2025 are outside the calibration years.** Thresholds were fitted on 2020–2023 only,
   so the rise above is an out-of-sample result, not a fitting artefact.
4. **"Stable" is defined by the forest label alone.** A cell can be stable in that sense and still
   change crops or burn. The 1% therefore includes real non-forest change; it is a false-alarm
   rate only with respect to forest loss.
5. **AUC disagrees with AP.** Ranked over all cells, raw `δ` has the highest AUC (0.73) but the
   lowest AP (0.066). The per-class score loses some ordering among low-change cells and gains it
   where it matters, at the top. The primary metric is AP, so the choice stands.
6. The classes come from 12 k-means clusters with one seed. Neither the number of clusters nor the
   1% level was tuned; both are fixed here and go into the pre-registration unchanged.
