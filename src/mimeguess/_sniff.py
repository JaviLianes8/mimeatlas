"""A deliberately narrow magic number sniffer.

The signatures are hand-written from the public format specifications. Only
formats with a fixed, unambiguous signature at offset 0 (or at offset 8 inside a
RIFF container) are listed; anything else returns None.
"""

from __future__ import annotations

# (prefix, MIME type), checked in order.
_PREFIXES: tuple[tuple[bytes, str], ...] = (
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
    (b"II*\x00", "image/tiff"),
    (b"MM\x00*", "image/tiff"),
    (b"%PDF-", "application/pdf"),
    (b"PK\x03\x04", "application/zip"),
    (b"PK\x05\x06", "application/zip"),
    (b"PK\x07\x08", "application/zip"),
    (b"\x1f\x8b\x08", "application/gzip"),
    (b"\xfd7zXZ\x00", "application/x-xz"),
    (b"\x28\xb5\x2f\xfd", "application/zstd"),
    (b"7z\xbc\xaf\x27\x1c", "application/x-7z-compressed"),
    (b"Rar!\x1a\x07\x00", "application/vnd.rar"),
    (b"Rar!\x1a\x07\x01\x00", "application/vnd.rar"),
    (b"OggS", "application/ogg"),
    (b"fLaC", "audio/flac"),
    (b"\x00asm", "application/wasm"),
    (b"wOFF", "font/woff"),
    (b"wOF2", "font/woff2"),
    (b"SQLite format 3\x00", "application/vnd.sqlite3"),
)

# RIFF containers: b"RIFF", a 4-byte size, then a 4-byte form type.
_RIFF_FORMS: dict[bytes, str] = {
    b"WEBP": "image/webp",
    b"WAVE": "audio/wav",
    b"AVI ": "video/x-msvideo",
}

SNIFF_BYTES = 16
"""How many leading bytes :func:`sniff` looks at; passing more is harmless."""


def sniff(data: bytes | bytearray | memoryview) -> str | None:
    """Return the MIME type of a few well-known formats from their first bytes.

    Recognised: PNG, JPEG, GIF, TIFF, WebP, PDF, ZIP, gzip, bzip2, xz, zstd,
    7-Zip, RAR, Ogg, FLAC, WAV, AVI, WebAssembly, WOFF, WOFF2 and SQLite 3.
    Anything else, including empty input, returns ``None``.

    This is not a general content detector. Container formats are reported as
    the container: a ``.docx``, ``.jar`` or ``.epub`` file is ``application/zip``.
    Use it to double-check an extension, not to replace one.

    C-contiguous memoryviews are read as raw bytes. Strided views must be
    one-dimensional with one-byte elements. Only the first 16 bytes are read.
    Fortran-only contiguous views are unsupported.

    Raises:
        TypeError: if ``data`` is not bytes-like or has an unsupported view layout.
        ValueError: if a memoryview has already been released.

    >>> import mimeguess as m
    >>> m.sniff(b"%PDF-1.7")
    'application/pdf'
    """
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("sniff() needs bytes, bytearray or memoryview")
    view = memoryview(data)
    if view.c_contiguous:
        if view.nbytes == 0:
            return None
        head = bytes(view.cast("B")[:SNIFF_BYTES])
    elif view.ndim == 1 and view.itemsize == 1:
        head = bytes(view[:SNIFF_BYTES])
    else:
        raise TypeError("sniff() needs a C-contiguous or one-byte one-dimensional view")
    for prefix, mime in _PREFIXES:
        if head.startswith(prefix):
            return mime
    if len(head) >= 4 and head.startswith(b"BZh") and head[3:4] in b"123456789":
        return "application/x-bzip2"
    if len(head) >= 12 and head.startswith(b"RIFF"):
        return _RIFF_FORMS.get(head[8:12])
    return None
