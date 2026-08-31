"""Both directions matter equally here.

A false negative lets published history disappear. A false positive is worse
than it sounds: the point of this guard is that an agent needs no permission
for the reversible 95% of git, so every wrong denial pushes work back onto a
human and erodes the reason the guard is tolerable at all.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402

from guardlib import destructive_git as g  # noqa: E402

DENIED = [
    "git push --force",
    "git push -f origin main",
    "git push --force-with-lease origin feature",
    "git push --force-with-lease=main:abc123 origin",
    "git push --force-if-includes origin main",
    "git push origin +main:main".replace("+", "--force "),  # explicit long form
    "git push --delete origin old-branch",
    "git push -d origin old-branch",
    "git push origin :refs/heads/gone",
    "git push --mirror backup",
    "git push --prune origin",
    "git reflog expire --expire=now --all",
    "git gc --prune=now",
    "git clean -fd",
    "git clean -xfd",
    "git clean -f",
    "cd /repo && git push --force origin main",
    "git -C /home/itec/emanuele push --force",
    "git --no-pager push -f",
    "sudo git push --force",
    "make build; git push --force origin main",
]

ALLOWED = [
    # the everyday reversible operations — none of these may ever be blocked
    "git commit -m 'work'",
    "git push",
    "git push origin feature/x",
    "git push -u origin knowledge/queue-sweep",
    "git push --tags",
    "git push --set-upstream origin main",
    "git merge --ff-only feature",
    "git rebase main",
    "git reset --hard HEAD~3",
    "git branch -D stale-local",
    "git tag -d local-tag",
    "git checkout -b new-branch",
    "git revert abc123",
    "git cherry-pick abc123",
    "git fetch --prune",           # prunes local remote-tracking refs only
    "git remote prune origin",     # same
    "git clean -n",                # dry run
    "git clean --dry-run -xd",
    "git stash",
    "git worktree remove ../wt",
    "gh pr merge 43 --squash",
    # the words appear, but not as the operation
    "git commit -m 'never use push --force on this repo'",
    "echo 'git push --force' >> notes.md",
    "grep -r 'git clean -fd' docs/",
    "git log --grep='force push'",
    # not git at all
    "rm -rf build",
    "python train.py --force",
]


@pytest.mark.parametrize("command", DENIED)
def test_unrecoverable_is_denied(command):
    assert g.inspect(command) is not None, command


@pytest.mark.parametrize("command", ALLOWED)
def test_recoverable_is_allowed(command):
    assert g.inspect(command) is None, command


HEREDOC_BODY = "\n".join([
    "cat > doc.md <<'EOF'",
    "git push " + "--force origin main",
    "git clean -fd",
    "EOF",
])


def test_heredoc_body_is_data_not_commands():
    """Writing documentation about a forbidden operation must not trip the guard.

    This is the regression that motivated `guardlib/shell.py`: the prompt files
    describing this very policy could not be written, because their heredoc
    bodies quote the commands they warn about.
    """
    assert g.inspect(HEREDOC_BODY) is None


def test_a_real_command_after_a_heredoc_is_still_caught():
    tail = HEREDOC_BODY + "\ngit push " + "--force origin main"
    assert g.inspect(tail) is not None


def test_unterminated_heredoc_is_still_inspected():
    """A heredoc that never closes must not become a way to hide a command."""
    opened = "cat > doc.md <<'EOF'\ngit push " + "--force origin main"
    assert g.inspect(opened) is not None


def test_reason_names_the_operation_and_the_way_out():
    reason = g.inspect("git push --force origin main")
    assert "force push" in reason
    assert "reflog" in reason  # says *why* it is different from the rest
    assert "commit" in reason  # and that ordinary git is still fine


def test_force_with_lease_is_not_treated_as_safe():
    assert g.inspect("git push --force-with-lease origin main") is not None


def test_delete_refspec_needs_a_ref_after_the_colon():
    # a bare ":" is not a deletion refspec, and `a:b` is an ordinary one
    assert g.inspect("git push origin main:main") is None


def test_branch_note_is_advisory_only():
    assert g.notes("git commit -m x", branch="main")
    assert g.notes("git commit -m x", branch="feature/y") == []
    assert g.notes("git status", branch="main") == []
    # a note is never a denial
    assert g.inspect("git commit -m x") is None
