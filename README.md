# Almanac

Forecasts of Earth-surface change, locked before the truth exists. The full plan is in
[BLUEPRINT.md](BLUEPRINT.md). This repository is at the end of **Phase 0 — Look**; the results are
in [docs/phase0/REPORT.md](docs/phase0/REPORT.md).

## Set up

Needs [uv](https://docs.astral.sh/uv/) and, for the GPU check, an NVIDIA GPU with a current driver.

```bash
uv sync --extra train
```

```bash
uv run --extra train almanac versions
```

The second command prints library versions and the GPU name. Without `--extra train` everything
except PyTorch is installed, which is enough for all of Phase 0.

## Check

```bash
uv run pytest
```

```bash
uv run pytest -m network
```

The first runs offline. The second reads one real block from the supplier and confirms the reader
still matches the supplier's north-up sidecar file.

## Reproduce Phase 0

Data is kept outside the repository, under `D:\almanac-data` (change `DATA` in
`tools/phase0/common.py` to move it). About 2.5 GB is written.

| Step | Command | Task |
|---|---|---|
| 1 | `uv run almanac index sync` | 0.2 |
| 2 | `uv run almanac index counts` | 0.2 |
| 3 | `uv run python tools/phase0/imagery.py` | 0.8 |
| 4 | `uv run python tools/phase0/download.py` | 0.6 |
| 5 | `uv run python tools/phase0/orientation.py` | 0.4 |
| 6 | `uv run python tools/phase0/pyramid.py` | 0.7 |
| 7 | `uv run python tools/phase0/analyse.py` | 0.8, 0.9, gate numbers |
| 8 | `uv run python tools/phase0/diffenc.py` | 0.11 |

Sites are listed in `configs/phase0/sites.json`.

## Layout

| Path | Contents |
|---|---|
| `src/almanac/io` | Supplier index queries; block reader with transfer accounting |
| `src/almanac/grid` | Tile and block identifiers |
| `src/almanac/quality` | Decoding, vector length, change, threshold |
| `src/almanac/data` | Difference encoding |
| `src/almanac/cli` | The `almanac` command |
| `tools/phase0` | One-off Phase 0 scripts; nothing in `src` imports them |
| `tests` | Unit, property, golden (orientation) and live-read tests |
| `docs/phase0` | Report, result tables and figures |
| `docs/adr` | Decision records |

## Attribution

The AlphaEarth Foundations Satellite Embedding dataset is produced by Google and Google DeepMind.

It is used under CC-BY 4.0, read from the Source Cooperative mirror. Figures in `docs/phase0`
contain modified Copernicus Sentinel data.
