# Cursor — pending verification

Checklist of items this platform must verify live. Unchecked `- [ ]` lines
trigger a SessionStart reminder.

- [x] SessionStart candidate / pending-verification reminders (sample payload + script probe 2026-07-27)
- [x] Progressive context nudges: beforeSubmitPrompt / stop / preCompact adapters (sample payloads; medium at stop 20; soft after warm; preCompact user_message)
- [x] `hooks.json` wired for sessionStart, beforeSubmitPrompt, stop, preCompact
- [x] Confirm live SessionStart fires after Cursor reloads `hooks.json` (2026-07-27 fresh chat `b90833db-…`: `~/.cursor/session-start.log` has real `session_id` + payload keys; `additional_context` also reached the agent via hooks_context)
- [x] Confirm whether live `stop` / `beforeSubmitPrompt` payloads include undocumented `context_usage_percent` (2026-07-27: `stop-probe.log` shows `has_fill: false` — stop has token counts / `loop_count` but **not** fill %; keep stop-count proxy in `context_nudge.py`)
- [x] Re-probe `beforeShellExecution` after hooks.json change (`rm -rf __guard_probe__` denied live 2026-07-27; probe log + failClosed deny)
- [x] Model-family gate: `preToolUse`/`Task` + `subagentStart` → `before-task.py` (2026-07-27 live: `claude-sonnet-5-thinking-high` denied; omit inherit allowed and `subagentStart` saw `cursor-grok-4.5-high`; log `~/.cursor/model-family-hook.log`)
- [x] **Tiered rule delivery (added 2026-07-28 from a Claude session — verified
  live 2026-08-31, Cursor session on `.agent-rules`).** Always-applied rules
  were host `AGENTS.md` twice (workspace file + `~/AGENTS.md`, same bytes),
  not `.claude/rules/*.md`. Asked to quote the research-code-tests section,
  this session cited `AGENTS.md` only. The `<!-- scope: … -->` comments are
  HTML comments; they did not change the rule text. `~/.claude/rules/host-research-code-tests-are-a-failsafe-not-a-formality.md`
  exists for Claude and was not injected here. This workspace has no
  `.cursor/rules/cursor-harness.mdc`; TIGAS still has the generated copy
  (`alwaysApply: true`); pointstream uses `host.mdc` pointers.
- [x] **Effort-tier nudge (added 2026-07-28 from a Claude session — verified
  live 2026-07-28).** `scripts/cursor/before-task.py` logs an effort-tier
  nudge from `../effort-models.json` when an allowed model is in-family but
  off the mapped low/medium/high tiers for cursor, and also returns it as
  `agent_message` while still `permission: allow`. Tier matching accepts
  live Cursor slugs (`cursor-grok-4.5-high` ≡ `grok-4.5`); `-fast` variants
  still nudge. Attempted upgrade to `{"permission": "ask"}` on a real
  `Task` spawn with `composer-2.5-fast` — Cursor rejected it with
  "The 'ask' permission for preToolUse hooks is not yet implemented. Use
  'allow' or 'deny' instead." So ask is **not** available on this hook yet
  (unlike `beforeShellExecution`); stay allow + log until Cursor implements
  it. Do not reopen unless that error goes away.
- [ ] **Effort-settability for subagents (added 2026-07-28 from a Claude
  session — not verified here).** Skipped 2026-08-31: this session did not
  spawn a `Task` with an `effort` parameter. `effort-models.json` carries an
  `effort` field on Cursor's medium/high (Grok 4.5) tiers, marked
  `verified: false`. Confirm whether Cursor/Grok exposes an effort parameter
  for a spawned `Task` subagent (vs. only for the interactive chat model
  picker), and whether Composer 2.5 has any tier concept at all — until
  confirmed, treat `effort` here as forward-looking data only.
- [ ] **Read-before-edit cost of large files (added 2026-08-31 from a Claude session — not verified here).**
  Skipped 2026-08-31 as a close: a default `Read` of a 573-line file returned
  the whole file, and `StrReplace` worked after that read. Did not test
  `StrReplace` without a prior read, and did not hit a per-call token cap.
  Not enough to promote or dismiss. On Claude Code, `Edit` refuses unless
  the file was read this conversation and a plain `Read` pulls up to 2000
  lines, so appending one line to a 67 KB doc cost ~17k tokens per session,
  again after each compaction; past ~25k tokens `Read` truncates. Recorded
  in `harness/claude.md`, deliberately **not** promoted to `AGENTS.md` until
  this is checked elsewhere. What to confirm here: (a) does this platform's
  edit tool require a prior read of the file, (b) does a default read pull
  the whole file, (c) is there a per-call result cap that forces pagination.
  If all three hold on every platform, promote the rule to `AGENTS.md`; if
  it is Claude-only, it stays in `harness/claude.md`.
  Candidate: `done/2026-07-29-claude-read-edit-cost-of-big-files.md`.
- [x] **Irreversible-git guard added to `cursor/before-shell.py` (2026-08-31,
  live in Cursor).** `beforeShellExecution` denied `git push --force`,
  `--force-with-lease`, `git push --delete origin <branch>`, and
  `git clean -fd`; the UI showed `user_message` "Blocked a git operation
  that cannot be undone" and the adapter JSON carried a readable
  `agent_message` naming the operation. In a `/tmp` repo, `git commit`,
  `git push -u origin <branch>`, `git merge --ff-only`, `git reset --hard
  HEAD~1`, and `git branch -D` ran with no prompt. A commit message that
  names a force push, and a heredoc whose body quotes one, were allowed;
  the same heredoc plus a real force push on the next line was denied.
  A `git commit` on `main` still succeeded; adapter stderr carried the
  branch-discipline note. Did **not** click Force Push in the Source
  Control panel (no UI from this agent). `vscode.git` in this session
  invoked `/usr/bin/git` itself (Git.log: `git rev-parse --show-toplevel`),
  so that panel is not on `beforeShellExecution`. `AGENTS.md` had said
  the boundary is the same wherever you are working; that overstated it
  and is corrected. Also fixed live: `_current_branch` was spawning
  `git rev-parse` on every shell call and could failClosed the hook when
  that hung on NFS; it now runs only for commit/push and cannot failClosed.
