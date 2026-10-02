# Cursor harness rules

Cursor-specific mechanics, to sit alongside the tool-agnostic host rules in
`../../AGENTS.md`. Dated hook probes live in `lessons/`.

**How this file reaches Cursor.** Cursor has no user-level rules file —
`~/.cursor/rules/` is not read. User Rules live in Settings as plain
text. Paste `USER-RULE.md`. Opening this repo also loads them.
A project `.mdc` that only points here is optional, never a copy.

## File tools over Shell

Prefer `Read`, `Glob`, `Grep`, `StrReplace`, and `Write` over Shell.
When Shell is required (git, conda, a job), batch into one call with `&&`.
Size `block_until_ms` to the expected runtime plus a buffer.
Use `AwaitShell` when the next step is blocked on that job.
Never hand-roll `pgrep` wait-loops; `guard-wait-loop.py` blocks them.

## Subagents

Spawn juniors by `subagent_type`. Omit Task `model` so the generated
file slug applies. Juniors are Grok 4.7 Medium and escalation is Grok 4.7
Extra High (`../effort-models.json`); the senior session stays High in
the product UI, on the 256k window. `../../scripts/install.py` writes
Cursor-native copies into `~/.cursor/agents/<n>.md`. Escalate with a
fresh `stuck-escalation` child after `STUCK: out of ideas.` or a failed
check.

The senior re-runs the child's check itself. `subagentStop` is wired but
cannot flag a broken report — the native payload has no child-final-text
(see `lessons/`).
