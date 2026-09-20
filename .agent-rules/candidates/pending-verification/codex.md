# Codex — pending verification

Unchecked items trigger the Codex SessionStart reminder.

- [ ] Fresh-session discovery: global `AGENTS.md` and all shared `~/.agents/skills` entries appear after installer wiring.
- [ ] Review and trust `$CODEX_HOME/hooks.json` with `/hooks`, then confirm SessionStart context reaches the agent.
- [x] Adapter probe (2026-09-02): `rm -rf __guard_probe__` returns Codex `permissionDecision: deny` and logs under `$CODEX_HOME`; the command is never executed. Live hook firing remains covered by the hook-trust item above.
- [ ] Confirm UserPromptSubmit, PreCompact, and Stop hooks fire with live Codex payloads.
- [ ] Confirm whether Codex TOML roles can faithfully map the shared Markdown `gpu-job-runner` and `paper-editor` agents before claiming subagent parity.
- [ ] Confirm the desktop app reloads changed global skills and hooks without restarting the remote app server.
- [ ] **Automated merged worktree cleanup (added 2026-09-07, candidate `2026-09-07-automated-merged-worktree-cleanup`).**
  Host-wide git post-merge hook (`~/.agent-rules/hooks/post-merge`) wired via `core.hooksPath`
  and `~/bin/git-clean-merged-worktrees` CLI on PATH. Confirm from a Codex session that git merge/pull operations
  safely trigger post-merge cleanup of merged worktrees while preserving dirty or unmerged worktrees. Manual test: run `git clean-merged-worktrees --dry-run`.
- [ ] **Shared agents as `$CODEX_HOME/agents/*.toml` and AGENTS concatenation (added 2026-09-19).**
  `scripts/install.py` now generates one TOML per shared agent under
  `$CODEX_HOME/agents/`, with `model` / `model_reasoning_effort` from
  `effort-models.json` (junior for all, escalation for `stuck-escalation`), and
  writes `$CODEX_HOME/AGENTS.md` at install time from `AGENTS.md` + `host.md` +
  `harness/codex/codex.md`.
  Confirm from a Codex session that the generated TOML files load, that
  `implementer` spawns on Luna max and `stuck-escalation` on Astra, and
  that `$CODEX_HOME/AGENTS.md` now carries the Codex harness section.
  Also: `$CODEX_HOME/config.toml` still defines its own `[agents.luna_medium]`,
  `[agents.terra_medium]` and `[agents.sol_medium]` tables next to the seven
  generated `agents/*.toml`. Once the generated ones spawn, remove those three
  tables so there is one ladder at user level; PointStream's project copy was
  deleted on 2026-09-19 for the same reason.
- [ ] **Explicit closeout adapter (added 2026-09-20).** `harness/codex/stop.py`
  now calls the shared adapter only for an explicit `closeout` boundary and
  stable event identity; ordinary Stop and re-entry remain advisory no-ops.
  Confirm from a fresh Codex session that the Stop payload exposes those fields,
  the receipt is written under `$CODEX_HOME`, and no continuation loop starts.
