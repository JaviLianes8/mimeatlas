"""The command line tool, driven in process through ``main``."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import mimeguess
from mimeguess._cli import main


def run(capsys: pytest.CaptureFixture[str], *args: str) -> tuple[int, str, str]:
    code = main(list(args))
    out, err = capsys.readouterr()
    return code, out, err


def test_type_of_one_path_prints_only_the_type(capsys: pytest.CaptureFixture[str]) -> None:
    assert run(capsys, "type", "report.pdf") == (0, "application/pdf\n", "")


def test_type_of_several_paths_prefixes_each_line(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = run(capsys, "type", "a.png", "b.css")
    assert code == 0 and out == "a.png\timage/png\nb.css\ttext/css\n"


def test_unknown_inputs_go_to_stderr_with_exit_one(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, err = run(capsys, "type", "a.png", "x.unknownext")
    assert code == 1 and out == "a.png\timage/png\n"
    assert "no MIME type known for input 2" in err


def test_content_type_and_encoding_modes(capsys: pytest.CaptureFixture[str]) -> None:
    assert run(capsys, "type", "--content-type", "i.html")[1] == "text/html; charset=utf-8\n"
    assert run(capsys, "type", "--encoding", "s.tar.gz")[1] == "application/x-tar\tgzip\n"
    assert run(capsys, "type", "--encoding", "dump.gz")[1] == "-\tgzip\n"
    assert run(capsys, "type", "--encoding", "a.pdf")[1] == "application/pdf\t-\n"


def test_ext_lists_extensions(capsys: pytest.CaptureFixture[str]) -> None:
    assert run(capsys, "ext", "image/jpeg")[1] == ".jpg .jpeg .jpe\n"
    assert run(capsys, "ext", "--preferred", "audio/mpeg")[1] == ".mp3\n"
    code, _, err = run(capsys, "ext", "application/x-nope")
    assert code == 1 and "no extension known for input 1" in err


def test_info_text_and_json(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = run(capsys, "info", "application/ld+json")
    assert code == 0 and "suffix: json" in out and "extensions: .jsonld" in out
    code, out, _ = run(capsys, "info", "--json", "application/json")
    data = json.loads(out)
    assert data["charset"] == "utf-8" and data["preferred_extension"] == ".json"
    code, _, err = run(capsys, "info", "application/x-nope")
    assert code == 1 and "unknown MIME type" in err


def test_sniff_reads_real_files(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    png = tmp_path / "picture.dat"
    png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 40)
    assert run(capsys, "sniff", str(png)) == (0, "image/png\n", "")
    text = tmp_path / "notes.dat"
    text.write_bytes(b"just text")
    code, _, err = run(capsys, "sniff", str(text))
    assert code == 1 and "unrecognised" in err
    code, _, err = run(capsys, "sniff", str(tmp_path / "missing.bin"))
    assert code == 1 and "cannot read" in err


def test_source_reports_provenance(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = run(capsys, "source", "--json")
    data = json.loads(out)
    assert code == 0 and data["name"] == "mime-db" and data["license"] == "MIT"
    assert "version: 1.54.0" in run(capsys, "source")[1]


def test_version_flag(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert capsys.readouterr().out.strip() == f"mimeguess {mimeguess.__version__}"


@pytest.mark.parametrize("args", [[], ["bogus"], ["type"], ["type", "--nope", "a"]])
def test_usage_errors_exit_one_on_stderr(
    capsys: pytest.CaptureFixture[str], args: list[str]
) -> None:
    with pytest.raises(SystemExit) as exc:
        main(args)
    out, err = capsys.readouterr()
    assert exc.value.code == 1 and out == "" and "error" in err


def test_unprintable_names_do_not_crash_a_narrow_console() -> None:
    src = str(Path(__file__).resolve().parents[1] / "src")
    search_path = "" if os.environ.get("MIMEGUESS_INSTALLED") else src
    env = {**os.environ, "PYTHONIOENCODING": "ascii", "PYTHONPATH": search_path}
    command = [sys.executable, "-m", "mimeguess", "type", "a.png", "\u0436.png"]
    result = subprocess.run(command, capture_output=True, env=env, check=False, timeout=60)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines()[1] == rb"\u0436.png" + b"\timage/png"


def test_help_shows_runnable_examples(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        main(["--help"])
    out = capsys.readouterr().out
    assert "examples:" in out and "mimeguess type report.pdf" in out
