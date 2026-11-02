"""Read-only MIME metadata queries shared by tables."""

from __future__ import annotations

from collections.abc import Mapping
from typing import NamedTuple

from ._mediatype import lenient_essence, real_charset, structured_suffix, textual
from ._models import MediaTypeInfo, Source


class Entry(NamedTuple):
    """Internal row: one MIME type and what the table knows about it."""

    source: Source
    charset: str | None
    compressible: bool | None
    extensions: tuple[str, ...]  # lowercase, no leading dot, preferred first


class _TableInfo:
    __slots__ = ()
    _types: Mapping[str, Entry]
    _extensions: Mapping[str, str]

    def extensions_for(self, mime: str) -> tuple[str, ...]:
        """Return every extension of a type with a leading dot, preferred first.

        Parameters and case are ignored. Returns an empty tuple when the type is
        unknown, malformed, or has no extensions.

        >>> import mimeguess as m
        >>> m.default_table().extensions_for("image/jpeg")
        ('.jpg', '.jpeg', '.jpe')
        """
        entry = self._entry(mime)
        return () if entry is None else tuple("." + ext for ext in entry.extensions)

    def guess_extension(self, mime: str) -> str | None:
        """Return the preferred extension of a type with a leading dot, or ``None``.

        >>> import mimeguess as m
        >>> m.default_table().guess_extension("image/jpeg")
        '.jpg'
        """
        exts = self.extensions_for(mime)
        return exts[0] if exts else None

    def media_type_info(self, mime: str) -> MediaTypeInfo | None:
        """Return everything known about a type, or ``None`` when it is unknown.

        >>> import mimeguess as m
        >>> m.default_table().media_type_info("image/png").type
        'image/png'
        """
        key = lenient_essence(mime)
        entry = None if key is None else self._types.get(key)
        if key is None or entry is None:
            return None
        return MediaTypeInfo(
            type=key,
            source=entry.source,
            extensions=tuple("." + ext for ext in entry.extensions),
            charset=real_charset(entry.charset),
            compressible=entry.compressible,
            suffix=structured_suffix(key),
        )

    def default_charset(self, mime: str) -> str | None:
        """Return the default charset for a type, lowercase, or ``None``.

        The charset the source data declares wins (``application/json`` gives
        ``"utf-8"``); otherwise any ``text/*`` type gets ``"utf-8"``, as in
        jshttp mime-types. Other types give ``None``. Unlike mime-types, the
        source annotations ``7-BIT`` and ``XML-BASED`` are not charsets and are
        never returned.

        >>> import mimeguess as m
        >>> m.default_table().default_charset("text/plain")
        'utf-8'
        """
        key = lenient_essence(mime)
        if key is None:
            return None
        entry = self._types.get(key)
        declared = None if entry is None else real_charset(entry.charset)
        if declared is not None:
            return declared
        return "utf-8" if key.startswith("text/") else None

    def is_textual(self, mime: str) -> bool:
        """Return whether a type carries text: ``text/*``, a type with a declared
        charset, or a ``+json``, ``+xml``, ``+yaml`` or ``+json-seq`` suffix.

        >>> import mimeguess as m
        >>> m.default_table().is_textual("application/ld+json")
        True
        """
        key = lenient_essence(mime)
        if key is None:
            return False
        entry = self._types.get(key)
        return textual(key, None if entry is None else real_charset(entry.charset))

    def is_compressible(self, mime: str) -> bool | None:
        """Return whether a type usually compresses well, ``None`` when unknown.

        >>> import mimeguess as m
        >>> m.default_table().is_compressible("image/png")
        False
        """
        entry = self._entry(mime)
        return None if entry is None else entry.compressible

    def known_types(self) -> tuple[str, ...]:
        """Return every MIME type in the table, sorted.

        >>> import mimeguess as m
        >>> "application/pdf" in m.default_table().known_types()
        True
        """
        return tuple(sorted(self._types))

    def known_extensions(self) -> tuple[str, ...]:
        """Return every extension the table resolves, with a leading dot, sorted.

        >>> import mimeguess as m
        >>> ".pdf" in m.default_table().known_extensions()
        True
        """
        return tuple(sorted("." + ext for ext in self._extensions))

    def _entry(self, mime: str) -> Entry | None:
        key = lenient_essence(mime)
        return None if key is None else self._types.get(key)
