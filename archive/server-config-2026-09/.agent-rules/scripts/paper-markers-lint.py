#!/usr/bin/env python3
"""Check a paper's STATUS/GOAL/HOLE/NOTE/NEXT/CLAIM marker lines.

Markers are LaTeX comments that carry the state of the manuscript. Prose
asks for them; this checks them:

    python3 paper-markers-lint.py <paper-dir>           # exit 1 on any failure
    python3 paper-markers-lint.py <paper-dir> --json    # machine-readable

Scans `*.tex` under the directory recursively, skipping `archive/`,
`build/`, and any directory starting with `.`. A marker is a comment line
matching `^\\s*%+\\s*(STATUS|GOAL|HOLE|NOTE|NEXT|CLAIM)\\(([^)]*)\\)(.*)$`.
Multi-line continuation is not required; only the marker line is parsed.

Rules enforced:

1. Every marker has a non-empty id inside the parentheses.
2. Every `CLAIM` carries `src=<path>` on its line. The path, resolved
   relative to the paper directory and, failing that, relative to the
   paper directory's parent (the project checkout), must exist. Missing
   `src=` and missing path are two different failure messages. Trailing
   `;,.)` characters are stripped from the captured value before it is
   resolved. A value starting with `http://` or `https://` is a URL: it
   passes without any filesystem check and is counted separately.
3. An id has at most one open `HOLE` across all files (a second `HOLE`
   with the same id is a failure).
4. An id that has both a `HOLE` and a `CLAIM` is a failure: the `HOLE`
   should have been cleared when the `CLAIM` landed.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

KINDS = ("STATUS", "GOAL", "HOLE", "NOTE", "NEXT", "CLAIM")
SKIP_DIRS = ("archive", "build")

MARKER = re.compile(r"^\s*%+\s*(" + "|".join(KINDS) + r")\(([^)]*)\)(.*)$")
SRC = re.compile(r"\bsrc=(\S+)")
SRC_TRAILING = ";,.)"


class Marker:
    def __init__(self, kind: str, ident: str, rest: str, rel: str, line: int) -> None:
        self.kind = kind
        self.ident = ident
        self.rest = rest
        self.rel = rel
        self.line = line

    @property
    def where(self) -> str:
        return f"{self.rel}:{self.line}"


def tex_files(root: Path) -> list[Path]:
    """Every `*.tex` under root, minus skipped directories."""
    out = []
    for path in sorted(root.rglob("*.tex")):
        parts = path.relative_to(root).parts[:-1]
        if any(p in SKIP_DIRS or p.startswith(".") for p in parts):
            continue
        out.append(path)
    return out


def scan(root: Path) -> list[Marker]:
    markers: list[Marker] = []
    for path in tex_files(root):
        rel = str(path.relative_to(root))
        text = path.read_text(encoding="utf-8", errors="replace")
        for number, line in enumerate(text.splitlines(), start=1):
            match = MARKER.match(line)
            if match:
                kind, ident, rest = match.groups()
                markers.append(Marker(kind, ident.strip(), rest, rel, number))
    return markers


def src_value(raw: str) -> str:
    """The captured `src=` value with trailing punctuation stripped."""
    return raw.rstrip(SRC_TRAILING)


def is_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


def src_exists(value: str, root: Path) -> bool:
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate.exists()
    return (root / candidate).exists() or (root.parent / candidate).exists()


def check(markers: list[Marker], root: Path) -> tuple[list[str], int]:
    failures: list[tuple[str, int, str]] = []
    urls = 0

    def fail(marker: Marker, message: str) -> None:
        failures.append((marker.rel, marker.line, f"{marker.where}: {message}"))

    holes: dict[str, Marker] = {}
    claims: dict[str, Marker] = {}

    for marker in markers:
        if not marker.ident:
            fail(marker, f"{marker.kind}() has an empty id")
        if marker.kind == "CLAIM":
            found = SRC.search(marker.rest)
            if not found:
                fail(marker, f"CLAIM({marker.ident}) has no src=")
            else:
                value = src_value(found.group(1))
                if is_url(value):
                    urls += 1
                elif not src_exists(value, root):
                    fail(marker, f"CLAIM({marker.ident}) src={value} does not exist")
            if marker.ident and marker.ident not in claims:
                claims[marker.ident] = marker
        if marker.kind == "HOLE" and marker.ident:
            first = holes.get(marker.ident)
            if first is None:
                holes[marker.ident] = marker
            else:
                fail(marker, f"HOLE({marker.ident}) duplicates the open HOLE at {first.where}")

    for ident, hole in holes.items():
        claim = claims.get(ident)
        if claim is not None:
            fail(hole, f"HOLE({ident}) has a CLAIM at {claim.where}; clear the HOLE when the CLAIM lands")

    return [text for _, _, text in sorted(failures)], urls


def counts(markers: list[Marker]) -> dict[str, dict[str, int]]:
    per_file: dict[str, dict[str, int]] = {}
    for marker in markers:
        row = per_file.setdefault(marker.rel, {kind: 0 for kind in KINDS})
        row[marker.kind] += 1
    return dict(sorted(per_file.items()))


def print_table(per_file: dict[str, dict[str, int]]) -> None:
    if not per_file:
        print("no markers found")
        return
    width = max([len("file")] + [len(name) for name in per_file])
    header = "file".ljust(width) + "".join(kind.rjust(7) for kind in KINDS)
    print(header)
    for name, row in per_file.items():
        print(name.ljust(width) + "".join(str(row[kind]).rjust(7) for kind in KINDS))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("paper_dir", help="directory holding the manuscript")
    parser.add_argument("--json", action="store_true", help="print JSON instead of a table")
    args = parser.parse_args(argv)

    root = Path(args.paper_dir).resolve()
    if not root.is_dir():
        print(f"FAIL {args.paper_dir}: not a directory")
        return 1

    markers = scan(root)
    failures, urls = check(markers, root)
    per_file = counts(markers)

    if args.json:
        print(json.dumps({"files": per_file, "failures": failures, "markers": len(markers), "urls": urls}, indent=2))
    else:
        print_table(per_file)
        for failure in failures:
            print(f"FAIL {failure}")
        if urls:
            print(f"{len(markers)} markers, {urls} url source(s), {len(failures)} failure(s)")
        else:
            print(f"{len(markers)} markers, {len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
