"""Memory bounds for large but valid custom inputs."""

from __future__ import annotations

import tracemalloc

import pytest

import mimeguess as m


def test_sniff_copies_only_the_required_prefix_of_a_multidimensional_view() -> None:
    data = bytearray(2_000_000)
    data[:5] = b"%PDF-"
    view = memoryview(data).cast("B", (1, len(data)))
    tracemalloc.start()
    try:
        assert m.sniff(view) == "application/pdf"
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert peak < 64_000


@pytest.mark.parametrize("size", [400_000, 4_000_000])
@pytest.mark.parametrize("stride", [2, -2])
def test_sniff_copies_only_the_required_prefix_of_a_strided_view(size: int, stride: int) -> None:
    data = bytearray(size)
    view = memoryview(data)[::stride]
    view[:5] = b"%PDF-"
    assert not view.c_contiguous
    tracemalloc.start()
    try:
        assert m.sniff(view) == "application/pdf"
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert peak < 64_000


def test_long_compound_extensions_do_not_allocate_every_possible_suffix() -> None:
    extension = "part." * 20_000 + "end"
    table = m.default_table().with_types({"text/x-long": [extension]})
    path = "file." + extension
    tracemalloc.start()
    try:
        assert table.guess_type(path) == "text/x-long"
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert peak < 8_000_000


def test_sniff_reads_exactly_the_documented_sixteen_byte_prefix() -> None:
    # The CLI reads SNIFF_BYTES from a file or stdin, so the bound is a promise, not a detail.
    from mimeguess._sniff import SNIFF_BYTES

    assert SNIFF_BYTES == 16
    assert "Only the first 16 bytes are read." in (m.sniff.__doc__ or "")
