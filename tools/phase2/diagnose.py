"""Compare two checkpoints of one configuration on the same training patches (amendment 2, section 1).

Usage: python tools/phase2/diagnose.py CONFIG CHECKPOINT_A CHECKPOINT_B

Uses training tiles only, on the CPU. For each checkpoint (its averaged weights) prints the losses,
the predicted embedding spread, and per block the largest attention logit, the mean attention
entropy and the share of attention rows with more than 99% of their weight on one position.
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))

from train import PatchSet, build

from almanac.model.data import BalancedSampler, PatchIndex
from almanac.model.net import SPREAD_FLOOR, Forecaster, losses


def attention_hook(stats: list):
    def hook(mod, inp, out):
        x = inp[0]
        d = x.shape[-1]
        h = mod.num_heads
        dh = d // h
        q, k, _ = torch.nn.functional.linear(x, mod.in_proj_weight, mod.in_proj_bias).chunk(3, dim=-1)
        q = q.reshape(*x.shape[:2], h, dh).transpose(1, 2)
        k = k.reshape(*x.shape[:2], h, dh).transpose(1, 2)
        logits = q @ k.transpose(-1, -2) / math.sqrt(dh)
        p = logits.softmax(-1)
        ent = -(p * p.clamp_min(1e-12).log()).sum(-1).mean()
        stats.append((float(logits.abs().amax()), float(ent), float((p.amax(-1) > 0.99).float().mean())))

    return hook


def main() -> None:
    cfg_path, *ckpts = (Path(a) for a in sys.argv[1:4])
    torch.set_num_threads(2)
    cfg = json.loads(cfg_path.read_text())
    dcfg, ncfg, w = build(cfg)
    with open(cfg["split"]) as f:
        tiles = sorted(r["tile_id"] for r in csv.DictReader(f) if r["split"] == "train")[::20]
    index = PatchIndex.build(tiles, cfg["train_targets"], dcfg)
    specs = BalancedSampler(index, dcfg, seed=99).draw(24, 0)
    ds = PatchSet(tiles, specs, dcfg)
    batch = torch.utils.data.default_collate([ds[i] for i in range(24)])
    for path in ckpts:
        ck = torch.load(path, map_location="cpu", weights_only=False)
        net = Forecaster(ncfg)
        net.load_state_dict(ck["ema"])
        net.eval()
        stats: list = []
        hooks = [b.attn.register_forward_hook(attention_hook(stats)) for b in net.blocks]
        with torch.no_grad():
            out = net(batch)
            ls = losses(out, batch, w)
        for hk in hooks:
            hk.remove()
        spread = out["emb_logspread"].exp()[batch["m_emb"]]
        print(f"== {path} (step {ck['step']})")
        print("   losses: " + ", ".join(f"{k} {float(v):.4f}" for k, v in ls.items()))
        at_floor = float((spread <= SPREAD_FLOOR * 1.01).float().mean())
        print(f"   embedding spread: median {spread.median():.2e}, share at floor {at_floor:.4f}")
        for i, (mx, ent, sat) in enumerate(stats):
            print(f"   block {i}: max |logit| {mx:9.1f}  entropy {ent:.2f}  rows >99% on one {sat:.3f}")


if __name__ == "__main__":
    main()
