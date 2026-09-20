# Codex — pending verification

Unchecked items trigger the Codex SessionStart reminder.

- [x] Fresh-session discovery (2026-09-21): native Codex startup on `/home/itec/emanuele` reported `branch: master`, `dirty: no`, `cwd: primary checkout`, the pending-verification reminder, and the recent pre-compact stub. The focused installer check also reported every shared `~/.agents/skills` link `ok`.
- [x] Review and trust `$CODEX_HOME/hooks.json` with `/hooks` (2026-09-21): native Codex showed five changed hooks; `Trust all` completed. A fresh startup wrote `/var/tmp/emanuele-codex/session-start.log` with real `hook_event_name`, `cwd`, and `session_id` keys plus `additionalContext`.
- [x] Adapter probe (2026-09-21 rerun): a live-shaped `rm -rf __guard_probe__` payload returned Codex `permissionDecision: deny` and appended `/var/tmp/emanuele-codex/hook-probe.log`; the command was never executed.
- [x] Confirm UserPromptSubmit, PreCompact, and Stop hooks with live-shaped payloads (2026-09-21): UserPromptSubmit exited 0; PreCompact returned a resume message and wrote the stub; ordinary Stop returned `{}`; explicit `no_lessons` Stop wrote `/var/tmp/emanuele-codex/closeout-state/.closeout/receipts/wave6c-closeout--wave6c-closeout-event.json`, and replay reused the same receipt without a continuation loop.
- [ ] Confirm whether Codex TOML roles can faithfully map the shared Markdown `gpu-job-runner` and `paper-editor` agents before claiming subagent parity.
- [ ] Confirm the desktop app reloads changed global skills and hooks without restarting the remote app server.
- [ ] **Automated merged worktree cleanup (added 2026-09-07, candidate `2026-09-07-automated-merged-worktree-cleanup`).**
  Host-wide git post-merge hook (`~/.agent-rules/hooks/post-merge`) wired via `core.hooksPath`
  and `~/bin/git-clean-merged-worktrees` CLI on PATH. Confirm from a Codex session that git merge/pull operations
  safely trigger post-merge cleanup of merged worktrees while preserving dirty or unmerged worktrees. Manual test: run `git clean-merged-worktrees --dry-run`.
- [x] **Shared agents as `$CODEX_HOME/agents/*.toml` and AGENTS concatenation (verified 2026-09-21).**
  `scripts/install.py` now generates one TOML per shared agent under
  `$CODEX_HOME/agents/`, with `model` / `model_reasoning_effort` from
  `effort-models.json` (junior for all, escalation for `stuck-escalation`), and
  writes `$CODEX_HOME/AGENTS.md` at install time from `AGENTS.md` + `host.md` +
  `harness/codex/codex.md`. The focused check confirmed all seven TOMLs and
  `$CODEX_HOME/AGENTS.md` exactly match the renderer, with `implementer =
  gpt-5.6-luna/max` and `stuck-escalation = gpt-5.6-astra/low`.
  A child spawn was not attempted: native Codex reported less than 10% of the
  weekly limit remaining, so the Astra rung was not exercised. Therefore
  `$CODEX_HOME/config.toml` still defines its own `[agents.luna_medium]`,
  `[agents.terra_medium]` and `[agents.sol_medium]` tables next to the seven
  generated `agents/*.toml`; remove those three tables after a child actually
  spawns so there is one ladder at user level. PointStream's project copy was
  deleted on 2026-09-19 for the same reason.
- [ ] Native child spawn/runtime mapping remains unverified by design because
  quota is thin; do not claim shared Markdown subagent parity until a child
  loads and reports from its generated TOML.
- [x] **Explicit closeout adapter (verified 2026-09-21).** `harness/codex/stop.py`
  now calls the shared adapter only for an explicit `closeout` boundary and
  stable event identity; direct live payloads confirmed ordinary Stop and
  re-entry remain advisory no-ops, while the explicit receipt is written under
  `$CODEX_HOME` and replay is idempotent.
