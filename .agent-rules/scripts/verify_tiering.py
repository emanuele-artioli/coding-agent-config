#!/usr/bin/env python3
"""Verify that tiering a project's AGENTS.md lost nothing.

The tiered layout splits each project's hand-written `AGENTS.md` into an
always-on core (`.claude/project-core.md`) plus one deferred rule file per
`<!-- scope: ... -->` section. The whole design rests on one claim:

    every line an agent used to read is still delivered, only later

That is exactly the kind of claim a smoke test cannot make -- the generator
will happily produce well-formed files that are missing a paragraph. So this
checks conservation directly: every non-blank line of `AGENTS.md`, outside the
generated host-rules block, must appear in the core or in exactly one rule
file, and nothing may appear in both.

    python3 verify_tiering.py            # every project in projects.json
    python3 verify_tiering.py pointstream presley

Exit status is 1 if any project fails, so it is usable as a gate. Safe to run
from any agent on any platform -- it only reads.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import sync_agent_rules as sync  # noqa: E402

HOST_DIR = Path(__file__).resolve().parent.parent
PROJECTS_JSON = HOST_DIR / "projects.json"


def project_roots(selected: list[str]) -> list[Path]:
    roots: list[Path] = []
    if PROJECTS_JSON.is_file():
        data = json.loads(PROJECTS_JSON.read_text())
        entries = data.get("projects", data) if isinstance(data, dict) else data
        for entry in entries:
            path = entry.get("path") if isinstance(entry, dict) else entry
            if path:
                roots.append(Path(path).expanduser())
    if selected:
        roots = [root for root in roots if root.name in selected]
    return roots


def meaningful(text: str) -> Counter[str]:
    """Non-blank content lines, ignoring generator scaffolding."""
    lines: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("<!-- scope:"):
            continue
        lines.append(line)
    return Counter(lines)


def strip_banner(text: str) -> str:
    """Drop generated frontmatter and the banner comment from a rule file."""
    body = text
    if body.startswith("---\n"):
        body = body.split("\n---\n", 1)[-1]
    if sync.BANNER in body:
        body = body.split("-->", 1)[-1]
    return body


def check(root: Path) -> list[str] | None:
    """Problems found, or None when this project is not tiered (nothing to check)."""
    agents_md = root / "AGENTS.md"
    core_md = root / ".claude" / "project-core.md"
    if not agents_md.is_file() or not core_md.is_file():
        return None

    source = sync.HOST_BLOCK.sub("\n", agents_md.read_text())
    expected = meaningful(source)

    delivered: Counter[str] = Counter()
    core_text = strip_banner(core_md.read_text())
    # The core's own "Rules that load on demand" index is generated signposting,
    # not project content; cut it before comparing.
    core_text = core_text.split("\n## Rules that load on demand", 1)[0]
    delivered += meaningful(core_text)

    rules_dir = root / ".claude" / "rules"
    seen_twice: list[str] = []
    if rules_dir.is_dir():
        for rule in sorted(rules_dir.glob("*.md")):
            text = rule.read_text()
            if sync.BANNER not in text:
                continue  # hand-written rule, not ours to account for
            counts = meaningful(strip_banner(text))
            for line in counts:
                if line in delivered and line in counts:
                    seen_twice.append(line)
            delivered += counts

    problems: list[str] = []
    missing = expected - delivered
    for line, count in sorted(missing.items()):
        problems.append(f"LOST ({count}x): {line[:96]}")
    extra = delivered - expected
    for line, count in sorted(extra.items()):
        problems.append(f"INVENTED ({count}x): {line[:96]}")
    for line in sorted(set(seen_twice)):
        # Duplicated one-liners like "- one" are noise; only flag real prose.
        if len(line) > 40:
            problems.append(f"DUPLICATED: {line[:96]}")
    return problems


def main() -> int:
    roots = project_roots(sys.argv[1:])
    if not roots:
        print("no projects found (checked projects.json)", file=sys.stderr)
        return 1

    failed = 0
    checked = 0
    for root in roots:
        problems = check(root)
        if problems is None:
            print(f"skip {root.name} (not tiered)")
            continue
        checked += 1
        if problems:
            failed += 1
            print(f"FAIL {root.name}")
            for problem in problems:
                print(f"     {problem}")
        else:
            print(f"ok   {root.name}")
    print()
    print(f"{checked - failed}/{checked} tiered project(s) conserve every rule line")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
