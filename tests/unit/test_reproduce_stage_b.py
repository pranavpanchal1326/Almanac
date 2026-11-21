"""The independent re-grader of stage B: its weighted AP, its draws and its guard."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest
from sklearn.metrics import average_precision_score

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "phase2"))
import reproduce_stage_b as r  # noqa: E402


def test_weighted_ap_matches_scikit_learn_with_ties() -> None:
    rng = np.random.default_rng(0)
    y = (rng.random(5000) < 0.1).astype(np.int8)
    score = np.round(rng.random(5000) + 0.3 * y, 2)  # rounding makes many ties
    tix = rng.integers(0, 40, 5000).astype(np.int32)
    s = r.Sorted(y, score, tix)
    assert s.ap(np.ones(y.size)) == pytest.approx(average_precision_score(y, score), abs=1e-12)
    w = rng.integers(0, 3, 40).astype(np.float64)
    assert s.ap(w[s.tix]) == pytest.approx(
        average_precision_score(y, score, sample_weight=w[tix]), abs=1e-12
    )


def test_draws_follow_the_preregistered_seed() -> None:
    counts = r.draws(7)
    assert counts.shape == (r.DRAWS, 7) and (counts.sum(axis=1) == 7).all()
    first = np.bincount(np.random.default_rng(20261115).integers(0, 7, 7), minlength=7)
    assert counts[0].tolist() == first.tolist()


def test_refuses_without_confirmation(monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", ["reproduce_stage_b.py", "somewhere"])
    with pytest.raises(SystemExit, match="confirm-reproduction"):
        r.main()


def test_refuses_a_second_read_of_the_test_truth(tmp_path: Path, monkeypatch) -> None:
    log = tmp_path / "touch.jsonl"
    log.write_text(json.dumps({"what": r.WHAT}) + "\n")
    monkeypatch.setattr(r, "TOUCH_LOG", log)
    monkeypatch.setattr(sys, "argv", ["reproduce_stage_b.py", "x", "--confirm-reproduction"])
    with pytest.raises(SystemExit, match="already logged"):
        r.main()
