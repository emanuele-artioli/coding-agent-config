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

## Knowledge loop

Invoke shared skills with `$name` or let descriptions trigger them. Use `end-of-session` for close-out, `evaluate-candidates` in config sessions, and `handoff` when work moves sessions.

Record unverified behavior in `../candidates/pending-verification/codex.md` and verify it from a fresh Codex session after hook changes.
