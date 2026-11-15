import numpy as np
import pytest
import torch

from almanac.model.data import (
    BalancedSampler,
    DataConfig,
    PatchIndex,
    PatchSpec,
    history_years,
    make_example,
)
from almanac.model.net import Forecaster, LossWeights, NetConfig, losses
from almanac.model.store import AUX, AUX_CHANNELS, TileStore

SIDE = 128


def _fake_store(rng: np.random.Generator) -> TileStore:
    emb = rng.integers(-127, 128, (9, 64, SIDE, SIDE), dtype=np.int8)
    aux = np.zeros((len(AUX_CHANNELS), SIDE, SIDE), dtype=np.float16)
    for name, i in AUX.items():
        if name.startswith("valid_"):
            aux[i] = 1
        elif name.startswith("forest_start_"):
            aux[i] = 0.8
        elif name == "land":
            aux[i] = 1
        elif name.startswith(("forest_lost_", "loss_", "emb_event_")):
            aux[i] = (rng.random((SIDE, SIDE)) < 0.05).astype(np.float16) * 0.5
    return TileStore("21S_E0_N0", emb, aux)


def test_history_years() -> None:
    assert history_years(2024, 5) == [2019, 2020, 2021, 2022, 2023]
    assert history_years(2019, 5)[0] == 2014  # placeholders before 2017 stay empty


def test_example_uses_nothing_from_the_target_year() -> None:
    rng = np.random.default_rng(0)
    store = _fake_store(rng)
    cfg = DataConfig()
    spec = PatchSpec(tile=0, target=2022, row=40, col=50, rot=1, flip=True, hide_first=0, hide_one=-1)
    a = make_example(store, spec, cfg)
    # Overwrite everything about 2022 and later; inputs must not change, targets must.
    for name, i in AUX.items():
        year = name.rsplit("_", 1)[-1]
        if year.isdigit() and int(year) >= 2022 and not name.startswith("forest_start_"):
            store.aux[i] = rng.random((SIDE, SIDE)).astype(np.float16)
    store.emb[5:] = rng.integers(-127, 128, store.emb[5:].shape, dtype=np.int8)  # 2022..2025
    b = make_example(store, spec, cfg)
    for key in ("emb", "valid", "year_scalars", "static", "present"):
        np.testing.assert_array_equal(a[key], b[key])
    assert not np.array_equal(a["y_forest"], b["y_forest"]) or not np.array_equal(a["y_emb"], b["y_emb"])


def test_example_shapes_and_hidden_years() -> None:
    store = _fake_store(np.random.default_rng(1))
    cfg = DataConfig()
    ex = make_example(store, PatchSpec(0, 2019, 0, 0, 0, False, 0, -1), cfg)
    assert ex["emb"].shape == (5, 64, 32, 32) and ex["static"].shape == (4, 32, 32)
    assert list(ex["present"]) == [False, False, False, True, True]  # 2014-2016 do not exist
    ex = make_example(store, PatchSpec(0, 2024, 0, 0, 0, False, 2, 4), cfg)
    assert list(ex["present"]) == [False, False, True, True, False]
    assert not ex["valid"][4].any() and (ex["emb"][4] == -128).all()


def test_sampler_reproduces_and_balances(tmp_path) -> None:
    rng = np.random.default_rng(2)
    store = _fake_store(rng)
    root = tmp_path / "L6"
    (root / "21S").mkdir(parents=True)
    np.save(root / "21S" / "21S_E0_N0.emb.npy", store.emb)
    np.save(root / "21S" / "21S_E0_N0.aux.npy", store.aux)
    cfg = DataConfig()
    idx = PatchIndex.build(["21S_E0_N0"], [2020, 2021], cfg, root=root)
    assert idx.tile.size == 2 * 7 * 7
    s1 = BalancedSampler(idx, cfg, seed=7).draw(200, epoch=3)
    s2 = BalancedSampler(idx, cfg, seed=7).draw(200, epoch=3)
    assert s1 == s2
    assert s1 != BalancedSampler(idx, cfg, seed=7).draw(200, epoch=4)
    assert all(0 <= s.row <= 96 and 0 <= s.col <= 96 for s in s1)


def test_sampler_positive_share() -> None:
    idx = PatchIndex(["a"])
    idx.tile = np.zeros(100, np.int32)
    idx.target = np.full(100, 2020, np.int16)
    idx.row = np.arange(100, dtype=np.int16)  # row identifies the candidate (no jitter below)
    idx.col = np.zeros(100, np.int16)
    idx.eligible = np.ones(100, np.int32)
    idx.events = np.r_[np.ones(5), np.zeros(95)].astype(np.int32)
    cfg = DataConfig(augment=False, jitter=0, patch=28)  # 100 - 28 keeps every row unclipped
    picks = BalancedSampler(idx, cfg, seed=0).draw(20_000, 0)
    share = np.mean([s.row < 5 for s in picks])
    # Half the draws are from positive patches; the uniform half adds another 5% of 50%.
    assert share == pytest.approx(0.5 + 0.5 * 0.05, abs=0.01)


@pytest.mark.slow
def test_store_matches_the_baselines_on_real_tiles() -> None:
    from almanac.baselines.features import tile_examples
    from almanac.data.cube import load_cube
    from almanac.model.store import embedding_eligible, forest_eligible, forest_event, load_rule, store_paths

    rule = load_rule()
    for tid in ("21S_E172320_N8935040", "20S_E581920_N8853120"):
        if not store_paths(tid)[1].exists():
            pytest.skip("training store not built")
        aux = np.asarray(TileStore.open(tid).aux)
        cube = load_cube(tid, embeddings=True)
        for year in (2020, 2024, 2025):
            for task, elig, truth in (
                ("forest", forest_eligible(aux, year), forest_event(aux, year)),
                ("embedding", embedding_eligible(aux, year), aux[AUX[f"emb_event_{year}"]] > 0),
            ):
                ex = tile_examples(cube, year, task, rule, with_features=False)
                np.testing.assert_array_equal(np.flatnonzero(elig.ravel()), ex.rows)
                np.testing.assert_array_equal(truth.ravel()[ex.rows], ex.y)


def _batch(b: int = 2, p: int = 8, k: int = 5, seed: int = 0) -> dict[str, torch.Tensor]:
    g = torch.Generator().manual_seed(seed)
    return {
        "emb": torch.randint(-127, 128, (b, k, 64, p, p), generator=g, dtype=torch.int8),
        "valid": torch.ones(b, k, p, p, dtype=torch.bool),
        "year_scalars": torch.rand(b, k, 3, p, p, generator=g),
        "static": torch.rand(b, 4, p, p, generator=g),
        "y_forest": (torch.rand(b, p, p, generator=g) < 0.1).float(),
        "m_forest": torch.ones(b, p, p, dtype=torch.bool),
        "y_change": (torch.rand(b, p, p, generator=g) < 0.1).float(),
        "m_change": torch.ones(b, p, p, dtype=torch.bool),
        "y_emb": torch.randint(-127, 128, (b, 64, p, p), generator=g, dtype=torch.int8),
        "m_emb": torch.ones(b, p, p, dtype=torch.bool),
    }


@pytest.mark.parametrize("spatial", [True, False])
def test_forward_shapes_and_finite_losses(spatial: bool) -> None:
    torch.manual_seed(0)
    net = Forecaster(NetConfig(size="S", spatial=spatial)).eval()
    batch = _batch()
    out = net(batch)
    assert out["forest"].shape == (2, 8, 8) and out["emb_mean"].shape == (2, 8, 8, 64)
    torch.testing.assert_close(out["emb_mean"].norm(dim=-1), torch.ones(2, 8, 8))
    ls = losses(out, batch, LossWeights())
    assert all(torch.isfinite(v) for v in ls.values())


def test_b5_sees_no_neighbours_and_full_model_does() -> None:
    torch.manual_seed(0)
    batch = _batch(b=1, p=9)
    changed = {k: v.clone() for k, v in batch.items()}
    changed["emb"][0, :, :, 0, 0] = 0  # change one corner cell
    for spatial, moves in ((False, False), (True, True)):
        net = Forecaster(NetConfig(size="S", spatial=spatial)).eval()
        with torch.no_grad():
            a, b = net(batch)["forest"], net(changed)["forest"]
        centre_moved = not torch.allclose(a[0, 4, 4], b[0, 4, 4])
        assert centre_moved == moves  # 6 blocks of 3x3 reach 4 cells away
        assert not torch.allclose(a[0, 0, 0], b[0, 0, 0])


def test_masked_cells_do_not_count() -> None:
    torch.manual_seed(0)
    net = Forecaster(NetConfig(size="S")).eval()
    batch = _batch()
    batch["m_forest"][:, :4] = False
    with torch.no_grad():
        out = net(batch)
        base = losses(out, batch, LossWeights())["forest"]
        batch["y_forest"][:, :4] = 1 - batch["y_forest"][:, :4]
        assert torch.allclose(losses(out, batch, LossWeights())["forest"], base)


def test_absent_years_do_not_change_the_output() -> None:
    torch.manual_seed(0)
    net = Forecaster(NetConfig(size="S")).eval()
    batch = _batch()
    batch["valid"][:, 0] = False
    other = {k: v.clone() for k, v in batch.items()}
    other["emb"][:, 0] = torch.randint(-127, 128, other["emb"][:, 0].shape, dtype=torch.int8)
    other["year_scalars"][:, 0] = 5.0
    with torch.no_grad():
        torch.testing.assert_close(net(batch)["forest"], net(other)["forest"])
