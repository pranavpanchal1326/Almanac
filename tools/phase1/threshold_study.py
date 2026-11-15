"""Task 1.8: choose the rule for an embedding change event, on training tiles only.

Usage: python tools/phase1/threshold_study.py configs/splits/amazon_cerrado_v1.csv

Candidates (src/almanac/data/change_rules.py): one regional threshold, a threshold per land class
(k-means clusters of the starting year's embedding), and a per-cell z-score against the cell's own
history. Each is calibrated to flag Q of label-stable land, using change pairs ending 2020..2023
(the training target years with at least two earlier pairs for the history rule). All are then
evaluated on pairs ending 2020..2025, still on training tiles only.

Label-stable cell: at least half land, valid in both years, and no forest loss in the source in
the year before, the year of, or the year after the pair's end year (where those years exist).
A loss cell: at least LOSS_EVENT of the cell lost in the pair's end year.

Decision rule, fixed before the run: the chosen rule is the one with the highest recall of loss
cells (flagged by the pair ending in the loss year) at the common false-alarm rate,
unless its event rate across land classes varies more than twice as much as the runner-up's (max
over min of class rates), in which case the runner-up is chosen.

Writes docs/phase1/threshold_study.json and configs/thresholds/amazon_cerrado_v1.json.
"""

from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path

import numpy as np
from sklearn.cluster import MiniBatchKMeans
from sklearn.metrics import average_precision_score, roc_auc_score

from almanac.common.constants import YEARS
from almanac.data.change_rules import class_thresholds, history_z, quantile_threshold
from almanac.data.cube import load_cube

REPO = Path(__file__).resolve().parents[2]
Q = 0.99
N_CLASSES = 12
LOSS_EVENT = 0.025  # 10 of 400 sample points, about 1 ha of the 41 ha cell
LOSS_LARGE = 0.2
FIT_ENDS = (2020, 2021, 2022, 2023)
EVAL_ENDS = (2020, 2021, 2022, 2023, 2024, 2025)
PHASE0_TAU = 0.0124  # pooled 99th percentile of stable sites at 640 m, ADR 0001
SEED = 20261115


def main() -> None:
    split_csv = Path(sys.argv[1])
    with split_csv.open() as f:
        train = [r["tile_id"] for r in csv.DictReader(f) if r["split"] == "train"]
    rng = np.random.default_rng(SEED)
    t0 = time.time()

    # 1. Land classes from a sample of training embeddings, years 2017..2022.
    sample = []
    for tid in rng.choice(train, 200, replace=False):
        cube = load_cube(str(tid), embeddings=True, forest=False)
        for year in YEARS[:6]:
            ok = cube.valid[YEARS.index(year)] & (cube.land >= 0.5)
            idx = np.flatnonzero(ok)
            if idx.size == 0:
                continue
            pick = rng.choice(idx, min(400, idx.size), replace=False)
            sample.append(cube.embedding(year).reshape(64, -1)[:, pick].T)
    sample_arr = np.concatenate(sample)
    km = MiniBatchKMeans(N_CLASSES, random_state=SEED, n_init=3, batch_size=8192).fit(sample_arr)
    print(f"k-means on {len(sample_arr)} cells, {time.time() - t0:.0f}s", flush=True)

    # 2. Per land cell and pair ending 2020..2025: delta, z, class, loss in years around the end.
    cols: dict[str, list[np.ndarray]] = {k: [] for k in ("end", "delta", "z", "cls", "prev", "now", "next")}
    for n, tid in enumerate(train):
        cube = load_cube(tid, embeddings=True, forest=False)
        z = history_z(cube.delta)
        land = (cube.land >= 0.5).ravel()
        for end in EVAL_ENDS:
            i = end - 2018  # pair index and label index of the end year
            start = end - 1
            ok = land & ~np.isnan(cube.delta[i].ravel())
            if not ok.any():
                continue
            emb = cube.embedding(start).reshape(64, -1)[:, ok].T
            cols["end"].append(np.full(ok.sum(), end, dtype=np.int16))
            cols["delta"].append(cube.delta[i].ravel()[ok])
            cols["z"].append(z[i].ravel()[ok])
            cols["cls"].append(km.predict(emb).astype(np.int8))
            cols["now"].append(cube.loss[i].ravel()[ok])
            cols["prev"].append(cube.loss[i - 1].ravel()[ok])
            nxt = cube.loss[i + 1].ravel()[ok] if i + 1 < len(cube.loss) else np.full(ok.sum(), np.nan)
            cols["next"].append(nxt.astype(np.float32))
        if (n + 1) % 100 == 0:
            print(f"{n + 1}/{len(train)} tiles, {time.time() - t0:.0f}s", flush=True)
    d = {k: np.concatenate(v) for k, v in cols.items()}
    nxt0 = np.nan_to_num(d["next"], nan=0.0)
    stable = (d["prev"] == 0) & (d["now"] == 0) & (nxt0 == 0)
    fit = np.isin(d["end"], FIT_ENDS)

    # 3. Calibrate each rule on stable cells of the fit years.
    tau_global = quantile_threshold(d["delta"][stable & fit], Q)
    tau_class = class_thresholds(d["delta"][stable & fit], d["cls"][stable & fit], N_CLASSES, Q)
    z_star = quantile_threshold(d["z"][stable & fit], Q)
    has_z = np.isfinite(d["z"])
    flags = {
        "global": d["delta"] > tau_global,
        "class": d["delta"] > tau_class[d["cls"]],
        "history": has_z & (d["z"] > z_star),
        "phase0_tau": d["delta"] > PHASE0_TAU,
        "fixed_0.2": d["delta"] > 0.2,
    }
    scores = {
        "global": d["delta"],
        "class": d["delta"] / tau_class[d["cls"]],
        "history": np.where(has_z, d["z"], -np.inf),
    }

    # 4. Evaluate on the rows where every rule is defined.
    loss_now = d["now"] >= LOSS_EVENT
    large_now = d["now"] >= LOSS_LARGE
    report: dict = {
        "task": "1.8",
        "split_file": split_csv.as_posix(),
        "tiles": len(train),
        "cell_pairs": int(d["end"].size),
        "q": Q,
        "loss_event_share": LOSS_EVENT,
        "fit_end_years": FIT_ENDS,
        "eval_end_years": EVAL_ENDS,
        "n_classes": N_CLASSES,
        "thresholds": {
            "global_tau": round(tau_global, 5),
            "class_tau": [round(float(t), 5) for t in tau_class],
            "history_z_star": round(z_star, 3),
        },
        "class_share_of_land": [round(float((d["cls"] == c).mean()), 4) for c in range(N_CLASSES)],
        "class_loss_rate": [round(float(loss_now[d["cls"] == c].mean()), 4) for c in range(N_CLASSES)],
        "rules": {},
    }
    eval_mask = has_z  # compare all rules on the same rows: those where the history rule is defined
    for name, flag in flags.items():
        f = flag & eval_mask
        by_year = {}
        for end in EVAL_ENDS:
            m = eval_mask & (d["end"] == end)
            by_year[str(end)] = {
                "stable_flag_rate": round(float(f[m & stable].mean()), 4),
                "land_flag_rate": round(float(f[m].mean()), 4),
                "loss_cell_recall": round(float(f[m & loss_now].mean()), 4),
            }
        class_rates = np.array(
            [f[eval_mask & stable & (d["cls"] == c)].mean() for c in range(N_CLASSES)], dtype=np.float64
        )
        present = class_rates[np.isfinite(class_rates)]
        flagged = f.sum()
        entry = {
            "stable_flag_rate": round(float(f[eval_mask & stable].mean()), 4),
            "land_flag_rate": round(float(f[eval_mask].mean()), 4),
            "loss_cell_recall_same_year": round(float(f[eval_mask & loss_now].mean()), 4),
            "large_loss_recall_same_year": round(float(f[eval_mask & large_now].mean()), 4),
            "flags_on_loss_cells_share": round(
                float((f & (loss_now | (nxt0 >= LOSS_EVENT))).sum() / max(flagged, 1)), 4
            ),
            "stable_flag_rate_by_class": [round(float(r), 4) for r in class_rates],
            "class_rate_max_over_min": round(float(present.max() / max(present.min(), 1e-6)), 2),
            "by_end_year": by_year,
        }
        report["rules"][name] = entry

    # Lagged recall: share of cells that lost forest in the year before the pair's end year and
    # are flagged by that pair (loss late in a year shows in the next annual composite).
    prev_loss = d["prev"] >= LOSS_EVENT
    for name, flag in flags.items():
        f = flag & eval_mask
        report["rules"][name]["loss_last_year_recall"] = round(float(f[eval_mask & prev_loss].mean()), 4)

    # Ranking quality of each continuous score against loss in the end year, on a random subset.
    sub = np.flatnonzero(eval_mask)
    sub = rng.choice(sub, min(4_000_000, sub.size), replace=False)
    for name, score in scores.items():
        s = np.nan_to_num(score[sub], nan=-np.inf, neginf=-1e9)
        y = loss_now[sub]
        report["rules"][name]["auc_vs_loss"] = round(float(roc_auc_score(y, s)), 4)
        report["rules"][name]["ap_vs_loss"] = round(float(average_precision_score(y, s)), 4)
        report["rules"][name]["ap_base_rate"] = round(float(y.mean()), 4)

    # 5. Apply the decision rule.
    cands = ["global", "class", "history"]
    ranked = sorted(cands, key=lambda r: -report["rules"][r]["loss_cell_recall_same_year"])
    best, second = ranked[0], ranked[1]
    spread = {r: report["rules"][r]["class_rate_max_over_min"] for r in cands}
    chosen = second if spread[best] > 2 * spread[second] else best
    report["decision"] = {"ranked_by_recall": ranked, "class_spread": spread, "chosen": chosen}
    report["seconds"] = round(time.time() - t0)

    out = REPO / "docs" / "phase1" / "threshold_study.json"
    out.write_text(json.dumps(report, indent=2))
    record = {
        "name": "amazon_cerrado_v1",
        "task": "1.8",
        "rule": chosen,
        "level": 6,
        "q": Q,
        "global_tau": report["thresholds"]["global_tau"],
        "class_tau": report["thresholds"]["class_tau"],
        "history_z_star": report["thresholds"]["history_z_star"],
        "history_spread_floor": 0.005,
        "history_min_pairs": 2,
        "kmeans_centres": [[round(float(v), 6) for v in c] for c in km.cluster_centers_],
        "calibrated_on": {"split": split_csv.as_posix(), "tiles": "train", "end_years": FIT_ENDS},
    }
    thr = REPO / "configs" / "thresholds" / "amazon_cerrado_v1.json"
    thr.parent.mkdir(parents=True, exist_ok=True)
    thr.write_text(json.dumps(record, indent=1))
    print(json.dumps({k: v for k, v in report.items() if k != "rules"}, indent=2))
    for name, entry in report["rules"].items():
        print(name, {k: v for k, v in entry.items() if k not in ("by_end_year", "stable_flag_rate_by_class")})


if __name__ == "__main__":
    main()
