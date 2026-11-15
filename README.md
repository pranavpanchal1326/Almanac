# Almanac

Forecasts of Earth-surface change, locked before the truth exists, then graded in public.

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
| 2 — Model | Next | |
| Lock of the 2026 forecast | 15 January 2027 | |

## The exam (pre-registration 2027.01)

- **Task:** forest loss of at least 2.5% of a cell (about 1 ha) in 2026, among cells with forest.
  Truth: Global Forest Change, an independent yearly map.
- **Exam tiles:** a test set and a held-out region (south-west Amazon) never used in training.
- **Reference:** the best simple baseline on validation, which is gradient-boosted trees (B4).
- **Win:** average precision at least 20% above the reference, the lower end of a 95% tile-bootstrap
  interval above 10%, and better than the reference on the test tiles and on the held-out region
  separately.
- **Text and proofs:** [docs/prereg/2027.01.md](docs/prereg/2027.01.md), timestamped on
  2026-11-15 by FreeTSA and DigiCert (RFC 3161) and OpenTimestamps.
  [How to verify](docs/prereg/proofs/README.md).

Baselines to beat, average precision on forest loss (base rate in brackets):

| | Last change (B2) | Proximity (B3) | Trees (B4) |
|---|---|---|---|
| Validation 2024 (0.066) | 0.089 | 0.200 | **0.246** |
| Test 2025 (0.035) | 0.063 | 0.160 | **0.315** |
| Held-out region 2025 (0.051) | 0.214 | 0.283 | **0.549** |

Full report: [docs/phase1/baseline_report.md](docs/phase1/baseline_report.md). If no model clears
the bar, the baseline's forecast is locked instead and the negative result is published.

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
| `src/almanac/cli` | The `almanac` command |
| `tools/phase0`, `tools/phase1` | Scripts that produce the evidence; nothing in `src` imports them |
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
