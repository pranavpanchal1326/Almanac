"""Automated part of the leakage review (blueprint 3.9 and 3.10; ADR 0005).

Usage: python tools/review/leakage_selfcheck.py

Runs from a clean clone with no data downloaded: every check reads only committed files, and the
tests it runs use synthetic data. It prints PASS or FAIL for each check and exits 0 only if all
pass. It is the part a machine can do; the judgement calls are in docs/review/LEAKAGE_REVIEW.md.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
failed = 0


def check(ok: bool, what: str, detail: str = "") -> None:
    global failed
    print(f"{'PASS' if ok else 'FAIL'}  {what}" + (f"  ({detail})" if detail else ""))
    failed += not ok


def sha(path: str) -> str:
    return hashlib.sha256((REPO / path).read_bytes()).hexdigest()


def main() -> int:
    prereg = (REPO / "docs/prereg/2027.01.md").read_text(encoding="utf-8")

    # 1. The split, threshold and data manifest are the ones fixed by the pre-registration.
    for path in ("configs/splits/amazon_cerrado_v1.json", "configs/splits/amazon_cerrado_v1.csv",
                 "configs/manifests/amazon_cerrado_v1.sha256", "configs/thresholds/amazon_cerrado_v1.json"):
        d = sha(path)
        check(d in prereg, f"{path} matches the digest in the pre-registration", d[:12])

    # 2. Split by tile; no scored tile touches a training tile; every split present.
    with (REPO / "configs/splits/amazon_cerrado_v1.csv").open() as f:
        rows = list(csv.DictReader(f))
    counts = Counter(r["split"] for r in rows)
    check(len({r["tile_id"] for r in rows}) == len(rows), "each tile is in exactly one split", f"{len(rows)} tiles")
    check(all(counts[s] > 0 for s in ("train", "buffer", "validation", "test", "held_out")),
          "train, buffer, validation, test and held-out splits all present", dict(counts).__repr__())
    report = json.loads((REPO / "configs/splits/amazon_cerrado_v1_report.json").read_text())
    touching = report.get("training_tiles_touching_a_scored_tile")
    check(touching == 0, "no training tile touches a scored tile (split report)", f"{touching}")

    # 3. Training targets end in 2023; validation is 2024; the test year 2025 is never a training target.
    for cfg in sorted((REPO / "configs/model").glob("stage_a2_*.json")):
        c = json.loads(cfg.read_text())
        check(max(c["train_targets"]) <= 2023 and c["split"] == "configs/splits/amazon_cerrado_v1.csv",
              f"{cfg.name}: trains on targets {min(c['train_targets'])}-{max(c['train_targets'])} of the pinned split")
    train_py = (REPO / "tools/phase2/train.py").read_text(encoding="utf-8")
    check('if max(cfg["train_targets"]) > 2023:' in train_py, "train.py refuses any training target after 2023")

    # 4. Calibration was fitted on validation 2024 only.
    val = json.loads((REPO / "docs/phase2/ensemble_m_a/validation.json").read_text())
    check("validation 2024" in val["what"] and val["tiles"] == counts["validation"],
          "calibration maps fitted on validation 2024 tiles only", f"{val['tiles']} tiles")

    # 5. Every read of the 2025 test truth is logged, and stage B happened once.
    log = [json.loads(x) for x in (REPO / "docs/phase1/test_touch_log.jsonl").read_text().splitlines() if x.strip()]
    stage_b = [t for t in log if t["what"].startswith("stage B")]
    check(len(stage_b) == 1, "stage B read the 2025 test truth exactly once", stage_b[0]["when"] if stage_b else "")
    for t in log:
        print(f"      logged read: {t['when'][:16]}  {t['what']}")

    # 6. The 2026 forecast was made from the frozen weights recorded before it.
    meta = json.loads((REPO / "docs/phase4/forecast_2026_meta.json").read_text())
    status = (REPO / "docs/phase2/STATUS.md").read_text(encoding="utf-8")
    frozen = set(re.findall(r"`([0-9a-f]{64})`", status))
    used = [*meta["model"]["seeds"].values(), meta["reference"]["checkpoint_sha256"]]
    check(all(h in frozen for h in used), "the 2026 forecast used the frozen weights listed in Phase 2 status",
          f"{len(used)} checkpoints")
    check(meta["target"] == 2026, "the forecast targets 2026")

    # 7. The data-free leakage tests (synthetic data): nothing from the target year reaches an input.
    tests = ["tests/unit/test_baselines.py::test_examples_use_nothing_from_the_target_year",
             "tests/unit/test_baselines.py::test_forecast_mode_changes_nothing_but_truth",
             "tests/unit/test_splits.py", "tests/unit/test_package.py"]
    model_tests = ["tests/unit/test_model.py::test_example_uses_nothing_from_the_target_year",
                   "tests/unit/test_model.py::test_inputs_only_example_matches_and_reads_no_labels"]
    if importlib.util.find_spec("torch"):
        tests += model_tests
    else:
        print("NOTE  the two model-input tests need PyTorch: run `uv sync --extra train` to include them")
    res = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *tests],
                         cwd=REPO, capture_output=True, text=True)
    last = (res.stdout.strip().splitlines() or ["no output"])[-1]
    check(res.returncode == 0, "leakage tests on synthetic data", last)

    print("ALL PASS" if failed == 0 else f"{failed} CHECK(S) FAILED")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
