"""Hand-written path, provenance, CLI and normalized override contracts."""

from __future__ import annotations

import dataclasses
import json
import os
import subprocess
import sys
from collections.abc import Callable
from datetime import date
from pathlib import Path
from types import FrameType

import pytest

import mimeguess as m

_Trace = Callable[[FrameType, str, object], "_Trace | None"]


@pytest.mark.parametrize("path", [r"directory\.pdf", r"directory\...png", r"a/b\.gz"])
def test_backslash_separators_preserve_hidden_filename_rules(path: str) -> None:
    assert m.guess_type(path) is None
    assert m.guess(path) == m.Guess(None, None, None)
    assert m.content_type_for(path) is None


def _cli(*args: str) -> subprocess.CompletedProcess[str]:
    src = str(Path(__file__).resolve().parents[1] / "src")
    env = {**os.environ, "PYTHONPATH": "" if os.environ.get("MIMEGUESS_INSTALLED") else src}
    return subprocess.run(
        [sys.executable, "-m", "mimeguess", *args],
        capture_output=True,
        text=True,
        env=env,
        check=False,
        timeout=300,
    )


def test_unknown_info_identifies_its_input_without_echoing_it() -> None:
    result = _cli("info", "application/x-certification-unknown")
    assert result.returncode == 1 and result.stdout == ""
    assert result.stderr == "mimeguess: unknown MIME type for input 1\n"


def test_all_provenance_fields_reach_the_api_and_cli() -> None:
    expected = {
        "name": "mime-db",
        "version": "1.54.0",
        "url": "https://raw.githubusercontent.com/jshttp/mime-db/v1.54.0/db.json",
        "sha256": "96b8a5746867c832ab56743c05e46e73c9facb04879677df0b356f20496cb6cd",
        "retrieved": "2026-10-12",
        "license": "MIT",
        "type_count": 2524,
        "extension_count": 1245,
    }
    source = m.data_source()
    assert date.fromisoformat(source.retrieved) == date(2026, 10, 12)
    assert dataclasses.asdict(source) == expected
    result = _cli("source", "--json")
    assert result.returncode == 0 and result.stderr == ""
    assert json.loads(result.stdout) == expected
    result = _cli("source")
    assert result.returncode == 0 and result.stderr == ""
    assert result.stdout.splitlines() == [f"{key}: {value}" for key, value in expected.items()]


@pytest.mark.parametrize(
    ("mime", "compressible", "shown"),
    [
        ("text/plain", True, "True"),
        ("image/png", False, "False"),
        ("application/x-bcpio", None, "-"),
    ],
)
def test_cli_text_distinguishes_compressibility_states(
    mime: str,
    compressible: bool | None,
    shown: str,
) -> None:
    result = _cli("info", mime)
    assert result.returncode == 0 and result.stderr == ""
    assert f"compressible: {shown}" in result.stdout.splitlines()
    result = _cli("info", mime, "--json")
    assert result.returncode == 0 and result.stderr == ""
    assert json.loads(result.stdout)["compressible"] is compressible


def test_normalized_overrides_preserve_order_metadata_and_last_assignment() -> None:
    table = m.default_table().with_types(
        {
            "IMAGE/PNG": ["a", "b", "png"],
            "text/x-test": ["b", "c"],
            " Image/Png ": ["c", "a", "C"],
        }
    )
    assert table.extensions_for("image/png") == (".c", ".a", ".b", ".png")
    assert table.extensions_for("text/x-test") == (".b", ".c")
    assert table.type_for_extension("b") == "text/x-test"
    assert table.type_for_extension("c") == "image/png"
    assert table.media_type_info("image/png") == m.MediaTypeInfo(
        "image/png",
        "iana",
        (".c", ".a", ".b", ".png"),
        None,
        False,
        None,
    )
    assert m.extensions_for("image/png") == (".png",)


def test_normalized_override_work_scales_with_input_size() -> None:
    base = m.default_table()
    package = str(Path(m.__file__).parent)

    def work(size: int) -> int:
        stem = "abcdefghijklmnop"
        mapping = {
            "text/" + "".join(c.upper() if i & (1 << bit) else c for bit, c in enumerate(stem)): [
                f"qa{i:05}"
            ]
            for i in range(size)
        }
        events = 0

        def trace(frame: FrameType, event: str, arg: object) -> _Trace:
            nonlocal events
            if event == "line" and frame.f_code.co_filename.startswith(package):
                events += 1
            return trace

        previous = sys.gettrace()
        try:
            sys.settrace(trace)
            table = base.with_types(mapping)
        finally:
            sys.settrace(previous)
        assert table.extensions_for("text/" + stem) == tuple(
            f".qa{i:05}" for i in reversed(range(size))
        )
        return events

    small, large = work(256), work(1024)
    assert large < 6 * small, (small, large)
