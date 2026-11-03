"""Hand-written, standard-library-only contracts for the memoryview layouts sniff() accepts."""

from __future__ import annotations

import ctypes
import math
import sys
from typing import Literal

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


_WideFormat = Literal["H", "h", "I", "i", "Q", "q"]


def _strided_wide_view(fmt: _WideFormat, stride: int, content: bytes) -> memoryview:
    itemsize = memoryview(bytes(8)).cast(fmt).itemsize
    count = 2 * len(content) // itemsize
    raw = bytearray(count * itemsize)
    for slot, element in enumerate(range(count)[::stride]):
        raw[element * itemsize : (element + 1) * itemsize] = content[
            slot * itemsize : (slot + 1) * itemsize
        ]
    return memoryview(raw).cast(fmt)[::stride]


@pytest.mark.parametrize("fmt", ["H", "h", "I", "i", "Q", "q"])
@pytest.mark.parametrize("stride", [2, -2])
def test_sniff_rejects_strided_views_with_wide_elements(fmt: _WideFormat, stride: int) -> None:
    content = b"%PDF-1.7" + bytes(24)
    view = _strided_wide_view(fmt, stride, content)
    assert view.ndim == 1 and view.itemsize > 1 and not view.c_contiguous
    # The logical bytes start with a PDF signature, so accepting the layout is visible.
    assert bytes(view) == content
    with pytest.raises(TypeError):
        m.sniff(view)


class _PyBuffer(ctypes.Structure):
    # The public Py_buffer layout from the C API reference, stable across supported versions.
    _fields_ = [
        ("buf", ctypes.c_void_p),
        ("obj", ctypes.c_void_p),
        ("len", ctypes.c_ssize_t),
        ("itemsize", ctypes.c_ssize_t),
        ("readonly", ctypes.c_int),
        ("ndim", ctypes.c_int),
        ("format", ctypes.c_char_p),
        ("shape", ctypes.POINTER(ctypes.c_ssize_t)),
        ("strides", ctypes.POINTER(ctypes.c_ssize_t)),
        ("suboffsets", ctypes.POINTER(ctypes.c_ssize_t)),
        ("internal", ctypes.c_void_p),
    ]


needs_cpython = pytest.mark.skipif(
    sys.implementation.name != "cpython", reason="builds a raw buffer through the CPython C API"
)


def _exported_view(
    keep: list[object], fmt: bytes, itemsize: int, shape: tuple[int, ...], strides: tuple[int, ...]
) -> memoryview:
    # Stands in for a third-party exporter: the standard library cannot produce these layouts.
    backing = (ctypes.c_ubyte * 16).from_buffer_copy(b"%PDF-1.7 trailer")
    dims = (ctypes.c_ssize_t * len(shape))(*shape)
    steps = (ctypes.c_ssize_t * len(strides))(*strides)
    length = itemsize * math.prod(shape)
    raw = _PyBuffer(
        ctypes.addressof(backing), None, length, itemsize, 1, len(shape), fmt, dims, steps
    )
    keep.extend([backing, dims, steps, raw])
    from_buffer = ctypes.pythonapi.PyMemoryView_FromBuffer
    from_buffer.restype = ctypes.py_object
    from_buffer.argtypes = [ctypes.POINTER(_PyBuffer)]
    view = from_buffer(ctypes.byref(raw))
    assert isinstance(view, memoryview)
    return view


@needs_cpython
def test_sniff_rejects_fortran_only_views_without_optional_packages() -> None:
    keep: list[object] = []
    view = _exported_view(keep, b"B", 1, (4, 4), (1, 4))
    assert view.f_contiguous and not view.c_contiguous and view.nbytes == 16
    with pytest.raises(TypeError, match="C-contiguous"):
        m.sniff(view)


@needs_cpython
def test_sniff_rejects_strided_views_with_zero_size_elements() -> None:
    keep: list[object] = []
    view = _exported_view(keep, b"0s", 0, (8,), (2,))
    assert view.ndim == 1 and view.itemsize == 0 and not view.c_contiguous
    with pytest.raises(TypeError):
        m.sniff(view)
