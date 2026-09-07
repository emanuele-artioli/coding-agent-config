#!/usr/bin/env python3
"""CLI: Safely clean up git worktrees whose branches/commits are fully merged.

Never touches dirty worktrees (modified, staged, or untracked).
Compares against origin/main (or origin/master) to ensure no unmerged work is lost.

Usage:
    python3 clean-merged-worktrees.py [--dry-run] [--quiet] [--target-ref REF]
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Keep bytecode off NFS
sys.pycache_prefix = os.environ.get("PYTHONPYCACHEPREFIX") or "/var/tmp/emanuele-pycache"

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from guardlib import worktree_cleanup  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report which worktrees would be removed without actually removing them.",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress output unless worktrees were removed or errors occur.",
    )
    parser.add_argument(
        "--target-ref",
        default=None,
        help="Upstream reference to compare against (default: auto-detect origin/main or origin/master).",
    )
    parser.add_argument(
        "--repo-dir",
        default=None,
        help="Path inside the git repository (default: current working directory).",
    )
    args = parser.parse_args(argv)

    repo_root = worktree_cleanup.get_repo_root(args.repo_dir or Path.cwd())
    if not repo_root:
        if not args.quiet:
            print("Error: Not inside a git repository.", file=sys.stderr)
        return 1

    report = worktree_cleanup.scan_worktrees(repo_root, target_ref=args.target_ref)

    to_remove = [w for w in report.worktrees if w.action == "remove"]
    if not to_remove and args.quiet:
        return 0

    if not args.quiet:
        print(f"Repository: {report.repo_root}")
        print(f"Upstream reference: {report.target_branch}")
        print(f"Total worktrees found: {len(report.worktrees)}")

    worktree_cleanup.execute_cleanup(report, dry_run=args.dry_run)

    for wt in report.worktrees:
        if wt.is_root:
            continue
        if wt.action == "remove":
            status = "[DRY-RUN WOULD REMOVE]" if args.dry_run else "[REMOVED]"
            print(f"{status} {wt.path} ({wt.reason})")
        elif not args.quiet:
            print(f"[SKIPPED] {wt.path} ({wt.reason})")
            if wt.unmerged_commits:
                for commit in wt.unmerged_commits[:5]:
                    print(f"    * {commit}")
                if len(wt.unmerged_commits) > 5:
                    print(f"    * ... and {len(wt.unmerged_commits) - 5} more commits")

    if not args.quiet:
        summary_action = "would be removed" if args.dry_run else "removed"
        print(f"\nDone: {report.removed_count} {summary_action}, {report.skipped_count} skipped.")

    return 0


if __name__ == "__main__":
    sys.exit(main())

