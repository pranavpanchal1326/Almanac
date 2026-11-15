"""Grade a forecast package against the truth (pre-registration sections 4 and 8).

Usage: python tools/phase5/grade.py PACKAGE_DIR YEAR [--task forest|embedding] [--model NAME]

Reads the package's ``tiles.csv`` and layers (``baselines/<B>_<task>.npy`` and, if present,
``forecast/<NAME>_<task>.npy``), takes truth and eligibility from the training store for YEAR,
scores every layer with the same function as the baseline report, and applies the win condition:

1. the model's AP is at least 20% above the reference's (B4) on all package tiles;
2. the lower end of the 95% paired tile-bootstrap interval of that improvement is above 10%;
3. the improvement is positive on the test tiles alone and on the held-out region alone.

Truth for 2026 needs the first Global Forest Change release with 2026 loss, built into the store
with the same sampling and forest definition; until then this grades past years only (used to
test the grader against the baseline report).
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "phase1"))

from baseline_report import evaluate

from almanac.evaluate.bootstrap import DRAWS, WIN_LOWER, WIN_RELATIVE, bootstrap_ap, interval, tile_draws
from almanac.evaluate.metrics import rank
from almanac.model.store import AUX, TileStore, embedding_eligible, forest_eligible, forest_event

REFERENCE = "B4"
SEED = 20261115


def truth(store: TileStore, year: int, task: str) -> tuple[np.ndarray, np.ndarray]:
    aux = np.asarray(store.aux)
    if task == "forest":
        return forest_eligible(aux, year), forest_event(aux, year)
    return embedding_eligible(aux, year), aux[AUX[f"emb_event_{year}"]] > 0


def load_layers(root: Path, task: str, model: str | None) -> dict[str, np.ndarray]:
    layers = {
        p.stem.rsplit("_", 1)[0]: np.load(p) for p in sorted((root / "baselines").glob(f"*_{task}.npy"))
    }
    if model:
        layers[model] = np.load(root / "forecast" / f"{model}_{task}.npy")
    return layers


def collect(root: Path, year: int, task: str, model: str | None, tiles: list[str]):
    layers = load_layers(root, task, model)
    ys, tix, rows = [], [], []
    probs: dict[str, list[np.ndarray]] = {k: [] for k in layers}
    for t, tid in enumerate(tiles):
        elig, ev = truth(TileStore.open(tid), year, task)
        r = np.flatnonzero(elig.ravel())
        # A cell is graded only if every forecast covers it (all eligibility known at issue time).
        cover = np.all([np.isfinite(layers[k][t].reshape(-1)[r]) for k in layers], axis=0)
        r = r[cover]
        ys.append(ev.ravel()[r])
        tix.append(np.full(r.size, t, np.int32))
        rows.append(r)
        for k in layers:
            probs[k].append(layers[k][t].reshape(-1)[r].astype(np.float64))
    return (
        np.concatenate(ys).astype(np.float64),
        np.concatenate(tix),
        np.concatenate(rows),
        {k: np.concatenate(v) for k, v in probs.items()},
    )


def relative_draws(y, tix, probs, a: str, b: str, n_tiles: int, subset: np.ndarray | None = None):
    if subset is not None:
        keep = np.isin(tix, subset)
        y, tix = y[keep], tix[keep]
        probs = {k: v[keep] for k, v in probs.items()}
    ranked = {k: rank(y, probs[k]) for k in (a, b)}
    boot = bootstrap_ap(ranked, tix, tile_draws(n_tiles, DRAWS, SEED))
    from almanac.evaluate.metrics import average_precision_ranked

    point = average_precision_ranked(ranked[a]) / average_precision_ranked(ranked[b]) - 1
    return point, boot[a] / boot[b] - 1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("package", type=Path)
    ap.add_argument("year", type=int)
    ap.add_argument("--task", default="forest", choices=["forest", "embedding"])
    ap.add_argument("--model")
    ap.add_argument("--split", type=Path, default=REPO / "configs" / "splits" / "amazon_cerrado_v1.csv")
    args = ap.parse_args()
    with (args.package / "tiles.csv").open() as f:
        tiles = [r["tile_id"] for r in csv.DictReader(f)]
    with args.split.open() as f:
        side = {r["tile_id"]: r["split"] for r in csv.DictReader(f)}
    y, tix, rows, probs = collect(args.package, args.year, args.task, args.model, tiles)
    result: dict = {"package": args.package.as_posix(), "year": args.year, "task": args.task}
    result["scores"] = evaluate(y, tix, rows, probs, len(tiles), SEED, REFERENCE)
    if args.model:
        m = args.model
        point, draws = relative_draws(y, tix, probs, m, REFERENCE, len(tiles))
        lo, hi = interval(draws)
        parts = {}
        for name in ("test", "held_out"):
            subset = np.array([i for i, t in enumerate(tiles) if side.get(t) == name])
            if subset.size:
                p, _ = relative_draws(y, tix, probs, m, REFERENCE, len(tiles), subset)
                parts[name] = p
        guard = bool(parts) and all(v > 0 for v in parts.values())
        result["verdict"] = {
            "model": m,
            "reference": REFERENCE,
            "relative_improvement": point,
            "ci95": [lo, hi],
            "condition_1_at_least_20pct": point >= WIN_RELATIVE,
            "condition_2_lower_bound_above_10pct": lo > WIN_LOWER,
            "condition_3_positive_on_each_part": guard,
            "improvement_by_part": parts,
            "win": bool(point >= WIN_RELATIVE and lo > WIN_LOWER and guard),
        }
    print(json.dumps(result, indent=1, default=float))


if __name__ == "__main__":
    main()
