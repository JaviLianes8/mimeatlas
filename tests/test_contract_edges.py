"""Error, value-object and boundary contracts beyond ordinary lookups."""

from __future__ import annotations

import dataclasses
import pickle
from array import array
from collections.abc import Callable
from typing import get_args, get_type_hints

import pytest

import mimeguess as m
from mimeguess._cli import main


def test_type_alias_and_public_identities() -> None:
    assert get_args(m.Source) == ("iana", "apache", "nginx", "mime-db", "supplement", "custom")
    for cls in (m.Guess, m.MediaTypeInfo, m.SourceInfo, m.MimeTable, m.InvalidMediaType):
        assert cls.__module__ == "mimeguess"
    for name in m.__all__:
        obj = getattr(m, name)
        if callable(obj) and name not in ("Source", "InvalidMediaType"):
            get_type_hints(obj)


def test_results_preserve_fields_and_pickle() -> None:
    values = [m.guess("a.tar.gz"), m.media_type_info("image/png"), m.data_source()]
    for value in values:
        assert pickle.loads(pickle.dumps(value)) == value
        assert value is not None
        with pytest.raises(dataclasses.FrozenInstanceError):
            setattr(value, "type", "changed")  # noqa: B010
    info = m.media_type_info("application/ld+json")
    assert info == m.MediaTypeInfo("application/ld+json", "iana", (".jsonld",), None, True, "json")


def test_override_deduplicates_preserves_metadata_and_conflicting_reverse_lists() -> None:
    table = m.default_table().with_types({" IMAGE/PNG ": [".ZZ", "zz", "png"]})
    assert table.extensions_for("image/png") == (".zz", ".png")
    assert table.media_type_info("image/png") == m.MediaTypeInfo(
        "image/png", "iana", (".zz", ".png"), None, False, None
    )
    table = table.with_types({"text/x-demo": ["zz"]})
    assert table.type_for_extension("zz") == "text/x-demo"
    assert table.extensions_for("image/png") == (".zz", ".png")
    assert table.with_types({}).known_types() == table.known_types()


@pytest.mark.parametrize("path", [".pdf", "...pdf", "a.pdf.", "a.pdf/", "a.pdf\\"])
def test_dotfiles_and_directories_are_not_extensions(path: str) -> None:
    assert m.guess_type(path) is None
    assert m.guess(path) == m.Guess(None, None, None)


def test_empty_segments_stop_compound_matching() -> None:
    table = m.default_table().with_types({"text/x-a": ["a.pdf"]})
    assert table.guess_type("x.a.pdf") == "text/x-a"
    assert table.guess_type("x.a..pdf") == "application/pdf"
    assert table.guess_type("x..a.pdf") == "text/x-a"
    assert m.guess("x.tar.gz.gz") == m.Guess("application/gzip", "gzip", "gz")


def test_suffix_matching_requires_a_dot_boundary() -> None:
    assert m.guess_type("file.notpdf") is None
    table = m.default_table().with_types({"text/x-demo": ["d.ts"]})
    assert table.guess_type("file.notd.ts") == "video/mp2t"


def test_non_string_paths_raise_type_error() -> None:
    for function in (m.guess, m.guess_type, m.content_type_for):
        with pytest.raises(TypeError, match="path must be a string"):
            function(None)  # type: ignore[arg-type]


def test_released_memoryviews_raise_value_error() -> None:
    view = memoryview(b"%PDF-")
    view.release()
    with pytest.raises(ValueError):
        m.sniff(view)


def test_errors_do_not_echo_input() -> None:
    secret = "credential-12345" * 10000
    calls: list[Callable[[], object]] = [
        lambda: m.essence(secret),
        lambda: m.default_table().with_types({secret: ["x"]}),
        lambda: m.default_table().with_types({"text/plain": [secret + "/"]}),
        lambda: m.default_table().with_types({"text/" + secret: []}),
        lambda: m.default_table().with_types({"text/" + secret: "abc"}),
    ]
    for call in calls:
        with pytest.raises(ValueError) as exc:
            call()
        assert len(str(exc.value)) < 100 and "credential" not in str(exc.value)


@pytest.mark.parametrize("command", ["type", "ext", "info", "sniff", "unknown"])
def test_cli_errors_do_not_echo_input(command: str, capsys: pytest.CaptureFixture[str]) -> None:
    secret = "credential-12345" * 1000
    try:
        code = main([command, secret])
    except SystemExit as exc:
        assert exc.code == 1
        code = 1
    assert code == 1
    out, err = capsys.readouterr()
    assert not out and "credential" not in err and len(err) < 500


def test_sniff_reads_raw_bytes_of_contiguous_views() -> None:
    data = bytearray(b"%PDF-1.7" + bytes(24))
    for view in (memoryview(data).cast("I"), memoryview(data).cast("B", (4, 8))):
        assert m.sniff(view) == "application/pdf"
    signed = array("b", [-119, 80, 78, 71, 13, 10, 26, 10])
    assert m.sniff(memoryview(signed)) == "image/png"
    interleaved = b"".join(bytes([c, 0]) for c in b"%PDF-")
    assert m.sniff(memoryview(interleaved)[::2]) == "application/pdf"
    with pytest.raises(TypeError):
        m.sniff(memoryview(data).cast("I")[::2])


def test_sniff_signature_boundaries() -> None:
    assert m.sniff(b"PK\x05\x06") == "application/zip"
    assert m.sniff(b"PK\x07\x08") == "application/zip"
    for digit in range(256):
        expected = "application/x-bzip2" if ord("1") <= digit <= ord("9") else None
        assert m.sniff(b"BZh" + bytes([digit])) == expected
    assert m.structured_suffix("a/b+c+d") == "d"
    assert m.structured_suffix("a/b+") is None
    assert m.is_textual("a/b+yaml") and m.is_textual("a/b+json-seq")
