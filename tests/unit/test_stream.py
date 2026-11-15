"""The streaming pass, run against a synthetic supplier held in memory."""

from pathlib import Path

import numpy as np
import pytest

from almanac.common.constants import YEARS
from almanac.data.stream import (
    INVALID_CODE,
    coverage,
    decode_delta,
    encode_delta,
    load_summary,
    run_stream,
    summary_path,
)
from almanac.grid.ids import TileRef
from almanac.io.http import RangeClient
from almanac.io.level import LevelRead
from almanac.quality.embedding import quantize, renormalize

SIDE = 8
LEVEL = 6


def _stored(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return quantize(renormalize(rng.normal(size=(64, SIDE, SIDE))))


class Supplier:
    """Tiles whose year ``y`` equals year ``y-1`` except in one changed cell, and one no-data cell."""

    def __init__(self, n_tiles: int, fail_after: int | None = None) -> None:
        self.calls: list[str] = []
        self.fail_after = fail_after
        self.work = []
        self.data: dict[str, np.ndarray] = {}
        for t in range(n_tiles):
            tile = TileRef("10N", 500000 + 81920 * t, 5079040)
            base = _stored(t)
            urls = {}
            for i, year in enumerate(YEARS):
                if t == 1 and year == 2020:
                    continue  # tile 1 lacks one year
                values = base.copy()
                if i >= 3:
                    values[:, 2, 5] = _stored(1000 + t)[:, 0, 0]  # a real change in 2019 -> 2020
                values[:, 0, 0] = -128
                url = f"mem://{tile.tile_id}/{year}"
                urls[year] = url
                self.data[url] = values
            self.work.append((tile, urls))

    def fetch(self, url: str) -> LevelRead:
        if self.fail_after is not None and len(self.calls) >= self.fail_after:
            raise ConnectionError("supplier went away")
        self.calls.append(url)
        return LevelRead(self.data[url], url, "etag", "date", 10_000, 100, "digest")


def test_delta_code_round_trip() -> None:
    delta = np.array([[0.0, 0.015, 0.2, 1.0, 1.7]], dtype=np.float32)
    valid = np.array([[True, True, True, True, False]])
    code = encode_delta(delta, valid)
    assert code.dtype == np.uint8 and code[0, 4] == INVALID_CODE
    back, ok = decode_delta(code)
    np.testing.assert_array_equal(ok, valid)
    np.testing.assert_allclose(back[0, :4], [0.0, 0.015, 0.2, 1.0], atol=0.004)
    assert np.isnan(back[0, 4])


def test_summary_contents(tmp_path: Path) -> None:
    supplier = Supplier(2)
    report = run_stream(supplier.work, LEVEL, tmp_path, supplier.fetch, workers=2)
    assert (report.tiles_done, report.tiles_failed, report.tiles_skipped) == (2, 0, 0)
    assert report.bytes_fetched == 100 * (9 + 8)

    s = load_summary(summary_path(tmp_path, LEVEL, supplier.work[0][0]))
    delta, ok = decode_delta(s["delta_code"])
    assert not ok[:, 0, 0].any()  # the no-data cell is invalid in every pair
    assert s["valid"][:, 0, 0].sum() == 0 and s["valid"][:, 1, 1].all()
    assert delta[2, 2, 5] > 0.5  # the change falls in the 2019 -> 2020 pair
    quiet = np.delete(delta, 2, axis=0)
    assert np.nanmax(quiet) < 1e-3
    assert np.nanmax(np.delete(delta[2].ravel(), 2 * SIDE + 5)) < 1e-3
    np.testing.assert_allclose(s["length_q"][:, 1], 1.0, atol=0.01)
    assert set(s["meta"]["lineage"]) == {str(y) for y in YEARS}

    gap = load_summary(summary_path(tmp_path, LEVEL, supplier.work[1][0]))
    missing = YEARS.index(2020)
    assert not gap["present"][missing] and gap["present"].sum() == 8
    assert (gap["delta_code"][missing - 1] == INVALID_CODE).all()  # 2019 -> 2020
    assert (gap["delta_code"][missing] == INVALID_CODE).all()  # 2020 -> 2021
    assert (gap["delta_code"][0] != INVALID_CODE).any()

    cov = coverage(tmp_path, LEVEL)
    assert cov["tiles"] == 2 and cov["tiles_per_year"][2020] == 1 and cov["tiles_per_year"][2021] == 2


def test_interrupt_and_resume_loses_nothing_and_refetches_nothing(tmp_path: Path) -> None:
    broken = Supplier(6, fail_after=9 + 8 + 4)  # dies part-way through the third tile
    first = run_stream(broken.work, LEVEL, tmp_path, broken.fetch, workers=1)
    assert first.tiles_done == 2 and first.tiles_failed == 4
    assert not list(tmp_path.rglob("*.part"))
    assert len(list(tmp_path.rglob("*.npz"))) == 2  # no partial summary was left behind

    healthy = Supplier(6)
    second = run_stream(healthy.work, LEVEL, tmp_path, healthy.fetch, workers=3)
    assert (second.tiles_skipped, second.tiles_done, second.tiles_failed) == (2, 4, 0)
    finished = {tile.tile_id for tile, _ in broken.work[:2]}
    assert not any(u.split("/")[2] in finished for u in healthy.calls)  # nothing read twice

    reference = Supplier(6)
    run_stream(reference.work, LEVEL, tmp_path / "clean", reference.fetch, workers=2)
    for tile, _ in reference.work:
        a = load_summary(summary_path(tmp_path, LEVEL, tile))
        b = load_summary(summary_path(tmp_path / "clean", LEVEL, tile))
        np.testing.assert_array_equal(a["delta_code"], b["delta_code"])
        np.testing.assert_array_equal(a["valid"], b["valid"])


def test_connection_cap_is_enforced() -> None:
    with pytest.raises(ValueError):
        RangeClient(connections=17)
    with pytest.raises(ValueError):
        RangeClient(connections=0)
