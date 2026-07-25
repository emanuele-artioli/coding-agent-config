"""Platform-agnostic hook policy, shared by every agent on this host.

Each module here answers one question about a shell command and returns a
plain verdict — a reason string, or `None` for "nothing to say". Nothing in
this package reads stdin, writes stdout, or knows what a hook payload looks
like: those contracts differ per agent (Claude Code answers with a
`hookSpecificOutput` block, Cursor with `{"permission": …}`, Antigravity and
Codex with their own shapes), and mixing them into the policy is what would
make the same rule drift apart across five tools.

The entry points that *do* know a platform's dialect are the `guard-*.py`
scripts in the parent directory (Claude Code, and Copilot CLI which reuses the
same payload shape) and `cursor/before-shell.py`.
"""
