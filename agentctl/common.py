"""Small host-local primitives shared by CLI and supervisor."""

import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import tempfile
from contextlib import contextmanager


class Refused(ValueError):
    """Action cannot satisfy the task or protection contract."""


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def read_json(path, default=None):
    path = Path(path)
    if not path.exists() and default is not None:
        return default
    return json.loads(path.read_text())


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".agentctl-")
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def execute(argv, cwd=None, timeout=30, **kwargs):
    result = subprocess.run(argv, cwd=cwd, timeout=timeout, capture_output=True, **kwargs)
    if result.returncode:
        detail = result.stderr.decode(errors="replace") if isinstance(result.stderr, bytes) else result.stderr
        raise Refused(f"{argv[0]} failed ({result.returncode}): {detail[-2000:]}")
    return result.stdout


def home():
    return Path(os.environ.get("AGENTCTL_HOME", str(Path.home() / ".local/state/agentctl"))).resolve()


def runtime():
    return Path(os.environ.get("AGENTCTL_RUNTIME", f"/var/tmp/agentctl-{os.getuid()}")).resolve()


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,95}", value):
        raise Refused("invalid task or host identifier")
    return value


def contained(path, root):
    return Path(path).resolve().is_relative_to(Path(root).resolve())


@contextmanager
def lock(name, readonly=False):
    if not readonly:
        runtime().mkdir(parents=True, exist_ok=True, mode=0o700)
    with (runtime() / f"{identifier(name)}.lock").open("r" if readonly else "a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def machine():
    return socket.gethostname()
