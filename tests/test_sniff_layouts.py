"""Hand-written, standard-library-only contracts for the memoryview layouts sniff() accepts."""

from __future__ import annotations

import ctypes

import pytest

import mimeguess as m


def _strided_two_dimensional(source: str, stride: int) -> memoryview:
    payload = b"%PDF" * 8
    if source == "cast":
        return memoryview(bytearray(payload)).cast("B", (8, 4))[::stride]
    rows = ((ctypes.c_ubyte * 4) * 8)()
    ctypes.memmove(rows, payload, len(payload))
    return memoryview(rows)[::stride]


@pytest.mark.parametrize("source", ["cast", "ctypes"])
@pytest.mark.parametrize("stride", [2, -2])
def test_sniff_rejects_non_contiguous_multidimensional_byte_views(source: str, stride: int) -> None:
    view = _strided_two_dimensional(source, stride)
    assert view.ndim == 2 and view.itemsize == 1
    assert not view.c_contiguous and not view.f_contiguous
    # Read as rows, the first bytes form a PDF signature, so accepting the layout is visible.
    assert bytes(view[:16]).startswith(b"%PDF")
    with pytest.raises(TypeError):
        m.sniff(view)
