# Improvements, this round

Progress for 1.0.0:
- [x] API, docs, errors, source checks and seeded contracts
- [x] Packaging and available interpreter
- [x] Mutation round and final gates
- [ ] Independent review, five QA lenses, merge and publication

The detailed evidence and current status are in
[CERT-1.0-REPORT.md](https://github.com/JaviLianes8/mimeguess/blob/release/1.0.0/CERT-1.0-REPORT.md).

Ranked by value to users. Everything here is additive: the 0.1.0 functions keep
their signatures and their documented behaviour.

1. **Generate the table from published sources instead of writing it by hand.**
   The 0.1.0 table had about 100 rows typed in manually. The new table is built
   by a committed generator (`scripts/generate_table.py`) from a committed
   snapshot of jshttp `mime-db` 1.54.0 (MIT), which itself merges the IANA
   registry, Apache httpd `mime.types` and nginx. The result covers 2,500+ types
   and 1,200+ extensions, records where each type comes from, and can be
   regenerated and checked byte for byte. A small, labelled, hand-written
   supplement keeps the few 0.1.0 extensions that `mime-db` does not list.
2. **Documented, reproducible conflict resolution.** When several types claim one
   extension (`mp4`, `xml`, `rtf`, `wav`, ...), the generator applies the same
   scoring as jshttp `mime-types` 3.0.2 (facet, source, top-level type, length).
   Apart from three documented supplement moves, the answers match that package.
3. **Full type to extension listing with a preferred extension.**
   `extensions_for(type)` returns every extension, preferred first.
4. **Typed results.** `media_type_info()` returns a frozen `MediaTypeInfo`
   (source, extensions, charset, compressible, structured suffix); `guess()`
   returns a `Guess` with the type, the content coding and the matched extension.
5. **Content coding and compound extensions.** `guess("a.tar.gz")` reports
   `application/x-tar` with encoding `gzip`, mirroring the standard library rules
   (`.tgz`, `.svgz`, ...). Lookups try the longest dotted suffix first, so custom
   compound extensions such as `d.ts` work.
6. **User overrides without global state.** `MimeTable.with_types()` returns a new
   table with extra or replacement mappings; the default table is never mutated.
7. **Charset defaults and ready Content-Type values.** `default_charset()` and
   `content_type_for(path)` give `text/html; charset=utf-8` style values.
8. **Structured syntax suffix awareness.** `structured_suffix()` and
   `is_textual()` understand `+json`, `+xml` and friends.
9. **Light Content-Type handling.** `essence()` lowercases and strips parameters,
   and raises `InvalidMediaType` (a `ValueError`) on malformed input. Full
   parameter parsing stays out of scope.
10. **Source introspection.** `data_source()` reports the snapshot name, version,
    URL, checksum, retrieval date, license and table size.
11. **Narrow magic number sniffing.** `sniff(data)` recognises a short, fixed list
    of unambiguous signatures (PNG, JPEG, GIF, PDF, ZIP, gzip, ...) and returns
    `None` for anything else. It is not a general content detector.
12. **Command line tool.** `mimeguess type|ext|info|sniff|source` for shell use.
13. **Verification.** Contract tests over the whole public promise, a test that
    the embedded table equals the generator output, cross-checks against the
    standard library and Apache `mime.types`, and an end to end test that installs
    the built wheel into a fresh virtual environment and runs the real script.
14. **Docs.** A GUIDE with the data policy, the differences from `mimetypes`, and
    recipes; full docstrings on every public name.
