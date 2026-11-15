"""Gate Q1 offline: north is up.

The fixture is every eighth cell of one real coastline block (Mediterranean coast near El Alamein,
Egypt, 2021), as
returned by the production reader, with a water mask from Sentinel-2 near-infrared and a frozen
linear water probe. Rebuilt by ``tools/phase0/orientation.py``.
"""

from pathlib import Path

import numpy as np

from almanac.quality.embedding import dequantize, renormalize

FIXTURE = Path(__file__).parent / "orientation_coast.npz"


def _probe(stored: np.ndarray, w: np.ndarray, b: float) -> np.ndarray:
    return np.einsum("c,chw->hw", w, renormalize(dequantize(stored))) > b


def test_fixture_shape_and_type() -> None:
    with np.load(FIXTURE) as f:
        assert f["stored"].shape == (64, 128, 128)
        assert f["stored"].dtype == np.int8
        assert f["reference_water"].shape == (128, 128)


def test_north_is_up_and_a_flipped_array_fails() -> None:
    with np.load(FIXTURE) as f:
        stored, ref, w, b = f["stored"], f["reference_water"], f["probe_w"], float(f["probe_b"])
    north_up = float((_probe(stored, w, b) == ref).mean())
    flipped = float((_probe(stored[:, ::-1, :], w, b) == ref).mean())
    assert north_up > 0.8, north_up
    assert flipped < 0.5, flipped
