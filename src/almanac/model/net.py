"""The forecasting network (blueprint 15.3, adapted to the regional forest task).

Per cell, a sequence of ``K`` history positions plus one query position for the target year:

    history position : project([decoded embedding (64), year scalars (3)]) -> d, or a learned
                       "absent" token where that year is missing or hidden
    every position   : + year encoding (position relative to the cutoff) + static projection
    query position   : learned query token + year encoding + static projection

    repeat L times (pre-normalisation, residual):
        temporal attention : each cell attends across its K + 1 positions (absent ones masked)
        spatial mixing     : 3x3 depthwise + pointwise convolution over the patch, per position
                             (disabled for baseline B5, which then sees no neighbours)
        feed-forward       : width 4d, GELU, dropout

    query output -> forest-loss logit, embedding-change logit, embedding mean (unit length) and
                    log-spread (64 each)

The network is translation-equivariant in space, so it can be run on patches of any size.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import torch
import torch.nn.functional as F
from torch import nn

from almanac.model.data import N_STATIC, N_YEAR_SCALARS

SIZES = {"S": (128, 6), "M": (192, 8), "L": (256, 10)}


@dataclass(frozen=True)
class NetConfig:
    size: str = "M"
    history: int = 5
    heads: int = 4
    dropout: float = 0.05
    spatial: bool = True  # False gives baseline B5
    qk_norm: bool = False  # amendment 2: normalise queries and keys per head (False = amendment 1)

    @property
    def width(self) -> int:
        return SIZES[self.size][0]

    @property
    def blocks(self) -> int:
        return SIZES[self.size][1]


def decode(stored: torch.Tensor) -> torch.Tensor:
    """int8 stored values -> unit-length float embeddings (NODATA cells become zeros)."""
    v = stored.float()
    x = (v / 127.5) ** 2 * torch.sign(v)
    x = torch.where(stored == -128, torch.zeros_like(x), x)
    return x / x.norm(dim=-1, keepdim=True).clamp_min(1e-6)


class QKNormAttention(nn.Module):
    """Multi-head self-attention with layer-normalised queries and keys (amendment 2).

    Normalising q and k per head bounds the attention logits, which grew to 1e5 and collapsed the
    attention of amendment 1's network onto single years (Dehghani et al. 2023; Wortsman et al.
    2023). With ``record`` set, the largest absolute logit and the mean attention entropy of the
    last call are kept in ``last_stats`` for monitoring.
    """

    def __init__(self, d: int, heads: int, dropout: float):
        super().__init__()
        self.h, self.dh = heads, d // heads
        self.qkv = nn.Linear(d, 3 * d)
        self.q_norm = nn.LayerNorm(self.dh)
        self.k_norm = nn.LayerNorm(self.dh)
        self.out = nn.Linear(d, d)
        self.dropout = dropout
        self.record = False
        self.last_stats: tuple[float, float] | None = None

    def forward(self, x: torch.Tensor, absent: torch.Tensor) -> torch.Tensor:
        n, t, d = x.shape
        q, k, v = self.qkv(x).reshape(n, t, 3, self.h, self.dh).permute(2, 0, 3, 1, 4)
        q, k = self.q_norm(q), self.k_norm(k)
        keep = ~absent[:, None, None, :]  # [N, 1, 1, T]; the query position is never absent
        if self.record:
            with torch.no_grad():
                logits = (q.float() @ k.float().transpose(-1, -2)) / math.sqrt(self.dh)
                logits = logits.masked_fill(~keep, float("-inf"))
                prob = logits.softmax(-1)
                ent = -(prob * prob.clamp_min(1e-12).log()).sum(-1).mean()
                self.last_stats = (float(logits[keep.expand_as(logits)].abs().max()), float(ent))
        a = F.scaled_dot_product_attention(
            q, k, v, attn_mask=keep, dropout_p=self.dropout if self.training else 0.0
        )
        return self.out(a.transpose(1, 2).reshape(n, t, d))


class Block(nn.Module):
    def __init__(self, d: int, heads: int, dropout: float, spatial: bool, qk_norm: bool = False):
        super().__init__()
        self.n1 = nn.LayerNorm(d)
        self.qk_norm = qk_norm
        if qk_norm:
            self.attn = QKNormAttention(d, heads, dropout)
        else:
            self.attn = nn.MultiheadAttention(d, heads, dropout=dropout, batch_first=True)
        self.spatial = spatial
        if spatial:
            self.n2 = nn.LayerNorm(d)
            self.depthwise = nn.Conv2d(d, d, 3, padding=1, groups=d)
            self.pointwise = nn.Conv2d(d, d, 1)
        self.n3 = nn.LayerNorm(d)
        self.ff = nn.Sequential(nn.Linear(d, 4 * d), nn.GELU(), nn.Dropout(dropout), nn.Linear(4 * d, d))
        self.drop = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor, absent: torch.Tensor, b: int, p: int) -> torch.Tensor:
        # x: [B*P*P, T, d]; absent: [B*P*P, T] True where the position is masked.
        h = self.n1(x)
        if self.qk_norm:
            a = self.attn(h, absent)
        else:
            a, _ = self.attn(h, h, h, key_padding_mask=absent, need_weights=False)
        x = x + self.drop(a)
        if self.spatial:
            t, d = x.shape[1], x.shape[2]
            h = self.n2(x).reshape(b, p, p, t, d).permute(0, 3, 4, 1, 2).reshape(b * t, d, p, p)
            h = self.pointwise(F.gelu(self.depthwise(h)))
            h = h.reshape(b, t, d, p, p).permute(0, 3, 4, 1, 2).reshape(b * p * p, t, d)
            x = x + self.drop(h)
        return x + self.drop(self.ff(self.n3(x)))


class Forecaster(nn.Module):
    def __init__(self, cfg: NetConfig):
        super().__init__()
        self.cfg = cfg
        d, k = cfg.width, cfg.history
        self.inp = nn.Linear(64 + N_YEAR_SCALARS, d)
        self.static = nn.Linear(N_STATIC, d)
        self.year = nn.Parameter(torch.zeros(k + 1, d))
        self.absent = nn.Parameter(torch.zeros(d))
        self.query = nn.Parameter(torch.zeros(d))
        for prm in (self.year, self.absent, self.query):
            nn.init.normal_(prm, std=0.02)
        self.blocks = nn.ModuleList(
            Block(d, cfg.heads, cfg.dropout, cfg.spatial, cfg.qk_norm) for _ in range(cfg.blocks)
        )
        self.norm = nn.LayerNorm(d)
        self.head_forest = nn.Linear(d, 1)
        self.head_change = nn.Linear(d, 1)
        self.head_emb = nn.Linear(d, 128)

    def forward(self, batch: dict[str, torch.Tensor]) -> dict[str, torch.Tensor]:
        emb, valid = batch["emb"], batch["valid"]  # [B,K,64,P,P] int8, [B,K,P,P] bool
        b, k, _, p, _ = emb.shape
        x = decode(emb.permute(0, 1, 3, 4, 2))  # [B,K,P,P,64]
        scal = batch["year_scalars"].permute(0, 1, 3, 4, 2)  # [B,K,P,P,3]
        h = self.inp(torch.cat([x, scal], dim=-1))
        h = torch.where(valid[..., None], h, self.absent.to(h.dtype))
        q = self.query.to(h.dtype).expand(b, 1, p, p, -1)
        h = torch.cat([h, q], dim=1)  # [B,K+1,P,P,d]
        h = h + self.year.to(h.dtype)[None, :, None, None, :]
        h = h + self.static(batch["static"].permute(0, 2, 3, 1))[:, None]
        h = h.permute(0, 2, 3, 1, 4).reshape(b * p * p, k + 1, -1)
        absent = torch.cat([~valid, torch.zeros_like(valid[:, :1])], dim=1)  # query never absent
        absent = absent.permute(0, 2, 3, 1).reshape(b * p * p, k + 1)
        for blk in self.blocks:
            h = blk(h, absent, b, p)
        out = self.norm(h[:, -1]).reshape(b, p, p, -1)
        e = self.head_emb(out)
        mean = F.normalize(e[..., :64].float(), dim=-1)
        return {
            "forest": self.head_forest(out)[..., 0].float(),
            "change": self.head_change(out)[..., 0].float(),
            "emb_mean": mean,
            "emb_logspread": e[..., 64:].float(),
        }


@dataclass(frozen=True)
class LossWeights:
    forest: float = 1.0
    change: float = 0.5
    embedding: float = 0.1


SPREAD_FLOOR = 1e-4


def losses(
    out: dict[str, torch.Tensor], batch: dict[str, torch.Tensor], w: LossWeights
) -> dict[str, torch.Tensor]:
    """Masked losses; invalid cells contribute nothing to any term (blueprint 15.5)."""

    def masked_bce(logit: torch.Tensor, y: torch.Tensor, m: torch.Tensor) -> torch.Tensor:
        loss = F.binary_cross_entropy_with_logits(logit, y, reduction="none")
        return (loss * m).sum() / m.sum().clamp_min(1)

    lf = masked_bce(out["forest"], batch["y_forest"], batch["m_forest"].float())
    lc = masked_bce(out["change"], batch["y_change"], batch["m_change"].float())
    target = decode(batch["y_emb"].permute(0, 2, 3, 1))  # [B,P,P,64]
    var = torch.exp(2 * out["emb_logspread"]).clamp_min(SPREAD_FLOOR**2)
    nll = 0.5 * ((target - out["emb_mean"]) ** 2 / var + torch.log(var)).mean(-1)
    me = batch["m_emb"].float()
    le = (nll * me).sum() / me.sum().clamp_min(1)
    total = w.forest * lf + w.change * lc + w.embedding * le
    return {"total": total, "forest": lf, "change": lc, "embedding": le}
