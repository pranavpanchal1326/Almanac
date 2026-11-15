"""Decode stored values, measure vector length, and compute change."""

from __future__ import annotations

import numpy as np

from almanac.io.reader import valid_mask


def dequantize(values: np.ndarray) -> np.ndarray:
    """Stored int8 -> float32 in [-1, 1]. Apply the validity mask separately."""
    v = values.astype(np.float32)
    return ((v / 127.5) ** 2) * np.sign(v)


def quantize(emb: np.ndarray) -> np.ndarray:
    """Inverse of :func:`dequantize` for values in [-1, 1]."""
    e = np.asarray(emb, dtype=np.float64)
    return np.rint(np.sqrt(np.abs(e)) * 127.5 * np.sign(e)).astype(np.int8)


def renormalize(emb: np.ndarray, axis: int = 0, eps: float = 1e-6) -> np.ndarray:
    """Unit-length vectors along ``axis``."""
    norm = np.linalg.norm(emb, axis=axis, keepdims=True)
    return emb / np.maximum(norm, eps)


def length_report(emb_chw: np.ndarray, valid_hw: np.ndarray) -> dict[str, float]:
    """Gate Q4: distribution of vector length over valid cells."""
    length = np.linalg.norm(emb_chw, axis=0)[valid_hw]
    if length.size == 0:
        return {"p01": float("nan"), "p50": float("nan"), "p99": float("nan"), "in_band": 0.0, "n": 0}
    q = np.percentile(length, [1, 50, 99])
    in_band = float(((length >= 0.98) & (length <= 1.02)).mean())
    return {
        "p01": float(q[0]),
        "p50": float(q[1]),
        "p99": float(q[2]),
        "in_band": in_band,
        "n": int(length.size),
    }


def cosine_change(a_chw: np.ndarray, b_chw: np.ndarray) -> np.ndarray:
    """``1 - a.b`` per cell for unit-length float arrays ``[64, H, W]``. Result in [0, 2]."""
    return 1.0 - np.einsum("chw,chw->hw", a_chw, b_chw)


def change_between(stored_a: np.ndarray, stored_b: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Change between two stored int8 arrays, and the mask of cells valid in both."""
    valid = valid_mask(stored_a) & valid_mask(stored_b)
    a = renormalize(dequantize(stored_a))
    b = renormalize(dequantize(stored_b))
    return cosine_change(a, b).astype(np.float32), valid


def threshold_from_stable(deltas: list[np.ndarray], percentile: float = 99.0) -> float:
    """Pool change values from stable control cells; return the chosen percentile."""
    pooled = np.concatenate([np.asarray(d).ravel() for d in deltas])
    return float(np.percentile(pooled, percentile))


def coarsen_mean(emb_chw: np.ndarray, valid_hw: np.ndarray, factor: int) -> tuple[np.ndarray, np.ndarray]:
    """Our own coarse level: mean of valid unit vectors in ``factor`` x ``factor`` groups, renormalised.

    A coarse cell is valid when at least half of its fine cells are.
    """
    c, h, w = emb_chw.shape
    if h % factor or w % factor:
        raise ValueError("array side must be a multiple of the factor")
    weights = valid_hw.astype(np.float32)
    masked = emb_chw * weights
    summed = masked.reshape(c, h // factor, factor, w // factor, factor).sum(axis=(2, 4))
    count = weights.reshape(h // factor, factor, w // factor, factor).sum(axis=(1, 3))
    return renormalize(summed), count >= (factor * factor) / 2
