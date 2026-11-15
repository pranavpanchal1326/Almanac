import numpy as np
import pytest

from almanac.io.index import to_https
from almanac.quality.embedding import (
    change_between,
    coarsen_mean,
    cosine_change,
    dequantize,
    length_report,
    renormalize,
    threshold_from_stable,
)


def test_dequantize_hand_values() -> None:
    v = np.array([0, 127, -127, 64, -64], dtype=np.int8)
    out = dequantize(v)
    assert out.dtype == np.float32
    np.testing.assert_allclose(
        out,
        [0.0, (127 / 127.5) ** 2, -((127 / 127.5) ** 2), (64 / 127.5) ** 2, -((64 / 127.5) ** 2)],
        rtol=1e-6,
    )


def test_cosine_change_known_vectors() -> None:
    a = np.zeros((64, 1, 3), dtype=np.float32)
    b = np.zeros((64, 1, 3), dtype=np.float32)
    a[0] = 1.0
    b[0, 0, 0] = 1.0  # same direction
    b[1, 0, 1] = 1.0  # orthogonal
    b[0, 0, 2] = -1.0  # opposite
    np.testing.assert_allclose(cosine_change(a, b), [[0.0, 1.0, 2.0]], atol=1e-6)


def test_change_between_masks_nodata() -> None:
    rng = np.random.default_rng(0)
    a = rng.integers(-127, 128, size=(64, 4, 4)).astype(np.int8)
    b = a.copy()
    b[:, 0, 0] = -128
    delta, valid = change_between(a, b)
    assert not valid[0, 0] and valid.sum() == 15
    np.testing.assert_allclose(delta[valid], 0.0, atol=1e-6)


def test_length_report_and_renormalize() -> None:
    emb = renormalize(np.random.default_rng(1).normal(size=(64, 8, 8)).astype(np.float32))
    rep = length_report(emb, np.ones((8, 8), dtype=bool))
    assert rep["n"] == 64 and rep["in_band"] == 1.0
    assert abs(rep["p50"] - 1.0) < 1e-5


def test_threshold_is_percentile_of_pool() -> None:
    assert threshold_from_stable([np.arange(50.0), np.arange(50.0, 101.0)], 99.0) == pytest.approx(99.0)


def test_coarsen_mean_renormalises_and_respects_validity() -> None:
    emb = np.zeros((64, 2, 4), dtype=np.float32)
    emb[0, :, :2] = 1.0
    emb[1, :, 2:] = 1.0
    valid = np.ones((2, 4), dtype=bool)
    valid[:, 2:] = False
    valid[0, 2] = True  # one valid cell of four: below half
    coarse, ok = coarsen_mean(emb, valid, 2)
    assert coarse.shape == (64, 1, 2)
    np.testing.assert_allclose(np.linalg.norm(coarse[:, 0, 0]), 1.0, atol=1e-6)
    assert ok.tolist() == [[True, False]]


def test_index_path_form() -> None:
    s3 = "s3://us-west-2.opendata.source.coop/tge-labs/aef/v1/annual/2017/10N/a-0000000000-0000000000.tiff"
    assert (
        to_https(s3)
        == "https://data.source.coop/tge-labs/aef/v1/annual/2017/10N/a-0000000000-0000000000.tiff"
    )
    with pytest.raises(ValueError):
        to_https("https://example.org/x.tiff")
