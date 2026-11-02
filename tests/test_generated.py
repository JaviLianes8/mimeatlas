"""The embedded table is exactly what the committed generator makes from the snapshot.

The mime-db snapshot is not committed: `python scripts/fetch_upstream.py` fetches it as
pinned in data/MANIFEST.json. The tests that read it skip until then.
"""

from __future__ import annotations

import gzip
import hashlib
import importlib.resources
import json
import sys
from pathlib import Path
from typing import Any

import pytest

import mimeguess
from mimeguess._load import load_raw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import _score  # noqa: E402
import _supplement  # noqa: E402
import generate_table  # noqa: E402

GOLDEN = ROOT / "tests" / "golden" / "mime-types-3.0.2-conflicts.json"
needs_snapshot = pytest.mark.skipif(
    not generate_table.SNAPSHOT.is_file(),
    reason="mime-db snapshot not fetched; run python scripts/fetch_upstream.py",
)


def _pure_build() -> dict[str, Any]:
    """Build from mime-db alone, with the hand-written supplement switched off."""
    result: dict[str, Any]
    saved = dict(_supplement.EXTRA_EXTENSIONS), dict(_supplement.PREFERRED_EXTENSION)
    _supplement.EXTRA_EXTENSIONS.clear()
    _supplement.PREFERRED_EXTENSION.clear()
    try:
        result = generate_table.build(json.loads(generate_table.snapshot_bytes()))
    finally:
        _supplement.EXTRA_EXTENSIONS.update(saved[0])
        _supplement.PREFERRED_EXTENSION.update(saved[1])
    return result


@needs_snapshot
def test_the_embedded_table_equals_the_generator_output() -> None:
    data, meta = generate_table.generate()
    package = importlib.resources.files("mimeguess")
    embedded = gzip.decompress(package.joinpath("_data.json.gz").read_bytes())
    assert embedded == data
    assert package.joinpath("_meta.py").read_text(encoding="utf-8") == meta


@needs_snapshot
@pytest.mark.skipif(not (ROOT / "src").is_dir(), reason="generator command needs a source checkout")
def test_the_generator_check_mode_passes() -> None:
    assert generate_table.main(["--check"]) == 0


@needs_snapshot
def test_the_snapshot_checksum_matches_the_recorded_provenance() -> None:
    digest = hashlib.sha256(generate_table.snapshot_bytes()).hexdigest()
    assert digest == mimeguess.data_source().sha256


def test_the_package_loads_the_same_table_it_ships() -> None:
    raw = load_raw()
    assert len(raw["types"]) == mimeguess.data_source().type_count
    assert len(raw["extensions"]) == mimeguess.data_source().extension_count
    assert len(mimeguess.known_types()) == len(raw["types"])
    assert len(mimeguess.known_extensions()) == len(raw["extensions"])


@needs_snapshot
def test_every_mime_db_type_and_extension_is_kept() -> None:
    db = json.loads(generate_table.snapshot_bytes())
    raw = load_raw()
    assert set(db) <= set(raw["types"])
    for mime, entry in db.items():
        assert set(entry.get("extensions", [])) <= set(raw["types"][mime][3])
        assert raw["types"][mime][:3] == [
            entry.get("source", "mime-db"),
            entry.get("charset"),
            entry.get("compressible"),
        ]


@needs_snapshot
def test_conflicts_resolve_exactly_like_mime_types_3_0_2() -> None:
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    db = json.loads(generate_table.snapshot_bytes())
    claims: dict[str, int] = {}
    for entry in db.values():
        for ext in entry.get("extensions", []):
            claims[ext] = claims.get(ext, 0) + 1
    assert set(golden) == {ext for ext, count in claims.items() if count > 1}
    assert {ext: _pure_build()["extensions"][ext] for ext in golden} == golden


@needs_snapshot
def test_the_supplement_moves_only_the_documented_extensions() -> None:
    pure = _pure_build()["extensions"]
    shipped = load_raw()["extensions"]
    moved = {ext for ext in pure if pure[ext] != shipped[ext]}
    assert moved == {"flac", "yaml", "yml"}
    added = set(shipped) - set(pure)
    assert added == {"cfg", "db", "py", "sqlite", "sqlite3", "zst"}


@needs_snapshot
def test_preferred_extension_reordering_only_reorders() -> None:
    pure = _pure_build()["types"]
    shipped = load_raw()["types"]
    for mime, ext in _supplement.PREFERRED_EXTENSION.items():
        assert sorted(pure[mime][3]) == sorted(shipped[mime][3])
        assert shipped[mime][3][0] == ext


def test_score_matches_the_published_examples() -> None:
    # Hand-written checks of the ported arithmetic.
    assert _score.mime_score("application/octet-stream", "iana") == 0
    assert _score.mime_score("video/mp4", "iana") > _score.mime_score("application/mp4", "iana")
    assert _score.mime_score("application/xml", "iana") > _score.mime_score("text/xml", "iana")
    assert _score.mime_score("image/bmp", "iana") > _score.mime_score("image/x-ms-bmp", "nginx")
