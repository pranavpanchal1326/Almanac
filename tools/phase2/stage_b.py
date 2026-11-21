"""Task 2.7, stage B: the frozen forecasts scored once on 2025 (amendment 1, section 7).

Usage:
  python tools/phase2/stage_b.py build OUT_DIR [--dry]
  python tools/phase2/stage_b.py grade OUT_DIR --dry
  python tools/phase2/stage_b.py grade OUT_DIR --confirm-single-touch

Stage B is a rehearsal of the exam one year early: the same package format, the same grader
(``tools/phase5/grade.py``) and the same win condition, with target 2025 on the 499 exam tiles
(test and held-out region) instead of 2026.

``build`` writes a forecast package and reads no truth of the target year:
- ``baselines/B0..B4_<task>.npy``: the fitted baseline models saved by the phase 4 forecast tool,
  used only after they score validation 2024 exactly as the published baseline report does;
- ``forecast/M_A2_<task>.npy``: the model. Forest loss: the mean over the three seeds of each
  seed's probability mapped by its isotonic map (``docs/phase2/ensemble_m_a/calibration.json``), as
  amendment 1 fixes. Embedding change (secondary; no calibration is defined for it): the mean of
  the three seeds' probabilities;
- ``forecast/B5_A2_<task>.npy``: the reference, B5 under amendment 2, its probabilities as they
  were when it was chosen on validation (not recalibrated);
- ``tiles.csv``, ``meta.json`` (checkpoints, maps and code, with SHA-256) and the manifest.

``grade`` is the single touch of the 2025 test truth. It refuses unless ``--confirm-single-touch``
is given and no stage B touch is logged yet, checks that the package is unchanged since it was
built, scores both tasks on all exam tiles, the test tiles and the held-out region, applies the win
condition against the reference, writes ``docs/phase2/stage_b_report.{json,md}`` and appends the
touch to ``docs/phase1/test_touch_log.jsonl``.

``--dry`` does the same on validation 2024 (146 tiles; no test data): it checks the whole path and
that the package reproduces known values (each baseline's AP in the baseline report, the model's
ensemble AP from ``ensemble.py``, the reference's logged AP). Nothing is logged.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import pickle
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import torch

REPO = Path(__file__).resolve().parents[2]
for sub in ("phase1", "phase2", "phase4", "phase5"):
    sys.path.insert(0, str(REPO / "tools" / sub))

from baseline_report import BASELINES, evaluate, load_rule, score_set
from forecast_baselines import forecast_layers
from grade import SEED, collect, relative_draws

from almanac.evaluate.bootstrap import WIN_LOWER, WIN_RELATIVE, interval
from almanac.evaluate.metrics import average_precision
from almanac.model.infer import predict_tile
from almanac.model.net import Forecaster
from almanac.model.store import SIDE, TileStore
from almanac.registry.package import build_manifest, verify, write_layer, write_tiles

RUNS = Path("D:/almanac-data/runs")
SEEDS = ("stage_a2_m_a_s1", "stage_a2_m_a_s2", "stage_a2_m_a_s3")
REFERENCE_RUN = "stage_a2_b5_s1"
MODEL, REFERENCE = "M_A2", "B5_A2"
TASKS = ("forest", "embedding")
HEAD = {"forest": "forest", "embedding": "change"}
BASELINE_MODELS = Path("D:/almanac-data/work/grader_check")
BASELINE_CONFIG = REPO / "configs" / "baselines" / "amazon_cerrado_v1.json"
CALIBRATION = REPO / "docs" / "phase2" / "ensemble_m_a" / "calibration.json"
ENSEMBLE_VALIDATION = REPO / "docs" / "phase2" / "ensemble_m_a" / "validation.json"
TOUCH_LOG = REPO / "docs" / "phase1" / "test_touch_log.jsonl"
STAGE_B = "stage B: model M (A2) ensemble, reference B5 (A2) and B0-B4, test_2025 and held_out_2025"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=REPO
    ).stdout.strip()


def split() -> dict[str, str]:
    with (REPO / "configs" / "splits" / "amazon_cerrado_v1.csv").open() as f:
        return {r["tile_id"]: r["split"] for r in csv.DictReader(f)}


def plan(dry: bool) -> tuple[list[str], int]:
    """Tiles (sorted, as the phase 4 package) and target year."""
    side = split()
    if dry:
        return sorted(t for t, s in side.items() if s == "validation"), 2024
    return sorted(t for t, s in side.items() if s in ("test", "held_out")), 2025


def sigmoid(z: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-z.astype(np.float64)))


def predict_layers(run: str, tiles: list[str], target: int, device: str) -> dict[str, np.ndarray]:
    """Raw probabilities ``[n, SIDE, SIDE]`` of both heads for every cell (no truth is read)."""
    cfg = json.loads((RUNS / run / "config.json").read_text())
    from train import build

    dcfg, ncfg, _ = build(cfg)
    ck = torch.load(RUNS / run / "best.pt", map_location="cpu", weights_only=False)
    net = Forecaster(ncfg)
    net.load_state_dict(ck["ema"])
    net.to(device).eval()
    out = {task: np.empty((len(tiles), SIDE, SIDE), np.float64) for task in TASKS}
    for t, tid in enumerate(tiles):
        logits = predict_tile(net, TileStore.open(tid), target, dcfg, device, batch=8)
        for task in TASKS:
            out[task][t] = sigmoid(logits[HEAD[task]])
        if (t + 1) % 100 == 0:
            print(f"  {run}: {t + 1}/{len(tiles)} tiles", flush=True)
    del net
    if device == "cuda":
        torch.cuda.empty_cache()
    return out


def baseline_models(task: str, rule) -> dict:
    """The saved phase 4 baseline models, after they reproduce the baseline report exactly."""
    with (BASELINE_MODELS / f"models_{task}.pkl").open("rb") as f:
        models = pickle.load(f)
    report = json.loads((REPO / "docs" / "phase1" / "baseline_report.json").read_text())
    published = report["tasks"][task]["sets"]["validation_2024"]["baselines"]
    val = sorted(t for t, s in split().items() if s == "validation")
    y, _, _, probs = score_set(val, 2024, task, rule, models)
    for k in BASELINES:
        ap = average_precision(y, probs[k])
        if ap != published[k]["ap"]:
            raise SystemExit(f"{task} {k}: AP {ap!r} != published {published[k]['ap']!r}; not using it")
    print(f"{task}: saved baseline models reproduce the baseline report exactly", flush=True)
    return models


def cmd_build(out: Path, dry: bool) -> None:
    if (out / "manifest.json").exists():
        raise SystemExit(f"{out} already holds a package; build into a new folder")
    tiles, target = plan(dry)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    t0 = time.time()
    out.mkdir(parents=True, exist_ok=True)
    write_tiles(out / "tiles.csv", tiles)
    cfg = json.loads(BASELINE_CONFIG.read_text())
    rule = load_rule(REPO / cfg["threshold"])
    for task in TASKS:
        layers = forecast_layers(tiles, target, task, rule, baseline_models(task, rule))
        for k, layer in layers.items():
            write_layer(out / "baselines" / f"{k}_{task}.npy", layer)
        print(f"{task}: baselines written, {time.time() - t0:.0f} s", flush=True)

    calib = json.loads(CALIBRATION.read_text())
    seeds = {}
    for run in SEEDS:
        raw = predict_layers(run, tiles, target, device)
        c = calib[run]
        seeds[run] = {
            "forest": np.interp(raw["forest"], np.array(c["x"]), np.array(c["y"])),
            "embedding": raw["embedding"],
        }
        print(f"{run}: predicted, {time.time() - t0:.0f} s", flush=True)
    for task in TASKS:
        write_layer(
            out / "forecast" / f"{MODEL}_{task}.npy", np.mean([seeds[r][task] for r in SEEDS], axis=0)
        )
    ref = predict_layers(REFERENCE_RUN, tiles, target, device)
    for task in TASKS:
        write_layer(out / "forecast" / f"{REFERENCE}_{task}.npy", ref[task])
    print(f"reference predicted, {time.time() - t0:.0f} s", flush=True)

    meta = {
        "what": "stage B dry run (validation 2024)" if dry else "stage B package (target 2025)",
        "target": target,
        "tiles": len(tiles),
        "model": {
            "name": MODEL,
            "seeds": {r: sha256(RUNS / r / "best.pt") for r in SEEDS},
            "calibration_sha256": sha256(CALIBRATION),
            "forest": "mean of the seeds' isotonic-mapped probabilities",
            "embedding": "mean of the seeds' probabilities (no calibration defined)",
        },
        "reference": {"name": REFERENCE, "checkpoint_sha256": sha256(RUNS / REFERENCE_RUN / "best.pt")},
        "baseline_models": {t: sha256(BASELINE_MODELS / f"models_{t}.pkl") for t in TASKS},
        "git_commit": git_commit(),
        "built": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "seconds": round(time.time() - t0),
    }
    (out / "meta.json").write_text(json.dumps(meta, indent=1) + "\n", newline="\n")
    digest = build_manifest(out, {"issue": "2027.01", "stage": "B", "dry": dry})
    print(f"package written to {out}, digest {digest}", flush=True)


def part(y, tix, rows, probs, keep_tiles: np.ndarray):
    """The cells of some tiles, with tile numbers renumbered from 0 for the bootstrap."""
    m = np.isin(tix, keep_tiles)
    renum = np.full(tix.max() + 1, -1, np.int32)
    renum[keep_tiles] = np.arange(keep_tiles.size, dtype=np.int32)
    return y[m], renum[tix[m]], rows[m], {k: v[m] for k, v in probs.items()}


def grade_task(out: Path, tiles: list[str], year: int, task: str, parts: dict[str, np.ndarray]) -> dict:
    y, tix, rows, probs = collect(out, year, task, [MODEL, REFERENCE], tiles)
    res: dict = {"all": evaluate(y, tix, rows, probs, len(tiles), SEED, REFERENCE)}
    for name, idx in parts.items():
        py, pt, pr, pp = part(y, tix, rows, probs, idx)
        res[name] = evaluate(py, pt, pr, pp, idx.size, SEED, REFERENCE)
    if task == "forest":
        point, draws = relative_draws(y, tix, probs, MODEL, REFERENCE, len(tiles))
        lo, hi = interval(draws)
        by_part = {name: res[name]["baselines"][MODEL]["ap_skill_vs_reference"] for name in parts}
        guard = bool(by_part) and all(v > 0 for v in by_part.values())
        res["verdict"] = {
            "model": MODEL,
            "reference": REFERENCE,
            "relative_improvement": point,
            "ci95": [lo, hi],
            "condition_1_at_least_20pct": point >= WIN_RELATIVE,
            "condition_2_lower_bound_above_10pct": lo > WIN_LOWER,
            "condition_3_positive_on_each_part": guard,
            "improvement_by_part": by_part,
            "win": bool(point >= WIN_RELATIVE and lo > WIN_LOWER and guard),
        }
    return res


def stage_b_logged() -> bool:
    if not TOUCH_LOG.exists():
        return False
    return any(
        json.loads(line).get("what", "").startswith("stage B")
        for line in TOUCH_LOG.read_text().splitlines()
        if line.strip()
    )


def dry_checks(report: dict) -> dict:
    """Known values the dry run must reproduce."""
    base = json.loads((REPO / "docs" / "phase1" / "baseline_report.json").read_text())
    ens = json.loads(ENSEMBLE_VALIDATION.read_text())["ensemble"]["ap"]
    logged = [
        json.loads(line)
        for line in (RUNS / REFERENCE_RUN / "log.jsonl").read_text().splitlines()
        if line.strip()
    ]
    ref_step = torch.load(RUNS / REFERENCE_RUN / "best.pt", map_location="cpu", weights_only=False)["step"]
    ref_logged = next(
        r["val2024_ap_forest"] for r in logged if r.get("step") == ref_step and "val2024_ap_forest" in r
    )
    checks = {}
    for task in TASKS:
        got = report["tasks"][task]["all"]["baselines"]
        want = base["tasks"][task]["sets"]["validation_2024"]["baselines"]
        for k in BASELINES:
            checks[f"{task}/{k}"] = (got[k]["ap"], want[k]["ap"], 1e-7)
    forest = report["tasks"]["forest"]["all"]["baselines"]
    checks["forest/M_A2 (ensemble.py)"] = (forest[MODEL]["ap"], ens, 1e-4)
    checks["forest/B5_A2 (training log)"] = (forest[REFERENCE]["ap"], ref_logged, 1e-4)
    out = {}
    for name, (got_v, want_v, tol) in checks.items():
        ok = abs(got_v - want_v) <= tol
        out[name] = {"got": got_v, "expected": want_v, "difference": got_v - want_v, "ok": ok}
        print(f"  {'ok ' if ok else 'BAD'} {name}: {got_v:.8f} vs {want_v:.8f}", flush=True)
    return out


def cmd_grade(out: Path, dry: bool, confirm: bool) -> None:
    if not dry:
        if not confirm:
            raise SystemExit("stage B reads the 2025 test truth once; pass --confirm-single-touch to proceed")
        if stage_b_logged():
            raise SystemExit(f"a stage B touch is already logged in {TOUCH_LOG}; it is done only once")
    meta = json.loads((out / "meta.json").read_text())
    tiles, year = plan(dry)
    if meta["target"] != year or meta["tiles"] != len(tiles):
        raise SystemExit("the package was not built for this run (dry and real packages are separate)")
    problems = verify(out)
    if problems:
        raise SystemExit("package changed since it was built: " + "; ".join(problems))
    with (out / "tiles.csv").open() as f:
        if [r["tile_id"] for r in csv.DictReader(f)] != tiles:
            raise SystemExit("package tiles differ from the plan")
    side = split()
    names = ("validation",) if dry else ("test", "held_out")
    parts = {n: np.array([i for i, t in enumerate(tiles) if side[t] == n]) for n in names}
    t0 = time.time()
    report: dict = {
        "what": meta["what"],
        "year": year,
        "package_digest": hashlib.sha256((out / "manifest.json").read_bytes()).hexdigest(),
        "package_meta": meta,
        "git_commit": git_commit(),
        "tasks": {},
    }
    for task in TASKS:
        report["tasks"][task] = grade_task(out, tiles, year, task, parts)
        print(f"{task}: graded, {time.time() - t0:.0f} s", flush=True)
    report["seconds"] = round(time.time() - t0)
    if dry:
        report["dry_checks"] = dry_checks(report)
        # Beside the package, not in it: the package must stay exactly as built.
        (out.parent / f"{out.name}_dry_report.json").write_text(
            json.dumps(report, indent=1, default=float) + "\n", newline="\n"
        )
        bad = [k for k, v in report["dry_checks"].items() if not v["ok"]]
        print(f"dry run: {len(report['dry_checks']) - len(bad)} checks ok, {len(bad)} failed", flush=True)
        if bad:
            raise SystemExit("dry run did not reproduce: " + ", ".join(bad))
        return
    text = json.dumps(report, indent=1, default=float) + "\n"
    (REPO / "docs" / "phase2" / "stage_b_report.json").write_text(text, newline="\n")
    write_markdown(report, REPO / "docs" / "phase2" / "stage_b_report.md")
    with TOUCH_LOG.open("a", newline="\n") as f:
        f.write(
            json.dumps(
                {
                    "when": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
                    "what": STAGE_B,
                    "git_commit": report["git_commit"],
                    "package_digest": report["package_digest"],
                    "report_sha256": hashlib.sha256(text.encode()).hexdigest(),
                }
            )
            + "\n"
        )
    v = report["tasks"]["forest"]["verdict"]
    print(f"stage B: improvement {v['relative_improvement']:+.1%}, win {v['win']}", flush=True)


def write_markdown(report: dict, path: Path) -> None:
    v = report["tasks"]["forest"]["verdict"]
    lines = [
        "# Stage B report (task 2.7)",
        "",
        f"Generated by `python tools/phase2/stage_b.py grade` at commit `{report['git_commit'][:10]}`; "
        f"package digest `{report['package_digest']}`. Target {report['year']}, 499 exam tiles.",
        "",
        "## Win condition (forest loss, all exam tiles)",
        "",
        f"Model `{v['model']}` against reference `{v['reference']}`: relative AP improvement "
        f"**{v['relative_improvement']:+.1%}** (95% interval {v['ci95'][0]:+.1%} to {v['ci95'][1]:+.1%}); "
        "by part: " + ", ".join(f"{k} {x:+.1%}" for k, x in v["improvement_by_part"].items()) + ".",
        "",
        f"1. At least 20%: {v['condition_1_at_least_20pct']}. 2. Lower bound above 10%: "
        f"{v['condition_2_lower_bound_above_10pct']}. 3. Positive on each part: "
        f"{v['condition_3_positive_on_each_part']}. **Win: {v['win']}.**",
        "",
    ]
    for task, t in report["tasks"].items():
        for name in ("all", "test", "held_out"):
            s = t[name]
            lines += [
                f"## {task}, {name}: {s['tiles']} tiles, {s['cells']:,} cells, {s['events']:,} events",
                "",
                "| Forecast | AP | AP 95% interval | AP skill vs reference | P@1% | Brier | Log loss | ECE |",
                "|---|---|---|---|---|---|---|---|",
            ]
            for k, b in s["baselines"].items():
                sk = b["ap_skill_vs_reference"]
                lines.append(
                    f"| {k} | {b['ap']:.4f} | {b['ap_ci95'][0]:.4f} to {b['ap_ci95'][1]:.4f} | "
                    f"{sk:+.1%} [{b['ap_skill_ci95'][0]:+.1%}, {b['ap_skill_ci95'][1]:+.1%}] | "
                    f"{b['precision_at_top']['0.01']:.3f} | {b['brier']:.5f} | {b['log_loss']:.4f} | {b['ece']:.4f} |"
                )
            lines.append("")
    path.write_text("\n".join(lines), newline="\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["build", "grade"])
    ap.add_argument("out", type=Path)
    ap.add_argument("--dry", action="store_true", help="validation 2024 instead of 2025; nothing logged")
    ap.add_argument("--confirm-single-touch", action="store_true")
    args = ap.parse_args()
    if args.command == "build":
        cmd_build(args.out, args.dry)
    else:
        cmd_grade(args.out, args.dry, args.confirm_single_touch)


if __name__ == "__main__":
    main()
