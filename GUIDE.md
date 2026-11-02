# mimeguess guide

## What the table is

The table is generated, not written by hand. `scripts/generate_table.py` reads a
snapshot of jshttp **mime-db 1.54.0** (`data/mime-db-1.54.0.json`, MIT), which is
not committed: `python scripts/fetch_upstream.py` fetches it as pinned in
`data/MANIFEST.json`. The generator writes `src/mimeguess/_data.json.gz` plus
`src/mimeguess/_meta.py`.
mime-db merges three upstreams and records which one each type came from:

| `source` | Meaning |
| --- | --- |
| `iana` | Registered in the IANA Media Types registry |
| `apache` | Listed in Apache httpd `mime.types` |
| `nginx` | Listed in nginx `mime.types` |
| `mime-db` | Defined by the mime-db project itself |
| `supplement` | One of the few hand-written additions in this package |
| `custom` | Added by you through `MimeTable.with_types` |

`mimeguess.data_source()` returns the snapshot name, version, URL, SHA-256,
retrieval date, license and the table size. Provenance details for every data
file are in `data/README.md`.

### Conflicts

Some extensions are claimed by several types (`mp4`, `xml`, `rtf`, `wav`, ...).
The generator resolves them with the scoring of jshttp **mime-types 3.0.2**
(ported in `scripts/_score.py`): standards-tree types beat `vnd.`, which beat
`x-`; then by source IANA (40) > types mime-db defines itself (30) > Apache
(20) > nginx (10), which is why `.exe` resolves to the unsourced
`application/x-msdos-program`; then `video` > `audio` / `font` > `application` >
other top-level types; then the shorter name. The test suite compares every
conflicting extension with the output of the real mime-types 3.0.2 package.
Before the supplement below, every extension matches mime-types 3.0.2.

### The hand-written supplement

`scripts/_supplement.py` is short and labelled as hand-written. It adds a few
extensions that mime-db lists no type for (`py`, `cfg`, `sqlite`, `sqlite3`,
`db`, `zst`, and registered types `audio/flac` and `application/yaml`), lists
`sqlite` and `db` under `application/x-sqlite3` too so the 0.1.0 reverse lookup
keeps working, and it moves an
everyday extension to the front of four types so the preferred extension is the
familiar one (`.mp3` for `audio/mpeg`, `.ogg` for `audio/ogg`, `.mov` for
`video/quicktime`, `.aac` for `audio/aac`). It never deletes anything mime-db
lists. Added extensions compete under the same scoring, which moves exactly
`flac`, `yaml` and `yml` to the registered types; the tests pin that list.

## Why not `mimetypes`

The standard library module is a good default, but its answers are not fixed:

- `mimetypes.init()` reads the host's files (`/etc/mime.types` and friends) and,
  on Windows, the registry. Installed software can change what `.js` or `.csv`
  maps to, so two machines can disagree.
- `mimetypes.init(files=[])` does not avoid that: it still reads the Windows
  registry and the default `knownfiles`, and appends your list to them.
- The built-in table changes between Python versions (`.rtf`, `.wav`, `.mkv`,
  `.avi` and others changed in 3.12 to 3.14) so its coverage also depends on Python.

`mimeguess` ships one table inside the wheel and never reads the host, so the
same input gives the same answer on every machine and Python version. The value
is determinism and coverage (2,500+ types, 1,200+ extensions), not a different
opinion.

### Measured differences

The tests compare against `mimetypes.MimeTypes(filenames=())`, an instance built
only from the tables compiled into Python. On 3.10 to 3.14 about 76 to 81 % of
the extensions both know agree. The rest fall into three groups:

- **Different conflict policy**: `.xml` is `application/xml` here (stdlib
  `text/xml`); `.rtf` is `application/rtf` (stdlib 3.13+ `text/rtf`); `.wav` is
  `audio/wav` (stdlib `audio/x-wav`, or `audio/vnd.wave` on 3.14).
- **More specific types**: `.exe` and `.dll` get Windows program types instead of
  `application/octet-stream`; `.c` and `.h` are `text/x-c` instead of
  `text/plain`; `.rdf` and `.wsdl` get their `+xml` types.
- **Extensions only the stdlib lists**: for example `.pyc`, `.h5`, `.a` and `.o`
  are unknown here, and `.rst` (in the stdlib table since 3.12).

## Recipes

```python
import mimeguess

# Type and content coding, the way a static file server needs them.
mimeguess.guess("site.tar.gz")  # Guess(type='application/x-tar', encoding='gzip', extension='tar')
mimeguess.guess("logo.svgz")  # Guess(type='image/svg+xml', encoding='gzip', extension='svg')

# A ready header value.
mimeguess.content_type_for("index.html")  # 'text/html; charset=utf-8'

# Everything about a type.
info = mimeguess.media_type_info("application/ld+json")
info.source, info.extensions, info.suffix  # ('iana', ('.jsonld',), 'json')

# Your own mappings, without global state.
table = mimeguess.default_table().with_types({"text/x-typescript": ["ts", "d.ts"]})
table.guess_type("index.d.ts")  # 'text/x-typescript'
mimeguess.guess_type("index.ts")  # still 'video/mp2t' (MPEG transport stream)

# Check a download really is what its name says.
with open("report.pdf", "rb") as handle:
    assert mimeguess.sniff(handle.read(16)) == "application/pdf"
```

### Content coding and browsers

`guess()` follows the standard library: a trailing `.gz`, `.bz2`, `.xz`, `.br`,
`.Z` or `.zst` becomes the encoding. That suits files stored pre-compressed for
transparent delivery (`app.js.gz` served as `text/javascript` with
`Content-Encoding: gzip`). Do not send that header for archives the user wants to
download as-is (`backup.tar.gz`): browsers decompress it. Use `guess_type()`,
which answers `application/gzip`, for downloads.

### Compound extensions

Lookups try the longest dotted suffix the table knows first. The default table
has no multi-dot entries because the upstream data has none, but overrides can
add them (`d.ts`, `tar.zst`, ...).

## What it does not do

- It does not parse Content-Type parameters. `essence()` returns the lowercase
  `type/subtype` and rejects malformed values; use a full parser for parameters.
- `sniff()` recognises 21 formats by fixed signatures and nothing else. Containers are
  reported as the container (`.docx` is `application/zip`).
- It does not read the host registry, ever. If you need the host's opinion,
  use `mimetypes`.

## Command line

```
mimeguess type report.pdf                 # application/pdf
mimeguess type a.png b.css                # one "path<TAB>type" line per path
mimeguess type index.html --content-type  # text/html; charset=utf-8
mimeguess type site.tar.gz --encoding     # application/x-tar<TAB>gzip
mimeguess ext image/jpeg                  # .jpg .jpeg .jpe
mimeguess ext image/jpeg --preferred      # .jpg
mimeguess info application/json --json
mimeguess sniff download.bin
mimeguess source
```

Unknown inputs are reported on stderr and the exit status is 1; usage errors
also exit 1.

## Regenerating the table

```
python scripts/generate_table.py           # rewrite the generated files
python scripts/generate_table.py --check   # fail if they are stale
```

To move to a new mime-db release, follow `data/README.md`.

## Stable input and error contracts

All lookup functions accept strings. MIME queries ignore parameters after the first
semicolon and surrounding whitespace. Unknown or malformed strings return `None`,
`False` or an empty tuple as appropriate. Paths are filenames, not URLs: query strings
and fragments are not stripped, and no percent decoding is performed. Both slash forms
are directory separators. Leading dots do not create extensions; empty segments stop
compound matching. Only one trailing content coding is removed by `guess()`.

`essence()` raises `InvalidMediaType`, a `ValueError`, for malformed values.
`with_types()` raises `ValueError` for invalid MIME names, malformed extensions, an
empty extension iterable, or a string used instead of an extension iterable. Other
wrong argument types are outside the typed contract; path functions and `sniff()`
explicitly raise `TypeError`. Lookup functions never read files.

`sniff()` examines at most 16 bytes. Contiguous memoryviews are interpreted as raw
bytes; a noncontiguous view must be one-dimensional with one-byte elements. Unsupported
layouts raise `TypeError`; released views raise `ValueError`. Recognizing a signature
is not validation of the rest of a file, nor the full WHATWG browser algorithm.

Validation errors omit input values. CLI errors use one-based input numbers and usage
errors suggest `--help`, without echoing arguments. They exit 1; successful commands exit 0.
The `sniff` command reads files (or `-` for standard input); other commands do no file I/O.

Obtain `MimeTable` values through `default_table()` and `with_types()`. Its constructor
and underscore attributes are internal. Overrides deduplicate normalized extensions,
keep original metadata when replacing an existing type, and preserve other types'
reverse lists even when an extension is reassigned. Iteration order breaks override
conflicts: the last assignment wins. Result dataclasses are frozen value objects;
their constructors store the given typed fields without validation.

The 1.0.0 release keeps all previous table answers. Its error messages, raw-memoryview
handling and public class identities are the changes listed in the
[CHANGELOG](https://github.com/JaviLianes8/mimeguess/blob/main/CHANGELOG.md).
