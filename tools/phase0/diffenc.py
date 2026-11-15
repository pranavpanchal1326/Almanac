"""Task 0.11: does year-to-year difference encoding save space?

For each site, at level 0 (a 512 x 512 centre crop, to bound memory) and at level 6 (built from
level 0 and re-quantised to int8), compares the size of the values as read with the size of the
difference-encoded values, both compressed with Zstandard through Zarr. Also tries byte shuffle,
and checks that the round trip is exact.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from numcodecs import Blosc

from almanac.data import diffenc
from almanac.io.reader import valid_mask
from almanac.quality.embedding import coarsen_mean, dequantize, quantize, renormalize

sys.path.insert(0, str(Path(__file__).parent))
from common import DOCS, load_sites

CODECS = {
    "zstd-9": Blosc(cname="zstd", clevel=9, shuffle=Blosc.NOSHUFFLE),
    "zstd-9+bitshuffle": Blosc(cname="zstd", clevel=9, shuffle=Blosc.BITSHUFFLE),
}


def compressed_size(arr_tchw: np.ndarray, codec: Blosc) -> int:
    """Bytes after compressing each year-by-band plane group as its own chunk."""
    return sum(len(codec.encode(np.ascontiguousarray(arr_tchw[t]))) for t in range(arr_tchw.shape[0]))


def level6(stored_tchw: np.ndarray) -> np.ndarray:
    out = []
    for t in range(stored_tchw.shape[0]):
        emb, _ = coarsen_mean(renormalize(dequantize(stored_tchw[t])), valid_mask(stored_tchw[t]), 64)
        out.append(quantize(emb))
    return np.stack(out)


def main() -> None:
    rows = []
    for site in load_sites(roles=("change", "stable")):
        stored = site.load_years()
        variants = {"L0 (512x512 crop)": stored[:, :, 256:768, 256:768], "L6 (16x16)": level6(stored)}
        for level_name, arr in variants.items():
            encoded = diffenc.encode(arr)
            if not np.array_equal(diffenc.decode(encoded), arr):
                raise AssertionError(f"round trip not exact for {site.name} {level_name}")
            for codec_name, codec in CODECS.items():
                as_read = compressed_size(arr, codec)
                diffed = compressed_size(encoded, codec)
                rows.append(
                    {
                        "site": site.name,
                        "level": level_name,
                        "codec": codec_name,
                        "raw_bytes": int(arr.nbytes),
                        "as_read_bytes": as_read,
                        "difference_bytes": diffed,
                        "gain": round(as_read / diffed, 3),
                        "round_trip_exact": True,
                    }
                )
                print(
                    f"{site.name:16s} {level_name:18s} {codec_name:18s} raw {arr.nbytes / 1e6:7.2f} MB  "
                    f"as read {as_read / 1e6:7.2f}  differenced {diffed / 1e6:7.2f}  gain {as_read / diffed:.2f}x",
                    flush=True,
                )
    (DOCS / "diffenc.json").write_text(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
