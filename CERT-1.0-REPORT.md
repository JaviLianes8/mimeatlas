# mimeguess 1.0.0 certification report

Progress:
- [x] Release branch from main `6be2c4896439472c44c481868f80d0d8cd03313b`
- [x] PyPI checked: HTTP 404 for https://pypi.org/pypi/mimeguess/json on 2026-11-02
- [x] API, errors, runnable examples, strict typing and contract review
- [x] Real sources fetched and independent reference implementation executed
- [x] Seeded fuzz and adversarial inputs
- [x] README, GUIDE, dated CHANGELOG and release metadata
- [x] Final wheel, sdist, installed consumer and available interpreter
- [x] Mutation round and final four gates
- [ ] Independent reviewer (item 16)
- [ ] Five QA lenses (item 19)
- [x] [PR #4](https://github.com/JaviLianes8/mimeguess/pull/4) open; guard CLEAN
- [ ] Merge and publication reserved for the maintainer

## Baseline

Main identifies itself as 0.2.1. There is no live PyPI release to upgrade from.
On CPython 3.14, the initial suite passed 173 tests with 10 upstream-data skips.
Initial lint and `mypy --strict src tests` passed. The wheel consumer tests passed.

## API and behavior

The 23 exported names and their lookup signatures remain. Table answers are unchanged.
Public names and methods now have executable examples (72 doctest examples), with the
`Source` Literal alias documented by the package docstring. Result dataclasses remain
frozen; their public module identities support stable serialization. `MimeTable` is
obtained from `default_table` or `with_types`; its constructor is internal.

Validation messages omit input values. CLI errors identify an input by position,
and usage errors report a generic reason. Non-string paths raise `TypeError`.
The sniffer reads raw bytes from C-contiguous views; other supported views have
one-byte elements and one dimension. The CHANGELOG lists each behavior change.

## Real ground truth

On 2026-11-02 the six URLs in `data/MANIFEST.json` were fetched, with byte sizes,
SHA-256 digests, revisions and licenses recorded. Copies remain outside the repository
under `MIMEGUESS_DATA_DIR`; `scripts/fetch_upstream.py` can reproduce the downloads.

- mime-db 1.54.0: generator output equals the shipped table; every source type,
  extension and metadata field is checked.
- Apache httpd revision 1930012: every extension is known and all disagreements are
  accounted for by the conflict policy or the documented FLAC supplement.
- RFC 9110: token characters extracted from the fetched ABNF drive ASCII acceptance tests.
- WHATWG MIME Sniffing: signature bytes extracted from the fetched HTML tables drive
  supported-signature tests. This library intentionally does not implement the full
  browser algorithm.
- Real Node.js mime-types 3.0.2 with mime-db 1.54.0: 1,239 extension answers compared;
  exactly `flac`, `yaml` and `yml` differ as documented. The committed conflict fixture
  equals fresh program output. Tarballs are hash-checked before executing them.
- The running Python standard library supplies independent MIME lookup, gzip and ZIP
  output comparisons. Hand-written cases and seeded generators are labelled as such.

## Test coverage

The contracts cover every public name, all public table methods, error and unknown
paths, MIME metadata, override precedence and deduplication, compound suffixes,
frozen results, serialization, memoryview layouts and CLI output.
All README and GUIDE Python blocks execute, and public docstrings run as doctests.
Seeded cases include 6,000 token pairs, 5,000 independent filename-oracle comparisons,
4,000 binary and Unicode cases, and inputs up to two million filename characters.
Every test has a 300-second timeout.

## Packaging and supported interpreters

The final wheel was built from the sdist, then installed with `--no-index --no-deps`
into a throwaway venv. Both `mimeguess` and `python -I -m mimeguess` were driven by
subprocess, including standard input, JSON metadata, success and failure paths.
An external consumer imported the public API, checked values and serialization,
and passed `mypy --strict` using the installed wheel's `py.typed` information.
`pip check` and `twine check --strict` passed.

Pre-QA results on CPython 3.14.6 (the only installed interpreter discovered):

| Run | Result |
| --- | --- |
| Source checkout, all optional source and artifact checks enabled | 225 passed |
| Installed wheel, source import path disabled | 225 passed |
| Extracted sdist tests, its `src` directory moved out, installed wheel | 224 passed, 1 skipped |

The skip is only the generator command that writes/checks source-checkout paths.
The installed table still matches the fetched source generator byte for byte.
The launcher listed 13 additional registrations whose executable files are absent:
3.10.19, 3.10.22, 3.11.5, 3.11.14, 3.11.17, 3.12.12, 3.12.15, 3.13.2, 3.13.16,
3.14.2, 3.14.2t, 3.14.8 and 3.14.8t. Python 3.10 through 3.13 and free-threaded builds
could not be run on this laptop. No remote machine was used.

Archive inspection confirmed the package, `py.typed`, generated table, MIT license
and both upstream license notices in the wheel. The sdist additionally contains the
intended tests, generator scripts, manifests and documentation. Neither contains
fetched source documents, package archives, environments, caches or certification notes.

| Artifact | Bytes | SHA-256 |
| --- | --- | --- |
| `mimeguess-1.0.0-py3-none-any.whl` | 54833 | `7a32a7b46e5a8cb214308176e0b9131f3481efff89f37ca29bbf50e0821fc297` |
| `mimeguess-1.0.0.tar.gz` | 79953 | `88a2008bb28e4526721980c390fd3ff00b82fb1ed9280822a27f62efa85ad687` |

## Resource bounds

The sniffer copies only 16 bytes, even from a two-megabyte multidimensional view.
Custom compound extensions with 20,000 dots stay below the eight-megabyte peak-memory
contract. Lookup work is bounded by the input and stored candidate lengths; override
merging uses set membership. Five-call timing samples (best of three) on 1,000,
10,000 and 100,000 elements were 0.21/2.92/23.95 ms for dotted filenames,
0.50/4.34/47.08 ms for custom compound filenames, and 0.016/0.069/0.878 ms for tokens.
These measurements support the linear bounds; timing is not a flaky test assertion.
The format-output tests also execute CPython 3.14.6's gzip, ZIP, bzip2, xz, WAV and
SQLite implementations, rather than using remembered signatures. The implementation
source is https://github.com/python/cpython/tree/v3.14.6/Lib (run 2026-11-02).

## Mutation round (item 18)

25 deliberate bugs were applied separately to a scratch copy of the final library.
The unmodified contract suite passed first (215 tests). Bytecode writing was disabled,
each source file was restored after its run, and every mutant exited 1 with a named
failing test. The wheel and archive tests were excluded from this round; they ran
separately against the final build. No mutation survived. M19 specifically exercises
the memory contract: reading elements instead of bytes can preserve the returned type
while allocating the entire large view.

| ID | Mutation | Caught by |
| --- | --- | --- |
| M01 | filename case sensitivity (`_paths.py`) | `tests/test_contract.py::test_lookups_are_case_insensitive_everywhere` |
| M02 | treat a leading dot as an extension (`_paths.py`) | `tests/test_contract_edges.py::test_dotfiles_and_directories_are_not_extensions[.pdf]` |
| M03 | keep the compression suffix in content lookup (`_paths.py`) | `tests/test_cli.py::test_content_type_and_encoding_modes` |
| M04 | discard short archive alias expansion (`_paths.py`) | `tests/test_crosscheck.py::test_content_coding_matches_the_standard_library[a.tgz]` |
| M05 | prefer the shortest compound candidate (`_table.py`) | `tests/test_contract_edges.py::test_empty_segments_stop_compound_matching` |
| M06 | reject dotted extensions (`_paths.py`) | `tests/test_contract_edges.py::test_override_deduplicates_preserves_metadata_and_conflicting_reverse_lists` |
| M07 | raise the wrong media type error (`_mediatype.py`) | `tests/test_contract.py::test_only_essence_raises_and_only_invalid_media_type` |
| M08 | retain MIME case (`_mediatype.py`) | `tests/test_contract.py::test_only_essence_raises_and_only_invalid_media_type` |
| M09 | return first instead of last structured suffix (`_mediatype.py`) | `tests/test_contract_edges.py::test_sniff_signature_boundaries` |
| M10 | classify binary media as textual (`_mediatype.py`) | `tests/test_mediatype_sniff.py::test_is_textual` |
| M11 | choose last preferred extension (`_table_info.py`) | `tests/test_cli.py::test_ext_lists_extensions` |
| M12 | omit extension dots (`_table_info.py`) | `tests/test_cli.py::test_ext_lists_extensions` |
| M13 | drop text charset fallback (`_table_info.py`) | `tests/test_cli.py::test_content_type_and_encoding_modes` |
| M14 | lose override precedence (`_table.py`) | `tests/test_contract_edges.py::test_override_deduplicates_preserves_metadata_and_conflicting_reverse_lists` |
| M15 | omit charset from Content-Type (`_table.py`) | `tests/test_cli.py::test_content_type_and_encoding_modes` |
| M16 | wrong PNG magic byte (`_sniff.py`) | `tests/test_cli.py::test_sniff_reads_real_files` |
| M17 | accept bzip2 block size zero (`_sniff.py`) | `tests/test_contract_edges.py::test_sniff_signature_boundaries` |
| M18 | shift RIFF form offset (`_sniff.py`) | `tests/test_mediatype_sniff.py::test_sniff_recognises_each_documented_signature[RIFF$\x00\x00\x00AVI LIST-video/x-msvideo]` |
| M19 | read view elements instead of raw bytes (`_sniff.py`) | `tests/test_resource_bounds.py::test_sniff_copies_only_the_required_prefix_of_a_multidimensional_view` |
| M20 | make Guess mutable (`_models.py`) | `tests/test_contract.py::test_results_are_frozen_dataclasses` |
| M21 | report success for unknown CLI input (`_cli.py`) | `tests/test_cli.py::test_unknown_inputs_go_to_stderr_with_exit_one` |
| M22 | restore unbounded validation error (`_mediatype.py`) | `tests/test_contract_edges.py::test_errors_do_not_echo_input` |
| M23 | remove the shared table cache (`_load.py`) | `tests/test_docs.py::test_all_public_docstrings_have_passing_examples` |
| M24 | drop an export (`__init__.py`) | `tests/test_contract.py::test_all_lists_exactly_the_public_api` |
| M25 | ignore suffix dot boundary (`_table.py`) | `tests/test_cli.py::test_unknown_inputs_go_to_stderr_with_exit_one` |

## Pre-QA scorecard and gates

Verification completed across 2026-11-02 and 2026-11-03; the release date is 2026-11-02.
The pre-QA library and tests are committed at `a64a029`; QA fixes are recorded below.

| Item | Result | Evidence |
| --- | --- | --- |
| 1 | PASS | 23 names, signatures and dataclass fields pinned; changes in CHANGELOG |
| 2 | PASS | `__all__` equals the whole public namespace |
| 3 | PASS | 72 doctest examples; README and GUIDE blocks executed |
| 4 | PASS | `mypy --strict src tests scripts` and installed consumer |
| 5 | PASS | Documented exception classes and errors without caller values |
| 6 | PASS | 225 tests covering the public contracts and failure paths |
| 7 | PASS | Six fetched sources, Node.js oracle and real format output |
| 8 | PASS | Clean wheel consumer, console and module CLI; PyPI HTTP 404 |
| 9 | PASS | Seeded properties, large inputs and memory contracts |
| 10 | PASS for available interpreter | CPython 3.14.6; unavailable versions listed above |
| 11 | PASS | Exact badge, absolute links, honest alternatives, strict twine check |
| 12 | PASS | Dated 1.0.0 section, 2026-11-02 |
| 13 | PASS | Version, stable classifier, Python classifiers, URLs and MIT metadata |
| 14 | PASS | Wheel and sdist inspected and tested |
| 15 | PASS | Each gate exited 0 independently |
| 16 | Pending | Independent reviewer |
| 17 | Ready for review | PR #4 open, guard CLEAN; merge and publication pending |
| 18 | PASS | 25 of 25 mutations caught |
| 19 | Pending | Five independent QA lenses |

Pre-QA format, lint, strict typing and pytest gates passed (225 tests; optional checks enabled).

## QA round 1: 2026-11-03

Base: `5fb1fd6`. Fix commit: `a0e4e533dce7d946851e6eed38e4d4d724020abb`.

| Findings | Resolution |
| --- | --- |
| A-001, A-003 | Document per-function fallbacks and separately fetched snapshot provenance. |
| A-002 | Unknown `info` errors identify `input 1`; subprocess contract added. |
| A-004, C-02 | Empty C-contiguous multidimensional views return `None`; released views still raise. |
| A-005 | Specify C-contiguous support throughout; Fortran-only rejection and its error are tested. |
| C-01 | Accumulate normalized updates once, preserving ordering, metadata and conflict precedence. |
| C-03 | Read binary subclasses through buffers and strings through base operations; bound allocations and errors. |
| E-01 | Hidden filenames behind backslashes tested for all three path APIs; M02 now fails. |
| E-02 | Every API and CLI provenance field pinned, including ISO retrieval date; M36 now fails. |
| E-03 | Plain CLI and JSON distinguish `True`, `False`, `None`; M47 now fails. |

New contracts: 12 failures before fixes, 20 passes afterward; all three surviving mutations caught.
All four gates exit 0: format, lint, `mypy --strict src`, pytest (245 passed, no skips).
Broader strict typing, fresh wheel/sdist builds, artifact checks and strict twine checks pass.
No findings disputed. Items 16 and 19 await review; item 17 awaits merge and publication.

## QA round 2: 2026-11-03

Base: `e2e025fecc698f42d4a3987e5a870d3e299e3412`.
Fix commit: `b5e13aca06dfdc5fc9e17f20e83b188ab1b31ca6`.

| Finding | Resolution |
| --- | --- |
| E-04 | Four public `sniff()` contracts cover bytes and bytearray subclasses whose indexing overrides substitute a different prefix or raise. Each asserts PDF recognition and zero override calls. |

This finding concerns missing coverage; the existing implementation already reads the
underlying buffer correctly. Production code, public API and runtime behavior are unchanged.
The CHANGELOG records the added contracts, and the existing memory-bound contracts remain.

The reported mutation, replacing `memoryview(data)` with
`memoryview(data[:SNIFF_BYTES])`, was applied to a scratch source copy. All four new
cases failed (two wrong-result assertions and two override exceptions); all four
passed against the unchanged source. The scratch mutation was then restored.
The catching test is
`tests/test_input_contracts.py::test_sniff_reads_binary_subclass_buffers_without_getitem`.

All four gates exit 0: `ruff format --check .`, `ruff check .`, `mypy --strict src`
and pytest (249 passed, no skips, 300-second per-test timeout). Broader
`mypy --strict src tests` also passes. Fresh wheel/sdist builds, distribution contents,
installed-wheel consumers and all optional upstream-source checks pass on CPython 3.14.6.
No findings disputed. Independent lens re-verification remains pending.

## QA round 3: 2026-11-03

Base: `93d019657d8638ca131526d26935852807f9d9ba`.
Fix commit: `b0001191ebd6a2fb2e25503d0859baa17dc17ef5`.

| Finding | Resolution |
| --- | --- |
| E-05 | Eight contracts cover bytes and bytearray subclasses with misleading or raising `__bool__` and `__len__` overrides; PDF recognition succeeds without calling the overrides. |
| E-06 | Four contracts cover misleading or raising `startswith` overrides on bytes and bytearray subclasses; PDF recognition succeeds without calling the overrides. |
| E-07 | Four memory contracts cover positive and negative strides over 400,000-byte and 4,000,000-byte buffers; recognition succeeds with peak allocation below 64,000 bytes, measured after input allocation. |

These are missing-coverage findings. All 16 new cases pass against the existing
implementation; production code, runtime behavior and the public API are unchanged.
The CHANGELOG records the strengthened contracts.

Each reported mutation was applied separately to a scratch source copy and tested
in a fresh process with bytecode writing disabled. The source copy was restored afterward.

| Finding | Mutation | Catching test | Result |
| --- | --- | --- | --- |
| E-05 | Insert `if not data: return None` before buffer creation | `test_sniff_ignores_binary_subclass_truthiness` | 8 failures |
| E-06 | Match prefixes using the bytes subclass's `startswith` | `test_sniff_ignores_binary_subclass_startswith` | 2 failures |
| E-07 | Replace `bytes(view[:SNIFF_BYTES])` with `bytes(view)[:SNIFF_BYTES]` | `test_sniff_copies_only_the_required_prefix_of_a_strided_view` | 4 failures |

E-07's mutated peak allocations were 400,337 and 4,000,337 bytes for both stride
directions. All three reported mutations are caught; no findings are disputed.

All four gates exit 0: `ruff format --check .`, `ruff check .`, `mypy --strict src`
and pytest (265 passed, no skips, 300-second per-test timeout). Broader
`mypy --strict src tests` also passes. Fresh wheel/sdist builds, distribution contents,
installed-wheel consumers and all optional upstream-source checks pass on CPython 3.14.6.
Independent lens re-verification remains pending.

## QA round 4: 2026-11-03

Base: `d2593528265775f9bbec8fa4a7e4d518550fe852`.
Fix commit: `ae1c5fbd344de7a0ff0c1d4570b65e6346a12c7a`.

| Finding | Resolution |
| --- | --- |
| E-08 | Direct signed and unsigned arrays raise `TypeError`; their memoryview wrappers recognize PDF. |
| E-09 | Signed one-byte views recognize PDF and PNG in positive and negative stride directions, including PNG bytes above 127. |
| E-10 | Positive and negative strided views reject the 15-byte SQLite prefix and recognize the complete 16-byte signature, with or without a trailing byte. |
| E-11 | Each alphabetic byte in 23 hand-written magic signatures is case-swapped independently and rejected; swapping all alphabetic bytes is also rejected, including lowercase `%pdf-`. |

These are missing-coverage findings. All 37 new cases pass against the existing
implementation; production code, runtime behavior and the public API are unchanged.
The CHANGELOG records the strengthened contracts.

Each reported mutation was applied separately to a scratch source copy and tested
in a fresh process with bytecode writing disabled. Baseline and restored-source
runs each passed all 37 cases. Catching tests are in `tests/test_sniff_contracts.py`.

| Finding | Mutation | Catching test | Result |
| --- | --- | --- | --- |
| E-08 | Replace the input-type guard with `if False:` | `test_sniff_rejects_direct_array_buffers` | 2 failures |
| E-09 | Require format `B` for one-byte strided views | `test_sniff_accepts_signed_one_byte_strided_views` | 4 failures |
| E-10 | Copy only `SNIFF_BYTES - 1` bytes from strided views | `test_sniff_checks_the_complete_sqlite_signature_in_strided_views` | 4 failures |
| E-11 | Lowercase both the input prefix and magic signature before matching | `test_sniff_rejects_case_altered_magic_signatures` | 19 failures |

All four reported mutations are caught; no findings are disputed.

All four gates exit 0: `ruff format --check .`, `ruff check .`, `mypy --strict src`
and pytest (302 passed, no skips, 300-second per-test timeout). Broader
`mypy --strict src tests scripts` and the table generator check also pass.
Fresh wheel/sdist builds, strict twine checks, distribution contents, installed-wheel
consumers and all optional upstream-source checks pass on CPython 3.14.6.
Independent lens re-verification remains pending.

## QA round 5: 2026-11-03

Base: `a504366f0f352d12ba22e46d12aff22ff7808fec`.
Fix commit: `d4333f9d41275ab7a1bc324ad540902b798b8dcd`.

| Finding | Resolution |
| --- | --- |
| E-12 | 208 cases require magic signatures at offset zero: 26 hand-written signatures shifted by one or three unrelated bytes, across bytes, bytearray and positive and negative strided memoryviews. |

This is a missing-coverage finding. All 208 new cases pass against the existing
implementation; production code, runtime behavior and the public API are unchanged.
The CHANGELOG records the strengthened contracts. Each signature is also checked
for recognition before shifting it.

The reported mutation, replacing `head.startswith(prefix)` with `prefix in head`,
was applied to a scratch source copy and tested in a fresh process with bytecode
writing disabled. Baseline and restored-source runs each passed all 208 cases.

| Finding | Mutation | Catching test | Result |
| --- | --- | --- | --- |
| E-12 | Accept prefix signatures at nonzero offsets | `tests/test_sniff_contracts.py::test_sniff_requires_magic_signatures_at_offset_zero` | 168 failures |

The remaining 40 cases cover the 16-byte SQLite signature, which no longer fits
inside the read window after shifting, and the separate bzip2 and RIFF branches.
The reported mutation is caught; no findings are disputed.

All four gates exit 0: `ruff format --check .`, `ruff check .`, `mypy --strict src`
and pytest (510 passed, no skips, 300-second per-test timeout). Broader
`mypy --strict src tests scripts` and the table generator check also pass.
Fresh wheel/sdist builds, strict twine checks, distribution contents, installed-wheel
consumers and all optional upstream-source checks pass on CPython 3.14.6.
Independent lens re-verification remains pending.

## QA round 6: 2026-11-03

Base: `e085d2e52a7a686660d55c1a2a47933eed256a08`.
Fix commit: `d549f0731c141b74ddd8f21d1bea659b0c6416b9`.

| Finding | Resolution |
| --- | --- |
| E-13 | `sniff(b"abc1BZh")` must return `None`: a bzip2 marker after unrelated bytes must not borrow the preceding byte as its block-size digit. |
| E-14 | `b"xxxxRIFFWEBP"`, `b"xxxxRIFFWAVE"` and `b"xxxxRIFFAVI "` must return `None`: a RIFF marker at offset 4 must not pair with a form type that happens to sit at bytes 8 to 12. |

Both are missing-coverage findings. The 16 new cases in
`tests/test_sniff_contracts.py::test_sniff_requires_bzip2_and_riff_markers_at_offset_zero`
cover bytes, bytearray and positive and negative strided memoryviews, and all pass
against the existing implementation; production code, runtime behavior and the public
API are unchanged. The CHANGELOG records the strengthened contracts.

Each reported mutation was applied to a scratch source copy and tested in a fresh
process with bytecode writing disabled; the restored source passed all 16 cases.

| Finding | Mutation | Catching test | Result |
| --- | --- | --- | --- |
| E-13 | `head.startswith(b"BZh")` replaced by `b"BZh" in head` | `test_sniff_requires_bzip2_and_riff_markers_at_offset_zero` | 4 failures |
| E-14 | `head.startswith(b"RIFF")` replaced by `b"RIFF" in head` | `test_sniff_requires_bzip2_and_riff_markers_at_offset_zero` | 12 failures |

No findings are disputed. All four gates exit 0: `ruff format --check .`, `ruff check .`,
`mypy --strict src` and pytest (521 passed, 5 skipped for absent optional inputs,
300-second per-test timeout, fresh CPython 3.14 venv). `mypy --strict src tests scripts`
also passes. Independent lens re-verification remains pending.

## QA round 7: 2026-11-03

Base: `08881f435c204ccd18a113fb5a4f5fb17f703b0e`.
Fix commit: `e350dafe27e81e056c03ce4cc8f5a3b82c8c2f4a`.

| Finding | Resolution |
| --- | --- |
| E-15 | `sniff(b"BZh")` must return `None`. For a 3-byte head the digit slice `head[3:4]` is empty and an empty slice is contained in every bytes object, so the `len(head) >= 4` guard is the only check that rejects a bare marker. |

This is a missing-coverage finding. The new
`tests/test_sniff_contracts.py::test_sniff_rejects_markers_one_byte_short_of_their_length_guard`
covers a bare `BZh` and RIFF headers of 11 bytes for each form type, for bytes, bytearray
and positive and negative strided memoryviews. All cases pass against the existing
implementation; production code, runtime behavior and the public API are unchanged.

The other length and offset checks in `src/mimeguess/_sniff.py` were probed the same way
(mutation applied to the source, fresh process, bytecode writing disabled, source restored):

| Mutation | Catching test | Result |
| --- | --- | --- |
| bzip2 guard `>= 4` to `>= 3` | `test_sniff_rejects_markers_one_byte_short_of_their_length_guard` | killed |
| bzip2 guard removed | `test_sniff_rejects_markers_one_byte_short_of_their_length_guard` | killed |
| RIFF guard `>= 12` to `>= 11`, or removed | none | equivalent: a slice shorter than 4 bytes never matches a 4-byte form key |
| empty check `nbytes == 0` removed | `test_empty_multidimensional_views_return_none` | killed |
| empty check `nbytes == 0` to `<= 2` | none | equivalent: the shortest signature is 3 bytes |
| empty check `nbytes == 0` to `<= 3` | `test_sniff_requires_magic_signatures_at_offset_zero` | killed |
| `SNIFF_BYTES` 16 to 15 | `test_sniff_recognises_each_documented_signature`, new prefix pin | killed |
| `SNIFF_BYTES` 16 to 17 | `test_sniff_reads_exactly_the_documented_sixteen_byte_prefix` (new) | killed |
| prefix slice removed (contiguous or strided path) | `tests/test_resource_bounds.py` | killed |

`SNIFF_BYTES` 16 to 17 survived before this round. The CLI reads `SNIFF_BYTES` bytes from
files and stdin and the `sniff()` docstring promises the first 16 bytes, so the new test in
`tests/test_resource_bounds.py` pins both. The two equivalent mutants cannot change any
result and are recorded here instead of being tested.

No findings are disputed. All four gates exit 0: `ruff format --check .`, `ruff check .`,
`mypy --strict src` and pytest (300-second per-test timeout, fresh CPython 3.14 venv).
Independent lens re-verification remains pending.
