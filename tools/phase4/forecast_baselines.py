"""Task 4.3: forecasts of baselines B0-B4 for 2026 on the exam tiles, for the locked package.

Usage: python tools/phase4/forecast_baselines.py configs/baselines/amazon_cerrado_v1.json OUT_DIR

The baselines are refitted exactly as in the baseline report (same configuration, seed and
training rows). Before anything is forecast, the refitted models score validation 2024 again and
every AP must equal the published report's value to the last digit; otherwise the script stops.
That shows the 2026 forecasts come from the same models that set the bar.

Writes, under OUT_DIR: ``tiles.csv`` (the 499 test and held-out tiles, sorted) and one layer per
baseline and task, ``baselines/<B>_<task>.npy``: float16 ``[499, 128, 128]``, probability of the
event in 2026, NaN where the cell is not eligible. Nothing from 2026 exists yet, and nothing from
2025 beyond what was known at the end of 2025 is used.
"""

from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.isotonic import IsotonicRegression

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "phase1"))

from baseline_report import BASELINES, collect_training, load_rule, score_set

from almanac.baselines.features import TASKS, tile_examples
from almanac.data.cube import load_cube
from almanac.evaluate.metrics import average_precision
from almanac.registry.package import SIDE, write_layer, write_tiles

TARGET = 2026


def fit(cfg: dict, train: list[str], task: str, rule) -> dict:
    x, y, w, raw, _ = collect_training(
        train, cfg["train_years"], task, rule, cfg["keep_negative_share"], cfg["seed"]
    )
    models: dict = {"base_rate": float(np.average(y, weights=w))}
    for k in ("B1", "B2", "B3"):
        models[k] = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1).fit(raw[k], y, sample_weight=w)
    models["B4"] = HistGradientBoostingClassifier(random_state=cfg["seed"], **cfg["gbt"]).fit(
        x, y, sample_weight=w
    )
    return models


def main() -> None:
    cfg_path, out = Path(sys.argv[1]), Path(sys.argv[2])
    cfg = json.loads(cfg_path.read_text())
    rule = load_rule(REPO / cfg["threshold"])
    with (REPO / cfg["split"]).open() as f:
        split = {r["tile_id"]: r["split"] for r in csv.DictReader(f)}
    by = {
        s: sorted(t for t, v in split.items() if v == s) for s in ("train", "validation", "test", "held_out")
    }
    exam = sorted(by["test"] + by["held_out"])
    report = json.loads((REPO / "docs" / "phase1" / "baseline_report.json").read_text())
    t0 = time.time()
    check: dict = {}
    for task in TASKS:
        models = fit(cfg, by["train"], task, rule)
        print(f"{task}: fitted, {time.time() - t0:.0f}s", flush=True)
        # Reproduction check on validation 2024 against the published report.
        y, _, _, probs = score_set(by["validation"], 2024, task, rule, models)
        published = report["tasks"][task]["sets"]["validation_2024"]["baselines"]
        for k in BASELINES:
            ap = average_precision(y, probs[k])
            check[f"{task}/{k}"] = {"refit": ap, "published": published[k]["ap"]}
            if ap != published[k]["ap"]:
                raise SystemExit(
                    f"{task} {k}: refit AP {ap!r} != published {published[k]['ap']!r}; not forecasting"
                )
        print(f"{task}: validation 2024 reproduces the report exactly", flush=True)
        layers = {k: np.full((len(exam), SIDE, SIDE), np.nan, np.float32) for k in BASELINES}
        for t, tid in enumerate(exam):
            cube = load_cube(tid, embeddings=True)
            ex = tile_examples(cube, TARGET, task, rule, truth=False)
            if ex.rows.size == 0:
                continue
            assert ex.features is not None
            p = {
                "B0": np.full(ex.rows.size, models["base_rate"]),
                "B4": models["B4"].predict_proba(ex.features)[:, 1],
                **{k: models[k].predict(ex.scores[k]) for k in ("B1", "B2", "B3")},
            }
            for k in BASELINES:
                layers[k][t].reshape(-1)[ex.rows] = p[k]
            if (t + 1) % 100 == 0:
                print(f"  {task}: forecast {t + 1}/{len(exam)} tiles, {time.time() - t0:.0f}s", flush=True)
        for k in BASELINES:
            write_layer(out / "baselines" / f"{k}_{task}.npy", layers[k])
    write_tiles(out / "tiles.csv", exam)
    (out / "baselines" / "reproduction_check.json").write_text(
        json.dumps(check, indent=1) + "\n", newline="\n"
    )
    print(
        f"done in {time.time() - t0:.0f}s: {len(exam)} tiles, {len(BASELINES) * len(TASKS)} layers",
        flush=True,
    )


if __name__ == "__main__":
    main()
