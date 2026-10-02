"""OS containment for the entire worker process tree, including local tools."""

import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
import tempfile

from .common import Refused, contained


def wrap(argv, writable, protected=(), network=False, readable=None):
    writable = [str(Path(path).resolve()) for path in writable]
    protected = [str(Path(path).resolve()) for path in protected]
    readable = [str(Path(path).resolve()) for path in readable] if readable is not None else None
    for root in writable:
        if any(contained(root, path) for path in protected):
            raise Refused("writable root overlaps a protected parent")
    if platform.system() == "Darwin" and shutil.which("sandbox-exec"):
        profile = ['(version 1)', '(deny default)',
                   '(allow process-exec process-fork)', '(allow sysctl-read)',
                   '(allow mach-lookup)',
                   '(deny mach-lookup (global-name "com.apple.securityd") (global-name "com.apple.secd") (global-name "com.apple.securityd.system") (global-name "com.apple.securityd.xpc"))',
                   '(allow file-write* (literal "/dev/null"))']
        if readable is None:
            profile.append('(allow file-read*)')
        else:
            profile.append('(allow file-read-metadata)')
            profile.append('(allow file-read* (literal "/"))')
            for path in ["/System", "/Library", "/usr", "/bin", "/sbin", "/opt", "/dev", "/private/etc", "/private/var/db/dyld", *readable, *writable]:
                profile.append(f'(allow file-read* (subpath {json.dumps(path)}))')
        for path in writable:
            profile.append(f'(allow file-write* (subpath {json.dumps(path)}))')
        for path in protected:
            profile.append(f'(deny file-write* (subpath {json.dumps(path)}))')
        if network:
            # TCP providers work; access to host Unix sockets is not granted.
            profile += ['(allow system-socket (socket-domain AF_INET) (socket-domain AF_INET6) (socket-domain AF_UNIX))',
                        '(allow network-outbound (remote ip))',
                        '(allow network-outbound (remote unix-socket (subpath "/private/var/run/mDNSResponder")))',
                        '(allow network-inbound (local ip))']
        return ["sandbox-exec", "-p", "\n".join(profile), *argv]
    bwrap = shutil.which("bwrap")
    if not bwrap:
        candidate = Path.home() / ".local/share/agentctl/tools/bubblewrap/usr/bin/bwrap"
        if candidate.is_file():
            bwrap = str(candidate)
    if platform.system() == "Linux" and bwrap:
        result = [bwrap, "--die-with-parent", "--new-session", "--unshare-all", "--cap-drop", "ALL"]
        if readable is None:
            result += ["--ro-bind", "/", "/"]
        result += ["--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp", "--tmpfs", "/run"]
        if readable is not None:
            # Bind inputs after fresh temporary mounts so /tmp inputs survive.
            for path in ["/usr", "/bin", "/sbin", "/lib", "/lib64", "/etc", *readable]:
                if Path(path).exists():
                    result += ["--ro-bind", path, path]
        if network:
            result += ["--share-net"]
        for path in writable:
            result += ["--bind", path, path]
        for path in protected:
            # Protection must not grant read access to unrelated host state.
            if any(contained(path, root) for root in writable):
                if not Path(path).exists():
                    raise Refused("protected path is absent inside a writable root; review declaration")
                result += ["--ro-bind", path, path]
        return [*result, "--remount-ro", "/", "--", *argv]
    raise Refused("verified OS sandbox unavailable: install bubblewrap on Linux or use attended execution")


def probe(scoped=False):
    """Verify success inside, denial outside, and denial through a symlink."""
    with tempfile.TemporaryDirectory(prefix="agentctl-probe-") as temporary:
        root = Path(temporary).resolve()
        work = root / "work"
        work.mkdir()
        outside = root / "evidence"
        outside.write_text("preserve")
        secret = root / "credential"
        secret.write_text("private")
        (work / "link").symlink_to(outside)
        code = '''import pathlib, sys
w=pathlib.Path(sys.argv[1]); p=pathlib.Path(sys.argv[2])
(w/'allowed').write_text('ok')
for target in [p,w/'link']:
    try: target.write_text('destroyed')
    except OSError: pass
    else: raise SystemExit(12)
try: p.unlink()
except OSError: pass
else: raise SystemExit(13)
'''
        if scoped:
            code += '''
try: (w.parent/'credential').read_text()
except OSError: pass
else: raise SystemExit(14)
'''
        try:
            command = wrap([sys.executable, "-B", "-c", code, str(work), str(outside)], [work], [outside],
                           readable=[sys.prefix, outside] if scoped else None)
            result = subprocess.run(command, capture_output=True, timeout=15)
            valid = result.returncode == 0 and outside.read_text() == "preserve" and (work / "allowed").read_text() == "ok"
            lifetime = False
            if valid and sys.platform == "linux":
                daemon = """import os,pathlib,time,sys
w=pathlib.Path(sys.argv[1])
if os.fork()==0:
 os.setsid()
 if os.fork(): os._exit(0)
 (w/'daemon-started').write_text('started')
 time.sleep(0.5)
 (w/'daemon-escaped').write_text('escaped')
 os._exit(0)
for _ in range(100):
 if (w/'daemon-started').exists(): break
 time.sleep(0.01)
else: raise SystemExit(15)
os._exit(0)
"""
                lifetime_command = wrap([sys.executable, "-B", "-c", daemon, str(work)], [work], [outside], readable=[sys.prefix])
                lifetime_result = subprocess.run(lifetime_command, capture_output=True, timeout=5)
                time.sleep(0.6)
                lifetime = lifetime_result.returncode == 0 and (work / "daemon-started").exists() and not (work / "daemon-escaped").exists()
            return {"verified": valid and lifetime, "filesystem_verified": valid,
                    "process_lifetime_verified": lifetime, "backend": command[0],
                    "returncode": result.returncode,
                    "detail": result.stderr.decode(errors="replace")[-1000:] or ("scoped read/write isolation probe failed" if not valid else "daemonized-process lifetime isolation is unverified; use attended execution" if not lifetime else "")}
        except (OSError, ValueError, subprocess.TimeoutExpired) as error:
            return {"verified": False, "detail": str(error)}
