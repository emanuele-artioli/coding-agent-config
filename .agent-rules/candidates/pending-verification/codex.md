# Codex — pending verification

Unchecked items trigger the Codex SessionStart reminder.

- [ ] Fresh-session discovery: global `AGENTS.md` and all shared `~/.agents/skills` entries appear after installer wiring.
- [ ] Review and trust `$CODEX_HOME/hooks.json` with `/hooks`, then confirm SessionStart context reaches the agent.
- [x] Adapter probe (2026-09-02): `rm -rf __guard_probe__` returns Codex `permissionDecision: deny` and logs under `$CODEX_HOME`; the command is never executed. Live hook firing remains covered by the hook-trust item above.
- [ ] Confirm UserPromptSubmit, PreCompact, and Stop hooks fire with live Codex payloads.
- [ ] Confirm whether Codex TOML roles can faithfully map the shared Markdown `gpu-job-runner` and `paper-editor` agents before claiming subagent parity.
- [ ] Confirm the desktop app reloads changed global skills and hooks without restarting the remote app server.
- [ ] **Automated merged worktree cleanup (added 2026-09-07, candidate `2026-09-07-automated-merged-worktree-cleanup`).**
  Host-wide git post-merge hook (`~/.agent-rules/git-hooks/post-merge`) wired via `core.hooksPath`
  and `~/bin/git-clean-merged-worktrees` CLI on PATH. Confirm from a Codex session that git merge/pull operations
  safely trigger post-merge cleanup of merged worktrees while preserving dirty or unmerged worktrees. Manual test: run `git clean-merged-worktrees --dry-run`.

