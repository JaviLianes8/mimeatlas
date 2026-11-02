"""Splitting file names into candidate extensions and content codings."""

from __future__ import annotations

# Hand-written: content codings implied by a trailing extension. The first five
# mirror the Python standard library's mimetypes.encodings_map; "zst" (zstd,
# RFC 8878) is added. Matching is case-insensitive here, unlike the stdlib.
ENCODINGS: dict[str, str] = {
    "gz": "gzip",
    "z": "compress",
    "bz2": "bzip2",
    "xz": "xz",
    "br": "br",
    "zst": "zstd",
}

# Hand-written: short forms that stand for a compound name, mirroring the
# standard library's mimetypes.suffix_map.
SUFFIX_ALIASES: dict[str, str] = {
    "svgz": "svg.gz",
    "tgz": "tar.gz",
    "taz": "tar.gz",
    "tz": "tar.gz",
    "tbz2": "tar.bz2",
    "txz": "tar.xz",
}


def basename(path: str) -> str:
    """Return the last path component, treating ``/`` and ``\\`` as separators."""
    if not isinstance(path, str):
        raise TypeError("path must be a string")
    return str.replace(path, "\\", "/").rsplit("/", 1)[-1]


def segments(path: str) -> list[str]:
    """Return the lowercase dotted extension segments of a path's file name.

    A leading dot does not start an extension (``.bashrc`` has none) and an
    empty trailing segment ends the search (``weird.`` has none).
    """
    name = basename(path).lower()
    parts = name.lstrip(".").split(".")
    if len(parts) < 2 or parts[-1] == "":
        return []
    rest = parts[1:]
    # Keep only the run of non-empty segments that touches the end of the name.
    tail: list[str] = []
    for part in reversed(rest):
        if part == "":
            break
        tail.append(part)
    return tail[::-1]


def expand_alias(parts: list[str]) -> list[str]:
    """Replace a trailing short form such as ``tgz`` with ``tar``, ``gz``."""
    if parts and parts[-1] in SUFFIX_ALIASES:
        return [*parts[:-1], *SUFFIX_ALIASES[parts[-1]].split(".")]
    return parts


def split_encoding(parts: list[str]) -> tuple[list[str], str | None]:
    """Expand aliases, then strip one trailing content coding.

    Mirrors the standard library: ``a.tar.gz`` gives ``(["tar"], "gzip")`` and a
    lone ``a.gz`` gives ``([], "gzip")``.
    """
    parts = expand_alias(parts)
    if parts and parts[-1] in ENCODINGS:
        return parts[:-1], ENCODINGS[parts[-1]]
    return parts, None


def normalize_extension(ext: str) -> str:
    """Lowercase an extension and drop one leading dot; reject malformed ones.

    Raises:
        ValueError: if the result is empty, has empty dotted segments, or
            contains whitespace, ``/`` or ``\\``.
    """
    if not isinstance(ext, str):
        raise ValueError("extension must be a string")
    key = str.lower(ext).removeprefix(".")
    bad = not key or any(not part for part in key.split("."))
    if bad or any(ch.isspace() or ch in "/\\" for ch in key):
        raise ValueError("not a valid file extension")
    return key
