"""Memory-mapped training store: one tile's inputs and targets, readable as random patches.

The region store keeps each tile in compressed ``.npz`` files, which must be decompressed whole.
Training reads thousands of small patches, so each tile is written once as two plain ``.npy``
files that are opened with ``mmap_mode="r"``:

- ``<tile>.emb.npy``  int8 ``[9, 64, 128, 128]``: stored embeddings 2017..2025, NODATA = -128.
- ``<tile>.aux.npy``  float16 ``[AUX, 128, 128]``: the channels in ``AUX_CHANNELS``.

Label values are copied bit for bit from the label stores (they are float16 there too), so every
threshold in this module gives exactly the eligibility and events the baselines use.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from almanac.baselines.features import FOREST_MIN, LAND_MIN, LOSS_EVENT, ChangeRule
from almanac.common.constants import YEARS
from almanac.data.cube import DATA, LABEL_YEARS, TileCube, load_cube
from almanac.grid.ids import parse_tile_id

STORE = DATA / "store_v1" / "L6"
SIDE = 128
THRESHOLD = Path(__file__).resolve().parents[3] / "configs" / "thresholds" / "amazon_cerrado_v1.json"


def load_rule(path: Path = THRESHOLD) -> ChangeRule:
    """The per-class change rule of task 1.8."""
    t = json.loads(path.read_text())
    if t["rule"] != "class":
        raise ValueError("expected the per-class rule")
    return ChangeRule(np.array(t["kmeans_centres"]), np.array(t["class_tau"]))


def _names() -> list[str]:
    names = [f"valid_{y}" for y in YEARS]
    names += [f"loss_{y}" for y in LABEL_YEARS]
    names += [f"forest_lost_{y}" for y in LABEL_YEARS]
    names += [f"forest_start_{y}" for y in (*LABEL_YEARS, 2026)]
    names += ["land", "loss_before_2018"]
    names += [f"emb_event_{y}" for y in LABEL_YEARS]  # change rule on the pair ending in y
    return names


AUX_CHANNELS: tuple[str, ...] = tuple(_names())
AUX = {name: i for i, name in enumerate(AUX_CHANNELS)}


def store_paths(tile_id: str, root: Path = STORE) -> tuple[Path, Path]:
    zone = parse_tile_id(tile_id).utm_zone
    return root / zone / f"{tile_id}.emb.npy", root / zone / f"{tile_id}.aux.npy"


def aux_from_cube(cube: TileCube, rule: ChangeRule) -> np.ndarray:
    assert cube.forest_start is not None and cube.forest_lost is not None
    planes: list[np.ndarray] = [cube.valid[i].astype(np.float16) for i in range(len(YEARS))]
    planes += [cube.loss[i].astype(np.float16) for i in range(len(LABEL_YEARS))]
    planes += [cube.forest_lost[i].astype(np.float16) for i in range(len(LABEL_YEARS))]
    planes += [cube.forest_start[i].astype(np.float16) for i in range(len(LABEL_YEARS) + 1)]
    planes += [cube.land.astype(np.float16), cube.loss_before.astype(np.float16)]
    planes += [rule.events(cube, y).astype(np.float16) for y in LABEL_YEARS]
    out = np.stack(planes)
    if out.shape[0] != len(AUX_CHANNELS):
        raise AssertionError("aux layout out of date")
    return out


def write_tile(tile_id: str, rule: ChangeRule, root: Path = STORE) -> None:
    emb_path, aux_path = store_paths(tile_id, root)
    if emb_path.exists() and aux_path.exists():
        return
    cube = load_cube(tile_id, embeddings=True)
    assert cube.stored is not None
    emb_path.parent.mkdir(parents=True, exist_ok=True)
    for path, arr in ((emb_path, cube.stored), (aux_path, aux_from_cube(cube, rule))):
        tmp = path.with_name(path.name + ".part")
        with tmp.open("wb") as f:
            np.save(f, np.ascontiguousarray(arr))
        tmp.replace(path)


@dataclass
class TileStore:
    """Read-only memory maps of one tile."""

    tile_id: str
    emb: np.ndarray  # int8 [9, 64, H, W]
    aux: np.ndarray  # float16 [AUX, H, W]

    @classmethod
    def open(cls, tile_id: str, root: Path = STORE) -> TileStore:
        e, a = store_paths(tile_id, root)
        return cls(tile_id, np.load(e, mmap_mode="r"), np.load(a, mmap_mode="r"))

    def channel(self, name: str) -> np.ndarray:
        return self.aux[AUX[name]]


def forest_eligible(aux: np.ndarray, target: int) -> np.ndarray:
    """Cells scored on the forest task for ``target`` (same rule as the baselines)."""
    land = aux[AUX["land"]].astype(np.float32)
    forest = aux[AUX[f"forest_start_{target}"]].astype(np.float32)
    valid_issue = aux[AUX[f"valid_{target - 1}"]] > 0
    return (land >= LAND_MIN) & (forest >= FOREST_MIN) & valid_issue


def forest_event(aux: np.ndarray, target: int) -> np.ndarray:
    return aux[AUX[f"forest_lost_{target}"]].astype(np.float32) >= LOSS_EVENT


def embedding_eligible(aux: np.ndarray, target: int) -> np.ndarray:
    land = aux[AUX["land"]].astype(np.float32)
    return (land >= LAND_MIN) & (aux[AUX[f"valid_{target - 1}"]] > 0) & (aux[AUX[f"valid_{target}"]] > 0)
