"""Public CLI and private transport/supervisor entry points."""

import argparse
import io
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile

from . import harnesses, install as installer, runner, sandbox, transport
from .common import Refused, execute, home, identifier, machine, read_json, runtime, write_json


def doctor(probe=False, catalog=False, project=None):
    codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    result = {"machine": machine(), "python": sys.version.split()[0], "platform": platform.system(),
              "effective_codex_home": str(codex_home),
              "effective_claude_home": os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude")),
              "cursor_cli_config": str(Path(os.environ.get("CURSOR_CONFIG_DIR", str(Path(os.environ["XDG_CONFIG_HOME"]) / "cursor") if sys.platform != "darwin" and os.environ.get("XDG_CONFIG_HOME") else str(Path.home() / ".cursor"))) / "cli-config.json"), "state": str(home()), "runtime": str(runtime()),
              "harnesses": {name: harnesses.capability(name) for name in harnesses.NAMES},
              "unattended_agents": "Codex only, conditional on scoped sandbox probe and isolated subscription OAuth profile",
              "unattended_gpu": False,
              "note": "Other native agents and GPU passthrough remain gated pending isolated authentication/tool/device verification."}
    if probe:
        result["sandbox"] = sandbox.probe(scoped=True)
    policy = read_json(home() / "policy.json", {})
    result["policy"] = policy
    result["instructions"] = {}
    for name, path in {"codex": codex_home / "AGENTS.md", "claude": Path(os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude"))) / "CLAUDE.md",
                       "antigravity": Path.home() / ".gemini/config/AGENTS.md"}.items():
        result["instructions"][name] = {"path": str(path), "managed_content_present": path.exists() and installer.MARKER in path.read_text(),
                                          "native_loading": "requires a native-session verification; file presence alone is insufficient"}
    if catalog:
        try:
            result["native_codex_catalog"] = harnesses.skill_catalog(project or Path.cwd())
        except (Refused, OSError, ValueError) as error:
            result["native_codex_catalog"] = {"verified": False, "detail": str(error)}
    return result


def collect(task, destination):
    record = runner.load(task)
    if runner.status(task)["status"] in {"running", "unknown", "prepared"}:
        raise Refused("collect requires a stopped known task; use status/logs for live work")
    destination = Path(destination).resolve()
    if destination.exists():
        raise Refused("collection destination must be new; existing evidence is never overwritten")
    destination.mkdir(parents=True)
    for name in ("worker.jsonl", "supervisor.log", "evidence.json", "pr-body.md"):
        source = Path(record["workspace"]).parent / name
        if source.exists():
            shutil.copyfile(source, destination / name)
    # Collect regular outputs, rejecting links to unrelated data or credentials.
    for source in Path(record["output"]).rglob("*"):
        if source.is_symlink():
            raise Refused("output collection refuses symlinks")
        if source.is_file():
            target = destination / "output" / source.relative_to(record["output"])
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    workspace = record["workspace"]
    git = runner.trusted_git(record)
    execute([*git, "bundle", "create", str(destination / "snapshot.bundle"), "HEAD"], cwd=workspace, timeout=120)
    (destination / "changes.patch").write_bytes(execute([*git, "diff", "--binary", "HEAD"], cwd=workspace))
    untracked = execute([*git, "ls-files", "--others", "--exclude-standard", "-z"], cwd=workspace).decode().split("\0")
    for name in filter(None, untracked):
        source = Path(workspace) / name
        if source.is_symlink() or not source.resolve().is_relative_to(Path(workspace).resolve()):
            raise Refused("untracked work escapes snapshot")
        target = destination / "untracked" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    write_json(destination / "task.json", record)
    return {"id": task, "collected": str(destination), "artifacts_preserved": True}


def parser():
    p = argparse.ArgumentParser(prog="agentctl")
    commands = p.add_subparsers(dest="command", required=True)
    d = commands.add_parser("doctor", help="inspect installed interfaces, paths and containment")
    d.add_argument("--host")
    d.add_argument("--probe", action="store_true")
    d.add_argument("--catalog", action="store_true")
    d.add_argument("--project", type=Path)
    e = commands.add_parser("enroll", help="deploy an isolated package release to an SSH host")
    e.add_argument("--host", required=True)
    e.add_argument("--python", default="python3")
    e.add_argument("--codex-home")
    i = commands.add_parser("install", help="render managed configuration with backups")
    i.add_argument("--dry-run", action="store_true")
    i.add_argument("--home", type=Path)
    i.add_argument("--project", type=Path)
    i.add_argument("--codex-home", type=Path)
    i.add_argument("--harness", action="append", choices=harnesses.NAMES)
    i.add_argument("--retire-legacy", action="store_true")
    i.add_argument("--host")
    r = commands.add_parser("rollback")
    r.add_argument("transaction")
    r.add_argument("--host")
    run = commands.add_parser("run", help="prepare and supervise a bounded task from JSON")
    run.add_argument("spec", type=Path)
    run.add_argument("--host")
    run.add_argument("--attended", action="store_true")
    for name in ("status", "logs", "cancel", "handoff", "collect", "continue"):
        item = commands.add_parser(name)
        item.add_argument("task")
        item.add_argument("--host")
        if name == "logs":
            item.add_argument("--lines", type=int, default=40)
        if name == "collect":
            item.add_argument("--destination", type=Path, required=True)
        if name == "continue":
            item.add_argument("--prompt", required=True)
            item.add_argument("--seconds", type=float, required=True)
            item.add_argument("--attended", action="store_true")
    hook = commands.add_parser("hook", help="native protection adapter")
    hook.add_argument("harness", choices=harnesses.NAMES)
    hook.add_argument("--policy", required=True)
    supervisor = commands.add_parser("_supervise", help=argparse.SUPPRESS)
    supervisor.add_argument("task")
    receive = commands.add_parser("_receive", help=argparse.SUPPRESS)
    receive.add_argument("task")
    export = commands.add_parser("_export", help=argparse.SUPPRESS)
    export.add_argument("task")
    return p


def invoke(args):
    command = args.command
    if command == "hook":
        from .policy import hook
        raise SystemExit(hook(args.harness, args.policy))
    if command == "enroll":
        return transport.enroll(args.host, args.python, codex_home=args.codex_home)
    if command == "doctor":
        if args.host:
            return json.loads(transport.remote(args.host, ["doctor", *(["--probe"] if args.probe else []), *(["--catalog"] if args.catalog else []), *(["--project", str(args.project)] if args.project else [])], timeout=60))
        return doctor(args.probe, args.catalog, args.project)
    if command == "install":
        if args.host:
            argv = ["install"]
            if args.dry_run:
                argv.append("--dry-run")
            if args.retire_legacy:
                argv.append("--retire-legacy")
            for name in args.harness or ["codex"]:
                argv += ["--harness", name]
            if args.codex_home:
                argv += ["--codex-home", str(args.codex_home)]
            if args.project:
                argv += ["--project", str(args.project)]
            return json.loads(transport.remote(args.host, argv))
        changes = installer.plan_install(args.home, args.project, args.codex_home, args.harness or harnesses.NAMES, args.retire_legacy)
        return installer.install(changes, args.dry_run)
    if command == "rollback":
        if args.host:
            return json.loads(transport.remote(args.host, ["rollback", args.transaction]))
        return installer.rollback(args.transaction)
    if command == "run":
        spec = runner.validate_spec(read_json(args.spec))
        if args.host:
            return transport.dispatch(args.host, spec, args.attended)
        return runner.launch(runner.prepare(spec), args.attended)
    if command == "_supervise":
        runner.supervise(args.task)
        return runner.load(args.task)
    if command == "_receive":
        payload = runtime() / "incoming" / identifier(args.task)
        transport.extract(sys.stdin.buffer.read(), payload)
        spec = read_json(payload / "spec.json")
        return runner.launch(runner.prepare(spec, payload, args.task))
    if command == "_export":
        destination = runtime() / "exports" / (identifier(args.task) + "-" + __import__("uuid").uuid4().hex)
        collect(args.task, destination)
        sys.stdout.buffer.write(transport.archive_paths(destination, [path for path in destination.rglob("*") if path.is_file()]))
        return None
    host = transport.routed_host(args.task, args.host)
    if host:
        if command == "collect":
            data = transport.remote(host, ["_export", args.task], timeout=120)
            transport.extract(data, args.destination)
            return {"id": args.task, "collected": str(args.destination), "host": host}
        argv = [command, args.task]
        if command == "logs":
            argv += ["--lines", str(args.lines)]
        if command == "continue":
            if args.attended:
                raise Refused("attended continuation requires a terminal on the enrolled host")
            argv += ["--prompt", args.prompt, "--seconds", str(args.seconds)]
        try:
            return json.loads(transport.remote(host, argv))
        except Refused as error:
            if command == "status":
                return {"id": args.task, "host": host, "status": "unknown", "reason": str(error)}
            raise
    if command == "status":
        return runner.status(args.task)
    if command == "cancel":
        return runner.cancel(args.task)
    if command == "continue":
        return runner.continuation(args.task, args.prompt, args.seconds, args.attended)
    if command == "collect":
        return collect(args.task, args.destination)
    record = runner.status(args.task)
    if command == "logs":
        if not 1 <= args.lines <= 1000:
            raise Refused("lines must be between 1 and 1000")
        path = Path(record["log"])
        # Bound read size as well as returned line count.
        if not path.exists():
            return {"id": args.task, "lines": []}
        with path.open("rb") as stream:
            stream.seek(max(0, path.stat().st_size - 1024 * 1024))
            return {"id": args.task, "lines": stream.read().decode(errors="replace").splitlines()[-args.lines:]}
    if command == "handoff":
        return {key: record.get(key) for key in ("id", "status", "reason", "spec", "source_repo", "revision", "changes", "changes_digest", "workspace", "native_session", "checks", "artifacts", "compute_evidence", "pull_request")}
    raise Refused("unknown command")


def main():
    args = parser().parse_args()
    try:
        result = invoke(args)
        if result is not None:
            print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    except (Refused, OSError, ValueError, KeyError, BlockingIOError, subprocess.TimeoutExpired) as error:
        print(json.dumps({"status": "needs_attention", "reason": str(error)}), file=sys.stderr)
        raise SystemExit(2)
