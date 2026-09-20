# OpenAI Codex — host harness

Read this after `../AGENTS.md`. Codex-only mechanics live here; shared policy stays in `AGENTS.md` and `scripts/guardlib/`.

## Discovery

- Active state uses `$CODEX_HOME`; this server sets it to `/var/tmp/emanuele-codex` so sockets and SQLite state do not cross hosts over NFS.
- Global prose is `$CODEX_HOME/AGENTS.md`, linked to `../AGENTS.md`. Repository `AGENTS.md` files still apply from git root to cwd.
- User skills load from `~/.agents/skills/<name>/SKILL.md`; repository skills load from `.agents/skills`. Codex follows symlinked skill directories.
- Global hooks are `$CODEX_HOME/hooks.json`, linked to `codex-hooks.json` beside this file. Review changed hooks with `/hooks`.
- User MCP configuration lives in `$CODEX_HOME/config.toml`. The shared MCP catalog is currently empty; preserve unrelated Codex entries.
- Codex custom subagents are TOML roles under `[agents]`, not Claude/Cursor Markdown agents. Do not claim shared `agents/*.agent.md` parity until mappings exist.

## Shell and waiting

Unified exec returns a session id for a continuing process. Use `write_stdin` with that id to collect output or wait. Never write a `pgrep`/sleep loop.

For work that must survive SSH or app-server loss, use `setsid`/`nohup`, checkpoint at least hourly, and append progress at least every ten minutes.

The shell hook blocks unrecoverable git operations and protected-path removal, and adds advisory context for long runs and branch discipline. Hooks are guardrails, not a complete security boundary.

## Rungs

Rung map in `../effort-models.json` (the model-family adapter is still
limited). Generated Codex junior roles use `gpt-5.6-luna` with maximum
reasoning effort. Senior: Sol medium — the
interactive model, whatever the user set in the Codex UI. Escalation:
Astra low, rarely — it often dies mid-prompt. `agents.job_max_runtime_seconds`
in `config.toml` is the mechanical budget for a junior. Codex custom
subagents are TOML `[agents]`, not the shared markdown files; the shared
agents are `implementer`, `paper-screener`, `data-condenser`,
`paper-editor`, `referee`, `gpu-job-runner`, `stuck-escalation`. Read skill
`session` before spawning helpers. The senior still re-runs the junior's
check itself. Stop hooks may record a closeout only when the payload carries
an explicit boundary and stable event identity; an ordinary Stop remains an
advisory nudge.

## Knowledge loop (Codex)

Queue layout and how to file a candidate: `../candidates/README.md`. The
procedure is the `end-of-session` skill; this platform's live-wiring status is
`../candidates/pending-verification/codex.md`.
