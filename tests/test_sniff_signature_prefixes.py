"""Hand-written contracts that every fixed magic signature is matched in full."""

from __future__ import annotations

import pytest

import mimeguess as m

# Every fixed-prefix signature sniff() documents, written by hand from the format specifications.
SIGNATURES = [
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
]


@pytest.mark.parametrize("kind", [bytes, bytearray])
@pytest.mark.parametrize("signature", SIGNATURES)
def test_sniff_rejects_every_proper_prefix_of_a_signature(
    signature: bytes, kind: type[bytes | bytearray]
) -> None:
    assert m.sniff(kind(signature)) is not None
    for end in range(len(signature)):
        assert m.sniff(kind(signature[:end])) is None, signature[:end]


@pytest.mark.parametrize("kind", [bytes, bytearray])
@pytest.mark.parametrize("signature", SIGNATURES)
def test_sniff_rejects_a_signature_whose_last_byte_differs(
    signature: bytes, kind: type[bytes | bytearray]
) -> None:
    for flip in (0x01, 0x80, 0xFF):
        altered = signature[:-1] + bytes([signature[-1] ^ flip]) + b"\xaa" * 16
        assert m.sniff(kind(altered)) is None, altered
