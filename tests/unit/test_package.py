import json

import numpy as np
import pytest

from almanac.registry.package import build_manifest, canonical, digest, verify, write_layer, write_tiles


def _package(root, seed: int = 0) -> str:
    rng = np.random.default_rng(seed)
    p = rng.random((2, 128, 128)).astype(np.float32)
    p[0, :3] = np.nan
    write_layer(root / "baselines" / "B4_forest.npy", p)
    write_tiles(root / "tiles.csv", ["20S_E1_N2", "21S_E3_N4"])
    (root / "code_ref.txt").write_text("abc\n", newline="\n")
    return build_manifest(root, {"issue": "test"})


def test_rebuild_gives_the_same_digest(tmp_path) -> None:
    a = _package(tmp_path / "a")
    b = _package(tmp_path / "b")
    assert a == b == digest(tmp_path / "a")
    assert verify(tmp_path / "a") == []


def test_any_change_is_detected(tmp_path) -> None:
    root = tmp_path / "p"
    d0 = _package(root)
    assert _package(tmp_path / "q", seed=1) != d0
    layer = root / "baselines" / "B4_forest.npy"
    data = bytearray(layer.read_bytes())
    data[-1] ^= 1
    layer.write_bytes(bytes(data))
    (root / "extra.txt").write_text("x")
    (root / "code_ref.txt").unlink()
    expected = ["changed baselines/B4_forest.npy", "missing code_ref.txt", "unlisted extra.txt"]
    assert sorted(verify(root)) == expected


def test_manifest_is_canonical(tmp_path) -> None:
    root = tmp_path / "p"
    _package(root)
    raw = (root / "manifest.json").read_bytes()
    assert raw == canonical(json.loads(raw)) and b" " not in raw.split(b'"files"')[1][:2]
    m = json.loads(raw)
    assert [e["path"] for e in m["files"]] == sorted(e["path"] for e in m["files"])


def test_layer_rules(tmp_path) -> None:
    with pytest.raises(ValueError):
        write_layer(tmp_path / "x.npy", np.full((1, 128, 128), 1.5))
    with pytest.raises(ValueError):
        write_layer(tmp_path / "x.npy", np.zeros((128, 128)))
    with pytest.raises(ValueError):
        write_tiles(tmp_path / "t.csv", ["b", "a"])
