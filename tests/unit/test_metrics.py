import numpy as np
import pytest
from sklearn.metrics import average_precision_score

from almanac.evaluate.bootstrap import interval, tile_draws, win_verdict
from almanac.evaluate.metrics import (
    average_precision,
    brier,
    calibration,
    fss_terms,
    log_loss,
    precision_at_top,
    rank,
)


def test_average_precision_by_hand() -> None:
    # Ranked: 1, 0, 1, 0 -> precision at the two hits: 1/1 and 2/3 -> AP = (1 + 2/3) / 2
    y = np.array([1, 0, 1, 0])
    s = np.array([0.9, 0.8, 0.7, 0.1])
    assert average_precision(y, s) == pytest.approx((1 + 2 / 3) / 2)


def test_average_precision_matches_sklearn_with_ties() -> None:
    rng = np.random.default_rng(1)
    y = rng.random(5000) < 0.05
    s = np.round(rng.random(5000) + y * 0.3, 2)  # many ties
    assert average_precision(y, s) == pytest.approx(average_precision_score(y, s), abs=1e-12)


def test_constant_score_gives_base_rate() -> None:
    y = np.array([1, 0, 0, 0, 1, 0, 0, 0, 0, 0])
    assert average_precision(y, np.zeros(10)) == pytest.approx(0.2)
    assert precision_at_top(rank(y, np.zeros(10)), 0.1) == pytest.approx(0.2)


def test_weights_equal_duplication() -> None:
    rng = np.random.default_rng(2)
    y = rng.random(300) < 0.2
    s = rng.random(300)
    w = rng.integers(0, 3, 300).astype(float)
    dup = np.repeat(np.arange(300), w.astype(int))
    assert average_precision(y, s, w) == pytest.approx(average_precision(y[dup], s[dup]))


def test_precision_at_top_by_hand() -> None:
    y = np.array([1, 1, 0, 0, 1, 0, 0, 0, 0, 0])
    s = np.array([10, 9, 8, 7, 6, 5, 4, 3, 2, 1])
    r = rank(y, s)
    assert precision_at_top(r, 0.2) == pytest.approx(1.0)
    assert precision_at_top(r, 0.5) == pytest.approx(3 / 5)
    assert precision_at_top(r, 0.25) == pytest.approx(2 / 2.5)  # half of the third cell


def test_proper_scores_and_calibration() -> None:
    y = np.array([0, 1])
    assert brier(y, np.array([0.0, 1.0])) == 0
    assert brier(y, np.array([0.5, 0.5])) == pytest.approx(0.25)
    assert log_loss(y, np.array([0.5, 0.5])) == pytest.approx(np.log(2))
    rng = np.random.default_rng(3)
    p = rng.random(100_000)
    yy = (rng.random(100_000) < p).astype(float)
    assert calibration(yy, p)["ece"] < 0.01
    assert calibration(yy, np.clip(p * 0.5, 0, 1))["ece"] > 0.2


def test_fss_perfect_and_disjoint() -> None:
    a = np.zeros((20, 20))
    a[5, 5] = 1
    num, ref = fss_terms(a, a, 3)
    assert num == 0 and ref > 0
    b = np.zeros((20, 20))
    b[15, 15] = 1
    num, ref = fss_terms(a, b, 1)
    assert 1 - num / ref == 0
    c = np.zeros((20, 20))
    c[5, 6] = 1  # one cell off: no credit at scale 1, credit at scale 3
    assert 1 - np.divide(*fss_terms(a, c, 1)) == 0
    assert 1 - np.divide(*fss_terms(a, c, 3)) > 0.5


def test_win_verdict() -> None:
    assert win_verdict(0.30, 0.20, np.full(100, 0.5))["win"]
    assert not win_verdict(0.23, 0.20, np.full(100, 0.15))["win"]  # 15% < 20%
    assert not win_verdict(0.30, 0.20, np.linspace(0.0, 1.0, 101))["win"]  # lower bound too low


@pytest.mark.slow
def test_bootstrap_interval_covers_true_mean() -> None:
    # The tile bootstrap of a smooth statistic (the event rate) covers the population value.
    from almanac.evaluate.bootstrap import bootstrap_stat

    rng = np.random.default_rng(4)
    truth = 1 / 16  # mean of Beta(1, 15)
    covered, reps = 0, 200
    for _ in range(reps):
        rate = rng.beta(1, 15, 60)
        tile = np.repeat(np.arange(60), 200)
        y = (rng.random(tile.size) < rate[tile]).astype(float)
        counts = tile_draws(60, 400, int(rng.integers(1 << 30)))
        lo, hi = interval(bootstrap_stat(lambda w, y=y: float(np.average(y, weights=w)), tile, counts))
        covered += lo <= truth <= hi
    assert 0.90 <= covered / reps <= 0.99


# Average precision is different: the same simulation with AP, or with the relative AP of two
# forecasts, covers the population value only 50-70% of the time at 60 tiles and about 88% at
# 240, and misses on the high side. tools/phase1/bootstrap_coverage.py measures this, and the
# pre-registration states it as a limit of the interval method.
