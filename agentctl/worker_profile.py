"""Minimal Codex subscription profile without host credentials or MCP config."""

from importlib.resources import files
import json
import os
from pathlib import Path
import shutil
import shlex
import sys
import tomllib

from .common import Refused, write_json


def codex(record):
    source = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    auth_path = source / "auth.json"
    if not auth_path.is_file():
        raise Refused("isolated Codex needs saved subscription OAuth authentication; use attended execution")
    auth = json.loads(auth_path.read_text())
    if auth.get("auth_mode") != "chatgpt" or not auth.get("tokens", {}).get("access_token"):
        raise Refused("subscription OAuth required; API-key/provider fallback is disabled")
    auth.pop("OPENAI_API_KEY", None)
    base = Path(record["workspace"]).parent / "native-home"
    base.mkdir(exist_ok=True, mode=0o700)
    target = base / ".codex"
    target.mkdir(exist_ok=True, mode=0o700)
    write_json(target / "auth.json", auth)
    if (source / "config.toml").exists():
        configuration = tomllib.loads((source / "config.toml").read_text())
        # Retain native model preferences, not user plugins/providers/MCP servers.
        preferences = {key: configuration[key] for key in ("model", "model_reasoning_effort", "model_verbosity") if isinstance(configuration.get(key), str)}
    else:
        preferences = {}
    text = "\n".join(f"{key} = {json.dumps(value)}" for key, value in preferences.items())
    features = '\n[features]\napps = false\nbrowser_use = false\nbrowser_use_external = false\ncomputer_use = false\nplugins = false\nremote_plugin = false\nskill_mcp_dependency_install = false\n'
    (target / "config.toml").write_text(text + '\napproval_policy = "never"\nsandbox_mode = "workspace-write"\n' + features)
    content = files("agentctl").joinpath("content")
    evaluation = record["spec"].get("evaluation_guidance")
    guidance = evaluation["text"] if evaluation else content.joinpath("personal.md").read_text()
    (target / "AGENTS.md").write_text(guidance)
    skill_names = () if evaluation and evaluation["label"] != "slim" else ("remote-work", "handoff", "compute-preflight")
    for name in skill_names:
        path = base / ".agents/skills" / name
        path.mkdir(parents=True, exist_ok=True)
        (path / "SKILL.md").write_text(content.joinpath("skills", name, "SKILL.md").read_text())
    workspace = Path(record["workspace"])
    # Never load a project-local plugin/server/provider that escapes isolation.
    project_config = workspace / ".codex/config.toml"
    if (workspace / ".codex").is_symlink() or project_config.is_symlink():
        raise Refused("project-native configuration symlinks need attended review")
    if project_config.exists():
        data = tomllib.loads(project_config.read_text())
        if set(data) - {"model", "model_reasoning_effort", "model_verbosity", "approval_policy", "sandbox_mode", "developer_instructions"}:
            raise Refused("project-native external tools/providers require attended review")
    (workspace / ".codex").mkdir(exist_ok=True)
    policy = base / "policy.json"
    launcher = base / "agentctl-managed-hook.py"
    launcher.write_text(f"import sys\nsys.path.insert(0, {str(Path(__file__).resolve().parent.parent)!r})\nfrom agentctl.cli import main\nmain()\n")
    guarded = [str(workspace / ".codex"), str(target / "config.toml"), str(target / "hooks.json"), str(policy), str(launcher)]
    write_json(policy, {"protected_paths": [*record["protected"], *guarded]})
    hook_command = shlex.join([sys.executable, "-B", str(launcher), "hook", "codex", "--policy", str(policy)])
    write_json(target / "hooks.json", {"hooks": {"PreToolUse": [{"matcher": ".*", "hooks": [
        {"type": "command", "command": hook_command, "timeout": 10}]}]}})
    record["protected"] = list(dict.fromkeys([*record["protected"], *guarded]))
    return {"HOME": str(base), "CODEX_HOME": str(target), "SSH_AUTH_SOCK": "", "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1"}, base
