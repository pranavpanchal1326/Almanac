"""Stage B's guards: the 2025 test truth is read once, on purpose, from an unchanged package."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "phase2"))
import stage_b  # noqa: E402


def test_grade_refuses_without_confirmation(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="confirm-single-touch"):
        stage_b.cmd_grade(tmp_path, dry=False, confirm=False)


def test_grade_refuses_a_second_touch(tmp_path: Path, monkeypatch) -> None:
    log = tmp_path / "touch.jsonl"
    log.write_text(json.dumps({"what": stage_b.STAGE_B}) + "\n")
    monkeypatch.setattr(stage_b, "TOUCH_LOG", log)
    assert stage_b.stage_b_logged()
    with pytest.raises(SystemExit, match="already logged"):
        stage_b.cmd_grade(tmp_path, dry=False, confirm=True)


def test_earlier_baseline_touches_do_not_count_as_stage_b(tmp_path: Path, monkeypatch) -> None:
    log = tmp_path / "touch.jsonl"
    log.write_text(json.dumps({"what": "baselines B0-B4, test_2025 and held_out_2025"}) + "\n")
    monkeypatch.setattr(stage_b, "TOUCH_LOG", log)
    assert not stage_b.stage_b_logged()


def test_grade_refuses_a_changed_package(tmp_path: Path) -> None:
    from almanac.registry.package import build_manifest, write_tiles

    tiles, year = stage_b.plan(dry=True)
    write_tiles(tmp_path / "tiles.csv", tiles)
    meta = {"what": "test", "target": year, "tiles": len(tiles)}
    (tmp_path / "meta.json").write_text(json.dumps(meta))
    build_manifest(tmp_path, {})
    (tmp_path / "meta.json").write_text(json.dumps({**meta, "what": "edited"}))
    with pytest.raises(SystemExit, match="changed"):
        stage_b.cmd_grade(tmp_path, dry=True, confirm=False)


def test_grade_refuses_a_package_built_for_the_other_run(tmp_path: Path, monkeypatch) -> None:
    # A dry (validation) package can never be graded as the real stage B; no manifest exists here,
    # so even a broken check would stop before any truth is read.
    monkeypatch.setattr(stage_b, "TOUCH_LOG", tmp_path / "empty.jsonl")
    tiles, year = stage_b.plan(dry=True)
    (tmp_path / "meta.json").write_text(json.dumps({"what": "x", "target": year, "tiles": len(tiles)}))
    with pytest.raises(SystemExit, match="not built for this run"):
        stage_b.cmd_grade(tmp_path, dry=False, confirm=True)


def test_plan_uses_the_exam_tiles_for_2025() -> None:
    tiles, year = stage_b.plan(dry=False)
    assert year == 2025 and len(tiles) == 499 and tiles == sorted(tiles)
    val, vyear = stage_b.plan(dry=True)
    assert vyear == 2024 and len(val) == 146 and not set(val) & set(tiles)


def test_part_renumbers_tiles_for_the_bootstrap() -> None:
    y = np.array([1.0, 0.0, 1.0, 0.0])
    tix = np.array([0, 1, 2, 2], np.int32)
    rows = np.arange(4)
    probs = {"a": np.array([0.9, 0.1, 0.8, 0.2])}
    py, pt, pr, pp = stage_b.part(y, tix, rows, probs, np.array([2]))
    assert py.tolist() == [1.0, 0.0] and pt.tolist() == [0, 0]
    assert pr.tolist() == [2, 3] and pp["a"].tolist() == [0.8, 0.2]
