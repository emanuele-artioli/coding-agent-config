"""Both directions matter, and the false positive is the one that bites daily.

A false negative costs an hour of wall clock: the watcher spins, the job
finishes unnoticed. A false positive costs the ability to *write about* the
rule — a PR body, a rule file, a prompt for another agent — which is exactly
how this policy's own documentation gets produced. On 2026-09-01 a
`gh pr create --body "$(cat <<EOF ... EOF)"` was denied because the PR text
quoted the patterns it was announcing as blocked; `inspect` was matching a
heredoc body, which `destructive_git` and `destructive_rm` had already
learned not to do.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402

from guardlib import wait_loop as w  # noqa: E402

# Assembled rather than written out, so this file stays quotable inside a
# command string on a host where some other tool has not learned about
# heredocs yet. Same convention as test_destructive_git.py.
SLEEP = "sleep" + " 5"
UNTIL_LOOP = "until ! pgrep -f trainer; do " + SLEEP + "; done"
WHILE_LOOP = "while pgrep -f trainer > /dev/null; do " + SLEEP + "; done"

DENIED = [
    UNTIL_LOOP,
    WHILE_LOOP,
    "while pidof python; do " + SLEEP + "; done",
    "until kill -0 12345; do " + SLEEP + "; done",
    "while ps -p 12345 > /dev/null; do " + SLEEP + "; done",
    "while ps aux | grep -q train; do " + SLEEP + "; done",
    "cd /repo && " + UNTIL_LOOP,
    UNTIL_LOOP + " && echo finished",
]

ALLOWED = [
    # each of the three ingredients alone, and any two of them
    "pgrep -f trainer",
    SLEEP,
    "ps -eo pid,args | grep -F trainer",
    "while read -r line; do echo $line; done < list.txt",
    "until [ -f /tmp/done ]; do " + SLEEP + "; done",      # a file, not a process
    "until curl -sf localhost:8000/health; do " + SLEEP + "; done",  # an endpoint
    "gh run watch 12345 --exit-status",                    # the right tool
    "while pgrep -f trainer; do echo still up; break; done",  # no sleep
    # not a waiter at all
    "python train.py",
    "git status",
]


@pytest.mark.parametrize("command", DENIED)
def test_hand_rolled_waiter_is_denied(command):
    assert w.inspect(command) is not None, command


@pytest.mark.parametrize("command", ALLOWED)
def test_everything_else_is_allowed(command):
    assert w.inspect(command) is None, command


HEREDOC_BODY = "\n".join([
    "cat > doc.md <<'EOF'",
    "Never write " + UNTIL_LOOP + " -- it self-matches.",
    "EOF",
])

# The 2026-09-01 shape: a heredoc nested inside a command substitution, which
# is how a PR body or an issue comment gets passed on the command line.
PR_BODY = "\n".join([
    "gh pr create --title t --body \"$(cat <<'EOF'",
    "- " + WHILE_LOOP + " -> wait-loop deny",
    "EOF",
    ")\"",
])


def test_a_loop_written_about_is_not_a_loop_run():
    assert w.inspect(HEREDOC_BODY) is None


def test_heredoc_inside_command_substitution_is_data():
    """The live case: `gh pr create --body "$(cat <<'EOF' ... EOF)"`."""
    assert w.inspect(PR_BODY) is None


def test_a_real_waiter_after_a_heredoc_is_still_caught():
    assert w.inspect(HEREDOC_BODY + "\n" + UNTIL_LOOP) is not None


def test_unterminated_heredoc_is_still_inspected():
    """A heredoc that never closes must not become a way to hide a waiter."""
    opened = "cat > doc.md <<'EOF'\n" + UNTIL_LOOP
    assert w.inspect(opened) is not None


def test_reason_names_the_self_match_and_the_way_out():
    reason = w.inspect(UNTIL_LOOP)
    assert "self" in reason or "matches its own" in reason
    assert "run_in_background" in reason  # claude is the default dialect


def test_dialect_selects_that_agent_vocabulary():
    assert "run_in_background" in w.inspect(UNTIL_LOOP, dialect="claude")
    assert "block_until_ms" in w.inspect(UNTIL_LOOP, dialect="cursor")
    # an unknown dialect still says something useful rather than raising
    assert w.inspect(UNTIL_LOOP, dialect="nosuch") is not None


def test_empty_command_is_allowed():
    assert w.inspect("") is None
