"""Module-level lookups backed by the default table."""

from __future__ import annotations

from ._load import default_table
from ._models import Guess, MediaTypeInfo


def guess_type(path: str) -> str | None:
    """Return the MIME type for a path from its extension, or None if unknown.

    The lookup uses the final extension (or a longer compound one when the
    table defines it), so ``"photo.tar.gz"`` is read as a gzip file. It never
    touches the host registry, so the result is the same on every operating
    system. See :func:`guess` to split off the content coding.

    >>> import mimeguess as m
    >>> m.guess_type("report.pdf")
    'application/pdf'
    """
    return default_table().guess_type(path)


def guess_extension(mime: str) -> str | None:
    """Return the preferred extension (with a leading dot) for a MIME type.

    Any parameters such as ``"; charset=utf-8"`` are ignored. Returns None when
    the type is not in the table or has no extension.

    >>> import mimeguess as m
    >>> m.guess_extension("image/jpeg")
    '.jpg'
    """
    return default_table().guess_extension(mime)


def guess(path: str) -> Guess:
    """Return the type, content coding and matched extension of a path.

    ``guess("site.tar.gz")`` is ``Guess("application/x-tar", "gzip", "tar")``.
    See :meth:`MimeTable.guess`.

    >>> import mimeguess as m
    >>> m.guess("site.tar.gz")
    Guess(type='application/x-tar', encoding='gzip', extension='tar')
    """
    return default_table().guess(path)


def type_for_extension(ext: str) -> str | None:
    """Return the MIME type for one extension, with or without a leading dot.

    ``type_for_extension(".PDF")`` is ``"application/pdf"``. Unknown or
    malformed extensions give ``None``.

    >>> type_for_extension(".PDF")
    'application/pdf'
    """
    return default_table().type_for_extension(ext)


def extensions_for(mime: str) -> tuple[str, ...]:
    """Return every extension of a type with a leading dot, preferred first.

    ``extensions_for("image/jpeg")`` is ``(".jpg", ".jpeg", ".jpe")``. Unknown
    types give an empty tuple.

    >>> import mimeguess as m
    >>> m.extensions_for("image/jpeg")
    ('.jpg', '.jpeg', '.jpe')
    """
    return default_table().extensions_for(mime)


def media_type_info(mime: str) -> MediaTypeInfo | None:
    """Return a :class:`MediaTypeInfo` for a type, or ``None`` when unknown.

    >>> import mimeguess as m
    >>> m.media_type_info("image/png").type
    'image/png'
    """
    return default_table().media_type_info(mime)


def default_charset(mime: str) -> str | None:
    """Return the default charset of a type (``"utf-8"`` for ``text/*``) or None.

    See :meth:`MimeTable.default_charset` for the exact policy.

    >>> import mimeguess as m
    >>> m.default_charset("text/plain")
    'utf-8'
    """
    return default_table().default_charset(mime)


def is_textual(mime: str) -> bool:
    """Return whether a type carries text. See :meth:`MimeTable.is_textual`.

    >>> import mimeguess as m
    >>> m.is_textual("application/ld+json")
    True
    """
    return default_table().is_textual(mime)


def is_compressible(mime: str) -> bool | None:
    """Return whether a type usually compresses well, or None when unknown.

    >>> import mimeguess as m
    >>> m.is_compressible("image/png")
    False
    """
    return default_table().is_compressible(mime)


def content_type_for(path: str) -> str | None:
    """Return a Content-Type value for a path, such as ``"text/html; charset=utf-8"``.

    >>> import mimeguess as m
    >>> m.content_type_for("index.html")
    'text/html; charset=utf-8'
    """
    return default_table().content_type_for(path)


def known_types() -> tuple[str, ...]:
    """Return every MIME type in the default table, sorted.

    >>> import mimeguess as m
    >>> "application/pdf" in m.known_types()
    True
    """
    return default_table().known_types()


def known_extensions() -> tuple[str, ...]:
    """Return every extension the default table resolves, with a leading dot, sorted.

    >>> import mimeguess as m
    >>> ".pdf" in m.known_extensions()
    True
    """
    return default_table().known_extensions()
