"""Native CLI adapters. No provider/model selection or custom agent loop."""

import os
from pathlib import Path
import re
import shutil
import subprocess

from .common import Refused


NAMES = ("codex", "claude", "cursor", "antigravity")


def binary(name):
    candidates = {"codex": ["codex"], "claude": ["claude"], "cursor": ["agent", "cursor-agent"],
                  "antigravity": ["agy", str(Path.home() / ".gemini/bin/agy")]}
    if name not in candidates:
        raise Refused("unsupported harness")
    for candidate in candidates[name]:
        found = shutil.which(candidate)
        if found:
            return found
    raise Refused(f"{name} native CLI unavailable")


def capability(name):
    try:
        executable = binary(name)
        version = subprocess.run([executable, "--version"], capture_output=True, timeout=10)
        help_result = subprocess.run([executable, "exec", "--help"] if name == "codex" else [executable, "--help"], capture_output=True, timeout=10)
        help_text = (help_result.stdout + help_result.stderr).decode(errors="replace")
        required = {"codex": ["--json", "--sandbox"], "claude": ["--output-format", "--resume"],
                    "cursor": ["--output-format", "--resume", "--sandbox"],
                    "antigravity": ["--output-format", "--conversation", "--sandbox"]}[name]
        return {"available": True, "binary": executable, "version": version.stdout.decode(errors="replace").strip(),
                "interface_verified": help_result.returncode == 0 and all(flag in help_text for flag in required)}
    except (Refused, OSError, subprocess.TimeoutExpired) as error:
        return {"available": False, "interface_verified": False, "detail": str(error)}


def command(name, prompt, session=None, model=None):
    executable = binary(name)
    if name == "codex":
        # Native defaults retained. External sandbox remains authoritative.
        argv = [executable, "exec"]
        if session:
            argv += ["resume", session]
        argv += ["--json", "-c", 'approval_policy="never"']
        if not session:
            argv += ["--sandbox", "workspace-write"]
    elif name == "claude":
        argv = [executable, "-p", "--output-format", "stream-json", "--verbose",
                "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}']
        if session:
            argv += ["--resume", session]
    elif name == "cursor":
        argv = [executable, "-p", "--output-format", "stream-json", "--sandbox", "enabled"]
        if session:
            argv += ["--resume", session]
    else:
        argv = [executable, "-p", "--output-format", "stream-json", "--sandbox"]
        if session:
            argv += ["--conversation", session]
    if model:
        argv += ["--model", model]
    return [*argv, prompt]


def event_session(name, event):
    if name == "codex" and event.get("type") == "thread.started":
        return event.get("thread_id")
    return event.get("session_id", event.get("conversation_id"))


def skill_catalog(cwd):
    """Query native discovery without inference, session creation or API fallback."""
    import json
    import select
    import signal
    import time
    process = subprocess.Popen([binary("codex"), "app-server"], stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, start_new_session=True)
    pending = bytearray()
    def send(value):
        process.stdin.write((json.dumps(value) + "\n").encode())
        process.stdin.flush()
    def receive(number):
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            while b"\n" in pending:
                line, _, rest = pending.partition(b"\n")
                pending[:] = rest
                response = json.loads(line)
                if response.get("id") == number:
                    if "error" in response:
                        raise Refused("native skills/list rejected: " + str(response["error"]))
                    return response.get("result", {})
            ready, _, _ = select.select([process.stdout], [], [], 0.5)
            if ready:
                chunk = os.read(process.stdout.fileno(), 65536)
                if not chunk:
                    raise Refused("native catalog process ended before replying")
                pending.extend(chunk)
                if len(pending) > 4 * 1024 * 1024:
                    raise Refused("native catalog response exceeded its bound")
        raise Refused("native catalog timed out; discovery remains unverified")
    try:
        send({"id": 1, "method": "initialize", "params": {"clientInfo": {"name": "agentctl-doctor", "version": "0.1.0"}}})
        receive(1)
        send({"method": "initialized", "params": {}})
        send({"id": 2, "method": "skills/list", "params": {"cwds": [str(Path(cwd).resolve())], "forceReload": True}})
        result = receive(2)
        if not isinstance(result.get("data"), list):
            raise Refused("unknown native catalog schema")
        return [{"cwd": entry["cwd"], "skills": [{key: skill.get(key) for key in ("name", "path", "scope", "enabled")} for skill in entry.get("skills", [])],
                 "errors": entry.get("errors", [])} for entry in result["data"]]
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        process.stdin.close()
        process.stdout.close()
