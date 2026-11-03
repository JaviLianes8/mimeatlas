"""How the sniff command reads its inputs: exactly one bounded read, and only "-" means stdin."""

from __future__ import annotations

import io
import sys
from pathlib import Path
from typing import IO, Any

import pytest

import mimeatlas._cli as cli
from mimeatlas._sniff import SNIFF_BYTES

SQLITE = b"SQLite format 3\x00" + bytes(100)
PNG = b"\x89PNG\r\n\x1a\n" + bytes(100)


class RecordingReader(io.BytesIO):
    """A binary stream that records the size argument of every read call."""

    def __init__(self, data: bytes) -> None:
        super().__init__(data)
        self.sizes: list[int | None] = []

    def read(self, size: int | None = -1, /) -> bytes:
        self.sizes.append(size)
        return super().read(size)


class FakeStdin:
    def __init__(self, data: bytes) -> None:
        self.buffer = RecordingReader(data)


def run(capsys: pytest.CaptureFixture[str], *args: str) -> tuple[int, str, str]:
    code = cli.main(list(args))
    out, err = capsys.readouterr()
    return code, out, err


def test_sniff_window_is_sixteen_bytes() -> None:
    assert SNIFF_BYTES == 16
    assert len(b"SQLite format 3\x00") == SNIFF_BYTES


def test_stdin_reads_one_full_window(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    stdin = FakeStdin(SQLITE)
    monkeypatch.setattr(sys, "stdin", stdin)
    assert run(capsys, "sniff", "-") == (0, "application/vnd.sqlite3\n", "")
    assert stdin.buffer.sizes == [SNIFF_BYTES]


def test_file_reads_one_full_window(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    db = tmp_path / "x.sqlite"
    db.write_bytes(SQLITE)
    readers: list[RecordingReader] = []

    def recording_open(name: str, mode: str = "r", *args: Any, **kwargs: Any) -> IO[bytes]:
        assert mode == "rb"
        with open(name, mode, *args, **kwargs) as handle:
            reader = RecordingReader(handle.read())
        readers.append(reader)
        return reader

    monkeypatch.setattr(cli, "open", recording_open, raising=False)
    assert run(capsys, "sniff", str(db)) == (0, "application/vnd.sqlite3\n", "")
    assert [r.sizes for r in readers] == [[SNIFF_BYTES]]


def test_only_a_bare_dash_means_stdin(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "-x.png").write_bytes(PNG)
    (tmp_path / "--").write_bytes(PNG)
    stdin = FakeStdin(SQLITE)
    monkeypatch.setattr(sys, "stdin", stdin)
    assert run(capsys, "sniff", "--", "-x.png") == (0, "image/png\n", "")
    assert run(capsys, "sniff", "--", "--") == (0, "image/png\n", "")
    assert stdin.buffer.sizes == []
