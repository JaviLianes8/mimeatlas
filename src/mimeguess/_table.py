"""The MimeTable: an immutable extension and MIME type lookup table."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Iterable, Mapping
from types import MappingProxyType

from ._mediatype import lenient_essence
from ._models import Guess
from ._paths import expand_alias, normalize_extension, segments, split_encoding
from ._table_info import Entry, _TableInfo


class MimeTable(_TableInfo):
    """An immutable mapping between file extensions and MIME types.

    The package-level functions use :func:`default_table`. Build a variant with
    :meth:`with_types` to add or override mappings without touching any global
    state. Lookups are case-insensitive and never consult the operating system.

    Obtain tables from :func:`default_table` and :meth:`with_types`; the
    constructor is internal and its arguments may change.

    >>> import mimeguess as m
    >>> isinstance(m.default_table(), m.MimeTable)
    True
    """

    __slots__ = ("_extensions", "_lengths", "_types")

    def __init__(self, types: Mapping[str, Entry], extensions: Mapping[str, str]) -> None:
        self._types = MappingProxyType(dict(types))
        self._extensions = MappingProxyType(dict(extensions))
        self._lengths = tuple(sorted({len(ext) for ext in self._extensions}, reverse=True))

    def with_types(self, mapping: Mapping[str, Iterable[str]]) -> MimeTable:
        """Return a new table where the given extensions map to the given types.

        ``mapping`` maps a MIME type to its extensions, preferred first; leading
        dots are optional and compound extensions such as ``"d.ts"`` are allowed::

            table = default_table().with_types({"text/x-typescript": ["ts", "d.ts"]})

        Each listed extension now resolves to its new type and goes to the front
        of that type's list (the first becomes its preferred extension), before
        any extensions it already had. Other types keep their lists unchanged.

        Raises:
            ValueError: on a malformed type or extension, or an empty list.

        >>> import mimeguess as m
        >>> m.default_table().with_types({"text/x-demo": ["demo"]}).guess_type("a.demo")
        'text/x-demo'
        """
        types = dict(self._types)
        extensions = dict(self._extensions)
        updates: dict[str, OrderedDict[str, None]] = {}
        for mime, exts in mapping.items():
            key = lenient_essence(mime)
            if key is None or key != str.strip(mime).lower():
                raise ValueError("not a bare type/subtype media type")
            if isinstance(exts, str):
                raise ValueError("extensions must be an iterable of strings, not a string")
            new = list(dict.fromkeys(normalize_extension(ext) for ext in exts))
            if not new:
                raise ValueError("no extensions given")
            if key not in updates:
                old = types.get(key, Entry("custom", None, None, ()))
                updates[key] = OrderedDict.fromkeys(old.extensions)
            ordered = updates[key]
            # Move only this batch, so normalized aliases never rescan prior batches.
            for ext in reversed(new):
                ordered[ext] = None
                ordered.move_to_end(ext, last=False)
            for ext in new:
                extensions[ext] = key
        for key, ordered in updates.items():
            old = types.get(key, Entry("custom", None, None, ()))
            types[key] = old._replace(extensions=tuple(ordered))
        return MimeTable(types, extensions)

    def type_for_extension(self, ext: str) -> str | None:
        """Return the MIME type for an extension such as ``"pdf"`` or ``".tar.gz"``.

        The whole value is one extension; it is not split. Returns ``None`` when
        the extension is unknown or malformed.

        >>> from mimeguess import default_table
        >>> default_table().type_for_extension(".PDF")
        'application/pdf'
        """
        try:
            key = normalize_extension(ext)
        except ValueError:
            return None
        return self._extensions.get(key)

    def _lookup(self, parts: list[str]) -> tuple[str, str] | tuple[None, None]:
        name = ".".join(parts)
        # Candidate work is bounded by the stored extension lengths, even when
        # a custom extension contains thousands of dots.
        for length in self._lengths:
            start = len(name) - length
            if start < 0 or (start and name[start - 1] != "."):
                continue
            ext = name[start:]
            mime = self._extensions.get(ext)
            if mime is not None:
                return mime, ext
        return None, None

    def guess_type(self, path: str) -> str | None:
        """Return the MIME type of a path from its extension, or ``None``.

        The longest dotted suffix the table knows wins, so with the default
        table ``backup.tar.gz`` is ``application/gzip``. Short forms the table
        does not list are read as their long form, so ``backup.tgz`` is also
        ``application/gzip``. Use :meth:`guess` to separate the content coding.

        >>> import mimeguess as m
        >>> m.default_table().guess_type("report.pdf")
        'application/pdf'
        """
        parts = segments(path)
        mime = self._lookup(parts)[0]
        return mime if mime is not None else self._lookup(expand_alias(parts))[0]

    def guess(self, path: str) -> Guess:
        """Return the type, content coding and matched extension of a path.

        A trailing compression extension becomes the encoding, following the
        standard library rules: ``a.tar.gz`` is ``application/x-tar`` with
        encoding ``gzip``, ``a.tgz`` is the same, and a lone ``a.gz`` has encoding
        ``gzip`` and no type.

        >>> import mimeguess as m
        >>> m.default_table().guess("site.tar.gz")
        Guess(type='application/x-tar', encoding='gzip', extension='tar')
        """
        parts, encoding = split_encoding(segments(path))
        mime, ext = self._lookup(parts)
        return Guess(type=mime, encoding=encoding, extension=ext)

    def content_type_for(self, path: str) -> str | None:
        """Return a Content-Type value for a path, with a charset when one applies.

        ``index.html`` gives ``"text/html; charset=utf-8"`` and ``photo.png``
        gives ``"image/png"``. Returns ``None`` when the type is unknown.

        >>> import mimeguess as m
        >>> m.default_table().content_type_for("index.html")
        'text/html; charset=utf-8'
        """
        mime = self.guess_type(path)
        if mime is None:
            return None
        charset = self.default_charset(mime)
        return mime if charset is None else f"{mime}; charset={charset}"
