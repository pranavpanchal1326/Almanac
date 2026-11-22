# Clean rebuild of the issue 2027.01 package (task 4.6, per ADR 0005)

**Result: PASS, 2026-11-22.** The package was rebuilt from scratch and every forecast layer is
byte-identical to the sealed one. With the sealed run record in place, the rebuild has the sealed
digest, `bc834b2691f0f1c9fdee05a0c0fbae87958efe3a8d3e670aeff113f9b02b7949`.

The blueprint asks for a second person to rebuild the package; Almanac has one maintainer, so
[ADR 0005](../adr/0005-single-maintainer.md) replaces this with a recorded clean-environment
rebuild by the maintainer. It proves the package can be rebuilt from its recorded inputs, not that
a second person followed the recipe.

## How it was rebuilt

| Step | What was done |
|---|---|
| Code | Fresh clone of the public repository (`https://github.com/pranavpanchal1326/Almanac`) into a new folder, checked out at `63f66f9`, the commit recorded in the forecast's `meta.json`; working tree clean |
| Environment | A new virtual environment from the committed lock file (`uv sync --extra train --frozen`): Python 3.12.16, PyTorch 2.14.1 (CUDA 13.0, cuDNN 9.24), NumPy 2.5.4, scikit-learn 1.9.1, the versions of the original build |
| Hardware | The machine of the original build (NVIDIA GeForce RTX 5060 Laptop GPU) |
| Baselines | `tools/phase4/forecast_baselines.py`: B0–B4 refitted from their configuration; both tasks reproduced the published validation 2024 AP to the last digit before forecasting (87 min) |
| Forecasts | `tools/phase4/forecast_exam.py`: checked the frozen checkpoints and calibration maps against the stage B record, then predicted 2026 with the three seeds and the reference (25 min); five tiles predicted twice were identical |
| Output | An empty new folder; nothing of the sealed package was read during the build |
| Comparison | `tools/phase4/compare_rebuild.py` (tests: `tests/unit/test_compare_rebuild.py`), report in [rebuild_2027.01.json](rebuild_2027.01.json) |

## What was compared

| File | Result |
|---|---|
| 10 baseline layers, `baselines/B{0..4}_{forest,embedding}.npy` | byte-identical |
| 4 forecast layers, `forecast/{M_A2,B5_A2}_{forest,embedding}.npy` | byte-identical |
| `tiles.csv`, `baselines/reproduction_check.json` | byte-identical |
| `forecast/meta.json` | differs only in `built` (03:55:13 sealed, 12:18:03 rebuilt) and `seconds` (1426, 1470); every other field, including the checkpoint and map hashes and the commit, is equal |

| Digest | Value |
|---|---|
| Sealed package | `bc834b2691f0f1c9fdee05a0c0fbae87958efe3a8d3e670aeff113f9b02b7949` |
| Rebuild, as built | `a5ae3acca3ab45a54c71b3c5d56cf02342cc9f57f3858ffa9643338ff19d9011` (its own build time) |
| Rebuild, with the sealed `forecast/meta.json` | `bc834b2691f0f1c9fdee05a0c0fbae87958efe3a8d3e670aeff113f9b02b7949`: **equal** |

## What this does not show

- **The digest includes a build time.** `forecast/meta.json` records when the forecast was built,
  so no rebuild reproduces the package digest byte for byte; the earlier statement that an
  independent rebuild "gives the same package digest" holds for every forecast layer, not for
  that file. The comparison therefore requires every layer to be identical and every other field
  of that file to be equal. A future issue should keep run records out of the digest.
- **Same inputs on disk.** The rebuild read the same prepared tile stores, embeddings and frozen
  checkpoints as the original build; the checkpoints and maps were hash-checked, the prepared
  inputs were not re-derived from the raw downloads.
- **Same machine.** Identical results on other GPUs or library versions are not tested; bit
  equality across hardware is not expected for the neural network, which is why the frozen
  weights and this record are published with the lock.
- **One person.** See ADR 0005.
