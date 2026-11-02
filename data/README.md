# Source snapshots

This folder holds upstream data that is not committed. `MANIFEST.json` pins each file
(URL, revision, size, SHA-256, licence) and `python scripts/fetch_upstream.py` downloads
the files here, checking every hash; git ignores everything but this README and the
manifest. Without the files the package still works and its tests pass: the generator
check and the tests that read them skip.

Set `MIMEGUESS_DATA_DIR` to download and test against a directory outside the checkout.
The manifest always stays here. The original embedded table retrieval date remains
2026-10-12; the manifest records the latest verification fetch separately.

## Specifications and reference packages

- `rfc9110.txt`: HTTP token ABNF, parsed by `tests/test_upstream.py`.
- `mimesniff.html`: WHATWG signature tables, parsed for supported binary signatures.
- `mime-types-3.0.2.tgz` and `mime-db-1.54.0.tgz`: pinned npm package archives.
  `scripts/reference_mime_types.py` verifies their hashes, extracts them under the
  data directory and runs Node.js to compare every extension and conflict result.
  No package installation or network access occurs during tests.

These files are neither committed nor included in either distribution. Moving sources
may change; a download that does not match its pinned hash is refused for review.

## mime-db-1.54.0.json

- What: `db.json` from jshttp mime-db 1.54.0 (published 2025-03-18). It merges
  the IANA Media Types registry, Apache httpd `mime.types` and nginx
  `mime.types`, recording for each type which of them it came from.
- License: MIT. The notice is in `LICENSES/mime-db.txt` and ships in the wheel,
  because `src/mimeguess/_data.json.gz` is derived from this file.
- Used by: `scripts/generate_table.py`, which builds `src/mimeguess/_data.json.gz`
  and `src/mimeguess/_meta.py` from it.

## apache-httpd-mime.types-r1930012

- What: `docs/conf/mime.types` from Apache httpd trunk, SVN revision 1930012.
- License: the file header places it in the public domain.
- Used by: `tests/test_crosscheck.py` only, as an independent check. It is not
  part of the generated table or the wheel.

## Updating

1. Change the URL, revision, size and SHA-256 in `MANIFEST.json` and run
   `python scripts/fetch_upstream.py`.
2. Update the paths and constants at the top of `scripts/generate_table.py`.
3. Run `python scripts/generate_table.py`, then the test suite. Review the diff
   of `tests/golden/` and the pinned counts in the tests; regenerate the golden
   conflict file from the matching mime-types release as described in
   `tests/golden/PROVENANCE.txt`.
