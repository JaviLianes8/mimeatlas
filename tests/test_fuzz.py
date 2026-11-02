"""Seeded grammar, filename and binary properties with hand-written generators."""

from __future__ import annotations

import random
import string

import pytest

import mimeguess as m


@pytest.mark.parametrize("seed", [4123, 8701, 9007])
def test_seeded_mime_grammar_and_malformed_inputs(seed: int) -> None:
    rng = random.Random(seed)
    alphabet = string.ascii_letters + string.digits + "!#$%&'*+-.^_`|~"
    for _ in range(2000):
        first = "".join(rng.choices(alphabet, k=rng.randint(1, 25)))
        second = "".join(rng.choices(alphabet, k=rng.randint(1, 25)))
        text = first + "/" + second
        assert m.essence(" \t" + text + " ; ignored") == text.lower()
        invalid = first + "\x00/" + second
        with pytest.raises(m.InvalidMediaType):
            m.essence(invalid)
        assert m.media_type_info(invalid) is None
        assert m.structured_suffix(invalid) is None


def test_seeded_path_lookup_matches_a_suffix_oracle() -> None:
    rng = random.Random(20261102)
    exts = ["a", "b", "c", "a.b", "b.c", "a.b.c"]
    mapping = {f"text/x-{i}": [ext] for i, ext in enumerate(exts)}
    table = m.default_table().with_types(mapping)
    for _ in range(5000):
        name = "file." + ".".join(rng.choices(["a", "b", "c", ""], k=rng.randint(1, 12)))
        match = next(
            (e for e in sorted(exts, key=len, reverse=True) if name.endswith("." + e)), None
        )
        expected = None if match is None else f"text/x-{exts.index(match)}"
        assert table.guess_type("folder.pdf\\" + name.upper()) == expected


def test_seeded_bytes_unicode_and_truncation() -> None:
    rng = random.Random(6121)
    for _ in range(4000):
        data = rng.randbytes(rng.randrange(80))
        assert m.sniff(data) == m.sniff(data[:16]) == m.sniff(bytearray(data))
        text = "".join(chr(rng.randrange(0x110000)) for _ in range(rng.randrange(50)))
        m.guess(text)
        m.guess_type(text)
        m.extensions_for(text)
        m.is_textual(text)
        m.type_for_extension(text)


def test_large_adversarial_shapes_finish_with_bounded_errors() -> None:
    for size in (10000, 100000, 1000000):
        assert m.guess_type("a." * size + "pdf") == "application/pdf"
        assert m.guess("a." * size + "tar.gz") == m.Guess("application/x-tar", "gzip", "tar")
        with pytest.raises(m.InvalidMediaType) as exc:
            m.essence("a" * size + "/")
        assert len(str(exc.value)) < 100
        assert m.essence("a/b;" + "x" * size) == "a/b"
        assert m.sniff(b"%PDF-" + bytes(size)) == "application/pdf"
