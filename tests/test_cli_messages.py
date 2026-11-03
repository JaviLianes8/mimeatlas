"""Exact text of every command line message: program name, usage lines and stderr lines."""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from mimeatlas._cli import _parser, main

TOP_USAGE = "usage: mimeatlas [-h] [--version] {type,ext,info,sniff,source} ...\n"
TYPE_USAGE = "usage: mimeatlas type [-h] [--content-type | --encoding] PATH [PATH ...]\n"


@pytest.fixture(autouse=True)
def plain_terminal(monkeypatch: pytest.MonkeyPatch) -> None:
    # Usage lines wrap with the terminal width and may be coloured on newer Pythons.
    monkeypatch.setenv("COLUMNS", "100")
    monkeypatch.setenv("NO_COLOR", "1")
    for name in ("FORCE_COLOR", "PYTHON_COLORS"):
        monkeypatch.delenv(name, raising=False)


def run(capsys: pytest.CaptureFixture[str], *args: str) -> tuple[int, str, str]:
    code = main(list(args))
    out, err = capsys.readouterr()
    return code, out, err


def usage_error(capsys: pytest.CaptureFixture[str], *args: str) -> tuple[object, str, str]:
    with pytest.raises(SystemExit) as exc:
        main(list(args))
    out, err = capsys.readouterr()
    return exc.value.code, out, err


def test_program_name_is_mimeatlas() -> None:
    assert _parser().prog == "mimeatlas"


def test_full_usage_line() -> None:
    stream = io.StringIO()
    _parser().print_usage(stream)
    assert stream.getvalue() == TOP_USAGE


def test_help_starts_with_the_usage_line(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, err = usage_error(capsys, "--help")
    assert code == 0 and err == "" and out.startswith(TOP_USAGE)


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        ([], TOP_USAGE + "mimeatlas: error: invalid arguments; use --help\n"),
        (["bogus"], TOP_USAGE + "mimeatlas: error: invalid choice; use --help\n"),
        (["type", "--nope", "a"], TOP_USAGE + "mimeatlas: error: invalid arguments; use --help\n"),
        (["source", "x"], TOP_USAGE + "mimeatlas: error: invalid arguments; use --help\n"),
        (["type"], TYPE_USAGE + "mimeatlas type: error: invalid arguments; use --help\n"),
        (
            ["type", "--content-type", "--encoding", "a"],
            TYPE_USAGE + "mimeatlas type: error: invalid arguments; use --help\n",
        ),
        (
            ["ext"],
            "usage: mimeatlas ext [-h] [--preferred] TYPE [TYPE ...]\n"
            "mimeatlas ext: error: invalid arguments; use --help\n",
        ),
        (
            ["info"],
            "usage: mimeatlas info [-h] [--json] TYPE\n"
            "mimeatlas info: error: invalid arguments; use --help\n",
        ),
        (
            ["sniff"],
            "usage: mimeatlas sniff [-h] FILE [FILE ...]\n"
            "mimeatlas sniff: error: invalid arguments; use --help\n",
        ),
    ],
)
def test_usage_errors_are_exact(
    capsys: pytest.CaptureFixture[str], args: list[str], expected: str
) -> None:
    assert usage_error(capsys, *args) == (1, "", expected)


def test_unknown_path_message_is_exact(capsys: pytest.CaptureFixture[str]) -> None:
    expected = "mimeatlas: no MIME type known for input 2\n"
    assert run(capsys, "type", "a.png", "x.unknownext") == (1, "a.png\timage/png\n", expected)
    expected = "mimeatlas: no MIME type known for input 1\n"
    assert run(capsys, "type", "--encoding", "x.unknownext") == (1, "", expected)


def test_unknown_type_message_is_exact(capsys: pytest.CaptureFixture[str]) -> None:
    expected = "mimeatlas: no extension known for input 1\n"
    assert run(capsys, "ext", "application/x-nope") == (1, "", expected)
    assert run(capsys, "ext", "--preferred", "application/x-nope") == (1, "", expected)


def test_info_message_is_exact(capsys: pytest.CaptureFixture[str]) -> None:
    expected = "mimeatlas: unknown MIME type for input 1\n"
    assert run(capsys, "info", "application/x-nope") == (1, "", expected)


def test_sniff_messages_are_exact(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    text = tmp_path / "notes.dat"
    text.write_bytes(b"just text")
    missing = str(tmp_path / "missing.bin")
    expected = "mimeatlas: unrecognised content for input 1\nmimeatlas: cannot read input 2\n"
    assert run(capsys, "sniff", str(text), missing) == (1, "", expected)
    assert run(capsys, "sniff", missing) == (1, "", "mimeatlas: cannot read input 1\n")


def test_sniff_reports_unopenable_names_as_unreadable(capsys: pytest.CaptureFixture[str]) -> None:
    # open() raises ValueError, not OSError, for a name with an embedded NUL.
    assert run(capsys, "sniff", "a\x00b") == (1, "", "mimeatlas: cannot read input 1\n")


def test_sniff_reads_a_full_sixteen_byte_signature_from_a_file(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    # The SQLite signature fills the whole sniff window (16 bytes), so a short read would miss it.
    db = tmp_path / "x.sqlite"
    db.write_bytes(b"SQLite format 3\x00" + bytes(100))
    assert run(capsys, "sniff", str(db)) == (0, "application/vnd.sqlite3\n", "")
