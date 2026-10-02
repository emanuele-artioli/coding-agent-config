"""Targeted mistake detection, not a substitute for OS isolation."""

import json
import os
import time
from pathlib import Path
import re
import shlex
import sys

from .common import Refused, contained


def expand_protected(paths, max_entries=100000, seconds=5):
    """Protect external symlink targets recursively, with bounded discovery."""
    roots = set()
    visited = set()
    pending = [Path(path).expanduser() for path in paths]
    count = 0
    deadline = time.monotonic() + seconds
    while pending:
        root = pending.pop().resolve()
        roots.add(str(root))
        if root in visited or not root.is_dir():
            continue
        visited.add(root)
        directories = [root]
        while directories:
            with os.scandir(directories.pop()) as entries:
                for entry in entries:
                    count += 1
                    if count > max_entries or time.monotonic() > deadline:
                        raise Refused("protected symlink discovery exceeded its bound; review roots before running")
                    if entry.is_symlink():
                        pending.append(Path(entry.path))
                    elif entry.is_dir(follow_symlinks=False):
                        directories.append(Path(entry.path))
    return sorted(roots)


def protected_path(path, cwd, protected):
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = Path(cwd) / candidate
    return any(contained(candidate, root) or contained(root, candidate) for root in protected)


def inspect(tool, args, cwd, protected=()):
    if not isinstance(args, dict) or not isinstance(cwd, str):
        raise Refused("malformed protection payload")
    if tool in {"Read", "read_file", "view_file", "Glob", "Grep", "list_dir", "search", "update_plan", "request_user_input"}:
        return
    if tool in {"Bash", "Shell", "exec_command", "run_command", "run_terminal_command"}:
        command = args.get("command", args.get("cmd", args.get("CommandLine")))
        if not isinstance(command, str):
            raise Refused("shell command missing")
        destructive = [r"\bgit\b[^\n;&|]*\breset\b[^\n;&|]*--hard\b",
                       r"\bgit\b[^\n;&|]*\bclean\b[^\n;&|]*-[a-zA-Z]*f",
                       r"\bgit\b[^\n;&|]*\bpush\b[^\n;&|]*(--force|-f\b|--mirror|--prune|--delete|\s:[^\s]+)",
                       r"\bgit\b[^\n;&|]*\b(worktree\s+remove|reflog\s+expire|gc\s+.*--prune)",
                       r"\bgh\s+pr\s+merge\b"]
        if any(re.search(pattern, command) for pattern in destructive):
            raise Refused("destructive Git/integration operation requires explicit recovery authority")
        tokens = shlex.split(command, posix=True)
        for token in tokens:
            if token.startswith("-") or token in {"rm", "rmdir", "unlink", "mv", "cp"}:
                continue
            if protected_path(token, cwd, protected):
                if re.match(r"^\s*(ls|cat|head|tail|stat|file|rg|grep|find)\b", command) and not re.search(r"[>;]|\b(delete|exec)\b", command):
                    return
                raise Refused("command touches a protected path; use a read-only interface")
        return
    if tool in {"Edit", "Write", "Delete", "edit_file", "write_file", "delete_file",
                "write_to_file", "replace_file_content", "multi_replace_file_content"}:
        path = args.get("file_path", args.get("path", args.get("TargetFile")))
        if not isinstance(path, str):
            raise Refused("write path missing")
        if protected_path(path, cwd, protected):
            raise Refused("protected path is read-only")
        return
    if tool == "apply_patch":
        patch = args.get("patch", args.get("input", ""))
        paths = re.findall(r"^\*\*\* (?:Add File|Update File|Delete File|Move to): (.+)$", patch, re.M)
        if not paths:
            raise Refused("unrecognized patch payload")
        if any(protected_path(path, cwd, protected) for path in paths):
            raise Refused("patch changes protected evidence")
        return
    raise Refused(f"unrecognized tool {tool!r}; inspect before permitting it")


def hook_result(harness, reason):
    denied = reason is not None
    if harness in {"codex", "claude"}:
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                "permissionDecision": "deny" if denied else "allow",
                "permissionDecisionReason": reason or "within policy"}}
    if harness == "cursor":
        return {"permission": "deny" if denied else "allow", "continue": not denied,
                "user_message": reason or "", "agent_message": reason or ""}
    if harness == "antigravity":
        return {"decision": "deny" if denied else "allow", "reason": reason or "within policy"}
    raise Refused("unknown hook dialect")


def hook(harness, policy):
    reason = None
    try:
        payload = json.load(sys.stdin)
        tool_call = payload.get("toolCall", {})
        tool = payload.get("tool_name", tool_call.get("name"))
        args = payload.get("tool_input", tool_call.get("args"))
        if harness == "cursor" and "command" in payload and not tool:
            tool, args = "Shell", {"command": payload["command"]}
        cwd = payload.get("cwd") or (args or {}).get("Cwd") or (payload.get("workspace_roots") or payload.get("workspacePaths") or [None])[0]
        protected = json.loads(Path(policy).read_text()).get("protected_paths", [])
        project = Path(cwd).resolve()
        for directory in (project, *project.parents):
            declaration = directory / ".agent-guards.json"
            if declaration.is_file():
                guards = json.loads(declaration.read_text())
                paths = guards.get("protected_paths", []) + guards.get("protected_dirs", [])
                if not isinstance(paths, list) or not all(isinstance(path, str) for path in paths):
                    raise Refused("malformed project protected paths")
                protected += [str(Path(path).expanduser() if Path(path).is_absolute() else directory / path) for path in paths]
            if (directory / ".git").exists():
                break
        inspect(tool, args, cwd, expand_protected(protected))
    except Exception as error:
        reason = str(error)
    print(json.dumps(hook_result(harness, reason)))
    return 2 if reason else 0
