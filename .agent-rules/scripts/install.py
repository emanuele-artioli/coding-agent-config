#!/usr/bin/env python3
"""Create and verify this host's agent-config symlink farm (and MCP configs).

Every agent insists on finding rules, skills, subagents and slash-commands at
its own path, under its own filename. The content is authored once in
`~/.agent-rules/` and each agent's directory gets a symlink into it, so there
are no copies to drift apart.

    python3 install.py            # create anything missing; upsert MCP configs
    python3 install.py --check    # report only, exit 1 if anything is missing

Deliberately conservative about which agents it touches:

  * A link is only created if its *parent agent directory already exists*
    (except `~/.gemini/config/`, which this script may create because
    Antigravity is installed and that is where it looks for global skills,
    workflows and MCP).
  * Codex (`~/.codex`, `~/.agents`) links are skipped until those tools exist.
  * A real file (not a symlink) sitting where a link belongs is reported as a
    conflict and left alone.

MCP configs are different: they are JSON/TOML files that may already hold
marketplace or personal servers. The catalog at `mcp/catalog.json` is upserted
by name only — unrelated entries are never removed. Secrets are never stored
in the catalog; use `${env:NAME}` placeholders.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

HOST = Path(__file__).resolve().parent.parent
HOME = Path.home()

SKILLS = HOST / "skills"
AGENTS = HOST / "agents"
WORKFLOWS = HOST / "workflows"
MCP_CATALOG = HOST / "mcp" / "catalog.json"
HOST_RULES = HOST / "AGENTS.md"


@dataclass
class Link:
    link: Path
    target: Path
    why: str
    # Directory that must already exist for this link to be wanted at all.
    requires: Path | None = None
    # Directories this script may create on the way (only ever inside an
    # agent directory that already exists, or ~/.gemini/config/).
    create_parents: bool = False

    @property
    def wanted(self) -> bool:
        return self.requires is None or self.requires.is_dir()

    def status(self) -> str:
        if not self.wanted:
            return "skipped"
        if self.link.is_symlink():
            return "ok" if self.link.resolve() == self.target.resolve() else "wrong"
        if self.link.exists():
            return "conflict"
        return "missing"


def plan() -> list[Link]:
    links: list[Link] = []

    # --- host-wide prose -------------------------------------------------
    links.append(
        Link(
            HOME / "AGENTS.md",
            HOST_RULES,
            "Cursor, for a session opened on the home directory",
        )
    )
    links.append(
        Link(
            HOME / "CLAUDE.md",
            HOST_RULES,
            "Claude Code, for a session opened on the home directory",
        )
    )
    links.append(
        Link(
            HOME / ".gemini" / "AGENTS.md",
            HOST_RULES,
            "Antigravity native global AGENTS.md (v1.20.3+)",
            requires=HOME / ".gemini",
        )
    )
    links.append(
        Link(
            HOME / ".codex" / "AGENTS.md",
            HOST_RULES,
            "Codex global scope",
            requires=HOME / ".codex",
        )
    )

    # --- skills ----------------------------------------------------------
    if SKILLS.is_dir():
        for skill in sorted(p for p in SKILLS.iterdir() if p.is_dir()):
            links.append(
                Link(
                    HOME / ".claude" / "skills" / skill.name,
                    skill,
                    "Claude Code (and Cursor, which also reads this path)",
                    requires=HOME / ".claude",
                    create_parents=True,
                )
            )
            links.append(
                Link(
                    HOME / ".gemini" / "config" / "skills" / skill.name,
                    skill,
                    "Antigravity global skills",
                    requires=HOME / ".gemini",
                    create_parents=True,
                )
            )
            links.append(
                Link(
                    HOME / ".copilot" / "skills" / skill.name,
                    skill,
                    "Copilot CLI personal skills",
                    requires=HOME / ".copilot",
                    create_parents=True,
                )
            )
            links.append(
                Link(
                    HOME / ".agents" / "skills" / skill.name,
                    skill,
                    "cross-tool global skills (Codex, Cursor, Copilot)",
                    requires=HOME / ".agents",
                    create_parents=True,
                )
            )

    # --- subagents -------------------------------------------------------
    if AGENTS.is_dir():
        for agent in sorted(AGENTS.glob("*.agent.md")):
            stem = agent.name.removesuffix(".agent.md")
            links.append(
                Link(
                    HOME / ".claude" / "agents" / f"{stem}.md",
                    agent,
                    "Claude Code (and Cursor, as a compatibility path)",
                    requires=HOME / ".claude",
                    create_parents=True,
                )
            )
            links.append(
                Link(
                    HOME / ".cursor" / "agents" / f"{stem}.md",
                    agent,
                    "Cursor native global agents path",
                    requires=HOME / ".cursor",
                    create_parents=True,
                )
            )
            links.append(
                Link(
                    HOME / ".copilot" / "agents" / agent.name,
                    agent,
                    "Copilot CLI personal agents",
                    requires=HOME / ".copilot",
                    create_parents=True,
                )
            )

    # --- workflows / slash commands --------------------------------------
    # Claude does not get these: its slash surface is skills. Cursor wants
    # ~/.cursor/commands/<name>.md; Antigravity wants
    # ~/.gemini/config/global_workflows/<name>.md.
    if WORKFLOWS.is_dir():
        for workflow in sorted(WORKFLOWS.glob("*.md")):
            if workflow.name.startswith("."):
                continue
            links.append(
                Link(
                    HOME / ".cursor" / "commands" / workflow.name,
                    workflow,
                    "Cursor global slash commands",
                    requires=HOME / ".cursor",
                    create_parents=True,
                )
            )
            links.append(
                Link(
                    HOME / ".gemini" / "config" / "global_workflows" / workflow.name,
                    workflow,
                    "Antigravity global workflows",
                    requires=HOME / ".gemini",
                    create_parents=True,
                )
            )

    return links


def relative_target(link: Path, target: Path) -> str:
    try:
        return os.path.relpath(target, link.parent)
    except ValueError:
        return str(target)


def apply(item: Link) -> None:
    if item.create_parents:
        item.link.parent.mkdir(parents=True, exist_ok=True)
    if item.link.is_symlink():
        item.link.unlink()
    item.link.symlink_to(relative_target(item.link, item.target))


# ---------------------------------------------------------------------------
# MCP catalog → per-platform configs
# ---------------------------------------------------------------------------


def load_catalog() -> dict[str, dict]:
    if not MCP_CATALOG.is_file():
        return {}
    data = json.loads(MCP_CATALOG.read_text())
    servers = data.get("servers") or {}
    if not isinstance(servers, dict):
        raise ValueError(f"{MCP_CATALOG}: 'servers' must be an object")
    return {str(k): v for k, v in servers.items() if isinstance(v, dict)}


def _cursor_entry(spec: dict) -> dict:
    """Cursor mcp.json entry from a catalog server spec."""
    if "url" in spec or "serverUrl" in spec:
        entry: dict = {"url": spec.get("url") or spec.get("serverUrl")}
        if "headers" in spec:
            entry["headers"] = spec["headers"]
        if "auth" in spec:
            entry["auth"] = spec["auth"]
        return entry
    entry = {"command": spec["command"]}
    if "args" in spec:
        entry["args"] = spec["args"]
    if "env" in spec:
        entry["env"] = spec["env"]
    if "envFile" in spec:
        entry["envFile"] = spec["envFile"]
    return entry


def _antigravity_entry(spec: dict) -> dict:
    """Antigravity mcp_config.json entry — remote servers use serverUrl."""
    if "url" in spec or "serverUrl" in spec:
        entry: dict = {"serverUrl": spec.get("serverUrl") or spec.get("url")}
        if "headers" in spec:
            entry["headers"] = spec["headers"]
        return entry
    entry = {"command": spec["command"]}
    if "args" in spec:
        entry["args"] = spec["args"]
    if "env" in spec:
        entry["env"] = spec["env"]
    return entry


def _claude_entry(spec: dict) -> dict:
    """Claude Code .mcp.json / ~/.claude.json mcpServers entry."""
    return _cursor_entry(spec)


def _read_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def upsert_mcp_servers(
    path: Path,
    key: str,
    catalog: dict[str, dict],
    render,
    *,
    check: bool,
) -> str:
    """Upsert catalog servers under `data[key]`. Returns a status token."""
    if not catalog:
        return "empty"
    data = _read_json(path)
    bucket = data.get(key)
    if not isinstance(bucket, dict):
        bucket = {}
    desired = {name: render(spec) for name, spec in catalog.items()}
    changed = False
    for name, entry in desired.items():
        if bucket.get(name) != entry:
            bucket[name] = entry
            changed = True
    data[key] = bucket
    if not changed and path.is_file():
        return "ok"
    if check:
        return "stale" if path.is_file() else "missing"
    _write_json(path, data)
    return "updated" if path.is_file() else "created"


def mcp_targets(catalog: dict[str, dict]) -> list[tuple[str, Path, str, object]]:
    """(label, path, json_key, render_fn) for each platform config we manage."""
    return [
        (
            "Cursor global MCP",
            HOME / ".cursor" / "mcp.json",
            "mcpServers",
            _cursor_entry,
        ),
        (
            "Antigravity global MCP",
            HOME / ".gemini" / "config" / "mcp_config.json",
            "mcpServers",
            _antigravity_entry,
        ),
        # Claude user-level MCP lives inside ~/.claude.json alongside credentials.
        # We only upsert the mcpServers key; everything else is left untouched.
        (
            "Claude Code user MCP (~/.claude.json)",
            HOME / ".claude.json",
            "mcpServers",
            _claude_entry,
        ),
    ]


def apply_mcp(*, check: bool) -> list[tuple[str, str]]:
    catalog = load_catalog()
    results: list[tuple[str, str]] = []
    if not catalog:
        results.append(("mcp catalog", "empty (no shared servers to upsert)"))
        return results
    for label, path, key, render in mcp_targets(catalog):
        # Only touch Claude's ~/.claude.json when it already exists — never
        # create a credentials file from scratch.
        if path.name == ".claude.json" and not path.is_file() and not path.is_symlink():
            results.append((label, "skipped (no ~/.claude.json yet)"))
            continue
        if path == HOME / ".gemini" / "config" / "mcp_config.json" and not (
            HOME / ".gemini"
        ).is_dir():
            results.append((label, "skipped"))
            continue
        if path == HOME / ".cursor" / "mcp.json" and not (HOME / ".cursor").is_dir():
            results.append((label, "skipped"))
            continue
        status = upsert_mcp_servers(path, key, catalog, render, check=check)
        results.append((label, status))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="report the farm's state without changing anything",
    )
    args = parser.parse_args()

    items = plan()
    width = max((len(str(i.link)) for i in items), default=40)
    problems = 0

    for item in items:
        state = item.status()
        if state in {"missing", "wrong"} and not args.check:
            apply(item)
            state = "created" if state == "missing" else "relinked"
        if state in {"missing", "wrong", "conflict"}:
            problems += 1
        print(f"{state:9} {str(item.link):{width}}  {item.why}")

    print()
    for label, status in apply_mcp(check=args.check):
        print(f"{status:9} {label}")
        if status in {"missing", "stale"}:
            problems += 1

    if args.check and problems:
        print(
            f"\n{problems} item(s) missing, wrong, stale or blocked. "
            "Run: python3 install.py",
            file=sys.stderr,
        )
        return 1
    if not args.check:
        conflicts = [i for i in items if i.status() == "conflict"]
        if conflicts:
            print(
                f"\n{len(conflicts)} path(s) hold a real file where a symlink belongs; "
                "left untouched, resolve by hand.",
                file=sys.stderr,
            )
            return 1
    print("\nsymlink farm: consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
