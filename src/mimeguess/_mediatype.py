"""Light handling of MIME type strings: essence, structured suffixes, charsets."""

from __future__ import annotations

import re

from ._models import InvalidMediaType

# RFC 9110 section 5.6.2 token characters.
_TOKEN = r"[!#$%&'*+.^_`|~0-9A-Za-z-]+"
_ESSENCE = re.compile(rf"({_TOKEN})/({_TOKEN})")

# Charset labels from the source data that are real charsets. mime-db also uses
# the annotations "7-BIT" and "XML-BASED", which are not charset names.
_REAL_CHARSETS = frozenset({"utf-8", "us-ascii"})

# Structured syntax suffixes whose payload is text (RFC 6839, RFC 9512).
_TEXT_SUFFIXES = frozenset({"json", "xml", "yaml", "json-seq"})


def essence(value: str) -> str:
    """Return the lowercase ``type/subtype`` of a MIME type or Content-Type value.

    Parameters after ``;`` are dropped and surrounding whitespace is ignored::

        >>> essence("Text/HTML; charset=UTF-8")
        'text/html'

    This is deliberately light: it does not parse parameters. Use a full parser
    when you need them.

    Raises:
        InvalidMediaType: if the value is not two RFC 9110 tokens joined by ``/``.
    """
    key = lenient_essence(value)
    if key is None:
        raise InvalidMediaType("not a type/subtype media type")
    return key


def lenient_essence(value: str) -> str | None:
    """Like :func:`essence` but return ``None`` instead of raising."""
    if not isinstance(value, str):
        return None
    head = str.split(value, ";", 1)[0].strip()
    match = _ESSENCE.fullmatch(head)
    return head.lower() if match else None


def structured_suffix(mime: str) -> str | None:
    """Return the structured syntax suffix of a MIME type, without the ``+``.

    ``application/ld+json`` gives ``"json"`` and ``image/svg+xml`` gives
    ``"xml"``. Returns ``None`` when there is no suffix or the value is malformed.

    >>> import mimeguess as m
    >>> m.structured_suffix("image/svg+xml")
    'xml'
    """
    key = lenient_essence(mime)
    if key is None:
        return None
    subtype = key.split("/", 1)[1]
    head, plus, tail = subtype.rpartition("+")
    return tail if plus and head and tail else None


def real_charset(label: str | None) -> str | None:
    """Return a lowercase charset label, or ``None`` for non-charset annotations."""
    if label is None:
        return None
    lowered = label.lower()
    return lowered if lowered in _REAL_CHARSETS else None


def textual(key: str, declared_charset: str | None) -> bool:
    """Decide whether a type carries text, given its table charset."""
    if key.startswith("text/") or declared_charset is not None:
        return True
    return structured_suffix(key) in _TEXT_SUFFIXES
