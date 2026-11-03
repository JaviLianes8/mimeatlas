"""Hand-written contracts for buffer layouts and active scalar subclasses."""

from __future__ import annotations

import ctypes
import tracemalloc
from typing import SupportsIndex, overload

import pytest

import mimeguess as m


@pytest.mark.parametrize("layout", ["slice", "outer", "inner"])
def test_empty_multidimensional_views_return_none(layout: str) -> None:
    if layout == "slice":
        view = memoryview(b"0123456789abcdef").cast("B", (4, 4))[:0]
    elif layout == "outer":
        view = memoryview(((ctypes.c_ubyte * 4) * 0)())
    else:
        view = memoryview(((ctypes.c_ubyte * 0) * 4)())
    assert view.c_contiguous and view.nbytes == 0
    assert m.sniff(view) is None
    view.release()
    with pytest.raises(ValueError):
        m.sniff(view)


def test_fortran_only_views_report_the_c_contiguous_requirement() -> None:
    np = pytest.importorskip("numpy")
    view = memoryview(np.ndarray((4, 4), dtype="u1", buffer=b"%PDF-12345678901", order="F"))
    assert view.f_contiguous and not view.c_contiguous
    with pytest.raises(TypeError, match="C-contiguous"):
        m.sniff(view)


class _Bytes(bytes):
    @overload
    def __getitem__(self, key: SupportsIndex) -> int: ...
    @overload
    def __getitem__(self, key: slice) -> bytes: ...
    def __getitem__(self, key: SupportsIndex | slice) -> int | bytes:
        return self if isinstance(key, slice) else super().__getitem__(key)


class _Bytearray(bytearray):
    @overload
    def __getitem__(self, key: SupportsIndex) -> int: ...
    @overload
    def __getitem__(self, key: slice) -> bytearray: ...
    def __getitem__(self, key: SupportsIndex | slice) -> int | bytearray:
        return self if isinstance(key, slice) else super().__getitem__(key)


@pytest.mark.parametrize("kind", [_Bytes, _Bytearray])
def test_binary_subclasses_cannot_expand_the_sniff_prefix(kind: type[bytes | bytearray]) -> None:
    data = kind(b"%PDF-" + bytes(2_000_000))
    tracemalloc.start()
    try:
        assert m.sniff(data) == "application/pdf"
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert peak < 64_000


@pytest.mark.parametrize("kind", [_Bytes, _Bytearray])
@pytest.mark.parametrize("behavior", ["substitute", "raise"])
def test_sniff_reads_binary_subclass_buffers_without_getitem(
    kind: type[bytes | bytearray], behavior: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[object] = []

    def getitem(self: bytes | bytearray, key: object) -> bytes:
        calls.append(key)
        if behavior == "raise":
            raise RuntimeError("slice override must not run")
        return b"not a signature"

    monkeypatch.setattr(kind, "__getitem__", getitem)
    assert m.sniff(kind(b"%PDF-1.7")) == "application/pdf"
    assert calls == []


@pytest.mark.parametrize("kind", [_Bytes, _Bytearray])
@pytest.mark.parametrize("method", ["__bool__", "__len__"])
@pytest.mark.parametrize("behavior", ["substitute", "raise"])
def test_sniff_ignores_binary_subclass_truthiness(
    kind: type[bytes | bytearray], method: str, behavior: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []

    def override(self: bytes | bytearray) -> bool:
        calls.append(method)
        if behavior == "raise":
            raise RuntimeError("truthiness override must not run")
        return False

    monkeypatch.setattr(kind, method, override, raising=False)
    assert m.sniff(kind(b"%PDF-1.7")) == "application/pdf"
    assert calls == []


@pytest.mark.parametrize("kind", [_Bytes, _Bytearray])
@pytest.mark.parametrize("behavior", ["substitute", "raise"])
def test_sniff_ignores_binary_subclass_startswith(
    kind: type[bytes | bytearray], behavior: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[object, ...]] = []

    def startswith(self: bytes | bytearray, *args: object) -> bool:
        calls.append(args)
        if behavior == "raise":
            raise RuntimeError("startswith override must not run")
        return False

    monkeypatch.setattr(kind, "startswith", startswith)
    assert m.sniff(kind(b"%PDF-1.7")) == "application/pdf"
    assert calls == []


class _Text(str):
    def __getattribute__(self, name: str) -> object:
        if name in {"split", "strip", "lower", "replace"}:
            raise RuntimeError("private-input" * 20_000)
        return super().__getattribute__(name)

    def __str__(self) -> str:
        raise RuntimeError("private-input" * 20_000)


def test_mime_queries_use_the_underlying_string_value() -> None:
    value = _Text(" Text/Plain; charset=ascii ")
    assert m.essence(value) == "text/plain"
    assert m.extensions_for(value) == m.extensions_for("text/plain")
    assert m.guess_extension(value) == ".txt"
    assert m.media_type_info(value) == m.media_type_info("text/plain")
    assert m.default_charset(value) == "utf-8"
    assert m.is_textual(value) is True
    assert m.is_compressible(value) is True
    assert m.structured_suffix(_Text("application/x-test+json")) == "json"
    with pytest.raises(m.InvalidMediaType, match=r"^not a type/subtype media type$"):
        m.essence(_Text("private-input" * 20_000))


def test_paths_use_the_underlying_string_value() -> None:
    path = _Text(r"directory\file.PDF")
    assert m.guess_type(path) == "application/pdf"
    assert m.guess(path) == m.Guess("application/pdf", None, "pdf")
    assert m.content_type_for(path) == "application/pdf"


def test_extensions_use_the_underlying_string_value() -> None:
    assert m.type_for_extension(_Text(".PDF")) == "application/pdf"
    assert m.type_for_extension(_Text("bad/extension")) is None


def test_overrides_use_underlying_string_values() -> None:
    table = m.default_table().with_types({_Text(" Text/X-Test "): [_Text(".TEST")]})
    assert table.guess_type("file.test") == "text/x-test"
    with pytest.raises(ValueError, match=r"^not a bare type/subtype media type$"):
        table.with_types({_Text("private-input" * 20_000): ["test"]})
    with pytest.raises(ValueError, match=r"^not a valid file extension$"):
        table.with_types({_Text("text/x-test"): [_Text("private/input" * 20_000)]})
