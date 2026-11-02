"""Typed results and errors returned by the public API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Source = Literal["iana", "apache", "nginx", "mime-db", "supplement", "custom"]
"""Where a type's definition comes from.

``iana``, ``apache`` and ``nginx`` are the upstream registries that mime-db
records; ``mime-db`` marks types that project defines itself; ``supplement``
marks the few hand-written additions shipped with this package; ``custom``
marks types added through :meth:`MimeTable.with_types`.
"""


class InvalidMediaType(ValueError):
    """Raised by :func:`essence` when a value is not a ``type/subtype`` token pair.

    >>> import mimeguess as m
    >>> isinstance(m.InvalidMediaType("invalid"), ValueError)
    True
    """


@dataclass(frozen=True)
class Guess:
    """The outcome of :func:`guess` for one path.

    Attributes:
        type: The MIME type of the content, or ``None`` when unknown.
        encoding: The content coding implied by a trailing compression
            extension (``"gzip"`` for ``.gz``), or ``None``.
        extension: The table extension that produced ``type``, without a
            leading dot (``"tar"`` for ``backup.tar.gz``), or ``None``.

    >>> import mimeguess as m
    >>> m.Guess("application/pdf", None, "pdf").extension
    'pdf'
    """

    type: str | None
    encoding: str | None
    extension: str | None


@dataclass(frozen=True)
class MediaTypeInfo:
    """Everything the table knows about one MIME type.

    Attributes:
        type: The lowercase ``type/subtype`` essence.
        source: Where the definition comes from, see :data:`Source`.
        extensions: Extensions with a leading dot, preferred first. May be empty
            for registered types that have no conventional extension.
        charset: The default charset declared for the type (lowercase), or
            ``None``. See :func:`default_charset` for the text fallback.
        compressible: Whether the content usually compresses well, ``None``
            when the source data does not say.
        suffix: The structured syntax suffix (``"json"`` for ``+json``) or ``None``.

    >>> import mimeguess as m
    >>> m.MediaTypeInfo("image/png", "custom", (".png",), None, False, None).preferred_extension
    '.png'
    """

    type: str
    source: Source
    extensions: tuple[str, ...]
    charset: str | None
    compressible: bool | None
    suffix: str | None

    @property
    def preferred_extension(self) -> str | None:
        """The first extension, the one :func:`guess_extension` returns.

        >>> import mimeguess as m
        >>> m.media_type_info("image/png").preferred_extension
        '.png'
        """
        return self.extensions[0] if self.extensions else None


@dataclass(frozen=True)
class SourceInfo:
    """Provenance of the embedded table, see :func:`data_source`.

    Attributes:
        name: Upstream data set name (``"mime-db"``).
        version: Upstream release the snapshot was taken from.
        url: The exact URL the snapshot was fetched from.
        sha256: Checksum of the fetched bytes.
        retrieved: ISO date the snapshot was fetched.
        license: License of the upstream data.
        type_count: Number of MIME types in the embedded table.
        extension_count: Number of extensions in the embedded table.

    >>> import mimeguess as m
    >>> isinstance(m.data_source(), m.SourceInfo)
    True
    """

    name: str
    version: str
    url: str
    sha256: str
    retrieved: str
    license: str
    type_count: int
    extension_count: int
