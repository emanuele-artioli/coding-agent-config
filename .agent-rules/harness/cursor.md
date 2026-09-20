# Cursor harness rules

Cursor-specific mechanics, to sit alongside the tool-agnostic host rules in
`../AGENTS.md`.

**How this file reaches Cursor.** Cursor has no user-level rules file —
`~/.cursor/rules/` is not read. User Rules live in Settings as plain
text. Paste `cursor-USER-RULE.md`. Opening this repo also loads them.
A project `.mdc` that only points here is optional, never a copy.

## File tools over Shell

Prefer `Read`, `Glob`, `Grep`, `StrReplace`, and `Write` over Shell.
When Shell is required (git, conda, a job), batch into one call with `&&`.
Size `block_until_ms` to the expected runtime plus a buffer.
Use `AwaitShell` when the next step is blocked on that job.
Never hand-roll `pgrep` wait-loops; `guard-wait-loop.py` blocks them.

## Subagents

Spawn juniors by `subagent_type`. Omit Task `model` so the generated
file slug applies. `../scripts/install.py` writes Cursor-native copies
into `~/.cursor/agents/<n>.md`. Escalate with a fresh `stuck-escalation`
child after `STUCK: out of ideas.` or a failed check.

The senior re-runs the child's check itself. `subagentStop` is wired and
logs keys to `~/.cursor/subagent-stop.log`, but the native payload has
no child-final-text field, so the adapter cannot flag a broken report.
Same as Antigravity here. The hook fires; the payload does not contain
the child's final text. `task` in that payload is the prompt, not the
child's last message.

## Where Cursor's own config lives

Every path, hook event name and payload shape: `../README.md`.
