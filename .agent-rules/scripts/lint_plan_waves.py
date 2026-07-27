#!/usr/bin/env python3
"""Soft linter: Cursor plan files must declare waves or an explicit skip.

Host rule (AGENTS.md): complex multi-part plans split into parallel-agent
waves; sequential/small plans say ``skipped: sequential/small``.

Soft by default (exit 0, print advisories). ``--strict`` exits 1 if any
fail — reserved for a later hard gate.
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

SKIP_RE = re.compile(r"(?i)skipped:\s*sequential/small")
# ATX heading whose title mentions wave/waves (e.g. "## Parallel-agent waves",
# "## Wave 1 — …").
WAVE_HEADING_RE = re.compile(r"(?im)^#{1,6}\s+.*\bwaves?\b")

ADVISORY = (
    "plan-waves: add a waves section (or mermaid/table under a waves heading) "
    "or write `skipped: sequential/small` — see AGENTS.md / enforceable-rules.md"
)


def plan_ok(text: str) -> bool:
    return bool(SKIP_RE.search(text) or WAVE_HEADING_RE.search(text))


def iter_plan_files(roots: list[Path]) -> list[Path]:
    found: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        root = root.expanduser()
        if root.is_file() and root.name.endswith(".md"):
            resolved = root.resolve()
            if resolved not in seen:
                seen.add(resolved)
                found.append(resolved)
            continue
        if not root.is_dir():
            continue
        for path in sorted(root.glob("*.plan.md")):
            if not path.is_file():
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            found.append(resolved)
    return found


def filter_mtime(paths: list[Path], mtime_days: float | None) -> list[Path]:
    if mtime_days is None:
        return paths
    cutoff = time.time() - (mtime_days * 86400.0)
    return [p for p in paths if p.stat().st_mtime >= cutoff]


def check_paths(paths: list[Path]) -> list[tuple[Path, str]]:
    failures: list[tuple[Path, str]] = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            failures.append((path, f"unreadable: {exc}"))
            continue
        if not plan_ok(text):
            failures.append((path, ADVISORY))
    return failures


def default_roots() -> list[Path]:
    home_plans = Path.home() / ".cursor" / "plans"
    cwd_plans = Path.cwd() / ".cursor" / "plans"
    roots = [home_plans]
    if cwd_plans.resolve() != home_plans.resolve():
        roots.append(cwd_plans)
    return roots


def _self_test() -> int:
    cases = [
        ("# Ok\n\nskipped: sequential/small\n", True),
        ("# Ok\n\n## Parallel-agent waves\n\nWave 1…\n", True),
        ("# Ok\n\n## Wave 1 — Subagents\n", True),
        ("# Bad\n\n## Implementation\n\nDo A then B.\n", False),
        ("# Bad\n\nWe will do waves later.\n", False),  # body mention ≠ heading
    ]
    failed = 0
    for text, expect in cases:
        got = plan_ok(text)
        if got != expect:
            print(f"self-test FAIL: expect {expect} got {got} for {text!r}", file=sys.stderr)
            failed += 1
    if failed:
        print(f"self-test: {failed} failure(s)", file=sys.stderr)
        return 1
    print("self-test: ok", file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Plan files or directories (default: ~/.cursor/plans and ./.cursor/plans)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 if any plan fails (hard gate; soft is default)",
    )
    parser.add_argument(
        "--mtime-days",
        type=float,
        default=None,
        help="Only check plans modified within N days (hook mode uses this)",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run built-in detection fixtures and exit",
    )
    parser.add_argument(
        "--quiet-ok",
        action="store_true",
        help="Print nothing when all checked plans pass",
    )
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()

    roots = list(args.paths) if args.paths else default_roots()
    plans = filter_mtime(iter_plan_files(roots), args.mtime_days)
    if not plans:
        if not args.quiet_ok:
            print("plan-waves: no plan files matched", file=sys.stderr)
        return 0

    failures = check_paths(plans)
    for path, reason in failures:
        print(f"plan-waves soft: {path}: {reason}", file=sys.stderr)

    if not failures and not args.quiet_ok:
        print(f"plan-waves: {len(plans)} plan(s) ok", file=sys.stderr)

    if failures and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
