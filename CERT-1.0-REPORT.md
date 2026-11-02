# mimeguess 1.0.0 certification report

Progress:
- [x] Release branch from main `6be2c4896439472c44c481868f80d0d8cd03313b`
- [x] PyPI checked: HTTP 404 for https://pypi.org/pypi/mimeguess/json on 2026-11-02
- [x] API, errors, runnable examples, strict typing and contract review
- [x] Real sources fetched and independent reference implementation executed
- [x] Seeded fuzz and adversarial inputs
- [x] README, GUIDE, dated CHANGELOG and release metadata
- [ ] Final wheel, sdist, installed consumer and interpreter matrix
- [ ] Mutation round and final four gates
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

## Independent stages

Items 16 and 19 are pending. No reviewer or QA lens verdict is claimed here.
Item 17 will remain pending for merge and publication after the pull request is prepared.
