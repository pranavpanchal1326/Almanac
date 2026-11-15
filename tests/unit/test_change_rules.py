import numpy as np
import pytest

from almanac.data.change_rules import (
    HISTORY_SPREAD_FLOOR,
    class_thresholds,
    history_z,
    quantile_threshold,
)


def test_history_z_uses_only_earlier_pairs() -> None:
    delta = np.zeros((5, 1, 2), dtype=np.float32)
    delta[:, 0, 0] = [0.01, 0.02, 0.03, 0.5, 0.01]
    delta[:, 0, 1] = [0.01, np.nan, np.nan, 0.5, 0.01]
    z = history_z(delta, min_history=2)
    assert np.isnan(z[:2]).all()
    # pair 2 against [0.01, 0.02]: median 0.015, MAD 0.005 -> spread 1.4826 * 0.005
    assert z[2, 0, 0] == pytest.approx((0.03 - 0.015) / (1.4826 * 0.005), rel=1e-4)
    # pair 3 against [0.01, 0.02, 0.03]: median 0.02, MAD 0.01
    assert z[3, 0, 0] == pytest.approx((0.5 - 0.02) / (1.4826 * 0.01), rel=1e-4)
    # changing a later pair never changes an earlier score
    later = delta.copy()
    later[4] = 1.0
    np.testing.assert_array_equal(history_z(later)[:4], z[:4])
    # second cell has only one valid earlier pair until pair 3
    assert np.isnan(z[3, 0, 1])


def test_history_z_spread_floor() -> None:
    delta = np.full((3, 1, 1), 0.02, dtype=np.float32)
    delta[2] = 0.03
    z = history_z(delta)
    assert z[2, 0, 0] == pytest.approx(0.01 / HISTORY_SPREAD_FLOOR, rel=1e-4)


def test_thresholds() -> None:
    rng = np.random.default_rng(0)
    score = np.concatenate([rng.uniform(0, 1, 10_000), rng.uniform(0, 10, 10_000), [np.nan]])
    classes = np.concatenate([np.zeros(10_000), np.ones(10_000), [0]]).astype(int)
    assert quantile_threshold(score, 0.5) == pytest.approx(1.0, abs=0.1)
    t = class_thresholds(score, classes, 3, 0.99)
    assert t[0] == pytest.approx(0.99, abs=0.02)
    assert t[1] == pytest.approx(9.9, abs=0.2)
    assert t[2] == quantile_threshold(score, 0.99)  # empty class falls back to pooled
