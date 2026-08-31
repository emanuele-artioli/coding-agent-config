"""Shared shell-string helpers for the guard policies.

One job so far: **a heredoc body is data, not commands.**

    cat > notes.md <<'EOF'
    <a line of prose naming a forbidden operation>
    EOF

Every policy here splits a command string on newlines to find simple commands,
which means a heredoc body's lines look exactly like commands. Writing the
documentation for a guard then trips that guard. That is not hypothetical: it
happened twice while writing the verification prompts that describe
`destructive_git`, and again while writing this module's own docstring.

The cost of getting this wrong runs both ways. Left unfixed, an agent cannot
write about the operations it is forbidden to run — including the rule files
that explain them. Fixed too eagerly, by stripping anything that merely looks
quoted, a real command hides behind a fake heredoc marker. So this strips only
a well-formed heredoc: an operator, a delimiter, and a terminator line that
actually appears.
"""

from __future__ import annotations

import re

# `<<EOF`, `<<-EOF`, `<<'EOF'`, `<<"EOF"`, with or without a space.
_HEREDOC_START = re.compile(
    r"<<-?\s*(?P<quote>['\"]?)(?P<delim>[A-Za-z_][A-Za-z0-9_]*)(?P=quote)"
)


def strip_heredocs(command: str) -> str:
    """Remove heredoc bodies, keeping the lines that are really commands.

    An unterminated heredoc keeps its body: better to over-inspect text that
    was never going to run than to let a real command escape by opening a
    heredoc that never closes.
    """
    if "<<" not in command:
        return command

    lines = command.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        out.append(lines[i])
        starts = _HEREDOC_START.findall(lines[i])
        i += 1
        for _quote, delim in starts:
            # Consume to the terminator, which may be indented for `<<-`.
            j = i
            while j < len(lines) and lines[j].strip() != delim:
                j += 1
            if j < len(lines):
                i = j + 1  # drop the body and the terminator line
            # else: unterminated -- leave the rest in place to be inspected
    return "\n".join(out)
