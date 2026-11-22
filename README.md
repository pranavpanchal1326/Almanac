# Almanac

Forecasts of Earth-surface change, locked before the truth exists, then graded in public.

**Scorecard of the first issue: https://pranavpanchal1326.github.io/Almanac/**

The first exam is regional: for every 640 m cell of forest in the Brazilian Amazon and Cerrado,
the probability of forest loss in **2026**, made from data up to 2025 and fixed before the 2026
loss maps are published. The rules of that exam, including what counts as a win, were written
and timestamped before any model was trained.

The full plan is in [BLUEPRINT.md](BLUEPRINT.md); the regional plan to the first lock is in
[docs/phase1/PLAN.md](docs/phase1/PLAN.md).

## Status

| Phase | State | Evidence |
|---|---|---|
| 0 — Look: is yearly change in the embeddings real? | Passed | [REPORT](docs/phase0/REPORT.md), [ADR 0001](docs/adr/0001-gate-0.md) |
| 1 — Scoreboard: a fair exam and simple competitors | Passed | [STATUS](docs/phase1/STATUS.md), [ADR 0003](docs/adr/0003-gate-1.md) |
| 2 — Model, backtested once on 2025 | **Partial**: best forecast on every part, short of the 20% margin | [STATUS](docs/phase2/STATUS.md), [ADR 0004](docs/adr/0004-gate-2.md) |
| 4 — Lock of the 2026 forecast | Forecast made and sealed 2026-11-22 (digest `bc834b26…7949`); formal lock 15 January 2027 | [STATUS](docs/phase4/STATUS.md), [label](docs/phase4/LABEL.md) |
| Exam | When the 2026 forest-loss maps are published (2027) | |

## The result so far, stated plainly

The model is a transformer over five years of AlphaEarth annual embeddings per 640 m cell, with
its neighbourhood; the forecast is the mean of three seeds. It was frozen, then scored **once** on
2025 (the backtest), on 499 tiles it never trained on: a test set and a held-out region in the
south-west Amazon.

| Forest-loss average precision, 2025 | All 499 tiles | Test (379) | Held-out region (120) |
|---|---|---|---|
| **Model M (A2)** | **0.468** | **0.361** | **0.673** |
| Reference: same network without neighbours (B5, A2) | 0.404 | 0.315 | 0.582 |
| Gradient-boosted trees (B4) | 0.386 | 0.315 | 0.549 |
| Proximity to past loss (B3) | 0.199 | 0.160 | 0.283 |
| Base rate | 0.040 | 0.035 | 0.051 |

- **Against the reference: +16.0%** (95% paired tile-bootstrap interval +10.7% to +22.3%), better on
  the test tiles (+14.4%) and the held-out region (+15.7%) separately.
- **Not a win.** The pre-registered win needs at least +20%. The bar was fixed before training and
  is not moved; the 2026 exam is graded against the same three conditions.
- **Weaknesses, published:** the probabilities ran high on 2025 (read the map as a ranking of
  risk); on validation 2024 the model was 4.6% *below* the reference; the 2025 test data were read
  twice, once by mistake, with no effect on any forecast ([ADR 0004](docs/adr/0004-gate-2.md)).
- **Reproduced** by separate code that shares nothing with the grader: 64 of 64 values within
  tolerance ([reproduction](docs/phase2/stage_b_reproduction.md)).

Full tables: [stage B report](docs/phase2/stage_b_report.md); every training run, including the
ones that collapsed: [Phase 2 status](docs/phase2/STATUS.md).

## The exam (pre-registration 2027.01)

- **Task:** forest loss of at least 2.5% of a cell (about 1 ha) in 2026, among cells with forest.
  Truth: Global Forest Change, an independent yearly map.
- **Exam tiles:** a test set and a held-out region (south-west Amazon) never used in training.
- **Reference:** the best on validation 2024 among the simple baselines and the no-neighbour
  network B5 ([amendment 2](docs/prereg/2027.01.amendment-2.md), section 4): B5 (A2).
- **Win:** average precision at least 20% above the reference, the lower end of a 95% tile-bootstrap
  interval above 10%, and better than the reference on the test tiles and on the held-out region
  separately.
- **Text and proofs:** [docs/prereg/2027.01.md](docs/prereg/2027.01.md), timestamped on
  2026-11-15 by FreeTSA and DigiCert (RFC 3161) and OpenTimestamps; amendments 1 and 2 timestamped
  before the runs they govern and anchored in Bitcoin blocks 976,013 and 976,246.
  [How to verify](docs/prereg/proofs/README.md).
- **Every read of the test truth** is logged: [test_touch_log.jsonl](docs/phase1/test_touch_log.jsonl).

## Scorecard page

**Live: https://pranavpanchal1326.github.io/Almanac/** — `site/index.html`, the issue's public page: the claim, the 2026 map, the backtest, the win
condition, the weaknesses, the digest and every read of the test truth. It is generated from the
committed records by `python tools/phase4/build_site.py`; no number on it is typed by hand.

## Verify a forecast package

The locked package is plain `.npy` layers, `tiles.csv` and a canonical manifest; its digest is the
SHA-256 of the manifest. The verifier needs only Python and NumPy and imports nothing from this
repository:

```bash
python tools/verify_issue.py PACKAGE_DIR --digest <published digest>
```

It checks every file's SHA-256, the digest, each layer's type, shape and range, and that the
headline and reference cover every cell the baselines forecast; it prints `VERIFIED` or the
checks that failed.

## Set up

Needs [uv](https://docs.astral.sh/uv/) and, for training, an NVIDIA GPU with a current driver.

```bash
uv sync --extra train
```

```bash
uv run --extra train almanac versions
```

Without `--extra train` everything except PyTorch is installed, which is enough for Phases 0 and 1.

## Check

```bash
uv run pytest
```

```bash
uv run pytest -m network
```

The first runs offline. The second reads one real block from the supplier and confirms the reader
still matches the supplier's north-up sidecar file.

## Reproduce

Data is kept outside the repository, under `D:\almanac-data` (about 17 GB for the region, plus 2.5 GB for Phase 0). Every
data file the exam depends on is listed with its SHA-256 in
[configs/manifests/amazon_cerrado_v1.sha256](configs/manifests/amazon_cerrado_v1.sha256).

**Phase 1** (Amazon + Cerrado, 2,020 tiles):

| Step | Command | Task |
|---|---|---|
| 1 | `uv run almanac stream level --out D:/almanac-data/summaries --keep D:/almanac-data/embeddings --region configs/regions/amazon_cerrado.json` | 1.1–1.3 |
| 2 | `uv run python tools/phase1/build_labels.py configs/regions/amazon_cerrado.json` | 1.4 |
| 3 | `uv run python tools/phase1/build_forest.py configs/splits/amazon_cerrado_v1.csv` | 1.4 |
| 4 | `uv run python tools/phase1/make_split.py configs/splits/amazon_cerrado_v1.json` | 1.7 |
| 5 | `uv run python tools/phase1/threshold_study.py configs/splits/amazon_cerrado_v1.csv` | 1.8 |
| 6 | `uv run python tools/phase1/baseline_report.py configs/baselines/amazon_cerrado_v1.json` | 1.9–1.11 (about 4 hours) |
| 7 | `uv run python tools/phase1/compare_reports.py <report_a.json> <report_b.json>` | reproduction check |

Steps 2 and 3 need the Global Forest Change v1.13 `lossyear`, `datamask` and `treecover2000`
rasters for the region in `D:/almanac-data/labels/gfc`.

**Phase 0:** `uv run almanac index sync`, then the scripts in `tools/phase0` (sites in
`configs/phase0/sites.json`); details in the Phase 0 report.

## Layout

| Path | Contents |
|---|---|
| `src/almanac/io` | Supplier index queries; block reader; HTTP range client |
| `src/almanac/grid` | Tile and block identifiers |
| `src/almanac/quality` | Decoding, vector length, change |
| `src/almanac/data` | Streaming pass, labels, split, change rules, per-tile data cube |
| `src/almanac/baselines` | Features available at issue time; baselines B0–B4 |
| `src/almanac/evaluate` | Metrics and the paired tile bootstrap |
| `src/almanac/model` | Training store, sampler, network, inference |
| `src/almanac/registry` | Forecast packages: layers, canonical manifest, digest |
| `src/almanac/cli` | The `almanac` command |
| `tools/phase0` … `tools/phase5` | Scripts that produce the evidence (training, stage B, its reproduction, the 2026 forecasts, the grader); nothing in `src` imports them |
| `tools/verify_issue.py` | Stand-alone package verifier (Python and NumPy only) |
| `tools/prereg` | Bundle and timestamp tools for pre-registrations |
| `configs` | Region, split, threshold, baseline and data-manifest files |
| `tests` | Unit, property, golden and live-read tests |
| `docs` | Phase reports, decision records, pre-registration and proofs |

## Licence

Code and documentation: [Apache License 2.0](LICENSE). Third-party data, figures and timestamp
certificates keep their own terms; see [NOTICE](NOTICE).

## Attribution

The AlphaEarth Foundations Satellite Embedding dataset is produced by Google and Google DeepMind.
It is used under CC-BY 4.0, read from the Source Cooperative mirror.

Forest labels: Hansen, M. C. et al. 2013, "High-Resolution Global Maps of 21st-Century Forest
Cover Change", Science 342: 850–853; Global Forest Change 2000–2025 v1.13, University of
Maryland, under CC-BY 4.0.

Figures in `docs/phase0` contain modified Copernicus Sentinel data.
