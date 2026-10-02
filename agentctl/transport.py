"""SSH transport with explicit enrollment and no automatic task replay."""

import io
import json
import os
from pathlib import Path
import shlex
import subprocess
import tarfile
import uuid

from .common import Refused, home, identifier, read_json, write_json


def profile(host):
    host = identifier(host)
    profiles = read_json(home() / "machines.json", {})
    if host not in profiles:
        raise Refused(f"{host} is not enrolled; use enroll with a verified Python runtime")
    return profiles[host]


def ssh(host, remote_command, data=None, timeout=45):
    try:
        result = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", "--", identifier(host), remote_command],
                                input=data, capture_output=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise Refused(f"SSH connectivity unknown: {error}; inspect the existing task, never replay") from error
    if result.returncode:
        raise Refused(f"SSH operation failed ({result.returncode}): {result.stderr.decode(errors='replace')[-2000:]}; never replay automatically")
    return result.stdout


def remote(host, argv, data=None, timeout=45):
    config = profile(host)
    command = shlex.join(["env", f"PYTHONPATH={config['package_root']}", f"AGENTCTL_HOME={config['state']}",
                          f"AGENTCTL_RUNTIME={config['runtime']}", *([f"CODEX_HOME={config['codex_home']}"] if config.get("codex_home") else []),
                          "PYTHONDONTWRITEBYTECODE=1", config["python"], "-m", "agentctl", *argv])
    return ssh(host, command, data, timeout)


def archive_paths(root, paths):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w:gz") as archive:
        for path in paths:
            path = Path(path)
            if path.is_symlink() or not path.is_file():
                raise Refused("transport accepts regular files only")
            archive.add(path, arcname=str(path.relative_to(root)), recursive=False)
    return stream.getvalue()


def extract(data, destination):
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=False)
    total = 0
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        for member in archive:
            target = destination / member.name
            total += member.size
            if not member.isfile() or not target.resolve().is_relative_to(destination) or total > 512 * 1024 * 1024:
                raise Refused("invalid, escaping or oversized transport archive")
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.extractfile(member) as source:
                target.write_bytes(source.read())


def enroll(host, python="python3", package_root=None, codex_home=None):
    host = identifier(host)
    package_root = package_root or f".local/share/agentctl/releases/{uuid.uuid4().hex}"
    source_root = Path(__file__).resolve().parent.parent
    payload = archive_paths(source_root, [path for path in (source_root / "agentctl").rglob("*") if path.is_file() and "__pycache__" not in path.parts])
    # Bootstrap works on Python 3.10, checks the requested runtime before any
    # write, and installs only into a fresh, non-home repository location.
    bootstrap = '''import io,json,os,pathlib,sys,tarfile
if sys.version_info < (3,11): raise SystemExit('Python 3.11+ required; select an existing compatible runtime')
root=pathlib.Path(sys.argv[1]).expanduser().resolve()
if root.exists(): raise SystemExit('release path already exists')
root.mkdir(parents=True)
total=0
with tarfile.open(fileobj=io.BytesIO(sys.stdin.buffer.read()),mode='r:gz') as archive:
 for member in archive:
  target=(root/member.name).resolve(); total+=member.size
  if not member.isfile() or not target.is_relative_to(root) or total>16777216: raise SystemExit('unsafe archive')
  target.parent.mkdir(parents=True,exist_ok=True)
  target.write_bytes(archive.extractfile(member).read())
print(json.dumps({'python':sys.executable,'package_root':str(root),'state':str(pathlib.Path.home()/'.local/state/agentctl'),'runtime':'/var/tmp/agentctl-'+str(os.getuid())}))
'''
    enrolled = json.loads(ssh(host, shlex.join([python, "-c", bootstrap, package_root]), payload, timeout=60))
    if codex_home:
        enrolled["codex_home"] = codex_home
    profiles = read_json(home() / "machines.json", {})
    profiles[host] = enrolled
    write_json(home() / "machines.json", profiles)
    return {"host": host, **enrolled}


def dispatch(host, spec, attended=False):
    from .common import runtime
    from .runner import snapshot
    if attended:
        raise Refused("attended SSH runs require a terminal on the enrolled host; use the printed native command there")
    task = uuid.uuid4().hex
    payload_root = runtime() / "outgoing" / task
    metadata = snapshot(spec, payload_root)
    spec = {**spec, "remote": True}
    write_json(payload_root / "metadata.json", metadata)
    write_json(payload_root / "spec.json", spec)
    data = archive_paths(payload_root, [payload_root / name for name in ("snapshot.bundle", "changes.patch", "untracked.json", "metadata.json", "spec.json")])
    # Save routing before submission: a lost reply must still be inspectable.
    write_json(home() / "routes" / f"{task}.json", {"host": host, "id": task})
    try:
        result = json.loads(remote(host, ["_receive", task], data, timeout=120))
    except Refused as error:
        return {"id": task, "host": host, "status": "unknown", "reason": str(error)}
    return {**result, "host": host}


def routed_host(task, explicit=None):
    if explicit:
        return explicit
    route = read_json(home() / "routes" / f"{identifier(task)}.json", {})
    return route.get("host")
