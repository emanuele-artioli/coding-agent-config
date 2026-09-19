#!/usr/bin/env python3
"""Lesson ledger over the candidates queue — find the earlier entry, record a repeat.

`AGENTS.md` makes a rule out of anything that has gone wrong *more than once*,
but nothing read the queue back, so a second occurrence looked like a first.
This reads frontmatter only (bodies are long; NFS opens are slow) and never
touches git.

    lessons.py list
    lessons.py match "one-line summary of what just went wrong"
    lessons.py record <id> --project <path> --platform <name>
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "candidates"
FULL_LIST_UNDER = 60  # below this, printing every summary beats any matcher

STOP = {
    "a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "it", "its",
    "is", "are", "was", "were", "that", "this", "with", "from", "by", "at",
    "as", "be", "not", "but", "than", "then", "when", "while", "into", "over",
    "out", "up", "do", "does", "did", "can", "will", "so", "if", "no", "any",
    "one", "two", "also", "here", "there", "which", "what", "how", "you",
}


def _stem(word: str) -> str:
    for suf in ("ing", "ies", "ed", "es", "s"):
        if suf == "s" and word.endswith("ss"):
            continue
        if word.endswith(suf) and len(word) > len(suf) + 2:
            return word[: -len(suf)]
    return word


def _tokens(text: str) -> set[str]:
    words = re.split(r"[^a-z0-9]+", text.lower())
    return {_stem(w) for w in words if len(w) > 2 and w not in STOP}


def _frontmatter(path: Path) -> dict[str, str]:
    """Parse the leading `---` block. Scalars only; lists stay raw strings."""
    fields: dict[str, str] = {}
    try:
        with path.open() as handle:
            if handle.readline().strip() != "---":
                return fields
            for line in handle:
                if line.strip() == "---":
                    break
                m = re.match(r"^([a-z_]+):\s*(.*)$", line.rstrip("\n"))
                if m:
                    fields[m.group(1)] = m.group(2).strip()
    except OSError:
        return {}
    return fields


class Entry:
    def __init__(self, path: Path, root: Path) -> None:
        self.path = path
        self.fm = _frontmatter(path)
        self.id = self.fm.get("id") or path.stem.removeprefix("promote-")
        self.summary = self.fm.get("summary", "")
        self.axis = self.fm.get("axis", "project")
        self.status = self.fm.get("status", "open")
        self.where = "open" if root / "open" in path.parents else "done"
        try:
            self.occurrences = int(self.fm.get("occurrences", "1"))
        except ValueError:
            self.occurrences = 1
        # No `keywords:` on the 18 legacy files — derive from the slug + summary.
        raw = self.fm.get("keywords", "")
        self.keywords = _tokens(raw) | _tokens(path.stem)
        self.summary_tokens = _tokens(self.summary)

    def score(self, query: set[str]) -> int:
        """Slug and keyword hits count double; summary hits count once."""
        return sum(
            2 if t in self.keywords else 1
            for t in query
            if t in self.keywords or t in self.summary_tokens
        )

    def line(self) -> str:
        return (
            f"{self.id} | {self.where}/{self.status} | {self.axis} | "
            f"x{self.occurrences} | {self.summary}"
        )


def load(root: Path = ROOT) -> list[Entry]:
    paths: list[Path] = []
    for directory in (root / "open" / "project", root / "open" / "platform", root / "done"):
        if directory.is_dir():
            paths += sorted(p for p in directory.iterdir() if p.suffix == ".md")
    return [Entry(p, root) for p in paths]


def cmd_list(entries: list[Entry]) -> int:
    for entry in entries:
        print(entry.line())
    return 0


def cmd_match(entries: list[Entry], query: str) -> int:
    tokens = _tokens(query)
    ranked = sorted(
        ((e.score(tokens), e) for e in entries), key=lambda p: (-p[0], p[1].id)
    )
    hits = [(s, e) for s, e in ranked if s > 0][:5]
    if hits:
        print(f"Best matches for: {query}")
        for score, entry in hits:
            print(f"  [{score}] {entry.line()}")
    else:
        print(f"No keyword overlap for: {query}")
    print(
        "\nOverlap is a recall aid, not a verdict — a restatement in different "
        "words scores zero. Read the list before deciding this is new."
    )
    if len(entries) < FULL_LIST_UNDER:
        print(f"\nAll {len(entries)} candidates:")
        cmd_list(entries)
    return 0


def cmd_record(
    entries: list[Entry], ident: str, project: str, platform: str,
    root: Path, when: str,
) -> int:
    found = [e for e in entries if e.id == ident]
    if not found:
        print(f"lessons: no candidate with id {ident}", file=sys.stderr)
        return 1
    entry = found[0]
    count = entry.occurrences + 1

    text = entry.path.read_text()
    head, sep, body = text.partition("\n---\n")
    if not sep:  # no parseable frontmatter; leave the file structure alone
        print(f"lessons: {entry.path} has no frontmatter block", file=sys.stderr)
        return 1
    lines = [
        re.sub(r"^status:.*$", "status: recurring", line)
        for line in head.splitlines()
    ]
    if any(line.startswith("occurrences:") for line in lines):
        lines = [
            re.sub(r"^occurrences:.*$", f"occurrences: {count}", line)
            for line in lines
        ]
    else:
        lines.append(f"occurrences: {count}")
    body += (
        f"\n---\n\n## Occurrence {count}, {when}, {project} ({platform})\n\n"
        "<!-- What happened this time, and why the earlier entry did not "
        "prevent it.\n     Then promote: evaluate-candidates, `recurring` "
        "branch. -->\n"
    )

    dest = root / "open" / entry.axis / f"promote-{entry.id}.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(lines) + "\n---\n" + body)
    if entry.path != dest:
        entry.path.unlink()
    print(f"lessons: {entry.id} now occurrences={count}, status=recurring")
    print(f"lessons: {dest}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT), help="candidates/ directory")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    p_match = sub.add_parser("match")
    p_match.add_argument("summary")
    p_record = sub.add_parser("record")
    p_record.add_argument("id")
    p_record.add_argument("--project", default=".")
    p_record.add_argument("--platform", default="claude")
    p_record.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args(argv)

    root = Path(args.root)
    entries = load(root)
    if args.cmd == "list":
        return cmd_list(entries)
    if args.cmd == "match":
        return cmd_match(entries, args.summary)
    return cmd_record(
        entries, args.id, args.project, args.platform, root, args.date
    )


if __name__ == "__main__":
    raise SystemExit(main())
