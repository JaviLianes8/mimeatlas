"""Hand-written contracts for accepted buffers and exact magic signatures."""

from __future__ import annotations

from array import array

import pytest

import mimeguess as m


@pytest.mark.parametrize("typecode", ["b", "B"])
def test_sniff_rejects_direct_array_buffers(typecode: str) -> None:
    data = array(typecode, b"%PDF-")
    with pytest.raises(TypeError):
        m.sniff(data)  # type: ignore[arg-type]


@pytest.mark.parametrize("typecode", ["b", "B"])
def test_sniff_accepts_memoryview_wrapped_arrays(typecode: str) -> None:
    assert m.sniff(memoryview(array(typecode, b"%PDF-"))) == "application/pdf"


@pytest.mark.parametrize("stride", [2, -2])
@pytest.mark.parametrize(
    ("signature", "expected"),
    [(b"%PDF-", "application/pdf"), (b"\x89PNG\r\n\x1a\n", "image/png")],
)
def test_sniff_accepts_signed_one_byte_strided_views(
    stride: int, signature: bytes, expected: str
) -> None:
    backing = bytearray(2 * len(signature))
    backing[::stride] = signature
    view = memoryview(array("b", backing))[::stride]
    assert view.format == "b" and not view.c_contiguous
    assert bytes(view) == signature
    assert m.sniff(view) == expected


@pytest.mark.parametrize("stride", [2, -2])
@pytest.mark.parametrize(
    ("signature", "expected"),
    [
        (b"SQLite format 3", None),
        (b"SQLite format 3\x00", "application/vnd.sqlite3"),
        (b"SQLite format 3\x00x", "application/vnd.sqlite3"),
    ],
    ids=["truncated", "complete", "trailing-byte"],
)
def test_sniff_checks_the_complete_sqlite_signature_in_strided_views(
    stride: int, signature: bytes, expected: str | None
) -> None:
    backing = bytearray(2 * len(signature))
    view = memoryview(backing)[::stride]
    view[:] = signature
    assert not view.c_contiguous and bytes(view) == signature
    assert m.sniff(view) == expected


@pytest.mark.parametrize(
    "signature",
    [
        b"\x89PNG\r\n\x1a\n",
        b"GIF87a",
        b"GIF89a",
        b"II*\x00",
        b"MM\x00*",
        b"%PDF-",
        b"PK\x03\x04",
        b"PK\x05\x06",
        b"PK\x07\x08",
        b"\xfd7zXZ\x00",
        b"7z\xbc\xaf\x27\x1c",
        b"Rar!\x1a\x07\x00",
        b"Rar!\x1a\x07\x01\x00",
        b"OggS",
        b"fLaC",
        b"\x00asm",
        b"wOFF",
        b"wOF2",
        b"SQLite format 3\x00",
        b"BZh9",
        b"RIFF\x00\x00\x00\x00WEBP",
        b"RIFF\x00\x00\x00\x00WAVE",
        b"RIFF\x00\x00\x00\x00AVI ",
    ],
)
def test_sniff_rejects_case_altered_magic_signatures(signature: bytes) -> None:
    assert m.sniff(signature) is not None
    for index, value in enumerate(signature):
        byte = bytes([value])
        if byte.isalpha():
            altered = signature[:index] + byte.swapcase() + signature[index + 1 :]
            assert m.sniff(altered) is None, altered
    assert m.sniff(signature.swapcase()) is None
