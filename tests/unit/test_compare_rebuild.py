import json
import subprocess
import sys
from pathlib import Path

import numpy as np

from almanac.registry.package import build_manifest, write_layer, write_tiles

TOOL = Path(__file__).resolve().parents[2] / "tools" / "phase4" / "compare_rebuild.py"
META = {"issue": "test", "target": 2026}


def make(root: Path, layer: np.ndarray, built: str, model: str = "m") -> None:
    root.mkdir()
    write_tiles(root / "tiles.csv", ["a", "b"])
    write_layer(root / "forecast" / "M_forest.npy", layer)
    (root / "forecast" / "meta.json").write_text(json.dumps({"model": model, "built": built, "seconds": 3}))


def run(sealed: Path, rebuilt: Path) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(TOOL), str(sealed), str(rebuilt)]
    return subprocess.run(cmd, capture_output=True, text=True)


def layer() -> np.ndarray:
    x = np.random.default_rng(0).random((2, 128, 128)).astype(np.float32)
    x[0, 0, 0] = np.nan
    return x


def test_identical_layers_pass_despite_a_new_build_time(tmp_path):
    make(tmp_path / "s", layer(), "2026-11-22")
    build_manifest(tmp_path / "s", META)
    make(tmp_path / "r", layer(), "2026-11-23")
    res = run(tmp_path / "s", tmp_path / "r")
    assert res.returncode == 0, res.stdout + res.stderr
    assert "PASS" in res.stdout


def test_a_changed_cell_fails(tmp_path):
    make(tmp_path / "s", layer(), "2026-11-22")
    build_manifest(tmp_path / "s", META)
    x = layer()
    x[1, 5, 5] += 1e-6
    make(tmp_path / "r", x, "2026-11-22")
    res = run(tmp_path / "s", tmp_path / "r")
    assert res.returncode == 1 and "FAIL" in res.stdout and '"cells_differing": 1' in res.stdout


def test_a_changed_non_volatile_meta_field_fails(tmp_path):
    make(tmp_path / "s", layer(), "2026-11-22")
    build_manifest(tmp_path / "s", META)
    make(tmp_path / "r", layer(), "2026-11-22", model="other")
    assert run(tmp_path / "s", tmp_path / "r").returncode == 1
