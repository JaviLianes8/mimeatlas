"""The ``mimeguess`` command line tool."""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from collections.abc import Callable, Sequence
from typing import NoReturn

from . import __version__
from ._guess import (
    content_type_for,
    extensions_for,
    guess,
    guess_extension,
    guess_type,
    media_type_info,
)
from ._load import data_source
from ._sniff import SNIFF_BYTES, sniff

EXAMPLES = """\
examples:
  mimeguess type report.pdf                 application/pdf
  mimeguess type index.html --content-type  text/html; charset=utf-8
  mimeguess type site.tar.gz --encoding     application/x-tar<TAB>gzip
  mimeguess type a.png b.css                one "path<TAB>type" line per path
  mimeguess ext image/jpeg                  .jpg .jpeg .jpe
  mimeguess ext image/jpeg --preferred      .jpg
  mimeguess info application/json --json    everything known about a type
  mimeguess sniff download.bin              type from the first bytes
  mimeguess source                          where the table comes from

With several inputs each line is prefixed by the input and a tab. Unknown
inputs are reported on stderr and make the exit status 1. Results never depend
on the operating system.
"""


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        reason = "invalid choice" if "invalid choice:" in message else "invalid arguments"
        self.exit(1, f"{self.prog}: error: {reason}; use --help\n")


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(
        prog="mimeguess",
        description="Map file extensions to MIME types and back, from a fixed table.",
        epilog=EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"mimeguess {__version__}")
    sub = parser.add_subparsers(dest="command", required=True, parser_class=_Parser)
    p = sub.add_parser("type", help="guess the MIME type of paths from their extensions")
    p.add_argument("paths", nargs="+", metavar="PATH")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument(
        "--content-type", action="store_true", help="print a Content-Type value with charset"
    )
    mode.add_argument(
        "--encoding", action="store_true", help="split off a compression extension (.gz, ...)"
    )
    p = sub.add_parser("ext", help="list the extensions of MIME types, preferred first")
    p.add_argument("types", nargs="+", metavar="TYPE")
    p.add_argument("--preferred", action="store_true", help="print only the preferred one")
    p = sub.add_parser("info", help="show everything known about a MIME type")
    p.add_argument("type", metavar="TYPE")
    p.add_argument("--json", action="store_true", help="print JSON")
    p = sub.add_parser("sniff", help="detect a few common formats from file contents")
    p.add_argument("files", nargs="+", metavar="FILE", help="a file, or - for stdin")
    p = sub.add_parser("source", help="show the provenance of the embedded table")
    p.add_argument("--json", action="store_true", help="print JSON")
    return parser


def _report(inputs: Sequence[str], lookup: Callable[[str], str | None], what: str) -> int:
    status = 0
    for index, item in enumerate(inputs, 1):
        try:
            value = lookup(item)
        except (OSError, ValueError):
            print(f"mimeguess: cannot read input {index}", file=sys.stderr)
            status = 1
            continue
        if value is None:
            print(f"mimeguess: {what} for input {index}", file=sys.stderr)
            status = 1
        elif len(inputs) == 1:
            print(value)
        else:
            print(f"{item}\t{value}")
    return status


def _type_of(content_type: bool, encoding: bool) -> Callable[[str], str | None]:
    def lookup(path: str) -> str | None:
        if content_type:
            return content_type_for(path)
        if not encoding:
            return guess_type(path)
        found = guess(path)
        if found.type is None and found.encoding is None:
            return None
        return f"{found.type or '-'}\t{found.encoding or '-'}"

    return lookup


def _exts_of(preferred: bool) -> Callable[[str], str | None]:
    def lookup(mime: str) -> str | None:
        if preferred:
            return guess_extension(mime)
        return " ".join(extensions_for(mime)) or None

    return lookup


def _sniff_file(name: str) -> str | None:
    if name == "-":
        return sniff(sys.stdin.buffer.read(SNIFF_BYTES))
    with open(name, "rb") as handle:
        return sniff(handle.read(SNIFF_BYTES))


def _info(mime: str, as_json: bool) -> int:
    found = media_type_info(mime)
    if found is None:
        print("mimeguess: unknown MIME type for input 1", file=sys.stderr)
        return 1
    data = dataclasses.asdict(found)
    data["extensions"] = list(found.extensions)
    data["preferred_extension"] = found.preferred_extension
    _emit(data, as_json)
    return 0


def _emit(data: dict[str, object], as_json: bool) -> None:
    if as_json:
        print(json.dumps(data, indent=2))
        return
    for key, value in data.items():
        shown = " ".join(value) if isinstance(value, list) else value
        print(f"{key}: {'-' if shown in (None, '') else shown}")


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line tool and return its exit status."""
    for stream in (sys.stdout, sys.stderr):
        # Never crash on a file name the console encoding cannot show.
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(errors="backslashreplace")
    args = _parser().parse_args(argv)
    if args.command == "type":
        return _report(args.paths, _type_of(args.content_type, args.encoding), "no MIME type known")
    if args.command == "ext":
        return _report(args.types, _exts_of(args.preferred), "no extension known")
    if args.command == "info":
        return _info(args.type, args.json)
    if args.command == "sniff":
        return _report(args.files, _sniff_file, "unrecognised content")
    _emit(dataclasses.asdict(data_source()), args.json)
    return 0
