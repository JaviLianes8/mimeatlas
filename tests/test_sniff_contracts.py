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


@pytest.mark.parametrize("buffer_kind", ["bytes", "bytearray", "stride-2", "stride-minus-2"])
@pytest.mark.parametrize("offset", [1, 3])
@pytest.mark.parametrize(
    "signature",
    [
        b"\x89PNG\r\n\x1a\n",
        b"\xff\xd8\xff",
        b"GIF87a",
        b"GIF89a",
        b"II*\x00",
        b"MM\x00*",
        b"%PDF-",
        b"PK\x03\x04",
        b"PK\x05\x06",
        b"PK\x07\x08",
        b"\x1f\x8b\x08",
        b"\xfd7zXZ\x00",
        b"\x28\xb5\x2f\xfd",
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
def test_sniff_requires_magic_signatures_at_offset_zero(
    signature: bytes, offset: int, buffer_kind: str
) -> None:
    assert m.sniff(signature) is not None
    shifted = b"x" * offset + signature
    data: bytes | bytearray | memoryview
    if buffer_kind == "bytes":
        data = shifted
    elif buffer_kind == "bytearray":
        data = bytearray(shifted)
    else:
        stride = 2 if buffer_kind == "stride-2" else -2
        backing = bytearray(2 * len(shifted))
        data = memoryview(backing)[::stride]
        data[:] = shifted
        assert not data.c_contiguous and bytes(data) == shifted
    assert m.sniff(data) is None


@pytest.mark.parametrize("buffer_kind", ["bytes", "bytearray", "stride-2", "stride-minus-2"])
@pytest.mark.parametrize(
    "data",
    [b"abc1BZh", b"xxxxRIFFWEBP", b"xxxxRIFFWAVE", b"xxxxRIFFAVI "],
    ids=["bzip2-at-3", "riff-webp-at-4", "riff-wave-at-4", "riff-avi-at-4"],
)
def test_sniff_requires_bzip2_and_riff_markers_at_offset_zero(
    data: bytes, buffer_kind: str
) -> None:
    # A misplaced marker must not borrow a version digit or form type from other bytes.
    buffer: bytes | bytearray | memoryview
    if buffer_kind == "bytes":
        buffer = data
    elif buffer_kind == "bytearray":
        buffer = bytearray(data)
    else:
        stride = 2 if buffer_kind == "stride-2" else -2
        buffer = memoryview(bytearray(2 * len(data)))[::stride]
        buffer[:] = data
        assert not buffer.c_contiguous and bytes(buffer) == data
    assert m.sniff(buffer) is None


@pytest.mark.parametrize("buffer_kind", ["bytes", "bytearray", "stride-2", "stride-minus-2"])
@pytest.mark.parametrize(
    "data",
    [b"BZh", b"RIFF\x00\x00\x00\x00WEB", b"RIFF\x00\x00\x00\x00WAV", b"RIFF\x00\x00\x00\x00AVI"],
    ids=["bzip2-3-bytes", "riff-webp-11-bytes", "riff-wave-11-bytes", "riff-avi-11-bytes"],
)
def test_sniff_rejects_markers_one_byte_short_of_their_length_guard(
    data: bytes, buffer_kind: str
) -> None:
    # A bare b"BZh" has an empty digit slice, and b"" is in every bytes object.
    buffer: bytes | bytearray | memoryview
    if buffer_kind == "bytes":
        buffer = data
    elif buffer_kind == "bytearray":
        buffer = bytearray(data)
    else:
        stride = 2 if buffer_kind == "stride-2" else -2
        buffer = memoryview(bytearray(2 * len(data)))[::stride]
        buffer[:] = data
        assert not buffer.c_contiguous and bytes(buffer) == data
    assert m.sniff(buffer) is None
