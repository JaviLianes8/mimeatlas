"""Cross-checks against the standard library and Apache httpd ``mime.types``.

The stdlib side uses ``mimetypes.MimeTypes(filenames=())``: an instance built
only from the tables compiled into Python. ``mimetypes.init(files=[])`` is not
used because it still reads the Windows registry and the host ``knownfiles``
(it appends the given files to them), so its answers vary per machine.

The Apache file is not committed: `python scripts/fetch_upstream.py` fetches it as pinned
in data/MANIFEST.json, and its tests skip until then.
"""

from __future__ import annotations

import hashlib
import json
import mimetypes
import os
from pathlib import Path

import pytest

import mimeguess

ROOT = Path(__file__).resolve().parents[1]
STDLIB = mimetypes.MimeTypes(filenames=(), strict=True)
STRICT = STDLIB.types_map[True]

# Hand-written: everyday extensions where both tables give the same answer on
# every supported Python (checked on 3.10.19, 3.11.5, 3.12.12, 3.13.2, 3.14.2).
AGREE = [
    *(".pdf", ".png", ".jpg", ".jpeg", ".gif", ".html", ".htm", ".css", ".json"),
    *(".txt", ".csv", ".svg", ".zip", ".tar", ".mp3", ".mp4", ".mpeg", ".mpg"),
    *(".mov", ".webm", ".ico", ".tif", ".tiff", ".doc", ".xls", ".ppt", ".py"),
    *(".sh", ".vcf", ".wasm", ".bin", ".md"),
]

# Hand-written: everyday extensions where the answers differ on purpose. The value
# is our answer; the stdlib answer depends on the Python version.
DIFFER = {
    ".xml": "application/xml",  # stdlib text/xml; mime-types prefers application/
    ".rtf": "application/rtf",  # stdlib 3.13+ text/rtf; same scoring rule
    ".wav": "audio/wav",  # stdlib audio/x-wav, or audio/vnd.wave on 3.14
    ".exe": "application/x-msdos-program",  # stdlib application/octet-stream
    ".c": "text/x-c",  # stdlib text/plain
    ".bat": "application/x-msdownload",  # stdlib text/plain
    ".mkv": "video/x-matroska",  # stdlib 3.14 video/matroska
}


@pytest.mark.parametrize("ext", AGREE)
def test_everyday_extensions_agree_with_the_standard_library(ext: str) -> None:
    if ext not in STRICT:
        pytest.skip(f"{ext} is not in this Python's built-in table")
    assert mimeguess.type_for_extension(ext) == STRICT[ext]


@pytest.mark.parametrize(("ext", "ours"), sorted(DIFFER.items()))
def test_documented_differences_are_ours_by_design(ext: str, ours: str) -> None:
    assert mimeguess.type_for_extension(ext) == ours


def test_most_shared_extensions_agree_with_the_standard_library() -> None:
    shared = [ext for ext in STRICT if mimeguess.type_for_extension(ext) is not None]
    agree = [ext for ext in shared if mimeguess.type_for_extension(ext) == STRICT[ext]]
    # Measured 0.76 to 0.81 on Python 3.10 to 3.14.
    assert len(shared) >= 120
    assert len(agree) / len(shared) >= 0.75


@pytest.mark.parametrize(
    "name", ["a.tar.gz", "a.tgz", "a.svgz", "a.tar.bz2", "a.tbz2", "a.txz", "a.gz", "a.br"]
)
def test_content_coding_matches_the_standard_library(name: str) -> None:
    std_type, std_encoding = STDLIB.guess_type(name, strict=True)
    ours = mimeguess.guess(name)
    assert ours.encoding == std_encoding
    assert ours.type == std_type


APACHE = (
    Path(os.environ.get("MIMEGUESS_DATA_DIR", str(ROOT / "data")))
    / "apache-httpd-mime.types-r1930012"
)
needs_apache = pytest.mark.skipif(
    not APACHE.is_file(), reason="Apache mime.types not fetched; run scripts/fetch_upstream.py"
)


def _apache() -> dict[str, list[str]]:
    table: dict[str, list[str]] = {}
    for line in APACHE.read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#"):
            mime, *exts = line.split()
            for ext in exts:
                table.setdefault(ext, []).append(mime)
    return table


@needs_apache
def test_the_apache_file_matches_the_manifest() -> None:
    entry = json.loads((ROOT / "data" / "MANIFEST.json").read_text(encoding="utf-8"))[APACHE.name]
    assert hashlib.sha256(APACHE.read_bytes()).hexdigest() == entry["sha256"]


@needs_apache
def test_every_apache_extension_is_known() -> None:
    apache = _apache()
    assert len(apache) > 900
    assert [ext for ext in apache if mimeguess.type_for_extension(ext) is None] == []


@needs_apache
def test_apache_disagreements_are_only_resolved_conflicts() -> None:
    golden = json.loads((ROOT / "tests" / "golden" / "mime-types-3.0.2-conflicts.json").read_text())
    explained = set(golden) | {"flac"}  # flac: see scripts/_supplement.py
    apache = _apache()
    differ = {
        ext
        for ext, types in apache.items()
        if len(types) == 1 and mimeguess.type_for_extension(ext) != types[0]
    }
    assert differ <= explained
    assert len(differ) == 22
