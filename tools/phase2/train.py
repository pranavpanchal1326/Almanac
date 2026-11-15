"""Phase 2 training (stage A) and the task 2.2 smoke test.

Usage:
  python tools/phase2/train.py configs/model/<run>.json --out D:/almanac-data/runs/<name>
  python tools/phase2/train.py configs/model/<run>.json --smoke

Guards: training uses only tiles marked "train" in the split and target years in the configuration,
which must all be 2023 or earlier; validation uses only "validation" tiles and target 2024. The test
year (2025) is never read here.

Smoke mode (task 2.2): overfits one fixed batch, then measures peak GPU memory and throughput for
each candidate batch size. Writes nothing but prints a JSON summary.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import math
import time
from pathlib import Path

import numpy as np
import torch

from almanac.evaluate.metrics import average_precision
from almanac.model.data import BalancedSampler, DataConfig, PatchIndex, make_example
from almanac.model.infer import predict_tile, tile_scores
from almanac.model.net import Forecaster, LossWeights, NetConfig, losses
from almanac.model.store import TileStore

REPO = Path(__file__).resolve().parents[2]
KEYS = (
    "emb",
    "valid",
    "year_scalars",
    "static",
    "y_forest",
    "m_forest",
    "y_change",
    "m_change",
    "y_emb",
    "m_emb",
)


class PatchSet(torch.utils.data.Dataset):
    def __init__(self, tiles: list[str], specs: list, cfg: DataConfig):
        self.tiles, self.specs, self.cfg = tiles, specs, cfg
        self._open: dict[int, TileStore] = {}

    def __len__(self) -> int:
        return len(self.specs)

    def __getitem__(self, i: int) -> dict[str, np.ndarray]:
        s = self.specs[i]
        if s.tile not in self._open:
            self._open[s.tile] = TileStore.open(self.tiles[s.tile])
        ex = make_example(self._open[s.tile], s, self.cfg)
        return {k: ex[k] for k in KEYS}


def load_config(path: Path) -> dict:
    cfg = json.loads(path.read_text())
    cfg["_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return cfg


def split_tiles(split_csv: Path) -> dict[str, list[str]]:
    with split_csv.open() as f:
        rows = list(csv.DictReader(f))
    return {s: sorted(r["tile_id"] for r in rows if r["split"] == s) for s in ("train", "validation")}


def build(cfg: dict) -> tuple[DataConfig, NetConfig, LossWeights]:
    return DataConfig(**cfg["data"]), NetConfig(**cfg["net"]), LossWeights(**cfg["loss"])


def lr_at(step: int, o: dict) -> float:
    if o["schedule"] == "constant":
        return o["lr"]
    if step < o["warmup"]:
        return o["lr"] * (step + 1) / o["warmup"]
    t = (step - o["warmup"]) / max(1, o["steps"] - o["warmup"])
    return o["lr"] * 0.5 * (1 + math.cos(math.pi * min(t, 1.0)))


def to_device(batch: dict, device: str) -> dict[str, torch.Tensor]:
    return {k: v.to(device, non_blocking=True) for k, v in batch.items()}


def validate(net: Forecaster, tiles: list[str], dcfg: DataConfig, device: str) -> dict[str, float]:
    out = {}
    for task in ("forest", "embedding"):
        ys, zs = [], []
        for tid in tiles:
            store = TileStore.open(tid)
            logits = predict_tile(net, store, 2024, dcfg, device)
            _, y, z = tile_scores(store, logits, 2024, task)
            ys.append(y)
            zs.append(z)
        out[f"val2024_ap_{task}"] = average_precision(np.concatenate(ys), np.concatenate(zs))
    return out


def smoke(cfg: dict, device: str) -> None:
    dcfg, ncfg, w = build(cfg)
    tiles = split_tiles(REPO / cfg["split"])["train"][:40]
    index = PatchIndex.build(tiles, cfg["train_targets"], dcfg)
    specs = BalancedSampler(index, dcfg, cfg["seed"]).draw(16, 0)
    ds = PatchSet(tiles, specs, dcfg)
    batch = to_device(torch.utils.data.default_collate([ds[i] for i in range(16)]), device)
    torch.manual_seed(cfg["seed"])
    net = Forecaster(ncfg).to(device)
    n_params = sum(p.numel() for p in net.parameters())
    opt = torch.optim.AdamW(net.parameters(), lr=1e-3)
    first = last = None
    for step in range(300):
        with torch.autocast(device_type="cuda", dtype=torch.bfloat16, enabled=device == "cuda"):
            ls = losses(net(batch), batch, w)
        opt.zero_grad(set_to_none=True)
        ls["total"].backward()
        opt.step()
        if step == 0:
            first = {k: float(v) for k, v in ls.items()}
        last = {k: float(v) for k, v in ls.items()}
    result: dict = {
        "size": ncfg.size,
        "spatial": ncfg.spatial,
        "parameters": n_params,
        "overfit_first": first,
        "overfit_last": last,
        "batches": {},
    }
    for bs in (8, 16, 32):
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()
        specs = BalancedSampler(index, dcfg, cfg["seed"]).draw(bs, 1)
        b = to_device(
            torch.utils.data.default_collate([PatchSet(tiles, specs, dcfg)[i] for i in range(bs)]), device
        )
        try:
            for i in range(13):
                if i == 3:
                    torch.cuda.synchronize()
                    t0 = time.time()
                with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                    ls = losses(net(b), b, w)
                opt.zero_grad(set_to_none=True)
                ls["total"].backward()
                opt.step()
            torch.cuda.synchronize()
            sec = (time.time() - t0) / 10
            result["batches"][bs] = {
                "peak_gib": round(torch.cuda.max_memory_allocated() / 2**30, 2),
                "seconds_per_step": round(sec, 3),
                "patches_per_second": round(bs / sec, 1),
            }
        except torch.OutOfMemoryError:
            result["batches"][bs] = "out of memory"
            break
    t0 = time.time()
    _ = [ds[i] for i in range(16)]
    result["cpu_seconds_per_patch"] = round((time.time() - t0) / 16, 4)
    print(json.dumps(result, indent=2))


def train(cfg: dict, out: Path, device: str) -> None:
    dcfg, ncfg, w = build(cfg)
    o = cfg["optim"]
    if max(cfg["train_targets"]) > 2023:
        raise SystemExit("stage A trains on targets up to 2023 only")
    split = split_tiles(REPO / cfg["split"])
    tiles, val_tiles = split["train"], split["validation"]
    out.mkdir(parents=True, exist_ok=True)
    (out / "config.json").write_text(json.dumps(cfg, indent=1), newline="\n")
    torch.manual_seed(cfg["seed"])
    np.random.seed(cfg["seed"])
    index = PatchIndex.build(tiles, cfg["train_targets"], dcfg)
    sampler = BalancedSampler(index, dcfg, cfg["seed"])
    net = Forecaster(ncfg).to(device)
    ema = copy.deepcopy(net).eval()
    for p in ema.parameters():
        p.requires_grad_(False)
    opt = torch.optim.AdamW(net.parameters(), lr=o["lr"], weight_decay=o["weight_decay"])
    log = (out / "log.jsonl").open("a", newline="\n")
    step, epoch, best = 0, 0, -1.0
    t0 = time.time()
    while step < o["steps"]:
        specs = sampler.draw(o["batch"] * o["eval_every"], epoch)
        loader = torch.utils.data.DataLoader(
            PatchSet(tiles, specs, dcfg),
            batch_size=o["batch"],
            num_workers=cfg["workers"],
            persistent_workers=False,
            pin_memory=True,
        )
        net.train()
        acc: dict[str, float] = {}
        for batch in loader:
            batch = to_device(batch, device)
            for g in opt.param_groups:
                g["lr"] = lr_at(step, o)
            with torch.autocast(device_type="cuda", dtype=torch.bfloat16, enabled=device == "cuda"):
                ls = losses(net(batch), batch, w)
            opt.zero_grad(set_to_none=True)
            ls["total"].backward()
            torch.nn.utils.clip_grad_norm_(net.parameters(), o["clip"])
            opt.step()
            with torch.no_grad():
                for pe, pn in zip(ema.parameters(), net.parameters(), strict=True):
                    pe.lerp_(pn, 1 - o["ema"])
            for k, v in ls.items():
                acc[k] = acc.get(k, 0.0) + float(v)
            step += 1
            if step >= o["steps"]:
                break
        n = max(1, step - epoch * o["eval_every"])
        rec = {"step": step, "minutes": round((time.time() - t0) / 60, 1), "lr": lr_at(step, o)}
        rec.update({f"train_{k}": round(v / n, 5) for k, v in acc.items()})
        rec.update({k: round(v, 5) for k, v in validate(ema, val_tiles, dcfg, device).items()})
        log.write(json.dumps(rec) + "\n")
        log.flush()
        print(json.dumps(rec), flush=True)
        if rec["val2024_ap_forest"] > best:
            best = rec["val2024_ap_forest"]
            torch.save({"ema": ema.state_dict(), "step": step, "config": cfg}, out / "best.pt")
        epoch += 1
    torch.save({"ema": ema.state_dict(), "step": step, "config": cfg}, out / "last.pt")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("config", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    cfg = load_config(args.config)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if args.smoke:
        smoke(cfg, device)
    else:
        if args.out is None:
            raise SystemExit("--out is required for training")
        train(cfg, args.out, device)


if __name__ == "__main__":
    main()
