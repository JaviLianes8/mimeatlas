"""MimeTable behaviour: lookups, compound extensions, overrides, immutability."""

from __future__ import annotations

import pytest

import mimeatlas
from mimeatlas import Guess, MimeTable, default_table


def test_default_table_is_shared_and_cached() -> None:
    assert default_table() is default_table()
    assert isinstance(default_table(), MimeTable)


def test_type_for_extension_accepts_dot_or_no_dot_any_case() -> None:
    for ext in ("pdf", ".pdf", ".PDF", "Pdf"):
        assert mimeatlas.type_for_extension(ext) == "application/pdf"


@pytest.mark.parametrize("ext", ["", ".", "a b", "a/b", "a\\b", "..gz", "tar..gz", "gz."])
def test_type_for_extension_rejects_malformed_values(ext: str) -> None:
    assert mimeatlas.type_for_extension(ext) is None


def test_extensions_for_lists_all_with_the_preferred_first() -> None:
    assert mimeatlas.extensions_for("image/jpeg") == (".jpg", ".jpeg", ".jpe")
    assert mimeatlas.extensions_for("AUDIO/MPEG; foo=bar")[0] == ".mp3"
    assert mimeatlas.extensions_for("application/x-nope") == ()
    assert mimeatlas.extensions_for("not a type") == ()


def test_registered_types_without_extensions_have_info_but_no_extension() -> None:
    info = mimeatlas.media_type_info("application/vnd.api+json")
    assert info is not None and info.source == "iana" and info.suffix == "json"
    assert info.extensions == () and info.preferred_extension is None
    assert mimeatlas.guess_extension("application/vnd.api+json") is None


def test_guess_splits_the_content_coding() -> None:
    assert mimeatlas.guess("site.tar.gz") == Guess("application/x-tar", "gzip", "tar")
    assert mimeatlas.guess("SITE.TGZ") == Guess("application/x-tar", "gzip", "tar")
    assert mimeatlas.guess("logo.svgz") == Guess("image/svg+xml", "gzip", "svg")
    assert mimeatlas.guess("data.json.zst") == Guess("application/json", "zstd", "json")
    assert mimeatlas.guess("dump.gz") == Guess(None, "gzip", None)
    assert mimeatlas.guess("report.pdf") == Guess("application/pdf", None, "pdf")
    assert mimeatlas.guess("Makefile") == Guess(None, None, None)


def test_guess_type_keeps_the_final_extension_rule() -> None:
    assert mimeatlas.guess_type("site.tar.gz") == "application/gzip"
    assert mimeatlas.guess_type("logo.svgz") == "image/svg+xml"


def test_guess_type_reads_short_archive_forms_as_their_long_form() -> None:
    assert mimeatlas.guess_type("site.tgz") == "application/gzip"
    assert mimeatlas.guess_type("site.TBZ2") == "application/x-bzip2"
    assert mimeatlas.guess_type("site.txz") == "application/x-xz"


def test_old_reverse_lookups_still_work() -> None:
    assert mimeatlas.guess_extension("application/x-sqlite3") == ".sqlite"
    assert mimeatlas.guess_type("app.sqlite") == "application/vnd.sqlite3"


def test_with_types_adds_compound_extensions_longest_first() -> None:
    table = default_table().with_types({"text/x-typescript": [".ts", "d.ts", "mts"]})
    assert table.guess_type("index.d.ts") == "text/x-typescript"
    assert table.guess_type("index.ts") == "text/x-typescript"
    assert table.guess("index.d.ts.gz") == Guess("text/x-typescript", "gzip", "d.ts")
    assert table.type_for_extension(".D.TS") == "text/x-typescript"
    assert table.extensions_for("text/x-typescript") == (".ts", ".d.ts", ".mts")
    info = table.media_type_info("text/x-typescript")
    assert info is not None and info.source == "custom"


def test_with_types_never_mutates_the_original() -> None:
    before = mimeatlas.guess_type("clip.ts")
    default_table().with_types({"text/x-typescript": ["ts"]})
    assert mimeatlas.guess_type("clip.ts") == before == "video/mp2t"


def test_with_types_prepends_to_an_existing_type() -> None:
    table = default_table().with_types({"image/jpeg": ["jfif"]})
    assert table.extensions_for("image/jpeg") == (".jfif", ".jpg", ".jpeg", ".jpe")
    assert table.guess_type("a.jfif") == "image/jpeg"
    info = table.media_type_info("image/jpeg")
    assert info is not None and info.source == "iana"


@pytest.mark.parametrize(
    "mapping",
    [
        {"text": ["x"]},
        {"text/plain; charset=utf-8": ["x"]},
        {"text/x-a": []},
        {"text/x-a": ["a/b"]},
        {"text/x-a": "abc"},
    ],
)
def test_with_types_rejects_bad_input(mapping: dict[str, list[str]]) -> None:
    with pytest.raises(ValueError):
        default_table().with_types(mapping)


def test_known_types_and_extensions_are_sorted_and_dotted() -> None:
    types = mimeatlas.known_types()
    exts = mimeatlas.known_extensions()
    assert list(types) == sorted(types) and "application/pdf" in types
    assert list(exts) == sorted(exts) and all(ext.startswith(".") for ext in exts)


def test_every_extension_resolves_to_a_type_that_lists_it() -> None:
    for ext in mimeatlas.known_extensions():
        mime = mimeatlas.type_for_extension(ext)
        assert mime is not None and ext in mimeatlas.extensions_for(mime)


def test_content_type_for_adds_charset_only_when_it_applies() -> None:
    assert mimeatlas.content_type_for("index.html") == "text/html; charset=utf-8"
    assert mimeatlas.content_type_for("data.json") == "application/json; charset=utf-8"
    assert mimeatlas.content_type_for("photo.png") == "image/png"
    assert mimeatlas.content_type_for("x.unknownext") is None


def test_charset_policy() -> None:
    assert mimeatlas.default_charset("text/csv") == "utf-8"
    assert mimeatlas.default_charset("application/json") == "utf-8"
    assert mimeatlas.default_charset("image/png") is None
    assert mimeatlas.default_charset("text/x-unknown-thing") == "utf-8"
    # mime-db annotates this type with "7-BIT", which is not a charset name.
    assert mimeatlas.default_charset("application/prs.cyn") is None
    assert mimeatlas.default_charset("garbage") is None


def test_compressible_flag() -> None:
    assert mimeatlas.is_compressible("text/html") is True
    assert mimeatlas.is_compressible("image/png") is False
    assert mimeatlas.is_compressible("application/x-nope") is None
