"""Calibrate each seed and form the three-seed ensemble on validation 2024 (amendment 1, section 7).

Usage: python tools/phase2/ensemble.py RUN_DIR [RUN_DIR ...] --out OUT_DIR [--tiles N]

For each run (its kept weights, ``best.pt``) every validation tile is predicted for target 2024
with the same code and cells as training's validation. The run's AP is checked against the value
logged when that checkpoint was kept. Each run's forest-loss probabilities are then mapped by
isotonic regression fitted on its own validation predictions, and the ensemble forecast is the
mean of the mapped probabilities.

Writes to OUT_DIR:
- ``calibration.json``: each run's isotonic map (thresholds), the frozen part of the forecast;
- ``validation.json``: AP and the secondary scores for each run and the ensemble;
- ``val2024_<run>.npz``: the raw logits, so the scores can be rechecked without a GPU.

Reads validation tiles only; the 2025 test truth is not touched. ``--tiles N`` scores only the
first N validation tiles (a quick check of the tool; the AP check is skipped).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
from sklearn.isotonic import IsotonicRegression

sys.path.insert(0, str(Path(__file__).resolve().parent))

from train import REPO, build, split_tiles

from almanac.evaluate.metrics import average_precision, brier, calibration, log_loss
from almanac.model.infer import predict_tile, tile_scores
from almanac.model.net import Forecaster
from almanac.model.store import TileStore

TARGET = 2024
AP_TOLERANCE = 0.002  # bf16 kernels can reorder sums; a larger gap means a loading or code change


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def logged_ap(run: Path, step: int) -> float:
    for line in (run / "log.jsonl").read_text().splitlines():
        rec = json.loads(line) if line.strip() else {}
        if rec.get("step") == step and "val2024_ap_forest" in rec:
            return rec["val2024_ap_forest"]
    raise SystemExit(f"{run}: no logged validation at step {step}")


def predict_run(run: Path, tiles: list[str], device: str):
    cfg = json.loads((run / "config.json").read_text())
    dcfg, ncfg, _ = build(cfg)
    ck = torch.load(run / "best.pt", map_location="cpu", weights_only=False)
    net = Forecaster(ncfg)
    net.load_state_dict(ck["ema"])
    net.to(device).eval()
    ys, zs, sizes = [], [], []
    for tid in tiles:
        store = TileStore.open(tid)
        logits = predict_tile(net, store, TARGET, dcfg, device, batch=8)
        _, y, z = tile_scores(store, logits, TARGET, "forest")
        ys.append(y)
        zs.append(z)
        sizes.append(y.size)
    del net
    if device == "cuda":
        torch.cuda.empty_cache()
    return ck["step"], cfg, np.concatenate(ys), np.concatenate(zs), np.array(sizes)


def scores(y: np.ndarray, p: np.ndarray) -> dict:
    cal = calibration(y, p)
    return {
        "ap": average_precision(y, p),
        "brier": brier(y, p),
        "log_loss": log_loss(y, p),
        "ece": cal["ece"],
        "reliability": {"mean_forecast": cal["mean_forecast"], "observed_rate": cal["observed_rate"]},
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", type=Path, nargs="+")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--tiles", type=int, default=0, help="first N validation tiles only (a check)")
    args = ap.parse_args()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    t0 = time.time()

    cfg0 = json.loads((args.runs[0] / "config.json").read_text())
    tiles = split_tiles(REPO / cfg0["split"])["validation"]
    full = not args.tiles
    if not full:
        tiles = tiles[: args.tiles]
    args.out.mkdir(parents=True, exist_ok=True)

    y_ref = None
    probs, report_runs, calib = [], {}, {}
    for run in args.runs:
        step, cfg, y, z, sizes = predict_run(run, tiles, device)
        if y_ref is None:
            y_ref, sizes_ref = y, sizes
        elif not (np.array_equal(y, y_ref) and np.array_equal(sizes, sizes_ref)):
            raise SystemExit(f"{run}: different validation cells from {args.runs[0]}")
        np.savez_compressed(args.out / f"val2024_{run.name}.npz", logits=z, y=y, tile_sizes=sizes)
        raw = 1 / (1 + np.exp(-z.astype(np.float64)))
        ap_now = average_precision(y, z)
        entry = {
            "checkpoint_step": int(step),
            "best_pt_sha256": sha256(run / "best.pt"),
            "config_sha256": cfg.get("_sha256"),
            "seed": cfg["seed"],
            "ap_recomputed": ap_now,
        }
        if full:
            entry["ap_logged"] = logged_ap(run, step)
            gap = abs(ap_now - entry["ap_logged"])
            print(f"{run.name}: step {step}, AP {ap_now:.5f} (logged {entry['ap_logged']:.5f})", flush=True)
            if gap > AP_TOLERANCE:
                raise SystemExit(f"{run.name}: recomputed AP differs from the logged value by {gap:.4f}")
        iso = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1).fit(raw, y)
        p = iso.predict(raw)
        probs.append(p)
        calib[run.name] = {
            "x": iso.X_thresholds_.tolist(),
            "y": iso.y_thresholds_.tolist(),
            "input": "sigmoid of the forest-loss logit",
        }
        entry["raw"] = scores(y, raw)
        entry["calibrated"] = scores(y, p)
        report_runs[run.name] = entry
        print(f"{run.name}: done in {time.time() - t0:.0f} s", flush=True)

    ens = np.mean(probs, axis=0)
    report = {
        "what": "model M (amendment 2, schedule a), validation 2024, forest-loss task",
        "tiles": len(tiles),
        "cells": int(y_ref.size),
        "events": int(y_ref.sum()),
        "base_rate": float(y_ref.mean()),
        "runs": report_runs,
        "ensemble": scores(y_ref, ens),
        "note": (
            "Each isotonic map is fitted on the same validation cells it is scored on, so the "
            "calibration scores here are in-sample; AP of a single run is unchanged by its map."
        ),
        "device": device,
        "torch": torch.__version__,
        "seconds": round(time.time() - t0),
    }
    (args.out / "calibration.json").write_text(json.dumps(calib) + "\n")
    (args.out / "validation.json").write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps({k: report["ensemble"][k] for k in ("ap", "brier", "log_loss", "ece")}), flush=True)
    print(f"ensemble of {len(probs)}: AP {report['ensemble']['ap']:.5f} on {len(tiles)} tiles", flush=True)


if __name__ == "__main__":
    main()
