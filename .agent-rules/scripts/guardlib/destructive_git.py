"""Policy: block the git operations that cannot be undone; allow the rest.

The line this draws is **recoverability**, not danger. Almost everything git
does is reversible from the reflog or from the remote, so an agent should get
on with it: commit, push a branch, merge, rebase, `reset --hard`, delete a
local branch, revert. If one of those turns out wrong, it can be undone.

A short list cannot be undone, and only that list is denied:

* **Rewriting or deleting published history** — a force push, a remote branch
  or tag deletion, `push --mirror`. Once a commit that only existed on the
  remote is gone from the remote, no reflog anywhere holds it.
* **Destroying the local recovery net** — `reflog expire --expire=now` and
  `gc --prune=now`, which are what make "reversible" true for everything else.
* **Deleting untracked files** — `git clean` with `-f`. Untracked files were
  never in git, so git cannot bring them back; this is `rm -rf` wearing a git
  hat, and it belongs with the same policy.

`--force-with-lease` is denied along with plain `--force`. It protects against
clobbering *someone else's* new commits; it does not make the commits it drops
recoverable, which is the property this guard is about.

Escape hatch: none in the guard. If a force push is genuinely wanted, a human
runs it. That asymmetry is deliberate — an agent that can undo its own mistakes
needs no permission, and an agent facing something it cannot undo should stop.

Like every module here, this only inspects a command string and returns a
reason or `None`. It reads no stdin and knows no hook dialect.
"""

from __future__ import annotations

import re
import shlex

SEGMENT_SPLIT = re.compile(r"&&|\|\||[;&|\n]")
_ENV_ASSIGNMENT = re.compile(r"^\w+=")

# Long and short spellings of "rewrite what the remote already has".
_FORCE_FLAGS = {"--force", "--force-with-lease", "-f"}
_FORCE_PREFIXES = ("--force-with-lease=", "--force-if-includes")


def _reason(what: str, detail: str) -> str:
    return (
        f"Blocked: {what}. {detail} Every other git operation is fair game — "
        "commit, push a branch, merge, rebase, reset --hard, delete a local "
        "branch — because those can be undone. This one cannot, so it is left "
        "for a human to run deliberately."
    )


def _simple_commands(command: str) -> list[list[str]]:
    """Split into simple commands, dropping env assignments and `sudo`.

    Only the tokens of a real command word are ever inspected, so a protected
    word inside a string literal — `git commit -m "never push --force"` — is
    not mistaken for the operation it names.
    """
    out: list[list[str]] = []
    for segment in SEGMENT_SPLIT.split(command):
        try:
            tokens = shlex.split(segment)
        except ValueError:
            tokens = segment.split()
        i = 0
        while i < len(tokens) and (
            tokens[i] == "sudo" or _ENV_ASSIGNMENT.match(tokens[i])
        ):
            i += 1
        if i < len(tokens):
            out.append(tokens[i:])
    return out


def _is_git(tokens: list[str]) -> bool:
    return bool(tokens) and tokens[0].split("/")[-1] == "git"


def _subcommand(tokens: list[str]) -> tuple[str | None, list[str]]:
    """The git subcommand and its arguments, skipping global options.

    `git -C /path --no-pager push …` has to resolve to `push`, and `-C` takes
    a value that must not itself be read as the subcommand.
    """
    i = 1
    while i < len(tokens):
        tok = tokens[i]
        if tok in ("-C", "-c", "--git-dir", "--work-tree", "--namespace"):
            i += 2
            continue
        if tok.startswith("-"):
            i += 1
            continue
        return tok, tokens[i + 1 :]
    return None, []


def _has_force(args: list[str]) -> bool:
    for a in args:
        if a in _FORCE_FLAGS or a.startswith(_FORCE_PREFIXES):
            return True
        # Bundled short flags: -uf, -fu … but never a long option.
        if len(a) > 1 and a[0] == "-" and a[1] != "-" and "f" in a[1:]:
            return True
    return False


def _deletes_remote_ref(args: list[str]) -> bool:
    """`git push --delete <ref>` or the colon refspec `git push origin :main`."""
    positional = [a for a in args if not a.startswith("-")]
    if "--delete" in args or "-d" in args:
        return True
    # A refspec whose source side is empty deletes the destination.
    return any(a.startswith(":") and len(a) > 1 for a in positional)


def inspect(command: str) -> str | None:
    """Return a deny reason if `command` is unrecoverable, else None."""
    if not command:
        return None

    for tokens in _simple_commands(command):
        if not _is_git(tokens):
            continue
        sub, args = _subcommand(tokens)
        if sub is None:
            continue

        if sub == "push":
            if _has_force(args):
                return _reason(
                    "this is a force push",
                    "It rewrites history the remote already has, and the "
                    "commits it drops exist in no reflog. --force-with-lease "
                    "counts: it stops you clobbering someone else's work, but "
                    "it does not make the discarded commits recoverable.",
                )
            if _deletes_remote_ref(args):
                return _reason(
                    "this deletes a branch or tag on the remote",
                    "Anything that lived only there is gone. Push a tag first "
                    "(`git tag archive/<name>` then `git push --tags`) if the "
                    "ref should be recoverable.",
                )
            if "--mirror" in args or "--prune" in args:
                return _reason(
                    "this push can delete remote refs wholesale",
                    "--mirror and --prune make the remote match your local "
                    "refs exactly, removing any it does not find.",
                )

        if sub == "reflog" and args and args[0] == "expire":
            if any(a.startswith("--expire") and "now" in a for a in args):
                return _reason(
                    "this expires the reflog",
                    "The reflog is what makes reset, rebase and branch "
                    "deletion recoverable. Dropping it turns every reversible "
                    "git operation into an irreversible one.",
                )

        if sub == "gc" and any(a.startswith("--prune=") and "now" in a for a in args):
            return _reason(
                "this prunes unreachable objects immediately",
                "It collects exactly the commits the reflog would otherwise "
                "let you recover.",
            )

        if sub == "clean" and _has_force(args):
            return _reason(
                "this deletes untracked files",
                "Untracked files were never in git, so git cannot restore "
                "them — this is rm -rf with a git spelling. Check `git clean "
                "-n` output and delete what you meant by name.",
            )

    return None


def notes(command: str, branch: str | None = None) -> list[str]:
    """Advisory, non-blocking observations. Never a reason to stop."""
    out: list[str] = []
    if not command or not branch or branch not in ("main", "master"):
        return out
    for tokens in _simple_commands(command):
        if not _is_git(tokens):
            continue
        sub, _args = _subcommand(tokens)
        if sub in ("commit", "push"):
            out.append(
                f"'{sub}' on '{branch}': the host rules ask for a branch, so "
                "intermediate work can be dropped without touching the "
                "default branch and parallel sessions do not collide."
            )
            break
    return out
