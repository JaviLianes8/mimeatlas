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
- [ ] Pull request; merge and publication reserved for the maintainer

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
The sniffer reads raw bytes from contiguous views; noncontiguous views must have
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

Final results on CPython 3.14.6 (the only installed interpreter discovered):

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

## Scorecard and final gates

Verification completed across 2026-11-02 and 2026-11-03; the release date is 2026-11-02.

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
| 17 | Pending | PR, merge and publication |
| 18 | PASS | 25 of 25 mutations caught |
| 19 | Pending | Five independent QA lenses |

The final four gates were `ruff format --check .`, `ruff check .`,
`mypy --strict src`, and `pytest` (225 passed, optional checks enabled).
The broader `mypy --strict src tests scripts` also exited 0.

## Independent stages

Items 16 and 19 are pending. No reviewer or QA lens verdict is claimed here.
Item 17 will remain pending for merge and publication after the pull request is prepared.
