#!/usr/bin/env python3
"""Regenerate marked mermaid regions in `.agent-rules/README.md`.

Walks the SoT tree so architecture diagrams cannot drift from the filesystem.
Usage:
  python3 render_architecture.py          # rewrite marked regions
  python3 render_architecture.py --check  # exit 1 if README is stale

Gate is standalone (not folded into install.py --check) so symlink-farm
checks stay fast and architecture freshness is an explicit opt-in.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HOST = Path(__file__).resolve().parent.parent
README = HOST / "README.md"

MARKERS = (
    ("arch:tree", "tree"),
    ("arch:flows", "flows"),
)


def _names(directory: Path, *, dirs: bool = False, suffix: str | None = None) -> list[str]:
    if not directory.is_dir():
        return []
    out: list[str] = []
    for path in sorted(directory.iterdir()):
        if path.name.startswith(".") or path.name == "__pycache__":
            continue
        if dirs and path.is_dir():
            out.append(path.name)
        elif not dirs and path.is_file():
            if suffix and not path.name.endswith(suffix):
                continue
            out.append(path.name)
    return out


def _safe_id(prefix: str, name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", name)
    return f"{prefix}_{cleaned}"


def _subgraph(lines: list[str], title: str, sid: str, names: list[str], prefix: str) -> None:
    lines.append(f"  subgraph {sid}[{title}]")
    if not names:
        lines.append(f"    {_safe_id(prefix, 'empty')}[(empty)]")
    for name in names:
        lines.append(f"    {_safe_id(prefix, name)}[{name}]")
    lines.append("  end")


def render_tree() -> str:
    skills = _names(HOST / "skills", dirs=True)
    agents = [n.removesuffix(".agent.md") for n in _names(HOST / "agents", suffix=".agent.md")]
    workflows = [n.removesuffix(".md") for n in _names(HOST / "workflows", suffix=".md")]
    harness = [n.removesuffix(".md") for n in _names(HOST / "harness", suffix=".md")]
    scripts = sorted(
        {
            *(_names(HOST / "scripts")),
            *(_names(HOST / "scripts", dirs=True)),
        }
        - {"cursor", "guardlib"}
    )
    cand = ["open/project", "open/platform", "done", "pending-verification"]

    lines = ["```mermaid", "flowchart TB"]
    _subgraph(lines, "skills/", "skills", skills, "sk")
    _subgraph(lines, "agents/", "agents", agents, "ag")
    _subgraph(lines, "workflows/", "workflows", workflows, "wf")
    _subgraph(lines, "harness/", "harness", harness, "ha")
    _subgraph(lines, "scripts/ (top-level)", "scripts", scripts, "sc")
    _subgraph(lines, "candidates/", "candidates", cand, "ca")
    lines.append("```")
    return "\n".join(lines) + "\n"


def render_flows() -> str:
    # Structural edges that the filesystem alone cannot fully express; kept
    # short and regenerated so skill/hook names stay current.
    cursor_hooks = [
        n.removesuffix(".py") for n in _names(HOST / "scripts" / "cursor", suffix=".py")
    ]
    has_eval = (HOST / "skills" / "evaluate-candidates").is_dir()
    has_eos = (HOST / "skills" / "end-of-session").is_dir()
    has_reminders = (HOST / "scripts" / "candidate-reminders.py").is_file()

    lines = [
        "```mermaid",
        "flowchart LR",
        "  subgraph cell [Any session]",
        "    Work[Project work on a platform]",
        "  end",
        "  Work -->|project axis| CQ[candidates queue]",
        "  Work -->|platform axis| CQ",
    ]
    if has_eval:
        lines += [
            "  CQ --> Eval[evaluate-candidates]",
            "  Eval -->|apply or discard| SoT[SoT / harness / projects]",
            "  Eval -->|needs other platform| Verify[pending-verification]",
        ]
    else:
        lines.append("  CQ --> SoT[SoT / harness / projects]")
    if has_reminders and has_eval:
        lines.append("  Verify -->|SessionStart reminder| OtherPlat[Owning platform]")
    if has_eos:
        lines += [
            "  Work -.->|close-out| Eos[end-of-session]",
            "  Eos -.-> CQ",
        ]
    if cursor_hooks:
        lines.append("  subgraph cursorHooks [Cursor adapters]")
        for name in cursor_hooks:
            lines.append(f"    {_safe_id('ch', name)}[{name}]")
        lines += [
            "  end",
            "  cursorHooks --> Guard[guardlib / context_nudge]",
            "  Install[install.py symlink farm] -.-> SoT",
        ]
    lines.append("```")
    return "\n".join(lines) + "\n"


RENDERERS = {
    "tree": render_tree,
    "flows": render_flows,
}


def _replace_region(text: str, marker: str, body: str) -> str:
    start = f"<!-- {marker}:start -->"
    end = f"<!-- {marker}:end -->"
    if start not in text or end not in text:
        raise SystemExit(f"README missing markers for {marker}")
    pattern = re.compile(
        re.escape(start) + r".*?" + re.escape(end),
        re.DOTALL,
    )
    replacement = f"{start}\n{body.rstrip()}\n{end}"
    new_text, n = pattern.subn(replacement, text, count=1)
    if n != 1:
        raise SystemExit(f"failed to replace region {marker}")
    return new_text


def render_readme(src: str) -> str:
    out = src
    for marker, key in MARKERS:
        out = _replace_region(out, marker, RENDERERS[key]())
    return out


def ensure_markers(text: str) -> str:
    """Insert markers if missing (bootstrap once)."""
    if "<!-- arch:flows:start -->" in text and "<!-- arch:tree:start -->" in text:
        return text
    if "<!-- arch:flows:start -->" not in text:
        text = re.sub(
            r"```mermaid\n.*?```",
            "<!-- arch:flows:start -->\n```mermaid\nPLACEHOLDER\n```\n<!-- arch:flows:end -->",
            text,
            count=1,
            flags=re.DOTALL,
        )
    if "<!-- arch:tree:start -->" not in text:
        needle = "## Layout\n"
        insert = (
            needle
            + "\n<!-- arch:tree:start -->\n```mermaid\nPLACEHOLDER\n```\n"
            "<!-- arch:tree:end -->\n"
        )
        if needle not in text:
            raise SystemExit("cannot bootstrap arch:tree — ## Layout missing")
        text = text.replace(needle, insert, 1)
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit 1 if README marked regions are stale",
    )
    args = parser.parse_args()

    current = README.read_text()
    bootstrapped = ensure_markers(current)
    rendered = render_readme(bootstrapped)

    if args.check:
        if current != rendered:
            print(
                "architecture diagrams stale — run: "
                "python3 .agent-rules/scripts/render_architecture.py",
                file=sys.stderr,
            )
            return 1
        print("architecture diagrams: fresh")
        return 0

    if current != rendered:
        README.write_text(rendered)
        print(f"updated {README}")
    else:
        print(f"unchanged {README}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
