"""Sniff real output produced by the running standard library implementations."""

from __future__ import annotations

import bz2
import io
import lzma
import sqlite3
import wave
from pathlib import Path

import mimeguess as m


def test_real_bzip2_and_xz_streams() -> None:
    payload = b"sample payload" * 100
    for level in range(1, 10):
        assert m.sniff(bz2.compress(payload, compresslevel=level)) == "application/x-bzip2"
    assert m.sniff(lzma.compress(payload, format=lzma.FORMAT_XZ)) == "application/x-xz"


def test_real_wave_output() -> None:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(8000)
        stream.writeframes(bytes(32))
    assert m.sniff(buffer.getvalue()) == "audio/wav"


def test_real_sqlite_output(tmp_path: Path) -> None:
    path = tmp_path / "sample.sqlite"
    connection = sqlite3.connect(path)
    try:
        connection.execute("CREATE TABLE sample (value INTEGER)")
        connection.commit()
    finally:
        connection.close()
    with path.open("rb") as stream:
        assert m.sniff(stream.read(16)) == "application/vnd.sqlite3"
