"""Task 4.2: the 2026 forecasts of issue 2027.01 for the model and the reference (ADR 0004).

Usage: python tools/phase4/forecast_exam.py [PACKAGE_DIR]   (default D:/almanac-data/packages/2027.01)

Writes, beside the baseline layers that task 4.3 already put in the package:

- ``forecast/M_A2_<task>.npy``: the headline. Forest loss: the mean over the three seeds of each
  seed's probability mapped by its fixed isotonic map; embedding change: the mean of the seeds'
  probabilities (amendment 1, section 7);
- ``forecast/B5_A2_<task>.npy``: the reference, its raw probabilities;
- ``forecast/meta.json``: checkpoints, maps, baseline layers and code, each with its SHA-256.

The prediction and calibration code is the stage B code (``tools/phase2/stage_b.py``), called with
target 2026, so the forecast is made by exactly the path that was backtested. Same frozen weights,
inputs up to 2025, no refit, no recalibration. No truth of 2026 exists; nothing of the 2025 test
truth is read beyond the model inputs that amendment 1, section 7 specifies.

Checks before anything is written as final:

1. the frozen checkpoints and the calibration file match the SHA-256 recorded in
   ``docs/phase2/STATUS.md`` and in the stage B package's ``meta.json``;
2. every layer is float32 ``[499, 128, 128]`` with values in [0, 1];
3. the model and the reference cover every cell that the baselines forecast;
4. predicting a sample of tiles a second time gives the same values (determinism, reported).
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

REPO = Path(__file__).resolve().parents[2]
for sub in ("phase1", "phase2", "phase4", "phase5"):
    sys.path.insert(0, str(REPO / "tools" / sub))

import stage_b

from almanac.registry.package import write_layer

TARGET = 2026
STAGE_B_META = Path("D:/almanac-data/packages/stage_b_2025/meta.json")
SAMPLE = 5  # tiles predicted twice for the determinism check


def frozen_hashes() -> dict[str, str]:
    """Checkpoint and map hashes, as stage B recorded them; they must not have changed."""
    m = json.loads(STAGE_B_META.read_text())
    want = {**m["model"]["seeds"], stage_b.REFERENCE_RUN: m["reference"]["checkpoint_sha256"]}
    for run, h in want.items():
        got = stage_b.sha256(stage_b.RUNS / run / "best.pt")
        if got != h:
            raise SystemExit(f"{run}: best.pt {got} differs from the stage B record {h}")
    if stage_b.sha256(stage_b.CALIBRATION) != m["model"]["calibration_sha256"]:
        raise SystemExit("calibration.json differs from the stage B record")
    return want


def check_layer(name: str, layer: np.ndarray, n: int, cover: np.ndarray) -> dict:
    if layer.shape != (n, stage_b.SIDE, stage_b.SIDE):
        raise SystemExit(f"{name}: shape {layer.shape}")
    fin = np.isfinite(layer)
    if (layer[fin] < 0).any() or (layer[fin] > 1).any():
        raise SystemExit(f"{name}: values outside [0, 1]")
    missing = int((cover & ~fin).sum())
    if missing:
        raise SystemExit(f"{name}: {missing} cells the baselines forecast are missing")
    v = layer[cover].astype(np.float64)
    return {"cells": int(cover.sum()), "mean": float(v.mean()), "p99": float(np.quantile(v, 0.99))}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("package", type=Path, nargs="?", default=Path("D:/almanac-data/packages/2027.01"))
    args = ap.parse_args()
    out = args.package
    if (out / "manifest.json").exists():
        raise SystemExit(f"{out} is already sealed by a manifest; nothing is rewritten")
    if (out / "forecast").exists():
        raise SystemExit(f"{out / 'forecast'} exists; build into a fresh package folder")
    with (out / "tiles.csv").open() as f:
        tiles = [r["tile_id"] for r in csv.DictReader(f)]
    exam, _ = stage_b.plan(dry=False)
    if tiles != exam:
        raise SystemExit("tiles.csv is not the 499 exam tiles in order")
    hashes = frozen_hashes()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    t0 = time.time()

    calib = json.loads(stage_b.CALIBRATION.read_text())
    seeds = {}
    for run in stage_b.SEEDS:
        raw = stage_b.predict_layers(run, tiles, TARGET, device)
        c = calib[run]
        seeds[run] = {
            "forest": np.interp(raw["forest"], np.array(c["x"]), np.array(c["y"])),
            "embedding": raw["embedding"],
        }
        print(f"{run}: predicted 2026, {time.time() - t0:.0f} s", flush=True)
    layers = {
        f"{stage_b.MODEL}_{task}": np.mean([seeds[r][task] for r in stage_b.SEEDS], axis=0)
        for task in stage_b.TASKS
    }
    ref = stage_b.predict_layers(stage_b.REFERENCE_RUN, tiles, TARGET, device)
    for task in stage_b.TASKS:
        layers[f"{stage_b.REFERENCE}_{task}"] = ref[task]
    print(f"reference predicted 2026, {time.time() - t0:.0f} s", flush=True)

    # Determinism: the first seed and the reference again on a sample of tiles.
    sample = tiles[:: len(tiles) // SAMPLE][:SAMPLE]
    idx = [tiles.index(t) for t in sample]
    again = stage_b.predict_layers(stage_b.SEEDS[0], sample, TARGET, device)
    c = calib[stage_b.SEEDS[0]]
    redo = np.interp(again["forest"], np.array(c["x"]), np.array(c["y"]))
    seed_diff = float(np.abs(redo - seeds[stage_b.SEEDS[0]]["forest"][idx]).max())
    again_ref = stage_b.predict_layers(stage_b.REFERENCE_RUN, sample, TARGET, device)
    ref_diff = float(np.abs(again_ref["forest"] - ref["forest"][idx]).max())

    summary = {}
    for task in stage_b.TASKS:
        cover = np.isfinite(np.load(out / "baselines" / f"B4_{task}.npy"))
        for name in (f"{stage_b.MODEL}_{task}", f"{stage_b.REFERENCE}_{task}"):
            layer = layers[name].astype(np.float32)
            summary[name] = check_layer(name, layer, len(tiles), cover)
            write_layer(out / "forecast" / f"{name}.npy", layer)
    meta = {
        "what": "issue 2027.01 forecasts for 2026 (ADR 0004: model M (A2) is the headline)",
        "target": TARGET,
        "tiles": len(tiles),
        "model": {
            "name": stage_b.MODEL,
            "seeds": {r: hashes[r] for r in stage_b.SEEDS},
            "calibration_sha256": stage_b.sha256(stage_b.CALIBRATION),
            "forest": "mean of the seeds' isotonic-mapped probabilities",
            "embedding": "mean of the seeds' probabilities (no calibration defined)",
        },
        "reference": {"name": stage_b.REFERENCE, "checkpoint_sha256": hashes[stage_b.REFERENCE_RUN]},
        "baseline_layers": {p.name: stage_b.sha256(p) for p in sorted((out / "baselines").glob("*.npy"))},
        "layers": summary,
        "determinism": {
            "tiles": sample,
            "max_abs_difference_seed_1_forest": seed_diff,
            "max_abs_difference_reference_forest": ref_diff,
        },
        "git_commit": stage_b.git_commit(),
        "built": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "seconds": round(time.time() - t0),
    }
    (out / "forecast" / "meta.json").write_text(json.dumps(meta, indent=1) + "\n", newline="\n")
    print(json.dumps({"layers": summary, "determinism": meta["determinism"]}, indent=1))
    print(f"done in {time.time() - t0:.0f} s; the package is not sealed yet (no manifest)")


if __name__ == "__main__":
    main()
