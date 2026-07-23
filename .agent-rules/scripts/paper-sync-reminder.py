#!/usr/bin/env python3
"""Stop hook: notice when a project's outputs have outrun its paper.

Shared across projects. Each project's own .claude/settings.json supplies
the outputs directory name, the paper repo's directory name, the per-run
summary filename, and the noun to use in the message, via CLI args, e.g.:

    paper-sync-reminder.py --outputs-dir outputs \\
        --paper-dir 67a9ea6275d3d9785ce57026 \\
        --summary-file run_summary.json --noun Runs

The paper is the primary living document, but folding results into it is a
separate step that is easy to postpone until the provenance of a number is
gone. This compares the newest run/result under the outputs dir against the
paper repo's last commit and says so if the outputs are ahead.

Advisory only, and deliberately so: plenty of sessions legitimately produce
output not worth writing up yet. It never blocks -- and to make sure a
missing/misconfigured copy of this script can't accidentally block either,
it must be invoked as a directly-executable file (chmod +x, no `python3`
prefix) in settings.json. That way, if the file ever goes missing, Claude
Code treats the command itself as not found and skips the hook (fails open),
rather than running `python3 <missing path>`, which would exit 2 -- and on a
Stop hook, exit 2 means "prevents Claude from stopping," which would hang
every session end for a reason that has nothing to do with this hook's own
logic.
"""

import os
import subprocess
import sys
from argparse import ArgumentParser
from pathlib import Path


def parse_args():
    parser = ArgumentParser()
    parser.add_argument("--outputs-dir", required=True)
    parser.add_argument("--paper-dir", required=True)
    parser.add_argument("--summary-file", required=True)
    parser.add_argument("--noun", default="Runs")
    args, _unknown = parser.parse_known_args()
    return args


def newest_mtime(root: Path, summary_file: str, limit: int = 4000) -> float:
    """Newest mtime among per-run summary files, capped so this stays instant."""
    newest = 0.0
    for count, path in enumerate(root.glob(f"*/{summary_file}")):
        if count >= limit:
            break
        try:
            newest = max(newest, path.stat().st_mtime)
        except OSError:
            continue
    return newest


def paper_last_commit(paper: Path) -> float:
    try:
        out = subprocess.run(
            ["git", "-C", str(paper), "log", "-1", "--format=%ct"],
            capture_output=True, text=True, timeout=10,
        )
        return float(out.stdout.strip()) if out.returncode == 0 and out.stdout.strip() else 0.0
    except (OSError, ValueError, subprocess.SubprocessError):
        return 0.0


def main() -> None:
    args = parse_args()

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if not project_dir:
        return  # not invoked as a live Claude Code hook; nothing to do
    repo = Path(project_dir)
    outputs = repo / args.outputs_dir
    paper = repo / args.paper_dir

    if not outputs.is_dir() or not paper.is_dir():
        return

    runs_at = newest_mtime(outputs, args.summary_file)
    paper_at = paper_last_commit(paper)
    if not runs_at or not paper_at or runs_at <= paper_at:
        return

    hours = (runs_at - paper_at) / 3600
    age = f"{hours:.0f}h" if hours >= 1 else f"{hours * 60:.0f}min"
    print(
        f"{args.noun} are {age} newer than the paper's last commit. "
        f"If this session produced something citable, run /update-paper; "
        f"if not, no action needed.",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
