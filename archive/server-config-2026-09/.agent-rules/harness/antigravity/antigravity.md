# Antigravity harness rules

Antigravity-specific mechanics, to sit alongside the tool-agnostic host rules in
`../../AGENTS.md`. Dated hook and role probes live in `lessons/`.

**How this file reaches Antigravity.** Imported by `~/.gemini/GEMINI.md` alongside
`../../AGENTS.md`. Antigravity reads both `AGENTS.md` and `GEMINI.md` and lets
`GEMINI.md` win on conflicts.

## File tools over Shell

Prefer `view_file`, `write_to_file`, and `replace_file_content` over `run_command`.
When `run_command` is required (git, conda, a job), size `WaitMsBeforeAsync` to
the expected runtime plus a buffer. Never hand-roll wait loops; `before-shell.py`
denies them.

## Subagents

Spawn juniors via `invoke_subagent` by `TypeName`. Omit `Model` or pass `inherit`
so the generated file model/effort applies. `../../scripts/install.py` writes
Antigravity-native copies into `~/.gemini/config/agents/<n>.md` with `subagent: true`.
Escalate with a fresh `stuck-escalation` child after `STUCK: out of ideas.` or a
failed check; never resume the stuck child.

Use `Workspace: "branch"` or `"share"` for parallel lanes that make filesystem or git
changes; `"inherit"` (default) for read-only coordination. Mapped rungs
(`../effort-models.json`): junior is Flash at medium, escalation is Flash at high.
There is no Gemini 3.8 Pro; do not pass `pro`.

The senior re-runs the child's check itself. Hook guards deny off-family models
(`guard-model-family.py`). Ordinary Stop is not closeout — the closeout adapter
(`stop.py`) captures only explicit boundaries.
