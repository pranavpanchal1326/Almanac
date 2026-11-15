"""Lossless year-to-year difference encoding for stored int8 values (blueprint section 8.6)."""

from __future__ import annotations

import numpy as np


def encode(stored_tchw: np.ndarray) -> np.ndarray:
    """Year one as read; each later year minus the previous one, int8 with wrap-around."""
    if stored_tchw.dtype != np.int8:
        raise TypeError("difference encoding expects int8")
    out = stored_tchw.copy()
    out[1:] = (stored_tchw[1:].view(np.uint8) - stored_tchw[:-1].view(np.uint8)).view(np.int8)
    return out


def decode(encoded_tchw: np.ndarray) -> np.ndarray:
    """Exact inverse of :func:`encode`."""
    if encoded_tchw.dtype != np.int8:
        raise TypeError("difference decoding expects int8")
    return np.cumsum(encoded_tchw.view(np.uint8), axis=0, dtype=np.uint8).view(np.int8)
