"""essence, structured suffixes, textual detection and the narrow sniffer."""

from __future__ import annotations

import gzip
import io
import zipfile

import pytest

import mimeatlas
from mimeatlas import InvalidMediaType


def test_essence_lowercases_and_strips_parameters() -> None:
    assert mimeatlas.essence("  Text/HTML ; charset=UTF-8") == "text/html"
    assert mimeatlas.essence("application/vnd.api+json") == "application/vnd.api+json"


@pytest.mark.parametrize("value", ["", "text", "text/", "/html", "te xt/html", "a/b/c", "a/b c"])
def test_essence_rejects_malformed_values(value: str) -> None:
    with pytest.raises(InvalidMediaType):
        mimeatlas.essence(value)


def test_invalid_media_type_is_a_value_error() -> None:
    assert issubclass(InvalidMediaType, ValueError)


def test_structured_suffix() -> None:
    assert mimeatlas.structured_suffix("application/ld+json") == "json"
    assert mimeatlas.structured_suffix("IMAGE/SVG+XML; x=1") == "xml"
    assert mimeatlas.structured_suffix("application/json") is None
    assert mimeatlas.structured_suffix("application/+json") is None
    assert mimeatlas.structured_suffix("nonsense") is None


def test_is_textual() -> None:
    assert mimeatlas.is_textual("text/plain")
    assert mimeatlas.is_textual("application/json")  # declared charset
    assert mimeatlas.is_textual("application/vnd.example+json")  # suffix
    assert mimeatlas.is_textual("application/atom+xml")
    assert not mimeatlas.is_textual("image/png")
    assert not mimeatlas.is_textual("application/zip")
    assert not mimeatlas.is_textual("garbage")


def _zip_bytes() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("a.txt", "hello")
    return buffer.getvalue()


SAMPLES = {
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR": "image/png",
    b"\xff\xd8\xff\xe0\x00\x10JFIF": "image/jpeg",
    b"GIF89a\x01\x00": "image/gif",
    b"GIF87a\x01\x00": "image/gif",
    b"II*\x00\x08\x00": "image/tiff",
    b"MM\x00*\x00\x00": "image/tiff",
    b"RIFF\x24\x00\x00\x00WEBPVP8 ": "image/webp",
    b"RIFF\x24\x00\x00\x00WAVEfmt ": "audio/wav",
    b"RIFF\x24\x00\x00\x00AVI LIST": "video/x-msvideo",
    b"%PDF-1.7\n": "application/pdf",
    b"BZh91AY&SY": "application/x-bzip2",
    b"\xfd7zXZ\x00\x00": "application/x-xz",
    b"\x28\xb5\x2f\xfd\x00": "application/zstd",
    b"7z\xbc\xaf\x27\x1c\x00\x04": "application/x-7z-compressed",
    b"Rar!\x1a\x07\x00": "application/vnd.rar",
    b"Rar!\x1a\x07\x01\x00": "application/vnd.rar",
    b"OggS\x00\x02": "application/ogg",
    b"fLaC\x00\x00": "audio/flac",
    b"\x00asm\x01\x00\x00\x00": "application/wasm",
    b"wOFF\x00\x01": "font/woff",
    b"wOF2\x00\x01": "font/woff2",
    b"SQLite format 3\x00\x10\x00": "application/vnd.sqlite3",
}


@pytest.mark.parametrize(("data", "expected"), sorted(SAMPLES.items()))
def test_sniff_recognises_each_documented_signature(data: bytes, expected: str) -> None:
    assert mimeatlas.sniff(data) == expected


def test_sniff_works_on_real_generated_files() -> None:
    assert mimeatlas.sniff(gzip.compress(b"hello")) == "application/gzip"
    assert mimeatlas.sniff(_zip_bytes()) == "application/zip"
    assert mimeatlas.sniff(bytearray(_zip_bytes())) == "application/zip"
    assert mimeatlas.sniff(memoryview(_zip_bytes())) == "application/zip"


@pytest.mark.parametrize(
    "data", [b"", b"hello world", b"BZh0", b"BZ", b"RIFF\x00\x00\x00\x00XXXX", b"RIFF", b"PK"]
)
def test_sniff_returns_none_for_anything_else(data: bytes) -> None:
    assert mimeatlas.sniff(data) is None


def test_sniff_rejects_text() -> None:
    with pytest.raises(TypeError):
        mimeatlas.sniff("%PDF-1.7")  # type: ignore[arg-type]


def test_every_sniffed_type_is_in_the_table() -> None:
    for mime in set(SAMPLES.values()) | {"application/zip", "application/gzip"}:
        assert mimeatlas.media_type_info(mime) is not None, mime
