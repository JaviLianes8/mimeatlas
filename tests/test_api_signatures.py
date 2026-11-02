"""Stable keyword argument names, defaults and result field layouts."""

from __future__ import annotations

import dataclasses
import inspect

import mimeguess as m


def test_lookup_parameter_names_and_defaults() -> None:
    parameters = {
        "guess_type": "path",
        "guess": "path",
        "content_type_for": "path",
        "guess_extension": "mime",
        "extensions_for": "mime",
        "media_type_info": "mime",
        "default_charset": "mime",
        "is_textual": "mime",
        "is_compressible": "mime",
        "structured_suffix": "mime",
        "type_for_extension": "ext",
        "essence": "value",
        "sniff": "data",
    }
    for name, argument in parameters.items():
        signature = inspect.signature(getattr(m, name))
        assert list(signature.parameters) == [argument]
        parameter = signature.parameters[argument]
        assert parameter.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
        assert parameter.default is inspect.Parameter.empty
        if hasattr(m.MimeTable, name):
            method = inspect.signature(getattr(m.MimeTable, name))
            assert list(method.parameters) == ["self", argument]
    for name in ("data_source", "default_table", "known_types", "known_extensions"):
        assert list(inspect.signature(getattr(m, name)).parameters) == []
    assert list(inspect.signature(m.MimeTable.with_types).parameters) == ["self", "mapping"]


def test_result_constructors_keep_the_field_order_and_no_defaults() -> None:
    expected = {
        m.Guess: ("type", "encoding", "extension"),
        m.MediaTypeInfo: ("type", "source", "extensions", "charset", "compressible", "suffix"),
        m.SourceInfo: (
            "name",
            "version",
            "url",
            "sha256",
            "retrieved",
            "license",
            "type_count",
            "extension_count",
        ),
    }
    for cls, names in expected.items():
        fields = dataclasses.fields(cls)
        assert tuple(field.name for field in fields) == names
        assert all(field.default is dataclasses.MISSING for field in fields)
        assert all(field.default_factory is dataclasses.MISSING for field in fields)
