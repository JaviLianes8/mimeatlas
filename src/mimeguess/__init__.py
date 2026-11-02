"""Deterministic, OS-independent extension and MIME type mapping from a vendored table.

The committed derived table is generated from a pinned, separately fetched snapshot
of jshttp mime-db (MIT), which merges the IANA registry, Apache httpd and nginx data.
Results never depend on the host operating system. See :func:`data_source` for provenance.

``Source`` is a Literal type alias for the six provenance labels:

>>> from typing import get_args
>>> get_args(Source)
('iana', 'apache', 'nginx', 'mime-db', 'supplement', 'custom')
"""

from __future__ import annotations

from ._guess import (
    content_type_for,
    default_charset,
    extensions_for,
    guess,
    guess_extension,
    guess_type,
    is_compressible,
    is_textual,
    known_extensions,
    known_types,
    media_type_info,
    type_for_extension,
)
from ._load import data_source, default_table
from ._mediatype import essence, structured_suffix
from ._models import Guess, InvalidMediaType, MediaTypeInfo, Source, SourceInfo
from ._sniff import sniff
from ._table import MimeTable

__version__ = "1.0.0"

__all__ = [
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

# Public identities keep pickles independent of the implementation module layout.
for _class in (Guess, InvalidMediaType, MediaTypeInfo, MimeTable, SourceInfo):
    _class.__module__ = __name__
del _class
del annotations
