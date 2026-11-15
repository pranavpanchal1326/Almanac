import numpy as np
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.extra import numpy as hnp

from almanac.data import diffenc
from almanac.quality.embedding import dequantize, quantize

int8_arrays = hnp.arrays(
    np.int8,
    st.tuples(st.integers(1, 9), st.integers(1, 4), st.integers(1, 5)),
    elements=st.integers(-128, 127),
)


@given(hnp.arrays(np.int8, st.integers(1, 200), elements=st.integers(-127, 127)))
def test_decode_then_encode_returns_the_stored_integers(values: np.ndarray) -> None:
    np.testing.assert_array_equal(quantize(dequantize(values)), values)


@given(int8_arrays)
@settings(max_examples=200)
def test_difference_encoding_round_trip_is_exact(stored: np.ndarray) -> None:
    np.testing.assert_array_equal(diffenc.decode(diffenc.encode(stored)), stored)


def test_difference_encoding_wraps() -> None:
    stored = np.array([[127], [-128], [127]], dtype=np.int8)
    encoded = diffenc.encode(stored)
    assert encoded.tolist() == [[127], [1], [-1]]
    np.testing.assert_array_equal(diffenc.decode(encoded), stored)
