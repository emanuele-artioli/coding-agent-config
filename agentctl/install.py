"""Transactional, ownership-aware native configuration rendering."""

import base64
from importlib.resources import files
import json
import os
from pathlib import Path
import re
import shlex
import sys
import uuid

from .common import Refused, digest, home, lock, machine, read_json, write_json


MARKER = "agentctl managed"
SAFETY_MATCHER = "Bash|Shell|exec_command|Write|Edit|Delete|write_file|edit_file|delete_file|apply_patch|run_command|run_terminal_command|write_to_file|replace_file_content|multi_replace_file_content|mcp__.*"


def snapshot(path):
    if path.is_symlink():
        return {"kind": "link", "target": os.readlink(path)}
    if path.exists():
        if not path.is_file():
            raise Refused(f"configuration path is not a regular file: {path}")
        return {"kind": "file", "data": base64.b64encode(path.read_bytes()).decode(), "mode": path.stat().st_mode & 0o777}
    return {"kind": "absent"}


def restore(path, state):
    path = Path(path)
    if state["kind"] == "absent":
        if path.exists() or path.is_symlink():
            path.unlink()
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        path.unlink()
    if state["kind"] == "link":
        if path.exists():
            path.unlink()
        path.symlink_to(state["target"])
    else:
        path.write_bytes(base64.b64decode(state["data"]))
        path.chmod(state["mode"])


def text_state(text):
    return {"kind": "file", "data": base64.b64encode(text.encode()).decode(), "mode": 0o600}


def managed_text(old, body):
    start, end = f"<!-- {MARKER} begin -->", f"<!-- {MARKER} end -->"
    block = f"{start}\n{body.strip()}\n{end}\n"
    if start in old:
        if old.count(start) != 1 or old.count(end) != 1:
            raise Refused("damaged instruction ownership markers")
        return re.sub(re.escape(start) + r".*?" + re.escape(end) + r"\n?", lambda _: block, old, flags=re.S)
    return old.rstrip() + ("\n\n" if old.strip() else "") + block


def old_text(path):
    if path.is_symlink():
        raise Refused(f"refusing to overwrite an unmanaged symlink: {path}")
    return path.read_text() if path.exists() else ""


def toml_safety(old):
    import tomllib
    # Edit only root keys; keep comments, models, profiles, plugins and other settings.
    tomllib.loads(old)
    lines = old.splitlines(keepends=True)
    boundary = next((i for i, line in enumerate(lines) if line.lstrip().startswith("[")), len(lines))
    root = "".join(lines[:boundary])
    for key, value in {"approval_policy": '"on-request"', "sandbox_mode": '"workspace-write"'}.items():
        expression = rf"(?m)^\s*{key}\s*=.*$"
        replacement = f"{key} = {value} # {MARKER}"
        root = re.sub(expression, replacement, root) if re.search(expression, root) else root.rstrip() + "\n" + replacement + "\n"
    result = root + "".join(lines[boundary:])
    tomllib.loads(result)
    return result


def merge_hooks(data, name, entry, retire):
    hooks = data.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise Refused("unrecognized native hooks configuration")
    for event, entries in list(hooks.items()):
        if not isinstance(entries, list):
            raise Refused("unrecognized native hook entries")
        preserved = []
        for existing in entries:
            def owned(item):
                command = item.get("command", "")
                return "agentctl-managed-hook.py" in command or "agentctl hook" in command or "-m agentctl hook" in command or (retire and "/.agent-rules/" in command)
            if "hooks" in existing:
                existing = dict(existing)
                existing["hooks"] = [item for item in existing["hooks"] if not owned(item)]
                if existing["hooks"]:
                    preserved.append(existing)
            elif not owned(existing):
                preserved.append(existing)
        hooks[event] = preserved
    hooks.setdefault(name, []).append(entry)
    return data


def plan_install(base=None, project=None, codex_home=None, harnesses=("codex", "claude", "cursor", "antigravity"), retire=False):
    base = Path(base or Path.home()).resolve()
    source = files("agentctl").joinpath("content")
    body = source.joinpath("personal.md").read_text()
    control = home()
    policy_path = control / "policy.json"
    current_policy = read_json(policy_path, {"protected_paths": [], "remote_agents_forbidden": ["pointstream"]})
    changes = {str(policy_path): text_state(json.dumps(current_policy, indent=2) + "\n")}
    # Launcher imports from a stable, protected package installation. Deployment
    # copies the package before installing; no mutable project imports.
    package_root = Path(__file__).resolve().parent.parent
    launcher = control / "hosts" / machine() / "agentctl-managed-hook.py"
    launcher_text = f"import sys\nsys.path.insert(0, {str(package_root)!r})\nfrom agentctl.cli import main\nmain()\n"
    changes[str(launcher)] = text_state(launcher_text)
    if retire:
        for directory in (base / ".claude/agents", base / ".claude/skills", base / ".cursor/skills", base / ".codex/skills", base / ".gemini/skills"):
            if directory.is_dir():
                for alias in directory.iterdir():
                    if alias.is_symlink() and ".agent-rules/" in os.readlink(alias):
                        changes[str(alias)] = {"kind": "absent"}
    for harness in harnesses:
        if harness == "codex":
            root = Path(codex_home or os.environ.get("CODEX_HOME", str(base / ".codex"))).resolve()
            instructions, skills, hooks_path, event = root / "AGENTS.md", base / ".agents/skills", root / "hooks.json", "PreToolUse"
            config = root / "config.toml"
            changes[str(config)] = text_state(toml_safety(old_text(config)))
        elif harness == "claude":
            root = Path(os.environ.get("CLAUDE_CONFIG_DIR", str(base / ".claude"))).expanduser().resolve()
            instructions, skills, hooks_path, event = root / "CLAUDE.md", root / "skills", root / "settings.json", "PreToolUse"
        elif harness == "cursor":
            root = base / ".cursor"
            instructions = Path(project).resolve() / ".cursor/rules/agentctl.mdc" if project else control / "cursor-user-rule.md"
            skills, hooks_path, event = base / ".agents/skills", root / "hooks.json", "preToolUse"
        elif harness == "antigravity":
            root = base / ".gemini/config"
            instructions, skills, hooks_path, event = root / "AGENTS.md", root / "skills", root / "hooks.json", "PreToolUse"
        else:
            raise Refused(f"unsupported harness {harness}")
        existing = old_text(instructions)
        instruction_body = body
        if harness == "cursor" and project:
            instruction_body = body
            if not existing:
                existing = "---\nalwaysApply: true\n---\n"
        changes[str(instructions)] = text_state(managed_text(existing, instruction_body))
        if harness == "claude" and project:
            shim = Path(project).resolve() / "CLAUDE.md"
            changes[str(shim)] = text_state(managed_text(old_text(shim), "@AGENTS.md"))
        for name in ("remote-work", "handoff", "compute-preflight"):
            target = skills / name / "SKILL.md"
            text = source.joinpath("skills", name, "SKILL.md").read_text()
            if target.exists() and not old_text(target).startswith("---\nname: " + name + "\n"):
                raise Refused(f"skill conflicts with unrelated file: {target}")
            changes[str(target)] = text_state(text)
            if harness == "antigravity":
                changes[str(base / ".gemini/antigravity-cli/skills" / name / "SKILL.md")] = text_state(text)
        command = shlex.join([sys.executable, str(launcher), "hook", harness, "--policy", str(policy_path)])
        data = read_json(hooks_path, {})
        if harness in {"codex", "claude"}:
            entry = {"matcher": SAFETY_MATCHER, "hooks": [{"type": "command", "command": command, "timeout": 10}]}
        elif harness == "cursor":
            data.setdefault("version", 1)
            entry = {"matcher": SAFETY_MATCHER, "command": command, "timeout": 10, "failClosed": True}
        else:
            # Top-level names contain event buckets, unlike Claude/Codex.
            data["agentctl"] = {"PreToolUse": [{"matcher": SAFETY_MATCHER, "hooks": [
                {"type": "command", "command": command, "timeout": 10}]}]}
            changes[str(hooks_path)] = text_state(json.dumps(data, indent=2) + "\n")
            continue
        changes[str(hooks_path)] = text_state(json.dumps(merge_hooks(data, event, entry, retire), indent=2) + "\n")
    return changes


def install(changes, dry_run=False):
    ownership_path = home() / "hosts" / machine() / "ownership.json"
    ownership = read_json(ownership_path, {})
    operations = []
    for name, after in changes.items():
        before = snapshot(Path(name))
        if name in ownership and before != ownership[name]:
            raise Refused(f"managed configuration was edited; review conflict before reinstall: {name}")
        if name not in ownership and before["kind"] != "absent" and "/skills/" in name and before != after:
            raise Refused(f"unmanaged skill would be replaced: {name}")
        if before != after:
            operations.append({"path": name, "before": before, "after": after})
    result = {"dry_run": dry_run, "changes": [item["path"] for item in operations]}
    if dry_run or not operations:
        return result
    with lock("install"):
        transaction = uuid.uuid4().hex
        journal = home() / "installs" / f"{transaction}.json"
        write_json(journal, {"operations": operations, "previous_ownership": ownership, "machine": machine()})
        try:
            for item in operations:
                if snapshot(Path(item["path"])) != item["before"]:
                    raise Refused("configuration changed during installation")
                restore(item["path"], item["after"])
                ownership[item["path"]] = item["after"]
            write_json(ownership_path, ownership)
        except Exception:
            for item in reversed(operations):
                if snapshot(Path(item["path"])) == item["after"]:
                    restore(item["path"], item["before"])
            raise
        result["transaction"] = transaction
        return result


def rollback(transaction):
    from .common import identifier
    with lock("install"):
        path = home() / "installs" / f"{identifier(transaction)}.json"
        record = read_json(path)
        if record["machine"] != machine():
            raise Refused("rollback must run on the host owning this transaction")
        for item in record["operations"]:
            if snapshot(Path(item["path"])) not in (item["after"], item["before"]):
                raise Refused(f"rollback would overwrite subsequent edits: {item['path']}")
        for item in reversed(record["operations"]):
            restore(item["path"], item["before"])
        write_json(home() / "hosts" / machine() / "ownership.json", record["previous_ownership"])
        return {"rolled_back": transaction}
