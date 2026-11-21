"""Independent reproduction of the stage B grade (task 2.8): the primary metric and the verdict.

Usage: python tools/phase2/reproduce_stage_b.py PACKAGE --confirm-reproduction

Written apart from the grading code on purpose. It imports nothing from ``almanac`` or from the
stage B and phase 5 tools; it works only from the pre-registration's text and the raw files:

- the package is checked against its own manifest, and the manifest's SHA-256 against the digest
  logged for stage B;
- truth and eligibility come from the source label stores (``labels/forest_loss``,
  ``labels/forest``) and the stream summaries' validity bits, not from the training store that
  stage B read, with each array indexed by the year it carries;
- the forest-loss event follows section 3 of the pre-registration: land share at least 0.5,
  ``forest_start(2025)`` at least 0.10, a valid embedding in 2024, event ``forest_lost(2025)``
  at least 0.025; a cell is scored only where every forecast in the package is finite;
- AP is computed by scikit-learn for every point value, and by a separate weighted routine for
  the bootstrap, which is first checked against scikit-learn on weighted draws;
- the interval follows section 4: paired bootstrap over tiles, 2,000 draws, seed 20261115.

It reads the 2025 test truth, so it refuses to run without ``--confirm-reproduction`` and logs
the run in ``docs/phase1/test_touch_log.jsonl`` (pre-registration, section 5). The tolerances
below were fixed before the first run.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from sklearn.metrics import average_precision_score

REPO = Path(__file__).resolve().parents[2]
DATA = Path("D:/almanac-data")
TOUCH_LOG = REPO / "docs" / "phase1" / "test_touch_log.jsonl"
REPORT = REPO / "docs" / "phase2" / "stage_b_report.json"
OUT = REPO / "docs" / "phase2" / "stage_b_reproduction"
SPLIT = REPO / "configs" / "splits" / "amazon_cerrado_v1.csv"
WHAT = "reproduction of stage B (task 2.8): forest loss, test_2025 and held_out_2025"

YEAR = 2025
MODEL, REFERENCE = "M_A2", "B5_A2"
DRAWS, SEED = 2000, 20261115
LAND_MIN, FOREST_MIN, LOSS_EVENT = 0.5, 0.10, 0.025
WIN_RELATIVE, WIN_LOWER = 0.20, 0.10

# Fixed before the first run. Counts must match exactly; AP and the improvement agree to float64
# rounding when the same cells and the same draws are used.
TOL_AP = 1e-9
TOL_REL = 1e-9
TOL_CI = 1e-9


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def stage_b_entry() -> dict:
    rows = [json.loads(x) for x in TOUCH_LOG.read_text().splitlines() if x.strip()]
    found = [r for r in rows if r["what"].startswith("stage B")]
    if len(found) != 1:
        raise SystemExit(f"expected exactly one stage B touch in the log, found {len(found)}")
    return found[0]


def reproduction_logged() -> bool:
    if not TOUCH_LOG.exists():
        return False
    return any(json.loads(x).get("what") == WHAT for x in TOUCH_LOG.read_text().splitlines() if x.strip())


def check_package(root: Path, digest: str) -> None:
    manifest = root / "manifest.json"
    if sha256(manifest) != digest:
        raise SystemExit("manifest digest differs from the logged stage B package digest")
    for f in json.loads(manifest.read_text())["files"]:
        p = root / f["path"]
        if p.stat().st_size != f["size"] or sha256(p) != f["sha256"]:
            raise SystemExit(f"package file changed: {f['path']}")


def by_year(years: np.ndarray, year: int) -> int:
    hits = np.flatnonzero(np.asarray(years) == year)
    if hits.size != 1:
        raise SystemExit(f"year {year} not found exactly once in {list(years)}")
    return int(hits[0])


def tile_truth(tile_id: str) -> tuple[np.ndarray, np.ndarray]:
    zone = tile_id.split("_", 1)[0]
    with np.load(DATA / "labels" / "forest_loss" / "L6" / zone / f"{tile_id}.npz") as f:
        land = f["land_share"].astype(np.float32)
    with np.load(DATA / "labels" / "forest" / "L6" / zone / f"{tile_id}.npz") as f:
        start = f["forest_start"][by_year(f["start_years"], YEAR)].astype(np.float32)
        lost = f["forest_lost"][by_year(f["lost_years"], YEAR)].astype(np.float32)
    with np.load(DATA / "summaries" / "L6" / zone / f"{tile_id}.npz", allow_pickle=False) as f:
        years = json.loads(str(f["meta"]))["years"]
        side = land.shape[-1]
        bits = np.unpackbits(f["valid_bits"][years.index(YEAR - 1)])[: side * side]
        valid_issue = bits.reshape(side, side).astype(bool)
    eligible = (land >= LAND_MIN) & (start >= FOREST_MIN) & valid_issue
    return eligible, lost >= LOSS_EVENT


def load(root: Path):
    with (root / "tiles.csv").open() as f:
        tiles = [r["tile_id"] for r in csv.DictReader(f)]
    layers = {p.stem[: -len("_forest")]: np.load(p, mmap_mode="r") for p in
              sorted([*root.glob("baselines/*_forest.npy"), *root.glob("forecast/*_forest.npy")])}
    y, tix, probs = [], [], {k: [] for k in layers}
    for t, tid in enumerate(tiles):
        elig, event = tile_truth(tid)
        cells = np.flatnonzero(elig.ravel())
        flat = {k: np.asarray(v[t]).reshape(-1)[cells] for k, v in layers.items()}
        keep = np.all([np.isfinite(v) for v in flat.values()], axis=0)
        y.append(event.ravel()[cells][keep])
        tix.append(np.full(int(keep.sum()), t, np.int32))
        for k in layers:
            probs[k].append(flat[k][keep].astype(np.float64))
    return (tiles, np.concatenate(y).astype(np.int8), np.concatenate(tix),
            {k: np.concatenate(v) for k, v in probs.items()})


class Sorted:
    """Cells sorted by falling score, with the last index of each run of equal scores."""

    def __init__(self, y: np.ndarray, score: np.ndarray, tix: np.ndarray) -> None:
        order = np.argsort(-score, kind="mergesort")
        s = score[order]
        self.y = y[order].astype(np.float64)
        self.tix = tix[order]
        self.ends = np.r_[np.flatnonzero(s[1:] != s[:-1]), s.size - 1]

    def ap(self, w: np.ndarray) -> float:
        tp = np.cumsum(w * self.y)[self.ends]
        n = np.cumsum(w)[self.ends]
        prev = np.r_[0.0, tp[:-1]]
        with np.errstate(invalid="ignore", divide="ignore"):
            return float(np.sum((tp - prev) * np.where(n > 0, tp / n, 0.0)) / tp[-1])


def draws(n_tiles: int) -> np.ndarray:
    rng = np.random.default_rng(SEED)
    return np.stack([np.bincount(rng.integers(0, n_tiles, n_tiles), minlength=n_tiles)
                     for _ in range(DRAWS)]).astype(np.float64)


def subset(y, tix, probs, tiles_kept: np.ndarray):
    m = np.isin(tix, tiles_kept)
    return y[m], tix[m], {k: v[m] for k, v in probs.items()}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("package", type=Path)
    ap.add_argument("--confirm-reproduction", action="store_true")
    args = ap.parse_args()
    if not args.confirm_reproduction:
        raise SystemExit("this reads the 2025 test truth; pass --confirm-reproduction")
    if reproduction_logged():
        raise SystemExit("a reproduction is already logged; amendment 1, section 8 allows no "
                         "further read of the 2025 test truth (see docs/adr/0004-gate-2.md)")
    started = time.time()
    entry = stage_b_entry()
    if sha256(REPORT) != entry["report_sha256"]:
        raise SystemExit("the stage B report differs from the one logged")
    check_package(args.package, entry["package_digest"])
    logged = json.loads(REPORT.read_text())["tasks"]["forest"]
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True,
                            text=True, check=True).stdout.strip()
    with TOUCH_LOG.open("a", newline="\n") as f:  # logged before any truth is read
        f.write(json.dumps({"when": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
                            "what": WHAT, "git_commit": commit,
                            "package_digest": entry["package_digest"]}) + "\n")

    tiles, y, tix, probs = load(args.package)
    with SPLIT.open() as f:
        side = {r["tile_id"]: r["split"] for r in csv.DictReader(f)}
    parts = {"all": np.arange(len(tiles))}
    for name in ("test", "held_out"):
        parts[name] = np.array([i for i, t in enumerate(tiles) if side[t] == name])
    print(f"truth read: {y.size:,} cells, {int(y.sum()):,} events, {time.time() - started:.0f} s",
          flush=True)

    checks: list[dict] = []

    def check(name: str, ours: float, theirs: float, tol: float) -> None:
        checks.append({"check": name, "reproduced": ours, "stage_b": theirs,
                       "difference": abs(ours - theirs), "tolerance": tol,
                       "ok": bool(abs(ours - theirs) <= tol)})

    result: dict = {"parts": {}}
    for part, kept in parts.items():
        py, _, pp = subset(y, tix, probs, kept)
        rec = {"tiles": int(kept.size), "cells": int(py.size), "events": int(py.sum()), "ap": {}}
        check(f"{part}: cells", py.size, logged[part]["cells"], 0)
        check(f"{part}: events", int(py.sum()), logged[part]["events"], 0)
        for k, v in pp.items():
            rec["ap"][k] = float(average_precision_score(py, v))
            check(f"{part}: AP {k}", rec["ap"][k], logged[part]["baselines"][k]["ap"], TOL_AP)
            rec.setdefault("brier", {})[k] = float(np.mean((v - py) ** 2))
            check(f"{part}: Brier {k}", rec["brier"][k], logged[part]["baselines"][k]["brier"], TOL_AP)
        rec["relative_improvement"] = rec["ap"][MODEL] / rec["ap"][REFERENCE] - 1
        result["parts"][part] = rec
    verdict = logged["verdict"]
    check("all: improvement", result["parts"]["all"]["relative_improvement"],
          verdict["relative_improvement"], TOL_REL)
    for name in ("test", "held_out"):
        check(f"{name}: improvement", result["parts"][name]["relative_improvement"],
              verdict["improvement_by_part"][name], TOL_REL)

    # Bootstrap on all exam tiles: the weighted routine is checked against scikit-learn first.
    counts = draws(len(tiles))
    ranked = {k: Sorted(y, probs[k], tix) for k in (MODEL, REFERENCE)}
    for d in range(3):
        w = counts[d][tix]
        for k in ranked:
            ref = average_precision_score(y, probs[k], sample_weight=w)
            ours = ranked[k].ap(counts[d][ranked[k].tix])
            check(f"weighted AP routine, draw {d}, {k}", ours, float(ref), 1e-9)
    boot = {k: np.array([r.ap(counts[d][r.tix]) for d in range(DRAWS)]) for k, r in ranked.items()}
    rel = boot[MODEL] / boot[REFERENCE] - 1
    lo, hi = (float(x) for x in np.quantile(rel[np.isfinite(rel)], [0.025, 0.975]))
    check("all: improvement interval, low", lo, verdict["ci95"][0], TOL_CI)
    check("all: improvement interval, high", hi, verdict["ci95"][1], TOL_CI)
    for k in ranked:
        klo, khi = (float(x) for x in np.quantile(boot[k], [0.025, 0.975]))
        check(f"all: AP interval {k}, low", klo, logged["all"]["baselines"][k]["ap_ci95"][0], TOL_CI)
        check(f"all: AP interval {k}, high", khi, logged["all"]["baselines"][k]["ap_ci95"][1], TOL_CI)

    point = result["parts"]["all"]["relative_improvement"]
    guard = all(result["parts"][p]["relative_improvement"] > 0 for p in ("test", "held_out"))
    result["verdict"] = {
        "model": MODEL, "reference": REFERENCE, "relative_improvement": point, "ci95": [lo, hi],
        "condition_1_at_least_20pct": point >= WIN_RELATIVE,
        "condition_2_lower_bound_above_10pct": lo > WIN_LOWER,
        "condition_3_positive_on_each_part": guard,
        "win": bool(point >= WIN_RELATIVE and lo > WIN_LOWER and guard),
    }
    check("win", float(result["verdict"]["win"]), float(verdict["win"]), 0)
    out = {"what": WHAT, "package_digest": entry["package_digest"], "git_commit": commit,
           "stage_b_report_sha256": entry["report_sha256"], "tolerances_fixed_before_run": True,
           "all_checks_pass": all(c["ok"] for c in checks), "checks": checks, **result,
           "seconds": round(time.time() - started)}
    OUT.with_suffix(".json").write_text(json.dumps(out, indent=1) + "\n", newline="\n")
    write_md(out)
    failed = [c["check"] for c in checks if not c["ok"]]
    print(f"{len(checks)} checks, {len(failed)} failed{': ' + ', '.join(failed) if failed else ''}")
    print(f"verdict: {point:+.1%} [{lo:+.1%}, {hi:+.1%}], win {result['verdict']['win']}")
    sys.exit(1 if failed else 0)


def write_md(out: dict) -> None:
    v = out["verdict"]
    lines = [
        "# Stage B reproduction (task 2.8)", "",
        f"Independent re-grade of package `{out['package_digest']}` by "
        "`tools/phase2/reproduce_stage_b.py` (no shared grading code; truth from the source label "
        f"stores), commit `{out['git_commit'][:10]}`. All checks pass: **{out['all_checks_pass']}**.",
        "",
        f"Verdict: `{v['model']}` against `{v['reference']}`, {v['relative_improvement']:+.2%} "
        f"(95% interval {v['ci95'][0]:+.2%} to {v['ci95'][1]:+.2%}); win: **{v['win']}**.", "",
        "| Check | Reproduced | Stage B | Difference | Tolerance | OK |", "|---|---|---|---|---|---|",
    ]
    for c in out["checks"]:
        lines.append(f"| {c['check']} | {c['reproduced']:.10g} | {c['stage_b']:.10g} | "
                     f"{c['difference']:.2e} | {c['tolerance']:g} | {'yes' if c['ok'] else 'NO'} |")
    OUT.with_suffix(".md").write_text("\n".join(lines) + "\n", newline="\n")


if __name__ == "__main__":
    main()
