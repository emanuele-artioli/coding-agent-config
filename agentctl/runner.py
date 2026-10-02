"""Detached native-task supervision and supervisor-owned compute admission."""

import base64
import hashlib
from contextlib import ExitStack
import json
import math
import os
from pathlib import Path
import resource
import shutil
import signal
import socket
import subprocess
import sys
import time
import threading
import uuid

from . import compute, harnesses, sandbox, worker_profile
from .common import Refused, contained, digest, execute, home, identifier, lock, machine, read_json, runtime, write_json
from .policy import inspect, expand_protected


TERMINAL = {"succeeded", "failed", "cancelled", "needs_attention"}


def record_path(task):
    return home() / "tasks" / f"{identifier(task)}.json"


def load(task):
    return read_json(record_path(task))


def save(record):
    record["updated"] = time.time()
    write_json(record_path(record["id"]), record)


def validate_spec(spec):
    if spec.get("kind") not in {"agent", "command", "compute"}:
        raise Refused("kind must be agent, command or compute")
    budget = spec.get("seconds")
    if not compute.finite(budget) or budget <= 0:
        raise Refused("positive finite seconds budget required")
    evaluation = spec.get("evaluation_guidance")
    if evaluation is not None and (not isinstance(evaluation, dict) or evaluation.get("label") not in {"native", "legacy", "slim"} or not isinstance(evaluation.get("text"), str) or spec.get("publish", True)):
        raise Refused("evaluation guidance requires a named explicit text profile and publication disabled")
    resources = spec.get("resources")
    if not isinstance(resources, dict) or not isinstance(resources.get("cpu_threads"), int) or isinstance(resources.get("cpu_threads"), bool) or resources["cpu_threads"] < 1:
        raise Refused("explicit positive cpu_threads resource limit required")
    memory = resources.get("memory_mb")
    if not compute.finite(memory) or memory <= 0:
        raise Refused("explicit positive memory_mb limit required")
    if spec.get("paid_compute") and not spec.get("paid_compute_authorized"):
        raise Refused("paid compute requires explicit task authority")
    if resources.get("gpu_uuid") and (not compute.finite(resources.get("gpu_memory_mb")) or resources["gpu_memory_mb"] <= 0):
        raise Refused("GPU jobs require a memory estimate")
    if resources.get("gpu_uuid") or budget >= 7200 or spec["kind"] == "compute":
        if spec["kind"] != "compute":
            raise Refused("GPU production and multi-hour commands must use kind=compute")
        compute.validate(spec.get("compute"), budget)
    if spec["kind"] == "agent":
        if spec.get("harness") not in harnesses.NAMES or not isinstance(spec.get("prompt"), str):
            raise Refused("agent tasks require a supported harness and prompt")
        if not spec.get("checks"):
            raise Refused("coding tasks require explicit verification commands")
    if spec["kind"] == "command":
        argv = spec.get("argv")
        if not isinstance(argv, list) or not argv or not all(isinstance(item, str) for item in argv):
            raise Refused("command tasks require argv as a nonempty string list")
    for argv in spec.get("checks", []):
        if not isinstance(argv, list) or not argv or not all(isinstance(item, str) for item in argv):
            raise Refused("checks must be argv lists")
    if spec.get("project_adapter") not in {None, "pointstream"}:
        raise Refused("unknown project adapter")
    if spec.get("project_adapter") == "pointstream":
        if spec["kind"] == "agent":
            raise Refused("PointStream prohibits remote agent sessions")
        argv = spec.get("argv", [])
        if spec["kind"] == "command" and "experiments.jobs.fleet" not in argv:
            raise Refused("PointStream dispatch must use its existing fleet entrypoint")
    return spec


def snapshot(spec, destination):
    repository = Path(spec["repo"]).expanduser().resolve()
    if not (repository / ".git").exists():
        raise Refused("repo must be a normal Git checkout or worktree")
    revision = execute(["git", "rev-parse", "--verify", spec.get("revision", "HEAD") + "^{commit}"], cwd=repository).decode().strip()
    selected = spec.get("changes", [])
    if not isinstance(selected, list) or not all(isinstance(item, str) for item in selected):
        raise Refused("changes must explicitly name relative files")
    for name in selected:
        path = repository / name
        if Path(name).is_absolute() or ".." in Path(name).parts or not contained(path, repository):
            raise Refused("selected change escapes the source checkout")
        if path.is_dir() or ".git" in Path(name).parts:
            raise Refused("select individual files, not directories or Git internals")
    destination.mkdir(parents=True, exist_ok=False)
    # HEAD is a named bundle tip; arbitrary revisions are represented by a
    # temporary independent bare repository, never by a ref in the source.
    bare = destination / "bundle-source.git"
    execute(["git", "clone", "--bare", "--no-hardlinks", "--", str(repository), str(bare)], timeout=120)
    execute(["git", "update-ref", "refs/heads/agentctl-snapshot", revision], cwd=bare)
    execute(["git", "bundle", "create", str(destination / "snapshot.bundle"), "refs/heads/agentctl-snapshot"], cwd=bare, timeout=120)
    patch = execute(["git", "--literal-pathspecs", "diff", "--binary", revision, "--", *selected], cwd=repository) if selected else b""
    (destination / "changes.patch").write_bytes(patch)
    untracked = {}
    for name in selected:
        tracked = execute(["git", "--literal-pathspecs", "ls-files", "--", name], cwd=repository)
        path = repository / name
        if not tracked and path.exists():
            if path.is_symlink():
                raise Refused("untracked symlinks are not transferred")
            untracked[name] = base64.b64encode(path.read_bytes()).decode()
    write_json(destination / "untracked.json", untracked)
    try:
        origin = execute(["git", "remote", "get-url", "origin"], cwd=repository).decode().strip()
    except Refused:
        origin = None
    # Remove only the temporary bare clone created above, never the source.
    shutil.rmtree(bare)
    return {"revision": revision, "changes": selected, "changes_digest": digest({"patch": base64.b64encode(patch).decode(), "untracked": untracked}),
            "origin": origin, "source_repo": str(repository)}


def prepare(spec, payload=None, task=None):
    validate_spec(spec)
    task = identifier(task or uuid.uuid4().hex)
    with lock(task):
        if record_path(task).exists():
            raise Refused("task already exists; inspect it instead of replaying")
        task_root = runtime() / "tasks" / task
        task_root.mkdir(parents=True, exist_ok=False, mode=0o700)
        if payload:
            payload = Path(payload).resolve()
            metadata = read_json(payload / "metadata.json")
        else:
            payload = task_root / "snapshot"
            metadata = snapshot(spec, payload)
        policy = read_json(home() / "policy.json", {"protected_paths": [], "remote_agents_forbidden": ["pointstream"]})
        forbidden = policy.get("remote_agents_forbidden", ["pointstream"])
        repository_names = {Path(metadata["source_repo"]).name.casefold(), str(metadata.get("origin") or "").rstrip("/").split("/")[-1].removesuffix(".git").casefold()}
        if spec["kind"] == "agent" and (repository_names.intersection(name.casefold() for name in forbidden) or spec.get("project_adapter") == "pointstream"):
            raise Refused("project policy prohibits remote agent sessions")
        workspace = task_root / "workspace"
        execute(["git", "clone", "--no-hardlinks", "--", str(payload / "snapshot.bundle"), str(workspace)], timeout=120)
        execute(["git", "switch", "-c", f"codex/agentctl-{task}", metadata["revision"]], cwd=workspace)
        patch = (payload / "changes.patch").read_bytes()
        if patch:
            execute(["git", "apply", "--binary", "-"], cwd=workspace, input=patch)
        for name, data in read_json(payload / "untracked.json").items():
            target = workspace / name
            if not contained(target, workspace) or ".git" in Path(name).parts or Path(name).is_absolute():
                raise Refused("snapshot path escapes checkout")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(base64.b64decode(data, validate=True))
        if metadata.get("origin"):
            execute(["git", "remote", "set-url", "origin", metadata["origin"]], cwd=workspace)
        artifact_root = home().parent / "agentctl-artifacts" / machine() / task
        artifact_root.mkdir(parents=True, exist_ok=False, mode=0o700)
        output = artifact_root / "output"
        output.mkdir()
        scratch = task_root / "scratch"
        scratch.mkdir()
        protected = [str(Path(path).expanduser().resolve()) for path in policy.get("protected_paths", [])]
        project_guards = read_json(workspace / ".agent-guards.json", {})
        if not isinstance(project_guards, dict):
            raise Refused("malformed project protection declarations")
        for path in project_guards.get("protected_paths", []) + project_guards.get("protected_dirs", []):
            candidate = Path(path).expanduser()
            protected.append(str((candidate if candidate.is_absolute() else workspace / candidate).resolve()))
        protected += [str((Path(path).expanduser() if Path(path).is_absolute() else workspace / path).resolve()) for path in spec.get("read_only", [])]
        protected = expand_protected(protected)
        protected += [str(home()), str(Path(__file__).resolve().parent), str(task_root / "evidence.json")]
        record = {"id": task, "status": "prepared", "spec": spec, **metadata,
                  "machine": machine(), "workspace": str(workspace), "output": str(output), "scratch": str(scratch),
                  "durable_artifacts": str(artifact_root), "log": str(task_root / "worker.jsonl"), "supervisor_log": str(task_root / "supervisor.log"),
                  "protected": protected, "configuration_revision": digest(policy),
                  "created": time.time(), "spent_seconds": 0, "checks": [], "artifacts": [str(output)]}
        save(record)
        return record


def launch(record, attended=False):
    if attended:
        supervise(record["id"], attended=True)
    else:
        # This process tree survives the client and its SSH connection.
        argv = [sys.executable, "-B", "-m", "agentctl", "_supervise", record["id"]]
        environment = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parent.parent), PYTHONDONTWRITEBYTECODE="1")
        with open(record["supervisor_log"], "ab") as stream:
            supervisor = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=stream, stderr=stream,
                             start_new_session=True, cwd=Path(__file__).resolve().parent.parent, env=environment)
        threading.Thread(target=supervisor.wait, daemon=True).start()
    return load(record["id"])


def gpu_admission(resources):
    requested = resources.get("gpu_uuid")
    if not requested:
        return None
    devices = execute(["nvidia-smi", "--query-gpu=uuid,memory.free,memory.used,utilization.gpu", "--format=csv,noheader,nounits"]).decode()
    processes = execute(["nvidia-smi", "--query-compute-apps=gpu_uuid,pid", "--format=csv,noheader,nounits"]).decode()
    for row in devices.splitlines():
        gpu, free, used, utilization = [part.strip() for part in row.split(",")]
        if gpu == requested:
            if gpu in processes or float(used) > 256 or float(utilization) > 5 or float(free) < resources["gpu_memory_mb"] + 4096:
                raise Refused("requested GPU is occupied or lacks the memory estimate plus 4 GiB headroom")
            return gpu
    raise Refused("requested GPU UUID is unavailable")


def descendant_rss(root, rows):
    """Include children that create new process groups or sessions."""
    processes = {}
    for row in rows:
        fields = row.split()
        if len(fields) == 3:
            pid, parent, rss = map(int, fields)
            processes[pid] = (parent, rss)
    owned = {root}
    while True:
        children = {pid for pid, (parent, _) in processes.items() if parent in owned}
        expanded = owned | children
        if expanded == owned:
            return sum(processes[pid][1] for pid in owned if pid in processes)
        owned = expanded


def worker_limits(resources):
    def apply():
        # Virtual reservations are not physical RAM (Node reserves large arenas).
        if sys.platform != "darwin" and resources.get("address_space_mb"):
            memory = int(resources["address_space_mb"] * 1024 * 1024)
            resource.setrlimit(resource.RLIMIT_AS, (memory, memory))
        if hasattr(os, "sched_setaffinity"):
            available = sorted(os.sched_getaffinity(0))
            os.sched_setaffinity(0, available[:resources["cpu_threads"]])
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    return apply


def run_process(record, argv, seconds, attended, label, environment=None):
    if seconds <= 0:
        raise Refused("task budget exhausted")
    inspect("exec_command", {"cmd": __import__("shlex").join(argv)}, record["workspace"], record["protected"])
    # No inherited provider/cloud credentials, agent sockets or host overrides.
    env = {key: value for key, value in os.environ.items() if key in {"PATH", "LANG", "TERM", "TZ", "SSL_CERT_FILE", "SSL_CERT_DIR"} or key.startswith("LC_")}
    isolated_home = Path(record["scratch"]) / "home"
    isolated_home.mkdir(exist_ok=True)
    env["HOME"] = str(isolated_home)
    if attended:
        # Attended native sessions use the human's existing subscription profile.
        env["HOME"] = str(Path.home())
        if os.environ.get("CODEX_HOME"):
            env["CODEX_HOME"] = os.environ["CODEX_HOME"]
    threads = str(record["spec"]["resources"]["cpu_threads"])
    env.update({"OMP_NUM_THREADS": threads, "MKL_NUM_THREADS": threads, "OPENBLAS_NUM_THREADS": threads,
                "TMPDIR": record["scratch"], "PYTHONDONTWRITEBYTECODE": "1",
                "CUDA_VISIBLE_DEVICES": record["spec"]["resources"].get("gpu_uuid", "-1"),
                "AGENTCTL_OUTPUT": record["output"]})
    env.update(environment or {})
    executable_root = str(Path(shutil.which(argv[0]) or argv[0]).resolve().parent)
    if not attended:
        writable = [record["output"], record["scratch"]]
        protected = list(record["protected"])
        if record["spec"]["kind"] == "compute":
            protected.append(record["workspace"])
        else:
            writable.append(record["workspace"])
        if record.get("native_home"):
            writable.append(record["native_home"])
        readable = [record["workspace"], sys.prefix, str(Path(__file__).resolve().parent.parent), executable_root]
        readable += record["spec"].get("read_only", []) + record["spec"].get("read_paths", [])
        readable += expand_protected([str(Path(path) if Path(path).is_absolute() else Path(record["workspace"]) / path) for path in record["spec"].get("read_only", [])])
        readable = [str((Path(path) if Path(path).is_absolute() else Path(record["workspace"]) / path).resolve()) for path in readable]
        if record.get("native_home"):
            readable.append(record["native_home"])
        argv = sandbox.wrap(argv, writable, protected, network=record["spec"].get("network", record["spec"]["kind"] == "agent"), readable=readable)
    start = time.monotonic()
    with open(record["log"], "ab", buffering=0) as stream:
        stream.write((json.dumps({"agentctl_stage": label, "started": time.time()}) + "\n").encode())
        process = subprocess.Popen(argv, cwd=record["workspace"], env=env, stdin=None if attended else subprocess.DEVNULL,
                                   stdout=stream, stderr=stream, start_new_session=True,
                                   preexec_fn=worker_limits(record["spec"]["resources"]))
        record["worker_pid"] = process.pid
        record["stage"] = label
        save(record)
        try:
            last_memory_check = 0
            while process.poll() is None:
                if (Path(record["workspace"]).parent / "cancel.request").exists():
                    raise InterruptedError("task cancelled; artifacts preserved")
                if time.monotonic() - start >= seconds:
                    raise Refused(f"{label}: runtime budget exhausted")
                if time.monotonic() - last_memory_check > 0.5:
                    rows = execute(["ps", "-eo", "pid=,ppid=,rss="], timeout=5).decode().splitlines()
                    rss = descendant_rss(process.pid, rows)
                    if rss > record["spec"]["resources"]["memory_mb"] * 1024:
                        raise Refused(f"{label}: process-tree memory budget exhausted")
                    last_memory_check = time.monotonic()
                time.sleep(0.1)
        finally:
            # The group is created by this Popen and is killed only while its
            # leader is our live child; never act on a stale recorded PID.
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
            if process.poll() is None:
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
            record["spent_seconds"] += time.monotonic() - start
            record.pop("worker_pid", None)
            save(record)
        if process.returncode:
            raise Refused(f"{label}: process exited {process.returncode}; inspect logs")


def compute_run(record, attended):
    spec = record["spec"]
    protocol = spec["compute"]
    required = compute.validate(protocol, spec["seconds"])
    def actual_identity():
        workspace = Path(record["workspace"])
        files = execute(["git", "ls-files", "-z"], cwd=workspace).decode().split("\0")
        files += execute(["git", "ls-files", "--others", "--exclude-standard", "-z"], cwd=workspace).decode().split("\0")
        identities = {}
        for name in filter(None, files):
            path = workspace / name
            if path.is_symlink():
                identities[name] = {"link": os.readlink(path)}
            elif path.is_file():
                identities[name] = hashlib.sha256(path.read_bytes()).hexdigest()
            else:
                identities[name] = "absent"
        for name in protocol.get("fingerprint_files", []):
            path = Path(name)
            path = path if path.is_absolute() else workspace / path
            hasher = hashlib.sha256()
            with path.open("rb") as source:
                for block in iter(lambda: source.read(1024 * 1024), b""):
                    hasher.update(block)
            identities["input:" + name] = hasher.hexdigest()
        executable_ids = {}
        for stage in protocol["stages"].values():
            executable = Path(shutil.which(stage["argv"][0]) or stage["argv"][0]).resolve()
            if executable.is_file():
                stat = executable.stat()
                executable_ids[str(executable)] = [stat.st_size, stat.st_mtime_ns]
        return compute.fingerprint(record["revision"], {"selected_changes": record["changes_digest"], "actual_files": identities}, protocol,
                                   {"declared": protocol["runtime_environment"], "python": sys.version, "executables": executable_ids},
                                   {"declared": protocol["hardware"], "machine": machine(), "gpu": spec["resources"].get("gpu_uuid")})
    identity = actual_identity()
    evidence_path = Path(record["workspace"]).parent / "evidence.json"
    evidence = read_json(evidence_path, {})
    if spec.get("reuse_evidence"):
        previous = load(spec["reuse_evidence"])
        if previous["machine"] != machine():
            raise Refused("evidence belongs to a different machine")
        evidence = read_json(Path(previous["workspace"]).parent / "evidence.json")
        if evidence.get("fingerprint") != identity:
            raise Refused("requested evidence is stale; run a new preflight")
        evidence = {**evidence, "reused_from": previous["id"]}
    # Evidence is supervisor-owned, outside every writable worker root.
    if evidence.get("fingerprint") != identity:
        evidence = {"fingerprint": identity, "stages": {}, "candidates": []}
    candidates = protocol["candidates"]
    selected = next((candidate for candidate in candidates if candidate["name"] == evidence.get("selected_candidate")), candidates[0])
    preflight_start = time.monotonic()
    for name in required:
        if name == "full":
            compute.admissible(evidence, identity, required)
        elif evidence["stages"].get(name, {}).get("passed"):
            continue
        stage = protocol["stages"][name]
        trials = candidates if name == "pilot" else [selected]
        eligible = []
        for candidate in trials:
            if actual_identity() != identity:
                raise Refused("code, inputs or runtime changed during preflight; evidence invalidated")
            output = Path(record["output"]) / f"{name}-{candidate['name']}"
            if output.exists():
                raise Refused("stage output already exists; inspect instead of overwriting evidence")
            output.mkdir()
            argv = compute.render(stage, candidate, output)
            remaining = spec["seconds"] - record["spent_seconds"]
            if name != "full":
                remaining = min(remaining, protocol["preflight_seconds"] - (time.monotonic() - preflight_start))
            run_process(record, argv, min(stage["seconds"], remaining), attended, f"{name}:{candidate['name']}")
            metrics_path = output / stage["metrics_file"]
            if not contained(metrics_path, output):
                raise Refused("metrics_file must remain inside its stage output")
            observed = compute.metrics(metrics_path, protocol["targets"], require_target=name in {"confirmation", "full"})
            if name != "pilot" or compute.meets(observed, protocol["targets"]):
                eligible.append((observed["cost"], candidate, observed))
        if name == "pilot":
            if not eligible:
                raise Refused("no pilot configuration met the target within the bounded search")
            _, selected, _ = min(eligible, key=lambda item: item[0])
            evidence["selected_candidate"] = selected["name"]
            evidence["candidates"] = [{"name": candidate["name"], "observed": observed} for _, candidate, observed in eligible]
        evidence["stages"][name] = {"passed": True, "completed": time.time(), "candidate": selected["name"]}
        if actual_identity() != identity:
            raise Refused("stage changed code, inputs or runtime; evidence invalidated")
        write_json(evidence_path, evidence)
        record["compute_evidence"] = evidence
        save(record)


def trusted_git(record):
    """Never execute worker-controlled hooks/helpers outside its sandbox."""
    workspace = Path(record["workspace"])
    gitdir = workspace / ".git"
    if gitdir.is_symlink() or not gitdir.is_dir() or gitdir.resolve().parent != workspace.resolve():
        raise Refused("worker altered Git directory ownership; recover manually")
    if any(path.is_symlink() for path in gitdir.rglob("*")):
        raise Refused("worker introduced a Git metadata symlink; recover manually")
    configuration = gitdir / "config"
    if configuration.is_symlink() or not configuration.is_file():
        raise Refused("worker altered Git configuration path; recover manually")
    backup = workspace.parent / "git-config-before-collection"
    if not backup.exists():
        backup.write_bytes(configuration.read_bytes())
    configuration.write_text('[core]\nrepositoryformatversion = 0\nbare = false\nlogallrefupdates = true\nfsmonitor = false\n')
    git = ["git", "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false", "-c", "commit.gpgSign=false"]
    if record.get("origin"):
        execute([*git, "remote", "add", "origin", record["origin"]], cwd=workspace)
    return git


def publish(record):
    workspace = record["workspace"]
    if not record.get("origin"):
        raise Refused("publication needs an origin; work remains recoverable")
    git = trusted_git(record)
    execute([*git, "add", "--all"], cwd=workspace)
    if execute([*git, "status", "--porcelain"], cwd=workspace):
        execute([*git, "commit", "-m", f"Complete agentctl task {record['id']}"], cwd=workspace, timeout=60)
    branch = f"codex/agentctl-{record['id']}"
    execute([*git, "push", "--set-upstream", "origin", branch], cwd=workspace, timeout=120)
    existing = json.loads(execute(["gh", "pr", "list", "--head", branch, "--state", "open", "--json", "url"], cwd=workspace))
    if existing:
        url = existing[0]["url"]
    else:
        body = Path(workspace).parent / "pr-body.md"
        body.write_text(f"Completed task {record['id']}.\n\nVerification:\n" + "\n".join(f"- {item['argv']}: passed" for item in record["checks"]) + "\n")
        url = execute(["gh", "pr", "create", "--draft", "--head", branch, "--title", f"Agentctl task {record['id']}", "--body-file", str(body)], cwd=workspace, timeout=60).decode().strip()
    record["pull_request"] = url
    record["published_revision"] = execute([*git, "rev-parse", "HEAD"], cwd=workspace).decode().strip()
    save(record)


def supervise(task, attended=False):
    with lock(task), ExitStack() as claims:
        record = load(task)
        if record["machine"] != machine() or record["status"] != "prepared":
            raise Refused("task is not prepared on this machine")
        record["supervisor_pid"] = os.getpid()
        record["started"] = time.time()
        record["status"] = "running"
        save(record)
        try:
            if not attended:
                verification = sandbox.probe(scoped=True)
                record["sandbox"] = verification
                if not verification["verified"]:
                    raise Refused(verification["detail"])
                # Local file/MCP children inherit isolation. Hosted tools and
                # socket/egress routes need independent harness attestation.
                if record["spec"]["kind"] == "agent" and record["spec"]["harness"] != "codex":
                    raise Refused("this harness lacks a verified isolated subscription/tool profile; use attended execution")
            resources = record["spec"]["resources"]
            if resources.get("cpu_threads", 1) > (os.cpu_count() or 1):
                raise Refused("CPU request exceeds host capacity")
            if resources.get("gpu_uuid"):
                claims.enter_context(lock("gpu-" + resources["gpu_uuid"]))
                record["gpu_claim"] = gpu_admission(resources)
                if not attended:
                    raise Refused("GPU device passthrough is not yet sandbox-verified; use the attended project dispatcher")
            spec = record["spec"]
            package = Path(__file__).resolve().parent
            record["runner_revision"] = digest({str(path.relative_to(package)): hashlib.sha256(path.read_bytes()).hexdigest() for path in package.rglob("*") if path.is_file() and "__pycache__" not in path.parts})
            if spec["kind"] == "compute":
                compute_run(record, attended)
            else:
                environment = None
                argv = spec["argv"] if spec["kind"] == "command" else harnesses.command(spec["harness"], spec["prompt"], record.get("native_session"), spec.get("model"))
                if spec["kind"] == "agent" and not attended:
                    environment, native_home = worker_profile.codex(record)
                    record["native_home"] = str(native_home)
                    argv.append("--dangerously-bypass-hook-trust")
                    argv += ["-c", 'sandbox_mode="danger-full-access"']
                    if "--sandbox" in argv:
                        argv[argv.index("--sandbox") + 1] = "danger-full-access"
                    # The outer scoped OS sandbox encloses file and subprocess
                    # tools; the isolated profile loads no plugins or MCP servers.
                    save(record)
                run_process(record, argv, spec["seconds"] - record["spent_seconds"], attended, "task", environment)
            if spec["kind"] == "agent":
                for line in Path(record["log"]).read_text(errors="replace").splitlines():
                    try:
                        session = harnesses.event_session(spec["harness"], json.loads(line))
                        if session:
                            record["native_session"] = session
                    except (ValueError, TypeError):
                        continue
            for argv in spec.get("checks", []):
                run_process(record, argv, spec["seconds"] - record["spent_seconds"], attended, "check")
                record["checks"].append({"argv": argv, "passed": True})
            if spec["kind"] == "agent" and spec.get("publish", spec.get("remote", False)):
                publish(record)
            record["status"] = "succeeded"
            record.pop("reason", None)
        except (InterruptedError, KeyboardInterrupt) as error:
            record["status"], record["reason"] = "cancelled", str(error)
        except Exception as error:
            record["status"], record["reason"] = "needs_attention", str(error)
        finally:
            if record.get("native_home"):
                (Path(record["native_home"]) / ".codex/auth.json").unlink(missing_ok=True)
            # Recover session IDs even when a native agent fails or exhausts quota.
            if record["spec"]["kind"] == "agent" and Path(record["log"]).exists():
                for line in Path(record["log"]).read_text(errors="replace").splitlines():
                    try:
                        session = harnesses.event_session(record["spec"]["harness"], json.loads(line))
                        if session:
                            record["native_session"] = session
                    except (ValueError, TypeError):
                        pass
            record["finished"] = time.time()
            if record.get("durable_artifacts"):
                try:
                    recovery = Path(record["durable_artifacts"]) / ("recovery-" + uuid.uuid4().hex)
                    recovery.mkdir(mode=0o700)
                    for name in ("worker.jsonl", "supervisor.log", "evidence.json"):
                        source = Path(record["workspace"]).parent / name
                        if source.is_file() and not source.is_symlink():
                            shutil.copyfile(source, recovery / name)
                    if record.get("native_home"):
                        sessions = Path(record["native_home"]) / ".codex/sessions"
                        for source in sessions.rglob("*.jsonl"):
                            if source.is_file() and not source.is_symlink():
                                target = recovery / "native-sessions" / source.relative_to(sessions)
                                target.parent.mkdir(parents=True, exist_ok=True)
                                shutil.copyfile(source, target)
                    git = trusted_git(record)
                    execute([*git, "bundle", "create", str(recovery / "snapshot.bundle"), "HEAD"], cwd=record["workspace"], timeout=120)
                    (recovery / "changes.patch").write_bytes(execute([*git, "diff", "--binary", "HEAD"], cwd=record["workspace"]))
                    names = execute([*git, "ls-files", "--others", "--exclude-standard", "-z"], cwd=record["workspace"]).decode().split("\0")
                    for name in filter(None, names):
                        source = Path(record["workspace"]) / name
                        if source.is_symlink() or not contained(source, record["workspace"]):
                            raise Refused("untracked recovery file escapes checkout")
                        target = recovery / "untracked" / name
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(source, target)
                    record["recovery"] = str(recovery)
                    write_json(recovery / "task.json", record)
                except Exception as error:
                    record["recovery_error"] = str(error)
                    record["status"] = "needs_attention"
            save(record)


def status(task):
    record = load(task)
    if record["machine"] != machine():
        return {**record, "status": "unknown", "reason": "record belongs to another host; query that host"}
    if record["status"] == "running":
        # A lock held by the supervisor is stronger evidence than PID existence.
        try:
            with lock(task, readonly=True):
                return {**record, "status": "unknown", "reason": "supervisor is absent; inspect artifacts, do not replay"}
        except BlockingIOError:
            pass
    return record


def cancel(task):
    record = status(task)
    if record["status"] != "running":
        raise Refused("only a live supervised task can be cancelled; no stale PID is killed")
    (Path(record["workspace"]).parent / "cancel.request").touch()
    return {"id": task, "cancellation_requested": True, "artifacts_preserved": True}


def continuation(task, prompt, seconds, attended=False):
    with lock(task):
        record = status(task)
        if record["status"] not in TERMINAL or not record.get("native_session"):
            raise Refused("continue requires a stopped task with a recorded native session")
        if record["spec"]["kind"] != "agent":
            raise Refused("ordinary commands are never automatically replayed")
        if not compute.finite(seconds) or seconds <= 0:
            raise Refused("continuation needs an explicit renewed seconds budget")
        record.setdefault("continuations", []).append({"native_session": record["native_session"], "previous_status": record["status"], "previous_reason": record.get("reason"), "previous_runner_revision": record.get("runner_revision"), "authorized_seconds": seconds, "at": time.time()})
        record["spec"]["prompt"] = prompt
        record["spec"]["seconds"] = record["spent_seconds"] + seconds
        record["status"] = "prepared"
        record["checks"] = []
        (Path(record["workspace"]).parent / "cancel.request").unlink(missing_ok=True)
        save(record)
    return launch(record, attended)
