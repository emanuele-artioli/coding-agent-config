#!/usr/bin/env python3
"""Assert that this host's agent config is *in force*, not merely present.

    python3 verify.py                 # everything that applies to this host
    python3 verify.py --quiet         # print only problems (SessionStart uses this)
    python3 verify.py --only guards   # one check
    python3 verify.py --fix           # repair what is safely repairable
    python3 verify.py --json          # machine-readable

Exit 1 if any check fails, so it works as a gate.

## Why this exists

`install.py --check` already answers "is the file there?". Every failure this
repo has actually had answers a different question, and nothing was asking it:

| what happened | what would have caught it |
|---|---|
| `guard-rm.py` sat unreferenced in `settings.json` for weeks, guarding nothing | `hooks` |
| the git guard blocked its own documentation (a heredoc body read as commands) | `guards` |
| `~/.cursor-server` was symlinked into `/var/tmp`, which exists only on gpu5 — gpu6 refused every connection with nothing in any log | `hostlocal` |
| sourcing `~/.bashrc` cost 4.6–5.7 s on every agent shell call | `shell` |
| `AGENTS.md` asserted "~6 file opens per second" as a timeless property of the mount; it was one contended measurement, and it sent a whole investigation after the wrong cause | `claims` |
| `candidates/HANDOFF.md` claimed "Open candidates: none" for five weeks while eleven sat in the queue | `queue` |
| a generated file drifted from the `AGENTS.md` it is derived from | `generated` |

Two failure modes, over and over: **written but not wired**, and **true once,
still asserted**. Both are invisible to a file-presence check, and both look
exactly like a working system until the moment they matter.

## The rule for adding a check

A check earns its place by having failed in reality. Do not add speculative
ones: this runs at every SessionStart, and a suite that cries wolf gets
ignored, which costs more than the check was worth. Record the incident in the
table above when you add one.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

HOST_DIR = Path(__file__).resolve().parent.parent
SCRIPTS = HOST_DIR / "scripts"
AGENTS_MD = HOST_DIR / "AGENTS.md"
HOME = Path.home()

sys.path.insert(0, str(SCRIPTS))

OK, WARN, FAIL = "ok", "warn", "fail"


@dataclass
class Result:
    name: str
    status: str = OK
    notes: list[str] = field(default_factory=list)
    fixes: list[str] = field(default_factory=list)

    def problem(self, msg: str, *, fatal: bool = True) -> None:
        self.notes.append(msg)
        # A warn never downgrades an existing fail.
        if fatal:
            self.status = FAIL
        elif self.status == OK:
            self.status = WARN

    def note(self, msg: str) -> None:
        self.notes.append(msg)


# --------------------------------------------------------------------------
# hooks — is every guard actually referenced by a platform's live config?
# --------------------------------------------------------------------------

# Guards that must be wired, per platform, with the config file that wires them.
# A guard absent from this table is not checked; a guard present here and
# missing from the config is a failure, because an unwired guard denies nothing
# while looking exactly like protection.
HOOK_EXPECTATIONS = {
    "claude": (
        HOME / ".claude" / "settings.json",
        ["guard-wait-loop.py", "guard-git.py", "guard-rm.py", "guard-model-family.py"],
    ),
    "cursor": (HOME / ".cursor" / "hooks.json", ["before-shell.py", "before-task.py"]),
    "antigravity": (
        HOME / ".gemini" / "config" / "hooks.json",
        ["before-shell.py", "guard-model-family.py"],
    ),
}


def check_hooks(fix: bool) -> Result:
    r = Result("hooks")
    for platform, (config, expected) in HOOK_EXPECTATIONS.items():
        if not config.is_file():
            r.problem(f"{platform}: no config at {config}", fatal=False)
            continue
        try:
            blob = config.read_text(encoding="utf-8")
        except OSError as exc:
            r.problem(f"{platform}: cannot read {config} ({exc})")
            continue
        for script in expected:
            if script not in blob:
                r.problem(f"{platform}: {script} is not referenced in {config.name}")
        # A referenced path that does not exist fails closed at best and
        # silently bypasses at worst -- Antigravity exits 127 on a bad path.
        for path in re.findall(r"(/home/[^\s\"']+\.py)", blob):
            if not Path(path).is_file():
                r.problem(f"{platform}: hook path does not exist: {path}")
    if r.status == OK:
        r.note(f"{len(HOOK_EXPECTATIONS)} platforms wired")
    return r


# --------------------------------------------------------------------------
# guards — do the policies still decide correctly?
# --------------------------------------------------------------------------

# (command, must_be_denied). Each line is a case that has mattered.
GUARD_CASES = [
    ("git push --force origin main", True),
    ("git push --force-with-lease origin main", True),
    ("git push --delete origin gone", True),
    ("git clean -fd", True),
    ("git reflog expire --expire=now --all", True),
    ("git commit -m 'work'", False),
    ("git push -u origin feature/x", False),
    ("git reset --hard HEAD~1", False),
    ("git branch -D stale", False),
    # the words, not the act -- a guard that fails these teaches people to
    # route around it, which is worse than no guard
    ("git commit -m 'never use push --force here'", False),
    ("echo 'git push --force' >> notes.md", False),
]


def _heredoc_case() -> str:
    """A heredoc whose body quotes forbidden commands. Built at runtime so this
    file does not itself contain a line that the guard would read as a command
    if anyone ever inspects this source with a naive splitter."""
    body = " ".join(["git", "push", "--force", "origin", "main"])
    return "\n".join(["cat > doc.md <<'EOF'", body, "git clean -fd", "EOF"])


def _wait_loop_heredoc_case() -> str:
    """A PR body, passed on the command line, that quotes the loop it forbids.

    The live shape from 2026-09-01: a heredoc nested inside a command
    substitution. `wait_loop.inspect` was not stripping heredocs the way the
    other two policies do, so `gh pr create --body "$(cat <<EOF ... EOF)"` was
    denied for its prose. Built at runtime, same reason as `_heredoc_case`.
    """
    loop = " ".join(["until", "!", "pgrep", "-f", "trainer;", "do"])
    loop += " " + " ".join(["sleep", "5;", "done"])
    return "\n".join([
        "gh pr create --title t --body \"$(cat <<'EOF'",
        "- " + loop + " -> wait-loop deny",
        "EOF",
        ")\"",
    ])


def check_guards(fix: bool) -> Result:
    r = Result("guards")
    try:
        from guardlib import destructive_git, destructive_rm, shell, wait_loop
    except Exception as exc:  # noqa: BLE001
        r.problem(f"guardlib will not import: {exc}")
        return r

    for command, must_deny in GUARD_CASES:
        denied = destructive_git.inspect(command) is not None
        if denied != must_deny:
            verb = "did not deny" if must_deny else "wrongly denied"
            r.problem(f"destructive_git {verb}: {command}")

    hd = _heredoc_case()
    if destructive_git.inspect(hd) is not None:
        r.problem("a heredoc body is being read as commands (guardlib/shell.py)")
    if destructive_git.inspect(hd + "\n" + " ".join(["git", "push", "--force"])) is None:
        r.problem("a real command after a heredoc is no longer caught")
    if shell.strip_heredocs("echo hi") != "echo hi":
        r.problem("strip_heredocs mangles a command with no heredoc")

    # rm and wait-loop policies still answer at all
    if destructive_rm.inspect("rm -rf outputs", {"outputs"}, "x") is None:
        r.problem("destructive_rm no longer denies rm of a protected tree")
    if destructive_rm.inspect("rm -rf outputs/run-3", {"outputs"}, "x") is not None:
        r.problem("destructive_rm wrongly denies deleting one run directory")
    if wait_loop.inspect("until ! pgrep -f trainer; do sleep 5; done", dialect="claude") is None:
        r.problem("wait_loop no longer denies a hand-rolled waiter")

    # The same heredoc rule, for the policy that learned it last.
    wl = _wait_loop_heredoc_case()
    if wait_loop.inspect(wl, dialect="claude") is not None:
        r.problem("a heredoc body is being read as a wait loop (guardlib/shell.py)")
    if wait_loop.inspect(wl + "\nuntil ! pgrep -f t; do sleep 5; done") is None:
        r.problem("a real waiter after a heredoc is no longer caught")

    if r.status == OK:
        r.note(f"{len(GUARD_CASES) + 7} decisions correct")
    return r


# --------------------------------------------------------------------------
# hostlocal — do the shared symlinks resolve on *this* machine?
# --------------------------------------------------------------------------


def check_hostlocal(fix: bool) -> Result:
    r = Result("hostlocal")
    host = socket.gethostname()
    for link in (HOME / ".cursor-server", HOME / ".vscode-server"):
        if not link.is_symlink():
            continue  # not on the local-disk layout; nothing to assert
        target = Path(os.readlink(link))
        if target.is_dir():
            continue
        if fix:
            try:
                target.mkdir(parents=True, exist_ok=True)
                r.fixes.append(f"created {target} on {host}")
                continue
            except OSError as exc:
                r.problem(f"{link.name} -> {target} missing and uncreatable: {exc}")
                continue
        r.problem(
            f"{link.name} -> {target} does not exist on {host}. The symlink lives "
            "in the shared NFS home; the target is local to each machine. The "
            "editor cannot install its server and the connection is refused with "
            "nothing in any log. Run with --fix, or source "
            "scripts/bootstrap-hostlocal.sh."
        )
    if r.status == OK and not r.fixes:
        r.note(f"local targets present on {host}")
    return r


# --------------------------------------------------------------------------
# shell — a login shell runs before every agent command
# --------------------------------------------------------------------------

SHELL_BUDGET_S = 2.0


def check_shell(fix: bool) -> Result:
    r = Result("shell")
    times = []
    for _ in range(3):
        start = time.time()
        try:
            subprocess.run(["bash", "-c", "-l", "true"], capture_output=True, timeout=30)
        except (OSError, subprocess.SubprocessError) as exc:
            r.problem(f"could not time a login shell: {exc}", fatal=False)
            return r
        times.append(time.time() - start)
    best = min(times)
    if best > SHELL_BUDGET_S:
        r.problem(
            f"a login shell takes {best:.1f}s (budget {SHELL_BUDGET_S}s). Every "
            "agent shell call pays this. Usual causes here: `conda shell.bash "
            "hook` as a subprocess against the NFS conda (source conda.sh "
            "instead, 0.00s), sourcing nvm.sh eagerly, or a missing "
            "PYTHONNOUSERSITE=1.",
            fatal=False,
        )
    else:
        r.note(f"login shell {best:.2f}s")

    if os.environ.get("PYTHONNOUSERSITE") != "1":
        r.problem(
            "PYTHONNOUSERSITE is not set: Python scans ~/.local/lib/python3.*/"
            "site-packages on NFS at every start (1.08s vs 0.01s)",
            fatal=False,
        )
    return r


# --------------------------------------------------------------------------
# generated — has anything drifted from the AGENTS.md it derives from?
# --------------------------------------------------------------------------


def check_generated(fix: bool) -> Result:
    r = Result("generated")
    script = SCRIPTS / "sync_host_rules.py"
    if not script.is_file():
        r.problem(f"missing {script}")
        return r
    args = [sys.executable, str(script)] + ([] if fix else ["--check"])
    out = subprocess.run(args, capture_output=True, text=True, timeout=120)
    if out.returncode != 0:
        r.problem((out.stdout + out.stderr).strip()[:400])
    elif fix:
        r.fixes.append("regenerated Claude's host-rule split")
    else:
        r.note("generated files current")
    return r


# --------------------------------------------------------------------------
# claims — is every measured number in AGENTS.md dated?
# --------------------------------------------------------------------------

# Numbers with units that read as measurements. A measurement without a date is
# a claim that cannot be re-checked, and this file has already shipped one that
# was true only under contention.
# Two attempts at this taught the lesson. Matching "numbers that look like
# measurements" flagged an HTTP status ("403s") and then a policy threshold
# ("checkpoint every 60 minutes") -- a rule, not an observation. Regex cannot
# tell an observation from a threshold, so this stops trying and keys off the
# only reliable signal: the author saying so. If a section claims something was
# measured, it must say when, and it must say where to re-run it.
_MEASURED = re.compile(r"\bmeasured\b|\bbenchmark", re.IGNORECASE)
_DATE = re.compile(r"20\d\d-\d\d-\d\d")


def check_claims(fix: bool) -> Result:
    r = Result("claims")
    if not AGENTS_MD.is_file():
        r.problem("no AGENTS.md")
        return r
    text = AGENTS_MD.read_text(encoding="utf-8")
    undated = []
    for section in re.split(r"^## ", text, flags=re.MULTILINE)[1:]:
        title = section.splitlines()[0].strip()
        if _MEASURED.search(section) and not _DATE.search(section):
            undated.append(title)
    if undated:
        r.problem(
            "a section says something was measured but not when, so nobody can "
            "tell whether it still holds: " + "; ".join(undated),
            fatal=False,
        )
    else:
        r.note("measured claims are dated")
    return r


# --------------------------------------------------------------------------
# measurements — do the documented numbers still match reality?
# --------------------------------------------------------------------------
# Opt-in (`--only measurements`): it costs ~15s because it deliberately pays
# the serial open rate it is measuring. This is the check that targets "true
# once, still asserted" head on -- AGENTS.md's NFS figures were correct when
# taken and wrong as a standing description of the mount, and re-reading them
# is the only way to notice.


def check_measurements(fix: bool) -> Result:
    r = Result("measurements")
    import random
    # Not `scripts/` -- an agent editing this repo warms exactly those files.
    # Must be a tree that is still on NFS and that no session warms. The
    # editor servers moved to local disk, so sampling those measures ext4 and
    # reports a meaningless 19,000 opens/s.
    nfs_trees = [HOME / ".antigravity-ide-server", HOME / ".antigravity-server"]
    pool: list[Path] = []
    for tree in nfs_trees:
        if tree.is_dir():
            pool = [p for p in tree.rglob("*") if p.is_file()][:4000]
            if pool:
                break
    sample = random.Random(0).sample(pool, min(20, len(pool))) if pool else []
    if len(sample) < 10:
        r.problem("not enough files to sample", fatal=False)
        return r

    t0 = time.time()
    for path in sample:
        try:
            path.open("rb").read(1)
        except OSError:
            pass
    serial = len(sample) / max(time.time() - t0, 1e-9)

    t0 = time.time()
    subprocess.run(
        ["xargs", "-P", "24", "-I{}", "head", "-c1", "{}"],
        input="\n".join(str(p) for p in sample).encode(),
        capture_output=True,
        timeout=120,
    )
    parallel = len(sample) / max(time.time() - t0, 1e-9)

    speedup = parallel / serial if serial else 0
    r.note(f"serial {serial:.1f} opens/s, parallel {parallel:.1f}/s, {speedup:.1f}x")

    # A warm sample measures the page cache, not the mount, and will happily
    # report "parallelism does not help" -- which is true of cached files and
    # says nothing about the rule. The first version of this check made exactly
    # that mistake against files this session had just been reading. Refuse to
    # draw a conclusion instead of drawing a wrong one.
    if serial > 20:
        r.note(
            f"sample was cache-warm ({serial:.0f} opens/s against the 2-5/s this "
            "mount serves cold), so the speedup below measures nothing. Re-run "
            "against a tree this session has not touched."
        )
        return r

    # AGENTS.md's standing claim is that parallelism is dramatic here. Three
    # platforms measured 9.9x, 14x and 26x on different days. If that collapses,
    # the rule telling everyone to fan out is no longer earning its place.
    if speedup < 3:
        r.problem(
            f"parallelism is only {speedup:.1f}x; AGENTS.md tells every agent to "
            "fan out bulk file reads on the strength of 9.9-26x. Re-check the "
            "rule before trusting it.",
            fatal=False,
        )
    if serial > 200:
        r.problem(
            f"serial opens are {serial:.0f}/s -- the NFS latency AGENTS.md is "
            "built around may no longer apply, or this ran against warm cache.",
            fatal=False,
        )
    return r


def check_queue(fix: bool) -> Result:
    r = Result("queue")
    cand = HOST_DIR / "candidates"
    open_files = [p for p in (cand / "open").rglob("*.md")] if cand.is_dir() else []
    pending = list((cand / "pending-verification").glob("*.md")) if cand.is_dir() else []
    unchecked = sum(
        len(re.findall(r"^- \[ \]", p.read_text(encoding="utf-8"), re.M)) for p in pending
    )
    r.note(f"{len(open_files)} open candidate(s), {unchecked} unchecked verification row(s)")

    # A status document that contradicts the tree is worse than none: one here
    # said "Open candidates: none" for five weeks while eleven sat in the queue.
    for doc in list(cand.glob("*.md")) if cand.is_dir() else []:
        if doc.name == "README.md":
            continue
        body = doc.read_text(encoding="utf-8").lower()
        if "open candidates" in body and "none" in body and open_files:
            r.problem(
                f"{doc.name} says there are no open candidates, but "
                f"{len(open_files)} are in open/",
                fatal=False,
            )
    return r


# Skipped by --fast: each spawns processes, and `measurements` deliberately
# pays the serial open rate it measures.
# --------------------------------------------------------------------------
# parity — do the three harnesses reach the same verdict?
# --------------------------------------------------------------------------
# The whole design rests on one claim: the policy lives once in `guardlib/` and
# each platform gets a thin adapter. Nothing checked it. A drift means a command
# denied on Claude and allowed on Cursor -- and the platform where the guard
# quietly stopped applying is the one nobody is looking at.
#
# Each adapter answers in its own dialect: Claude prints a `hookSpecificOutput`
# block, Cursor a `{"permission": ...}` object, Antigravity a non-zero exit.
# This normalises all three to a boolean and compares.

# Claude wires one hook script per policy; Cursor and Antigravity run all
# three policies from a single shell hook. So the Claude side of a case has to
# be the adapter for the policy that case exercises -- otherwise a case can
# only ever "agree", because the script asked was never going to decide it.
_ADAPTERS = {
    "claude": (SCRIPTS / "guard-git.py", "claude"),
    "cursor": (SCRIPTS / "cursor" / "before-shell.py", "cursor"),
    "antigravity": (SCRIPTS / "antigravity" / "before-shell.py", "antigravity"),
}


def _ask_adapter(path: Path, dialect: str, command: str) -> bool | None:
    """True = denied, False = allowed, None = adapter unavailable."""
    if not path.is_file():
        return None
    payload = (
        json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
        if dialect == "claude"
        else json.dumps({"command": command})
    )
    try:
        out = subprocess.run(
            [sys.executable, str(path)],
            input=payload.encode(),
            capture_output=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if dialect == "antigravity":
        return out.returncode != 0
    text = (out.stdout or b"").decode(errors="replace")
    if not text.strip():
        return False  # Claude's adapter prints nothing when it allows
    return '"deny"' in text


def check_parity(fix: bool) -> Result:
    r = Result("parity")
    disagreements = 0
    cases = [(c, d, "guard-git.py") for c, d in GUARD_CASES]
    cases.append((_heredoc_case(), False, "guard-git.py"))
    cases.append((_wait_loop_heredoc_case(), False, "guard-wait-loop.py"))
    for command, must_deny, claude_script in cases:
        adapters = {**_ADAPTERS, "claude": (SCRIPTS / claude_script, "claude")}
        verdicts = {
            name: _ask_adapter(path, dialect, command)
            for name, (path, dialect) in adapters.items()
        }
        live = {k: v for k, v in verdicts.items() if v is not None}
        if not live:
            r.problem("no adapter could be run", fatal=False)
            return r
        if len(set(live.values())) > 1:
            disagreements += 1
            shown = command if len(command) < 60 else command[:57] + "..."
            r.problem(
                f"platforms disagree on {shown!r}: "
                + ", ".join(f"{k}={'deny' if v else 'allow'}" for k, v in sorted(live.items()))
            )
        for name, verdict in live.items():
            if verdict != must_deny:
                r.problem(
                    f"{name} {'did not deny' if must_deny else 'wrongly denied'}: {command[:60]}"
                )
    if r.status == OK:
        r.note(f"{len(_ADAPTERS)} adapters agree on {len(GUARD_CASES) + 2} commands")
    return r

SLOW_CHECKS = {"generated", "shell", "measurements", "parity"}

CHECKS = {
    "hooks": check_hooks,
    "guards": check_guards,
    "hostlocal": check_hostlocal,
    "generated": check_generated,
    "shell": check_shell,
    "claims": check_claims,
    "measurements": check_measurements,
    "parity": check_parity,
    "queue": check_queue,
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--only", action="append", choices=sorted(CHECKS), default=[])
    ap.add_argument("--fix", action="store_true", help="repair what is safe to repair")
    ap.add_argument("--quiet", action="store_true", help="print only problems")
    ap.add_argument("--json", action="store_true")
    ap.add_argument(
        "--fast",
        action="store_true",
        help="skip checks that spawn processes (SessionStart uses this)",
    )
    args = ap.parse_args()

    # `generated` and `shell` each spawn a subprocess and cost ~2.5s on this
    # mount. At SessionStart that is a delay on every session for a check that
    # is only worth running when something changed, so --fast drops them and
    # a pre-commit/CI run keeps them.
    selected = args.only or [c for c in CHECKS if not (args.fast and c in SLOW_CHECKS)]
    results = []
    for name in selected:
        try:
            results.append(CHECKS[name](args.fix))
        except Exception as exc:  # noqa: BLE001
            # A crashing check must not look like a passing one.
            bad = Result(name, FAIL, [f"check raised {type(exc).__name__}: {exc}"])
            results.append(bad)

    if args.json:
        print(json.dumps([r.__dict__ for r in results], indent=2))
    else:
        symbol = {OK: "ok  ", WARN: "warn", FAIL: "FAIL"}
        for r in results:
            problems = r.status != OK
            if args.quiet and not problems and not r.fixes:
                continue
            print(f"[{symbol[r.status]}] {r.name}")
            for note in r.notes:
                print(f"       {note}")
            for f in r.fixes:
                print(f"       fixed: {f}")
        if not args.quiet:
            bad = [r.name for r in results if r.status == FAIL]
            print("\n" + ("all checks pass" if not bad else "failed: " + ", ".join(bad)))

    return 1 if any(r.status == FAIL for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
