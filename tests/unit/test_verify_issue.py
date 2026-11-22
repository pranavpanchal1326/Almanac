"""The stand-alone verifier passes an intact package and fails a tampered one."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np

from almanac.registry.package import build_manifest, write_layer, write_tiles

REPO = Path(__file__).resolve().parents[2]
TOOL = REPO / "tools" / "verify_issue.py"


def make(root: Path) -> str:
    tiles = ["18N_E1_N1", "18N_E2_N2"]
    write_tiles(root / "tiles.csv", tiles)
    rng = np.random.default_rng(0)
    for task in ("forest", "embedding"):
        base = rng.random((2, 128, 128)).astype(np.float32)
        base[:, :10] = np.nan  # not eligible
        for b in ("B0", "B1", "B2", "B3", "B4"):
            write_layer(root / "baselines" / f"{b}_{task}.npy", base)
        for m in ("M_A2", "B5_A2"):
            write_layer(root / "forecast" / f"{m}_{task}.npy", rng.random((2, 128, 128)).astype(np.float32))
    return build_manifest(root, {"issue": "test"})


def run(root: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(TOOL), str(root), *extra], capture_output=True, text=True)


def test_intact_package_verifies(tmp_path: Path) -> None:
    digest = make(tmp_path)
    res = run(tmp_path, "--digest", digest)
    assert res.returncode == 0 and "VERIFIED" in res.stdout


def test_wrong_digest_fails(tmp_path: Path) -> None:
    make(tmp_path)
    assert run(tmp_path, "--digest", "0" * 64).returncode == 1


def test_changed_layer_fails(tmp_path: Path) -> None:
    make(tmp_path)
    p = tmp_path / "forecast" / "M_A2_forest.npy"
    a = np.load(p)
    a[0, 50, 50] = 0.5 if a[0, 50, 50] != 0.5 else 0.25
    np.save(p, a)
    res = run(tmp_path)
    assert res.returncode == 1 and "FAIL" in res.stdout


def test_gap_in_headline_fails(tmp_path: Path) -> None:
    make(tmp_path)
    p = tmp_path / "forecast" / "M_A2_forest.npy"
    a = np.load(p)
    a[1, 100, 100] = np.nan  # a baseline cell the headline no longer covers
    write_layer(p, a)
    build_manifest(tmp_path, {"issue": "test"})
    res = run(tmp_path)
    assert res.returncode == 1 and "covers" in res.stdout
