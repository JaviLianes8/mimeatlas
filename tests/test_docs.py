"""Executable public documentation and examples."""

from __future__ import annotations

import doctest
import inspect
import re
from pathlib import Path

import pytest

import mimeguess


def test_all_public_docstrings_have_passing_examples() -> None:
    runner = doctest.DocTestRunner()
    parser = doctest.DocTestParser()
    objects: list[object] = [mimeguess]
    objects.extend(getattr(mimeguess, n) for n in mimeguess.__all__ if n != "Source")
    objects.extend(
        getattr(mimeguess.MimeTable, n) for n in dir(mimeguess.MimeTable) if not n.startswith("_")
    )
    objects.append(mimeguess.MediaTypeInfo.preferred_extension)
    for obj in objects:
        doc = inspect.getdoc(obj)
        assert doc and ">>>" in doc, obj
        test = parser.get_doctest(doc, vars(mimeguess).copy(), str(obj), "public", 0)
        runner.run(test)
    assert runner.summarize().failed == 0
    assert runner.tries >= 72


@pytest.mark.parametrize("name", ["README.md", "GUIDE.md"])
def test_markdown_examples_execute(
    name: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = Path(__file__).resolve().parents[1]
    content = (root / name).read_text(encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    (tmp_path / "report.pdf").write_bytes(b"%PDF-1.7\n")
    namespace: dict[str, object] = {}
    blocks = re.findall(r"```python\n(.*?)```", content, re.DOTALL)
    assert blocks
    for code in blocks:
        exec(compile(code, name, "exec"), namespace)
