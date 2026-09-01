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
- [x] **Effort-settability for subagents (added 2026-07-28, closed 2026-09-01).**
  Cursor's `Task` tool schema in this session has `model` and no `effort`
  field. Live `subagentStart` payloads (2026-08-26 log and this session)
  have keys `model` / `subagent_model` and never `effort`. Composer 2.5
  (the low-tier mapping) has no effort key in `effort-models.json` and no
  tier concept in the spawn API. The `-high` / `-medium` suffix on live
  slugs (`cursor-grok-4.5-high`) is part of the **model name**, not a
  separate parameter.   Treat `effort` in `effort-models.json` as unused on
  Cursor; pick the mapped `model` only. A live inherit Task spawn on
  2026-09-01 completed after the Claude `/usr/bin/env` import was fixed
  (see the next item). The earlier failClosed that day was that import,
  not a missing `effort` field.
- [x] **Read-before-edit cost of large files (added 2026-08-31, closed 2026-09-01).**
  Cursor is **not** Claude here, so do not promote that rule to `AGENTS.md`.
  (a) `StrReplace` on `projects.json` with no prior `Read` this conversation
  did **not** refuse for lack of a read; it searched the file and returned
  "string to replace was not found." (b) A default `Read` of a 508-line
  file (`CONCEPTS.md`) returned the whole file; so did 35-line and 573-line
  files. There is no 2000-line default page. (c) There **is** a per-call
  cap: `Read` of vscode.git `dist/main.js` (453,563 characters) failed with
  "exceeds maximum allowed characters (100000)" and asked for `offset` /
  `limit`. Cost exists for huge files, but the Claude coupling (must-read
  before edit + 2000-line default) does not. Stays in `harness/claude.md`.
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
  so that panel is not on `beforeShellExecution`. Closed 2026-09-01 without
  a UI click: vscode.git contributes `git.pushForce` as its own command
  (`enablement`: `config.git.allowForcePush`, default **false**) and this
  session's Git.log already showed it invoking `/usr/bin/git` itself. A
  throwaway branch cannot put that path onto `beforeShellExecution`. The
  Source Control panel hanging on this workspace is the parent git repo at
  `/home/itec/emanuele` (Git.log: `parent repositories (1)`); opening it
  runs `git status` on the home tree over NFS. `.vscode/settings.json` now
  sets `git.openRepositoryInParentFolders` to `never`. `AGENTS.md` had said
  the boundary is the same wherever you are working; that overstated it
  and is corrected. Also fixed live: `_current_branch` was spawning
  `git rev-parse` on every shell call and could failClosed the hook when
  that hung on NFS; it now runs only for commit/push and cannot failClosed.
- [x] **Cursor importing Claude `command`+`args` as `/usr/bin/env` (closed
  2026-09-01).** After reload, every Shell call (including `echo ping` and
  `git commit`) still failed with `Hook "/usr/bin/env" returned invalid
  JSON`. That was not `before-shell.py` and not the git guard. Cursor was
  loading `~/.claude/settings.json` PreToolUse entries whose `command` was
  `/usr/bin/env` with `args` setting `PYTHONPYCACHEPREFIX` and invoking
  `python3`. Cursor drops `args`, so it ran bare `env` (which prints the
  environment, not JSON) and fail-closed the action. Emptying
  `beforeShellExecution` in `~/.cursor/hooks.json` did not help, which is
  how this was distinguished from the Cursor-native adapter. Fix: Claude
  `command` is now `/usr/bin/python3 /path/script.py`; the pycache prefix
  is set inside the four `guard-*.py` scripts. After that, `echo ping`
  returned, a `/tmp` `git commit` whose message named a force-push
  succeeded, and a standalone `git push --force` was denied with
  "Blocked a git operation that cannot be undone." An inherit `Task` spawn
  completed. `failClosed` on the Cursor-native hooks is `true` again.
  Candidate: `done/2026-09-01-cursor-drops-claude-hook-args.md`
  (`needs_verification` on Claude).
