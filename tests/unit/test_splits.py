from collections import Counter

from almanac.data.splits import (
    BUFFER,
    HELD_OUT,
    TEST,
    TRAIN,
    VALIDATION,
    SplitConfig,
    assign,
    boxes_touch,
    super_block,
)
from almanac.grid.ids import TileRef

CONFIG = SplitConfig(
    seed="test-seed",
    block_deg=2.0,
    train_share=0.7,
    validation_share=0.1,
    held_out_box=(-10.0, -10.0, -6.0, -6.0),
)


def _grid() -> dict[TileRef, tuple[float, float, float, float]]:
    """A 40 x 40 lattice of 0.75-degree tiles that touch edge to edge."""
    out = {}
    for i in range(40):
        for j in range(40):
            west, south = -20 + 0.75 * i, -20 + 0.75 * j
            out[TileRef("20S", i * 81920, j * 81920)] = (west, south, west + 0.75, south + 0.75)
    return out


def test_super_block_is_the_floor_of_the_centre() -> None:
    assert super_block((-55.9, -7.4, -55.1, -6.6), 2.0) == "-8_-56"
    assert super_block((0.1, 0.1, 0.9, 0.9), 2.0) == "+0_+0"


def test_touching_boxes() -> None:
    assert boxes_touch((0, 0, 1, 1), (1, 0, 2, 1), 0.0)
    assert not boxes_touch((0, 0, 1, 1), (1.5, 0, 2, 1), 0.01)


def test_assignment_is_deterministic_and_order_free() -> None:
    footprints = _grid()
    a = assign(footprints, CONFIG)
    b = assign(dict(reversed(list(footprints.items()))), CONFIG)
    assert a == b


def test_no_scored_tile_touches_a_training_tile() -> None:
    footprints = _grid()
    result = assign(footprints, CONFIG)
    train = [footprints[t] for t, (_, s) in result.items() if s == TRAIN]
    scored = [footprints[t] for t, (_, s) in result.items() if s in (VALIDATION, TEST, HELD_OUT)]
    assert train and scored
    assert not any(boxes_touch(a, b, CONFIG.touch_margin_deg) for a in train for b in scored)


def test_held_out_region_and_every_split_present() -> None:
    footprints = _grid()
    result = assign(footprints, CONFIG)
    counts = Counter(s for _, s in result.values())
    assert set(counts) == {TRAIN, VALIDATION, TEST, HELD_OUT, BUFFER}
    for tile, (_, split) in result.items():
        w, s, e, n = footprints[tile]
        inside = -10 <= (w + e) / 2 < -6 and -10 <= (s + n) / 2 < -6
        assert (split == HELD_OUT) == inside
    # Tiles of one super-block share a split, apart from training tiles moved to the buffer.
    by_block: dict[str, set[str]] = {}
    for block, split in result.values():
        by_block.setdefault(block, set()).add(split)
    assert all(len(s - {BUFFER, HELD_OUT}) <= 1 for s in by_block.values())
