import numpy as np
import pytest

from almanac.baselines.features import (
    ChangeRule,
    great_circle_next,
    proximity,
    proximity_kernel,
    tile_examples,
)
from almanac.data.cube import TileCube
from almanac.grid.ids import TileRef
from almanac.quality.embedding import quantize


def test_proximity_kernel_and_decay() -> None:
    k = proximity_kernel()
    assert k.shape == (15, 15) and k[7, 7] == 1.0
    assert k[7, 7 + 7] == pytest.approx(1 - 7 * 640 / 5000)
    assert k[0, 0] == 0.0  # corner is beyond 5 km
    m = np.zeros((32, 32))
    m[16, 16] = 1.0
    p = proximity(m)
    assert p[16, 16] == 1.0 and p[16, 20] < p[16, 18] and p[16, 24] == 0.0


def test_great_circle_score_equals_last_change() -> None:
    rng = np.random.default_rng(0)
    a = rng.normal(size=(64, 4, 4))
    b = rng.normal(size=(64, 4, 4))
    a /= np.linalg.norm(a, axis=0)
    b /= np.linalg.norm(b, axis=0)
    pred = great_circle_next(a, b)
    np.testing.assert_allclose(np.linalg.norm(pred, axis=0), 1.0, atol=1e-9)
    np.testing.assert_allclose(1 - (b * pred).sum(0), 1 - (a * b).sum(0), atol=1e-9)


def _cube(rng: np.random.Generator, side: int = 16) -> TileCube:
    emb = rng.normal(size=(9, 64, side, side))
    emb /= np.linalg.norm(emb, axis=1, keepdims=True)
    stored = quantize(emb)
    delta = rng.uniform(0, 0.3, (8, side, side)).astype(np.float32)
    return TileCube(
        TileRef("21S", 0, 0),
        valid=np.ones((9, side, side), bool),
        delta=delta,
        loss=rng.uniform(0, 0.05, (8, side, side)).astype(np.float32),
        loss_before=np.zeros((side, side), np.float32),
        land=np.ones((side, side), np.float32),
        forest_start=np.ones((9, side, side), np.float32),
        forest_lost=rng.uniform(0, 0.05, (8, side, side)).astype(np.float32),
        stored=stored,
    )


@pytest.mark.parametrize("task", ["forest", "embedding"])
def test_examples_use_nothing_from_the_target_year(task: str) -> None:
    rng = np.random.default_rng(1)
    cube = _cube(rng)
    rule = ChangeRule(centres=np.eye(64)[:4], class_tau=np.full(4, 0.15))
    target = 2023
    base = tile_examples(cube, target, task, rule)
    # Change everything about the target year and later; inputs must not move.
    t = target - 2018
    cube.delta[t:] = rng.uniform(0, 1, cube.delta[t:].shape)
    cube.forest_lost[t:] = rng.uniform(0, 1, cube.forest_lost[t:].shape)
    cube.loss[t:] = rng.uniform(0, 1, cube.loss[t:].shape)
    cube.stored[t + 1 :] = rng.integers(-127, 127, cube.stored[t + 1 :].shape, dtype=np.int8)
    after = tile_examples(cube, target, task, rule)
    np.testing.assert_array_equal(base.rows, after.rows)
    np.testing.assert_array_equal(base.features, after.features)
    for k in base.scores:
        np.testing.assert_array_equal(base.scores[k], after.scores[k])
    assert not np.array_equal(base.y, after.y)


@pytest.mark.parametrize("task", ["forest", "embedding"])
def test_forecast_mode_changes_nothing_but_truth(task: str) -> None:
    rng = np.random.default_rng(3)
    cube = _cube(rng)
    rule = ChangeRule(centres=np.eye(64)[:4], class_tau=np.full(4, 0.15))
    cube.valid[8, :4] = False  # some cells invalid in 2025: the embedding task drops them
    full = tile_examples(cube, 2025, task, rule)
    fc = tile_examples(cube, 2025, task, rule, truth=False)
    if task == "forest":
        np.testing.assert_array_equal(full.rows, fc.rows)
    else:
        assert set(full.rows) < set(fc.rows)
    keep = np.isin(fc.rows, full.rows)
    np.testing.assert_array_equal(full.features, fc.features[keep])
    for k in full.scores:
        np.testing.assert_array_equal(full.scores[k], fc.scores[k][keep])
    assert not fc.y.any()
    # 2026 has no truth at all and still works in forecast mode.
    f26 = tile_examples(cube, 2026, task, rule, truth=False)
    assert f26.rows.size > 0 and f26.features is not None and not f26.y.any()
