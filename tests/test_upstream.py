"""Live-fetched sources, with URLs and checksums in data/MANIFEST.json."""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
import shutil
import string
import subprocess
import sys
from pathlib import Path

import pytest

import mimeguess as m

ROOT = Path(__file__).resolve().parents[1]
FOLDER = Path(os.environ.get("MIMEGUESS_DATA_DIR", str(ROOT / "data")))


def fetched(name: str) -> bytes:
    path = FOLDER / name
    if not path.exists():
        pytest.skip("upstream file absent; run scripts/fetch_upstream.py")
    entry = json.loads((ROOT / "data" / "MANIFEST.json").read_text(encoding="utf-8"))[name]
    data = path.read_bytes()
    assert len(data) == entry["size"]
    assert hashlib.sha256(data).hexdigest() == entry["sha256"]
    return data


def test_rfc9110_token_characters_from_fetched_abnf() -> None:
    text = fetched("rfc9110.txt").decode()
    rule = re.search(r"   tchar = (.*?)\n   time-of-day", text, re.DOTALL)
    assert rule
    allowed = set(re.findall(r'"(.)"', rule[1])) | set(string.ascii_letters + string.digits)
    assert len(allowed) == 77
    for number in range(128):
        char = chr(number)
        # Inserting inside the token avoids the documented surrounding whitespace policy.
        text = "a" + char + "b/c"
        if char in allowed:
            assert m.essence(text) == text.lower()
        else:
            with pytest.raises(m.InvalidMediaType):
                m.essence(text)


def test_signatures_extracted_from_fetched_whatwg_tables() -> None:
    document = fetched("mimesniff.html").decode()
    supported = {
        "image/png",
        "image/jpeg",
        "image/gif",
        "image/webp",
        "application/pdf",
        "application/zip",
        "application/gzip",
        "application/vnd.rar",
        "audio/wave",
        "video/avi",
        "application/ogg",
        "font/woff",
        "font/woff2",
    }
    aliases = {"audio/wave": "audio/wav", "video/avi": "video/x-msvideo"}
    checked = set()
    for row in re.split(r"<tr\b[^>]*>", document):
        cells = re.split(r"<td\b[^>]*>", row)[1:]
        cells = [html.unescape(re.sub(r"<[^>]*>", "", c)).strip() for c in cells]
        if len(cells) < 4 or cells[3] not in supported:
            continue
        pattern = cells[0]
        if not re.fullmatch(r"[0-9A-F\s]+", pattern):
            continue
        signature = bytes.fromhex(pattern)
        assert m.sniff(signature) == aliases.get(cells[3], cells[3])
        checked.add(cells[3])
    assert {"image/png", "image/jpeg", "image/gif", "application/pdf", "application/zip"} <= checked


def test_every_extension_against_real_node_reference() -> None:
    fetched("mime-types-3.0.2.tgz")
    fetched("mime-db-1.54.0.tgz")
    if shutil.which("node") is None:
        pytest.skip("Node.js is absent")
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "reference_mime_types.py")],
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    reference = json.loads(result.stdout)
    differences = {
        ext: m.type_for_extension(ext)
        for ext, mime in reference["types"].items()
        if m.type_for_extension(ext) != mime
    }
    assert differences == {
        "flac": "audio/flac",
        "yaml": "application/yaml",
        "yml": "application/yaml",
    }
    golden = json.loads((ROOT / "tests/golden/mime-types-3.0.2-conflicts.json").read_text())
    assert golden == reference["conflicts"]
    assert len(reference["types"]) == 1239
