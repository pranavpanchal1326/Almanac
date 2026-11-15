"""Tasks 1.9-1.11: fit and score baselines B0-B4 on the validation and test tiles.

Usage: python tools/phase1/baseline_report.py configs/baselines/amazon_cerrado_v1.json

One command regenerates docs/phase1/baseline_report.{json,md}. Everything is seeded. The test year
is read once per run; every run that reads it is appended to docs/phase1/test_touch_log.jsonl.

Protocol:
- Fit (B4's trees, and the isotonic maps that turn B1-B3 scores into probabilities) on training
  tiles, target years 2019-2023. Negatives are subsampled with a fixed seed and reweighted.
- Validation: validation tiles, target 2024 (the year the reference baseline is chosen on).
  Also reported: validation tiles, target 2023.
- Test: test tiles, target 2025; held-out region, target 2025. Reported separately.
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.isotonic import IsotonicRegression

from almanac.baselines.features import TASKS, ChangeRule, tile_examples
from almanac.data.cube import load_cube
from almanac.evaluate.bootstrap import DRAWS, bootstrap_ap, interval, tile_draws
from almanac.evaluate.metrics import (
    average_precision_ranked,
    brier,
    calibration,
    fss_terms,
    log_loss,
    precision_at_top,
    rank,
)

REPO = Path(__file__).resolve().parents[2]
BASELINES = ("B0", "B1", "B2", "B3", "B4")
TOP = (0.001, 0.01, 0.05)
FSS_SCALES = (1, 3, 9)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_rule(path: Path) -> ChangeRule:
    t = json.loads(path.read_text())
    if t["rule"] != "class":
        raise ValueError("baselines are written for the per-class rule chosen in task 1.8")
    return ChangeRule(np.array(t["kmeans_centres"]), np.array(t["class_tau"]))


def collect_training(
    tiles: list[str], years: list[int], task: str, rule: ChangeRule, keep_neg: float, seed: int
):
    xs, ys, ws, raw = [], [], [], {k: [] for k in ("B1", "B2", "B3")}
    names: list[str] = []
    for n, tid in enumerate(tiles):
        cube = load_cube(tid, embeddings=True)
        rng = np.random.default_rng([seed, n])
        for year in years:
            ex = tile_examples(cube, year, task, rule)
            if ex.rows.size == 0:
                continue
            keep = ex.y | (rng.random(ex.y.size) < keep_neg)
            xs.append(ex.features[keep])
            ys.append(ex.y[keep])
            ws.append(np.where(ex.y[keep], 1.0, 1.0 / keep_neg))
            for k in raw:
                raw[k].append(ex.scores[k][keep])
            names = ex.feature_names
        if (n + 1) % 100 == 0:
            print(f"  train {task}: {n + 1}/{len(tiles)} tiles", flush=True)
    return (
        np.concatenate(xs),
        np.concatenate(ys),
        np.concatenate(ws),
        {k: np.concatenate(v) for k, v in raw.items()},
        names,
    )


def score_set(tiles: list[str], year: int, task: str, rule: ChangeRule, models: dict):
    """Probabilities of every baseline on every eligible cell, with tile index and cell index."""
    out = {k: [] for k in BASELINES}
    ys, tix, rows = [], [], []
    for n, tid in enumerate(tiles):
        cube = load_cube(tid, embeddings=True)
        ex = tile_examples(cube, year, task, rule)
        if ex.rows.size == 0:
            continue
        ys.append(ex.y)
        tix.append(np.full(ex.rows.size, n, dtype=np.int32))
        rows.append(ex.rows)
        out["B0"].append(np.full(ex.rows.size, models["base_rate"]))
        for k in ("B1", "B2", "B3"):
            out[k].append(models[k].predict(ex.scores[k]))
        out["B4"].append(models["B4"].predict_proba(ex.features)[:, 1])
    return (
        np.concatenate(ys).astype(np.float64),
        np.concatenate(tix),
        np.concatenate(rows),
        {k: np.concatenate(v) for k, v in out.items()},
    )


def fss(y, p, tix, rows, n_tiles, side=128):
    """Fractions skill score with the forecast cut to as many events as were observed."""
    k = int(y.sum())
    if k == 0:
        return {str(s): float("nan") for s in FSS_SCALES}
    cut = np.sort(p)[-k]
    f = p >= cut
    out = {}
    for s in FSS_SCALES:
        num = ref = 0.0
        for t in range(n_tiles):
            m = tix == t
            if not m.any():
                continue
            fo = np.zeros(side * side)
            ob = np.zeros(side * side)
            fo[rows[m]] = f[m]
            ob[rows[m]] = y[m]
            a, b = fss_terms(fo.reshape(side, side), ob.reshape(side, side), s)
            num += a
            ref += b
        out[str(s)] = 1 - num / ref if ref > 0 else float("nan")
    return out


def evaluate(y, tix, rows, probs, n_tiles, seed, reference: str | None):
    ranked = {k: rank(y, p) for k, p in probs.items()}
    counts = tile_draws(n_tiles, DRAWS, seed)
    boot = bootstrap_ap(ranked, tix, counts)
    res: dict = {"cells": int(y.size), "events": int(y.sum()), "base_rate": float(y.mean()), "tiles": n_tiles}
    res["baselines"] = {}
    for k, p in probs.items():
        ap = average_precision_ranked(ranked[k])
        lo, hi = interval(boot[k])
        cal = calibration(y, p)
        res["baselines"][k] = {
            "ap": ap,
            "ap_ci95": [lo, hi],
            "precision_at_top": {str(t): precision_at_top(ranked[k], t) for t in TOP},
            "brier": brier(y, p),
            "log_loss": log_loss(y, p),
            "ece": cal["ece"],
            "reliability": {"mean_forecast": cal["mean_forecast"], "observed_rate": cal["observed_rate"]},
            "fss": fss(y, p, tix, rows, n_tiles),
        }
    if reference is not None:
        ref_ap = res["baselines"][reference]["ap"]
        ref_brier = res["baselines"][reference]["brier"]
        for k in probs:
            e = res["baselines"][k]
            rel = boot[k] / boot[reference] - 1
            e["ap_skill_vs_reference"] = e["ap"] / ref_ap - 1
            e["ap_skill_ci95"] = list(interval(rel))
            e["brier_skill_vs_reference"] = 1 - e["brier"] / ref_brier
    return res


def main() -> None:
    cfg_path = Path(sys.argv[1])
    cfg = json.loads(cfg_path.read_text())
    seed = cfg["seed"]
    split_path = REPO / cfg["split"]
    thr_path = REPO / cfg["threshold"]
    rule = load_rule(thr_path)
    with split_path.open() as f:
        split = {r["tile_id"]: r["split"] for r in csv.DictReader(f)}
    by = {
        s: sorted(t for t, v in split.items() if v == s) for s in ("train", "validation", "test", "held_out")
    }
    t0 = time.time()
    report: dict = {
        "config": cfg_path.as_posix(),
        "config_sha256": _digest(cfg_path),
        "split_sha256": _digest(split_path),
        "threshold_sha256": _digest(thr_path),
        "git_commit": subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=REPO
        ).stdout.strip(),
        "git_tree_dirty": bool(
            subprocess.run(
                ["git", "status", "--porcelain", "--untracked-files=no", "src", "tools", "configs"],
                capture_output=True,
                text=True,
                cwd=REPO,
            ).stdout.strip()
        ),
        "python": platform.python_version(),
        "tasks": {},
    }
    for task in TASKS:
        print(f"task {task}", flush=True)
        x, y, w, raw, names = collect_training(
            by["train"], cfg["train_years"], task, rule, cfg["keep_negative_share"], seed
        )
        models: dict = {"base_rate": float(np.average(y, weights=w))}
        for k in ("B1", "B2", "B3"):
            models[k] = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1).fit(
                raw[k], y, sample_weight=w
            )
        gbt = HistGradientBoostingClassifier(random_state=seed, **cfg["gbt"])
        models["B4"] = gbt.fit(x, y, sample_weight=w)
        print(
            f"  fitted on {y.size} rows ({int(y.sum())} events), {gbt.n_iter_} trees, {time.time() - t0:.0f}s",
            flush=True,
        )
        t_rep: dict = {
            "training_rows": int(y.size),
            "training_events": int(y.sum()),
            "training_base_rate_weighted": models["base_rate"],
            "gbt_trees": int(gbt.n_iter_),
            "feature_names": names,
            "sets": {},
        }
        # Validation first: choose the reference on it.
        sets = [("validation_2024", by["validation"], 2024), ("validation_2023", by["validation"], 2023)]
        reference = None
        for name, tiles, year in sets:
            yy, tix, rows, probs = score_set(tiles, year, task, rule, models)
            res = evaluate(yy, tix, rows, probs, len(tiles), seed, None)
            if name == "validation_2024":
                cands = [k for k in BASELINES if k != "B0"]
                reference = max(cands, key=lambda k: res["baselines"][k]["ap"])
            res = evaluate(yy, tix, rows, probs, len(tiles), seed, reference)
            t_rep["sets"][name] = res
            print(
                f"  {name}: " + ", ".join(f"{k} {v['ap']:.4f}" for k, v in res["baselines"].items()),
                flush=True,
            )
        t_rep["reference_chosen_on_validation_2024"] = reference
        for name, tiles, year in (("test_2025", by["test"], 2025), ("held_out_2025", by["held_out"], 2025)):
            yy, tix, rows, probs = score_set(tiles, year, task, rule, models)
            t_rep["sets"][name] = evaluate(yy, tix, rows, probs, len(tiles), seed, reference)
            print(
                f"  {name}: "
                + ", ".join(f"{k} {v['ap']:.4f}" for k, v in t_rep["sets"][name]["baselines"].items()),
                flush=True,
            )
        report["tasks"][task] = t_rep
    report["seconds"] = round(time.time() - t0)
    out = REPO / "docs" / "phase1" / "baseline_report.json"
    text = json.dumps(report, indent=1, default=float)
    out.write_text(text)
    with (REPO / "docs" / "phase1" / "test_touch_log.jsonl").open("a") as f:
        f.write(
            json.dumps(
                {
                    "when": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
                    "what": "baselines B0-B4, test_2025 and held_out_2025",
                    "git_commit": report["git_commit"],
                    "report_sha256": hashlib.sha256(text.encode()).hexdigest(),
                }
            )
            + "\n"
        )
    write_markdown(report, REPO / "docs" / "phase1" / "baseline_report.md")


def write_markdown(report: dict, path: Path) -> None:
    lines = [
        "# Baseline report (tasks 1.9-1.11)",
        "",
        f"Generated by `python tools/phase1/baseline_report.py {report['config']}` at commit `{report['git_commit'][:10]}`.",
        "",
    ]
    for task, t in report["tasks"].items():
        ref = t["reference_chosen_on_validation_2024"]
        lines += [
            f"## Task: {task}",
            "",
            f"Reference baseline, chosen on validation 2024: **{ref}**. Training rows {t['training_rows']:,} ({t['training_events']:,} events), B4 trees {t['gbt_trees']}.",
            "",
        ]
        for name, s in t["sets"].items():
            lines += [
                f"### {name}: {s['tiles']} tiles, {s['cells']:,} cells, {s['events']:,} events, base rate {s['base_rate']:.4f}",
                "",
            ]
            lines += [
                "| Baseline | AP | AP 95% interval | AP skill vs reference | P@0.1% | P@1% | P@5% | Brier | Log loss | ECE | FSS 1 / 3 / 9 |",
                "|---|---|---|---|---|---|---|---|---|---|---|",
            ]
            for k, b in s["baselines"].items():
                sk = b.get("ap_skill_vs_reference")
                skill = (
                    f"{sk:+.1%} [{b['ap_skill_ci95'][0]:+.1%}, {b['ap_skill_ci95'][1]:+.1%}]"
                    if sk is not None
                    else "—"
                )
                p = b["precision_at_top"]
                f = b["fss"]
                lines.append(
                    f"| {k} | {b['ap']:.4f} | {b['ap_ci95'][0]:.4f} to {b['ap_ci95'][1]:.4f} | {skill} | {p['0.001']:.3f} | {p['0.01']:.3f} | {p['0.05']:.3f} | {b['brier']:.5f} | {b['log_loss']:.4f} | {b['ece']:.4f} | {f['1']:.3f} / {f['3']:.3f} / {f['9']:.3f} |"
                )
            lines.append("")
    path.write_text("\n".join(lines))


if __name__ == "__main__":
    main()
