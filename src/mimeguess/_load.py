"""Loading the embedded table and its provenance."""

from __future__ import annotations

import functools
import gzip
import importlib.resources
import json
from typing import Any, cast, get_args

from . import _meta
from ._models import Source, SourceInfo
from ._table import MimeTable
from ._table_info import Entry

_SOURCES = frozenset(get_args(Source))


def _entry(mime: str, row: Any) -> Entry:
    source, charset, compressible, exts = row
    if source not in _SOURCES:
        raise RuntimeError(f"corrupt embedded table: bad source for {mime!r}")
    return Entry(cast(Source, source), charset, compressible, tuple(exts))


def load_raw() -> dict[str, Any]:
    """Return the decoded embedded table as stored in the package."""
    blob = importlib.resources.files("mimeguess").joinpath("_data.json.gz").read_bytes()
    return cast("dict[str, Any]", json.loads(gzip.decompress(blob)))


@functools.cache
def default_table() -> MimeTable:
    """Return the shared table loaded from the embedded derived data.

    It is loaded on first use and cached. The table is immutable, so sharing it
    is safe; use :meth:`MimeTable.with_types` to derive a customised copy.

    >>> import mimeguess as m
    >>> m.default_table() is m.default_table()
    True
    """
    raw = load_raw()
    types = {mime: _entry(mime, row) for mime, row in raw["types"].items()}
    return MimeTable(types, raw["extensions"])


def data_source() -> SourceInfo:
    """Return where the embedded table comes from and how big it is.

    The values describe the pinned, separately fetched snapshot used to generate
    the committed derived table. Its manifest records the source; these values give
    the upstream release, the exact URL it was fetched from, the SHA-256 of the
    fetched bytes, the retrieval date and the upstream license.

    >>> import mimeguess as m
    >>> m.data_source().version
    '1.54.0'
    """
    return SourceInfo(
        name=_meta.NAME,
        version=_meta.VERSION,
        url=_meta.URL,
        sha256=_meta.SHA256,
        retrieved=_meta.RETRIEVED,
        license=_meta.LICENSE,
        type_count=_meta.TYPE_COUNT,
        extension_count=_meta.EXTENSION_COUNT,
    )
