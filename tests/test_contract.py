"""The complete public promise of mimeguess, one assertion group per promise."""

from __future__ import annotations

import dataclasses
import importlib.resources
import os
import sys
from pathlib import Path
from typing import Any

import pytest

import mimeguess

ROOT = Path(__file__).resolve().parents[1]


def _project() -> dict[str, Any]:
    tomllib = pytest.importorskip("tomllib" if sys.version_info >= (3, 11) else "tomli")
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    project: dict[str, Any] = tomllib.loads(text)["project"]
    return project


# The public API. This list is the contract; the test below fails if the module
# and this list disagree.
PUBLIC_API: list[str] = [
    "Guess",
    "InvalidMediaType",
    "MediaTypeInfo",
    "MimeTable",
    "Source",
    "SourceInfo",
    "content_type_for",
    "data_source",
    "default_charset",
    "default_table",
    "essence",
    "extensions_for",
    "guess",
    "guess_extension",
    "guess_type",
    "is_compressible",
    "is_textual",
    "known_extensions",
    "known_types",
    "media_type_info",
    "sniff",
    "structured_suffix",
    "type_for_extension",
]


def test_all_lists_exactly_the_public_api() -> None:
    assert sorted(mimeguess.__all__) == sorted(PUBLIC_API)
    assert {name for name in vars(mimeguess) if not name.startswith("_")} == set(PUBLIC_API)


def test_every_exported_name_resolves_and_is_documented() -> None:
    for name in mimeguess.__all__:
        obj = getattr(mimeguess, name)
        if name != "Source":
            assert obj.__doc__ and obj.__doc__.strip(), name


def test_version_is_a_three_part_string_matching_the_project() -> None:
    parts = mimeguess.__version__.split(".")
    assert len(parts) == 3 and all(part.isdigit() for part in parts)
    project = _project()
    assert project["version"] == mimeguess.__version__
    assert project["scripts"]["mimeguess"] == "mimeguess._cli:main"


def test_the_package_ships_type_information_and_its_table() -> None:
    files = importlib.resources.files("mimeguess")
    assert files.joinpath("py.typed").is_file()
    assert files.joinpath("_data.json.gz").is_file()
    if os.environ.get("MIMEGUESS_INSTALLED"):
        assert "site-packages" in str(files)


def test_results_are_frozen_dataclasses() -> None:
    for cls in (mimeguess.Guess, mimeguess.MediaTypeInfo, mimeguess.SourceInfo):
        assert dataclasses.is_dataclass(cls)
        params = getattr(cls, "__dataclass_params__")  # noqa: B009
        assert params.frozen


def test_lookups_never_raise_on_bad_input_and_return_none_or_empty() -> None:
    for bad in ("", "nonsense", "a/b/c", ";", " "):
        assert mimeguess.guess_type(bad) is None
        assert mimeguess.guess_extension(bad) is None
        assert mimeguess.type_for_extension(bad) is None
        assert mimeguess.extensions_for(bad) == ()
        assert mimeguess.media_type_info(bad) is None
        assert mimeguess.default_charset(bad) is None
        assert mimeguess.is_compressible(bad) is None
        assert mimeguess.is_textual(bad) is False
        assert mimeguess.structured_suffix(bad) is None
        assert mimeguess.content_type_for(bad) is None
        assert mimeguess.guess(bad) == mimeguess.Guess(None, None, None)


def test_only_essence_raises_and_only_invalid_media_type() -> None:
    with pytest.raises(mimeguess.InvalidMediaType):
        mimeguess.essence("nonsense")
    assert mimeguess.essence("A/B") == "a/b"


def test_lookups_are_case_insensitive_everywhere() -> None:
    assert mimeguess.guess_type("A.PDF") == mimeguess.guess_type("a.pdf")
    assert mimeguess.guess("A.TAR.GZ") == mimeguess.guess("a.tar.gz")
    assert mimeguess.extensions_for("IMAGE/PNG") == mimeguess.extensions_for("image/png")
    assert mimeguess.media_type_info("Text/Html") == mimeguess.media_type_info("text/html")


def test_round_trip_for_every_type_with_extensions() -> None:
    for mime in mimeguess.known_types():
        exts = mimeguess.extensions_for(mime)
        assert mimeguess.guess_extension(mime) == (exts[0] if exts else None)
        info = mimeguess.media_type_info(mime)
        assert info is not None and info.type == mime and info.extensions == exts


def test_every_type_has_a_known_source() -> None:
    allowed = {"iana", "apache", "nginx", "mime-db", "supplement"}
    for mime in mimeguess.known_types():
        info = mimeguess.media_type_info(mime)
        assert info is not None and info.source in allowed


def test_data_source_describes_the_snapshot() -> None:
    info = mimeguess.data_source()
    assert (info.name, info.version, info.license) == ("mime-db", "1.54.0", "MIT")
    assert info.url.startswith("https://") and len(info.sha256) == 64
    assert info.type_count > 2500 and info.extension_count > 1200


def test_results_do_not_depend_on_the_host_registry() -> None:
    import mimetypes

    before = [mimeguess.guess_type(name) for name in ("a.pdf", "a.xml", "a.ts")]
    mimetypes.add_type("application/x-host-override", ".pdf")
    try:
        after = [mimeguess.guess_type(name) for name in ("a.pdf", "a.xml", "a.ts")]
    finally:
        mimetypes.init()
    assert before == after == ["application/pdf", "application/xml", "video/mp2t"]


def test_license_notices_for_the_data_ship_with_the_project() -> None:
    project = _project()
    assert "LICENSES/mime-db.txt" in project["license-files"]
    assert "LICENSES/mime-types.txt" in project["license-files"]
