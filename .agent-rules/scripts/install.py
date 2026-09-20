#!/usr/bin/env python3
"""Create and verify this host's agent-config symlink farm (and MCP configs).

Every agent insists on finding rules, skills, subagents and slash-commands at
its own path, under its own filename. The content is authored once in
`~/.agent-rules/` and each agent's directory gets a symlink into it, so there
are no copies to drift apart.

This directory is also an Agent Plugins v1 package: portable core is
`plugin.json` + `AGENTS.md` + `skills/` + `mcp.json`. Hooks, `host.md`,
subagents, and the symlink farm are host-only (see `plugin.json` →
`extensions`).

    python3 install.py            # create anything missing; upsert MCP configs
    python3 install.py --check    # report only, exit 1 if anything is missing
                                  # (also validates the Agent Plugins core)

Deliberately conservative about which agents it touches:

  * A link is only created if its *parent agent directory already exists*
    (except `~/.gemini/config/`, which this script may create because
    Antigravity is installed and that is where it looks for global skills,
    workflows and MCP).
  * Codex links use `$CODEX_HOME` when set. The user skills path remains
    `~/.agents/skills`, which the installer creates once Codex exists.
  * A real file (not a symlink) sitting where a link belongs is reported as a
    conflict and left alone.

MCP configs are different: they are JSON files that may already hold
marketplace or personal servers. Shared servers are authored in portable
`mcp.json` (Agent Plugins schema) and upserted by name only — unrelated
entries are never removed. Secrets: `${env:NAME}` placeholders, never
plaintext.

Shared subagents reach Codex as generated `$CODEX_HOME/agents/<n>.toml`
files (written, not linked: Codex wants model and effort inline), with the
rungs read from `effort-models.json`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

HOST = Path(__file__).resolve().parent.parent
HOME = Path.home()
CODEX_HOME = Path(os.environ.get("CODEX_HOME", HOME / ".codex")).expanduser()

SKILLS = HOST / "skills"
AGENTS = HOST / "agents"
WORKFLOWS = HOST / "workflows"
PLUGIN_JSON = HOST / "plugin.json"
MCP_JSON = HOST / "mcp.json"
HOST_RULES = HOST / "AGENTS.md"
# Codex reads one concatenated AGENTS.md; sync_host_rules.py may generate a
# Codex-flavoured copy. Fall back to the plain host rules until it exists.
CODEX_HOST_RULES = HOST / "generated" / "codex-AGENTS.md"
EFFORT_MODELS = HOST / "effort-models.json"
CODEX_HOME_SET = "CODEX_HOME" in os.environ

PLUGIN_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
MCP_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"
PLUGIN_NAME_RE = re.compile(
    r"^(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$"
)
PLUGIN_TOP_LEVEL = {
    "$schema",
    "name",
    "version",
    "description",
    "author",
    "homepage",
    "repository",
    "license",
    "keywords",
    "extensions",
}


# ---------------------------------------------------------------------------
# Agent Plugins v1 portable core
# ---------------------------------------------------------------------------


def _frontmatter(path: Path) -> dict[str, str]:
    """Minimal YAML-ish frontmatter: `key: value` lines between --- fences."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    block = text[3:end].strip()
    out: dict[str, str] = {}
    for line in block.splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, _, val = line.partition(":")
        out[key.strip()] = val.strip().strip("\"'")
    return out


def validate_plugin() -> list[tuple[str, str]]:
    """Return (label, status) rows. Statuses other than ok/empty are problems."""
    rows: list[tuple[str, str]] = []

    if not PLUGIN_JSON.is_file():
        rows.append(("plugin.json", "missing"))
        return rows

    try:
        manifest = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        rows.append(("plugin.json", f"invalid JSON: {exc}"))
        return rows

    if not isinstance(manifest, dict):
        rows.append(("plugin.json", "not an object"))
        return rows

    unknown = sorted(set(manifest) - PLUGIN_TOP_LEVEL)
    if unknown:
        rows.append(("plugin.json", f"unknown top-level fields: {', '.join(unknown)}"))
    if manifest.get("$schema") != PLUGIN_SCHEMA:
        rows.append(("plugin.json $schema", "wrong or missing"))
    else:
        rows.append(("plugin.json $schema", "ok"))

    name = manifest.get("name")
    if not isinstance(name, str) or not PLUGIN_NAME_RE.match(name):
        rows.append(("plugin.json name", "invalid"))
    else:
        rows.append(("plugin.json name", "ok"))

    if MCP_JSON.is_file():
        try:
            mcp = json.loads(MCP_JSON.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            rows.append(("mcp.json", f"invalid JSON: {exc}"))
            mcp = None
        if isinstance(mcp, dict):
            if mcp.get("$schema") != MCP_SCHEMA:
                rows.append(("mcp.json $schema", "wrong or missing"))
            else:
                rows.append(("mcp.json $schema", "ok"))
            servers = mcp.get("mcpServers")
            if not isinstance(servers, dict):
                rows.append(("mcp.json mcpServers", "missing or not an object"))
            else:
                rows.append(
                    (
                        "mcp.json mcpServers",
                        "ok" if servers else "empty (no shared servers)",
                    )
                )
                for sname, spec in servers.items():
                    if not isinstance(spec, dict) or "type" not in spec:
                        rows.append((f"mcp.json:{sname}", "missing type"))
                    elif spec["type"] not in {"stdio", "streamable-http", "sse"}:
                        rows.append((f"mcp.json:{sname}", f"bad type {spec['type']!r}"))
                    else:
                        rows.append((f"mcp.json:{sname}", "ok"))
    else:
        rows.append(("mcp.json", "absent (ok until shared MCP is added)"))

    if not SKILLS.is_dir():
        rows.append(("skills/", "missing"))
        return rows

    skill_dirs = sorted(p for p in SKILLS.iterdir() if p.is_dir() and not p.name.startswith("."))
    if not skill_dirs:
        rows.append(("skills/", "empty"))
    for skill in skill_dirs:
        skill_md = skill / "SKILL.md"
        if not skill_md.is_file():
            rows.append((f"skills/{skill.name}", "missing SKILL.md"))
            continue
        fm = _frontmatter(skill_md)
        issues = []
        if not fm.get("name"):
            issues.append("no name")
        elif fm["name"] != skill.name:
            issues.append(f"name {fm['name']!r} != dir")
        if not fm.get("description"):
            issues.append("no description")
        rows.append(
            (
                f"skills/{skill.name}",
                "ok" if not issues else ", ".join(issues),
            )
        )
    return rows


def _ap_server_to_catalog(spec: dict) -> dict:
    """Map Agent Plugins mcpServers entry → host upsert shape."""
    stype = spec.get("type")
    if stype == "stdio":
        entry: dict = {"command": spec["command"]}
        if "args" in spec:
            entry["args"] = spec["args"]
        if "env" in spec:
            entry["env"] = spec["env"]
        return entry
    if stype in {"streamable-http", "sse"}:
        entry = {"url": spec["url"]}
        if "headers" in spec:
            entry["headers"] = spec["headers"]
        return entry
    raise ValueError(f"unsupported MCP server type: {stype!r}")


def load_catalog() -> dict[str, dict]:
    """Shared MCP servers, from the portable `mcp.json`."""
    if not MCP_JSON.is_file():
        return {}
    data = json.loads(MCP_JSON.read_text(encoding="utf-8"))
    servers = data.get("mcpServers") or {}
    if not isinstance(servers, dict):
        raise ValueError(f"{MCP_JSON}: 'mcpServers' must be an object")
    out: dict[str, dict] = {}
    for name, spec in servers.items():
        if not isinstance(spec, dict):
            raise ValueError(f"{MCP_JSON}: server {name!r} must be an object")
        out[str(name)] = _ap_server_to_catalog(spec)
    return out


# ---------------------------------------------------------------------------
# Symlink farm
# ---------------------------------------------------------------------------


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
            HOME / ".gemini" / "AGENTS.md",
            HOST_RULES,
            "Antigravity native global AGENTS.md (v1.20.3+)",
            requires=HOME / ".gemini",
        )
    )
    if not CODEX_HOST_RULES.is_file():
        # No generated concatenation yet: fall back to the portable source.
        # When it exists, apply_codex_agents() writes the absolutised copy.
        links.append(
            Link(
                CODEX_HOME / "AGENTS.md",
                HOST_RULES,
                "Codex global scope",
                requires=CODEX_HOME,
            )
        )

    links.append(
        Link(
            CODEX_HOME / "hooks.json",
            HOST / "harness" / "codex-hooks.json",
            "Codex lifecycle hooks",
            requires=CODEX_HOME,
        )
    )
    links.append(
        Link(
            HOME / "bin" / "git-clean-merged-worktrees",
            HOST / "scripts" / "clean-merged-worktrees.py",
            "cross-project git worktree cleanup CLI on PATH",
            requires=HOME / "bin",
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
                    requires=CODEX_HOME if CODEX_HOME.is_dir() else HOME / ".agents",
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
                    HOME / ".gemini" / "config" / "agents" / f"{stem}.md",
                    agent,
                    "Antigravity global agents",
                    requires=HOME / ".gemini" / "config",
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


def apply(item: Link) -> bool:
    """Create a missing link, preserving a link with an unexpected target."""
    if item.link.is_symlink():
        try:
            managed = item.link.resolve() == item.target.resolve()
        except OSError:
            managed = False
        return managed
    if item.link.exists():
        return False
    if item.create_parents:
        item.link.parent.mkdir(parents=True, exist_ok=True)
    item.link.symlink_to(relative_target(item.link, item.target))
    return True


# ---------------------------------------------------------------------------
# Shared subagents → generated Codex agent TOML
# ---------------------------------------------------------------------------
#
# Codex has no agent-file format that can be symlinked: it wants a TOML file
# per agent under `$CODEX_HOME/agents/`, carrying the model and reasoning
# effort inline. So these are *written*, not linked, and `--check` compares
# the rendered text with what is on disk. The rungs come from
# `effort-models.json` so this host has one map, not two.

# Every shared agent is a junior rung except the escalation one.
CODEX_ESCALATION_AGENTS = {"stuck-escalation"}
CODEX_OWNER_MARKER = "# coding-agent-config installer ownership: codex-v1"
CODEX_DIGEST_PREFIX = "# coding-agent-config installer digest: sha256:"

# Codex's native role schema is deliberately narrower than the shared Claude
# agent frontmatter.  Keep this contract next to the renderer so a source
# field cannot silently become a Codex setting just because it has a similar
# name on another harness.
CODEX_REQUIRED_RUNG_METADATA = {
    "junior": {"model": "gpt-5.6-luna", "effort": "max"},
    "escalation": {"model": "gpt-5.6-astra", "effort": "low"},
}
CODEX_CLAUDE_ONLY_FIELDS = ("tools", "omitClaudeMd", "maxTurns")
CODEX_SUPPORTED_FIELDS = (
    "name",
    "description",
    "developer_instructions",
    "model",
    "model_reasoning_effort",
)


def _split_frontmatter(path: Path) -> tuple[dict[str, str], str]:
    """Return (frontmatter mapping, body text after the closing fence)."""
    text = path.read_text(encoding="utf-8")
    fm = _frontmatter(path)
    if not text.startswith("---"):
        return fm, text.strip() + "\n"
    end = text.find("\n---", 3)
    if end < 0:
        return fm, text.strip() + "\n"
    rest = text[end + 4 :]
    _, _, body = rest.partition("\n")
    return fm, body.strip() + "\n"


def _toml_basic(value: str) -> str:
    """A TOML single-line basic string."""
    out = value.replace("\\", "\\\\").replace('"', '\\"')
    out = out.replace("\n", "\\n").replace("\t", "\\t").replace("\r", "\\r")
    return f'"{out}"'


def _toml_multiline(value: str) -> str:
    """A TOML multi-line basic string, safe for prose with quotes."""
    out = value.replace("\\", "\\\\").replace('"""', '\\"\\"\\"')
    if out.endswith('"'):
        out = out[:-1] + '\\"'
    return '"""\n' + out + '"""'


def _owned_codex_text(payload: str) -> str:
    """Prefix generated text with an ownership marker and payload digest."""
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"{CODEX_OWNER_MARKER}\n{CODEX_DIGEST_PREFIX}{digest}\n{payload}"


def _codex_ownership(text: str) -> str | None:
    """Return ``managed``, ``modified``, or ``None`` for legacy text."""
    lines = text.splitlines(keepends=True)
    if len(lines) < 3 or lines[0].rstrip("\r\n") != CODEX_OWNER_MARKER:
        return None
    digest_line = lines[1].rstrip("\r\n")
    if not digest_line.startswith(CODEX_DIGEST_PREFIX):
        return "modified"
    digest = digest_line[len(CODEX_DIGEST_PREFIX) :]
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        return "modified"
    payload = "".join(lines[2:])
    expected = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return "managed" if digest == expected else "modified"


def _atomic_write_text(path: Path, content: str) -> None:
    """Replace ``path`` atomically using a temporary file in its directory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    old_mode: int | None = None
    try:
        old_mode = path.stat().st_mode & 0o777
    except OSError:
        pass
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if old_mode is not None:
            os.chmod(temp_name, old_mode)
        os.replace(temp_name, path)
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass


def codex_rungs() -> dict[str, dict]:
    """The `codex` platform block of effort-models.json."""
    if not EFFORT_MODELS.is_file():
        return {}
    data = json.loads(EFFORT_MODELS.read_text(encoding="utf-8"))
    platforms = data.get("platforms")
    if not isinstance(platforms, dict):
        return {}
    codex = platforms.get("codex")
    return codex if isinstance(codex, dict) else {}


def validate_codex_rungs(rungs: dict[str, dict]) -> list[str]:
    """Return errors for stale or unsafe Codex role metadata.

    The model and effort values are a checked interface, rather than a best
    effort fallback.  A typo here would otherwise generate a valid-looking
    TOML file that dispatches the wrong rung.
    """
    issues: list[str] = []
    for rung, expected in CODEX_REQUIRED_RUNG_METADATA.items():
        spec = rungs.get(rung)
        if not isinstance(spec, dict):
            issues.append(f"missing platforms.codex.{rung} metadata")
            continue
        for key, value in expected.items():
            actual = spec.get(key)
            if actual != value:
                issues.append(
                    f"platforms.codex.{rung}.{key}={actual!r}; expected {value!r}"
                )

    capabilities = rungs.get("capabilities")
    if not isinstance(capabilities, dict):
        issues.append("missing platforms.codex.capabilities metadata")
    else:
        supported = capabilities.get("supported_fields")
        if supported != list(CODEX_SUPPORTED_FIELDS):
            issues.append(
                "platforms.codex.capabilities.supported_fields does not match "
                "the native Codex renderer"
            )
        omitted = capabilities.get("omitted_source_fields")
        if not isinstance(omitted, list) or any(
            field not in omitted for field in CODEX_CLAUDE_ONLY_FIELDS
        ):
            issues.append(
                "platforms.codex.capabilities.omitted_source_fields must include "
                "tools, omitClaudeMd, maxTurns"
            )
        if capabilities.get("diagnostic_mode") != "comments":
            issues.append(
                "platforms.codex.capabilities.diagnostic_mode must be 'comments'"
            )
    return issues


def _role_rung(agent: Path, frontmatter: dict[str, str]) -> str:
    """Read portable ``rung`` metadata, with a legacy filename fallback."""
    stem = agent.name.removesuffix(".agent.md")
    rung = frontmatter.get("rung")
    if rung is None:
        # Keep old source files readable while all canonical roles carry the
        # explicit field.  Once present, an invalid value is an error rather
        # than silently routing the role to junior.
        return "escalation" if stem in CODEX_ESCALATION_AGENTS else "junior"
    if rung not in CODEX_REQUIRED_RUNG_METADATA:
        raise ValueError(f"agents/{agent.name}: unsupported rung {rung!r}")
    return rung


def _codex_capabilities(rungs: dict[str, dict]) -> dict:
    capabilities = rungs.get("capabilities")
    return capabilities if isinstance(capabilities, dict) else {}


def codex_role_diagnostics(agent: Path, rungs: dict[str, dict]) -> list[str]:
    """Describe source controls intentionally omitted from a Codex artifact."""
    fm, _ = _split_frontmatter(agent)
    capabilities = _codex_capabilities(rungs)
    omitted = capabilities.get("omitted_source_fields")
    if not isinstance(omitted, list):
        omitted = list(CODEX_CLAUDE_ONLY_FIELDS)
    omitted_names = ", ".join(str(field) for field in omitted)
    present = [field for field in omitted if field in fm]
    present_note = (
        "present in this source: " + ", ".join(str(field) for field in present)
        if present
        else "none are present in this source"
    )
    return [
        "Codex capability diagnostics: omitted Claude-only source controls: "
        f"{omitted_names} ({present_note}).",
        "Codex capability diagnostics: source model/effort are overridden by "
        "the validated platforms.codex rung metadata.",
    ]


def render_codex_agent(agent: Path, rungs: dict[str, dict]) -> str:
    """Render one shared agent file as a Codex agent TOML."""
    issues = validate_codex_rungs(rungs)
    if issues:
        raise ValueError("invalid Codex role metadata: " + "; ".join(issues))
    fm, body = _split_frontmatter(agent)
    stem = agent.name.removesuffix(".agent.md")
    name = fm.get("name") or stem
    rung = _role_rung(agent, fm)
    spec = rungs.get(rung) or {}
    model = spec.get("model", "")
    effort = spec.get("effort", "")
    diagnostics = codex_role_diagnostics(agent, rungs)
    payload = (
        f"# Generated by scripts/install.py from agents/{agent.name}\n"
        f"# Rung: {rung} (effort-models.json → platforms.codex.{rung})\n"
        "# Edit the agent file, not this one.\n"
        + "".join(f"# {diagnostic}\n" for diagnostic in diagnostics)
        + f"name = {_toml_basic(name)}\n"
        + f"description = {_toml_basic(fm.get('description', ''))}\n"
        + f"developer_instructions = {_toml_multiline(body)}\n"
        + f"model = {_toml_basic(model)}\n"
        + f"model_reasoning_effort = {_toml_basic(effort)}\n"
    )
    return _owned_codex_text(payload)


def codex_host_rules_file() -> list[tuple[Path, str]]:
    """`$CODEX_HOME/AGENTS.md` with in-tree pointers made absolute.

    `generated/codex-AGENTS.md` stays portable so every checkout produces the
    same bytes and CI can check it. Codex reads its copy from outside the
    repo, where `` `../ `` resolves to nothing, so the absolute form is
    written here rather than generated into the tree.
    """
    if not CODEX_HOST_RULES.is_file():
        return []
    body = CODEX_HOST_RULES.read_text(encoding="utf-8")
    return [
        (
            CODEX_HOME / "AGENTS.md",
            _owned_codex_text(body.replace("`../", f"`{HOST}/")),
        )
    ]


def codex_agent_files() -> list[tuple[Path, str]]:
    """(destination path, rendered content) for every shared agent."""
    if not AGENTS.is_dir():
        return []
    rungs = codex_rungs()
    issues = validate_codex_rungs(rungs)
    if issues:
        raise ValueError("invalid Codex role metadata: " + "; ".join(issues))
    out: list[tuple[Path, str]] = []
    for agent in sorted(AGENTS.glob("*.agent.md")):
        stem = agent.name.removesuffix(".agent.md")
        out.append((CODEX_HOME / "agents" / f"{stem}.toml", render_codex_agent(agent, rungs)))
    return out


def _known_codex_symlink_target(dest: Path) -> Path | None:
    """Return the exact legacy target that this destination may replace."""
    if dest == CODEX_HOME / "AGENTS.md":
        # Older installers linked this file to the portable host rules. Keep
        # the generated copy in place when that exact link is encountered.
        return HOST_RULES
    agents_dir = CODEX_HOME / "agents"
    if dest.parent == agents_dir and dest.suffix == ".toml":
        source = AGENTS / f"{dest.stem}.agent.md"
        return source if source.is_file() else None
    return None


def apply_codex_agents(*, check: bool) -> list[tuple[str, str]]:
    """Write (or check) the generated Codex agent TOML files."""
    if not CODEX_HOME_SET or not CODEX_HOME.is_dir():
        return [("Codex shared agents (*.toml)", "skipped")]
    results: list[tuple[str, str]] = []
    try:
        generated = codex_host_rules_file() + codex_agent_files()
    except ValueError as exc:
        return [("Codex role model metadata", f"conflict: {exc}")]
    for dest, content in generated:
        label = (
            "Codex host rules AGENTS.md"
            if dest.name == "AGENTS.md"
            else f"Codex agent {dest.name}"
        )
        known_symlink = False
        if dest.is_symlink():
            # Only the exact links emitted by an older installer may be
            # replaced. A symlink into this checkout is not ownership proof.
            managed_target = _known_codex_symlink_target(dest)
            try:
                exact = managed_target is not None and dest.resolve() == managed_target.resolve()
            except OSError:
                exact = False
            if not exact or check:
                results.append((label, "conflict"))
                continue
            known_symlink = True
        if dest.exists() and not dest.is_file():
            results.append((label, "conflict"))
            continue
        current = dest.read_text(encoding="utf-8") if dest.is_file() else None
        if current == content:
            if dest.is_symlink():
                # An exact legacy link is still retired in apply mode so the
                # generated artifact owns its destination going forward.
                _atomic_write_text(dest, content)
                results.append((label, "updated"))
            else:
                results.append((label, "ok"))
            continue
        if check:
            results.append((label, "stale" if current is not None else "missing"))
            continue
        if current is not None and not known_symlink and _codex_ownership(current) != "managed":
            results.append((label, "conflict"))
            continue
        _atomic_write_text(dest, content)
        results.append((label, "updated" if current is not None else "created"))
    return results


# ---------------------------------------------------------------------------
# MCP catalog → per-platform configs
# ---------------------------------------------------------------------------


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
        results.append(("mcp.json shared servers", "empty (nothing to upsert)"))
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


def _plugin_row_is_problem(status: str) -> bool:
    if status in {"ok", "absent (ok until shared MCP is added)"}:
        return False
    if status.startswith("empty"):
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="report the farm's state without changing anything",
    )
    args = parser.parse_args()

    problems = 0

    print("Agent Plugins portable core:")
    for label, status in validate_plugin():
        print(f"{status:9} {label}")
        if _plugin_row_is_problem(status):
            problems += 1
    print()

    items = plan()
    width = max((len(str(i.link)) for i in items), default=40)

    for item in items:
        state = item.status()
        if state in {"missing", "wrong"} and not args.check:
            if apply(item):
                state = "created" if state == "missing" else "relinked"
            else:
                state = "conflict"
        if state in {"missing", "wrong", "conflict"}:
            problems += 1
        print(f"{state:9} {str(item.link):{width}}  {item.why}")

    print()
    for label, status in apply_codex_agents(check=args.check):
        print(f"{status:9} {label}")
        if status in {"missing", "stale", "conflict"}:
            problems += 1

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
        if problems:
            print(
                f"\n{problems} Agent Plugins core problem(s); farm links may still be ok.",
                file=sys.stderr,
            )
            return 1
    print("\nsymlink farm: consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
