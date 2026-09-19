# Claude Code — pending verification

Items that were authored or documented from another platform. Close each only
from a Claude Code session after live verification.

- [x] Wire SessionStart reminder: `scripts/claude/session-start.py` (thin
  adapter over `candidate-reminders.py`) in `~/.claude/settings.json`, direct
  executable (fail-open). 2026-07-28: driven with a realistic stdin payload
  (`session_id`/`cwd`/`hook_event_name`/`source`) — printed the 8-open-item
  reminder to stdout (exit 0, per docs this is injected straight into
  context) and appended a real line to `~/.claude/session-start.log`.
- [x] Wire Stop nudge toward `end-of-session` (fail-open, direct executable):
  `scripts/claude/stop.py`. 2026-07-28: driven with sample payloads —
  dirty-tree hint fired correctly (repo was dirty), `stop_hook_active: true`
  correctly short-circuited (no recursion), always exits 0 (Stop's exit 2
  would otherwise block Claude from stopping).
- [x] Wire UserPromptSubmit task-change detection (log-only, per locked
  decision — `CONTEXT_NUDGE_BLOCK_SOFT` unset): `scripts/claude/user-prompt-submit.py`.
  2026-07-28: normal prompt and a task-change-phrased prompt below the soft
  stop-count threshold both correctly produced no nudge, exit 0.
- [x] Wire PreCompact strong handoff / end-of-session nudge:
  `scripts/claude/pre-compact.py`. 2026-07-28: sample `PreCompact` payload
  produced the strong nudge on stdout, exit 0 (docs: PreCompact has no
  fill-percentage field, confirmed absent from stdin — message is
  unconditional here, unlike the Cursor fill-% probe).
- [x] Confirm progressive-nudge messages appear in Claude's hook output
  channel **in a live running session** (not a piped sample payload).
  2026-07-28: verified from a genuinely fresh session (`session_id
  10984e7c-6314-4ff1-b351-c8ed1c8d9276`) — `~/.claude/session-start.log`
  recorded that real session_id, and the "2 open pending-verification
  item(s)" reminder actually appeared as a `<system-reminder>` at the top of
  this turn's context, confirming the hook fires and injects on process
  start of a real session, not just under a piped sample payload.
- [x] Confirm global skills `end-of-session`, `evaluate-candidates`, `handoff`
  resolve via symlink farm. 2026-07-28: `ls -la ~/.claude/skills/` shows all
  three (plus `results-report`, `reviewer-response`, `test-design`,
  `update-paper`) as live symlinks into `.agent-rules/skills/`, not broken.
- [x] Wire model-family gate: `PreToolUse` matcher `Agent|Task` →
  `python3 /home/itec/emanuele/.agent-rules/scripts/guard-model-family.py`
  in `~/.claude/settings.json` (fail-closed via `python3 <path>`; adapter
  authored from Cursor, wiring done from Claude).
- [x] Live deny test: spawn `Agent` with an off-family model (e.g. `grok-*`)
  → expect deny; spawn with omit / `sonnet` → allow. 2026-07-28 resolved as
  N/A-by-design, not left open: in this harness the only tool matching the
  `Agent|Task` hook that carries a `model` field is `Agent`, and its JSON
  schema hard-restricts `model` to `sonnet|opus|haiku|fable` at the
  tool-call-validation layer — confirmed again this session that `TaskCreate`
  (the other tool `Task` could refer to) has no `model` field at all, so
  there is no tool surface in Claude Code that can ever pass an off-family
  model string down to the PreToolUse hook. A live hook-level deny is
  therefore structurally unreachable here, not unverified — the schema *is*
  the enforcement, and the hook is redundant defense-in-depth (already
  confirmed correct via direct script invocation with synthetic payloads,
  2026-07-28). Nothing further to check from a Claude Code session; do not
  reopen this line without a harness change that adds a schema-unrestricted
  spawn path. See [[cursor]] for contrast: Cursor's `Task` tool does *not*
  restrict `model` by schema, so its hook-level deny is both necessary and
  was actually exercised live.
- [x] **Effort-tier nudge (added 2026-07-28).** `guard-model-family.py` now
  also emits `hookSpecificOutput.permissionDecision: "ask"` (not deny) when
  an `Agent` spawn's `model` is in-family (`sonnet`/`opus`/`haiku`/`fable`)
  but not one of the tier-mapped models in `../effort-models.json` for
  claude (script-level verified with a synthetic `{"model": "haiku"}`
  payload — correctly emitted `ask` with the tier table; `{"model":
  "sonnet"}` correctly emitted nothing). 2026-07-28: closed live — spawned a
  real `Agent` with `model: "haiku"` from a running session, and the user
  confirmed a permission prompt actually appeared for that call. The `ask`
  decision surfaces to the user on a genuine spawn, not just in the hook's
  stdout.
- [x] **Effort-settability for subagents (added 2026-07-28).** Confirmed via
  this session's own `Agent` tool schema that `model` is a fixed enum
  (`sonnet|opus|haiku|fable`) with no effort/thinking-level channel — so
  `effort-models.json`'s `low` and `medium` tiers for claude both resolve to
  `model: "sonnet"` today, and the `effort` field on every claude entry is
  `verified: false`. 2026-07-28: re-checked this session's own `Agent` tool
  schema again — still the same fixed enum, no effort/thinking-level field.
  Closed as N/A-by-design, same footing as the live-deny-test line above:
  there is currently no channel in Claude Code to set subagent effort
  beyond model choice, so `effort` stays non-actionable for claude until a
  harness change adds one. Do not reopen without a schema change (a new
  field, a bracket-suffix model format actually landing).
- [x] **PreToolUse `command` is a python3 string, no `args` (added 2026-09-01
  from Cursor).** Cursor imports these hooks and drops `args`, so
  `"command": "/usr/bin/env"` plus an args array ran bare `env` and
  fail-closed every Cursor Shell call. `~/.claude/settings.json` now uses
  `/usr/bin/python3 /path/guard-*.py`. Confirm from a live Claude session
  that Bash PreToolUse (wait-loop, irreversible git, protected rm) and
  `Agent|Task` (model-family) still fire. Do not restore `command`+`args`
  through `/usr/bin/env`. See `done/2026-09-01-cursor-drops-claude-hook-args.md`.
  2026-09-01: closed live from a Claude session. All three Bash guards denied
  a real tool call with the new command-string wiring — `rm -rf __guard_probe__`
  (protected dir), `git reflog expire --expire=now --all --dry-run` and
  `git push --force-with-lease` (irreversible git), and both `until ! pgrep …`
  and `while pgrep … ; do sleep` (wait loop). The `Agent|Task` entry was not
  exercised by a live spawn (spawning an agent was out of scope for the
  session); its command string was run against a synthetic `{"model":
  "haiku"}` payload and correctly emitted the effort-tier `ask`, and it is the
  same one-string form as the three Bash entries that do fire live — the live
  spawn path itself was already closed on 2026-07-28 above.
  **Correction found while verifying:** the `os.environ.setdefault(
  "PYTHONPYCACHEPREFIX", …)` line the fix moved into each guard script did
  nothing — CPython reads that variable at startup, so it cannot affect the
  script's own imports, and guardlib `.pyc` files kept being written to the
  NFS source tree. Replaced with `sys.pycache_prefix = …` in all four guards
  (verified: bytecode now lands under `/var/tmp/emanuele-pycache`, nothing
  next to the source), and the wording corrected in both harness files.
- [ ] **Automated merged worktree cleanup (added 2026-09-07, candidate `2026-09-07-automated-merged-worktree-cleanup`).**
  Host-wide git post-merge hook (`~/.agent-rules/git-hooks/post-merge`) wired via `core.hooksPath`
  and `~/bin/git-clean-merged-worktrees` CLI on PATH. Confirm from a Claude Code session that executing
  `git merge`, `git pull`, or `gh pr merge` executes post-merge cleanup, deletes clean fully-merged linked worktrees
  and local branches, and preserves dirty or unmerged worktrees. Manual test: run `git clean-merged-worktrees --dry-run`.
- [ ] **Junior rung via agent-file `effort` (added 2026-09-18).** Vendor docs now
  list `effort: low|medium|high|xhigh|max` in subagent frontmatter and nesting up
  to three layers; this supersedes the closed 'Effort-settability' item above.
  `implementer` and the other junior files carry `effort: low`, `stuck-escalation`
  carries `effort: xhigh`. Confirm from a fresh Claude session that (a) `implementer`
  is spawnable by name, (b) the harness reports the child at low effort, (c) the
  `SubagentStop` hook `scripts/claude/subagent-stop.py` injects a system message
  when a child's last message lacks the report headings.
  2026-09-18, same session that authored it: (a) closed live, `implementer`
  was spawned by name and completed a bounded task; it became available
  about ten minutes after `install.py` linked the file, without a restart.
  (b) not closable: the `Agent` result reports tokens, tool uses and
  duration, not model or effort, and the child cannot see its own effort.
  2026-09-19, (b) closed from the transcripts instead: every assistant
  record carries an `effort` field, and the two `implementer` children of
  2026-09-18 (`agent-aafcf592de2ea65c5`, `agent-aa3080c70738fbb79`) record
  `effort: "low"` while the seven general-purpose children of the same
  wave (`a23f05d453ef8c1b8`, `a29d1c3152e7f2fb0`, `a36f4668105da868c`,
  `a42a5afdc736e9d82`, `a4aa038496b2f4584`, `a9955c5bfdf9df40f`,
  `adb3f207a9f6b1a20`) record the session effort, `high`.
  (c) still open: the `SubagentStop` entry was added to `~/.claude/settings.json`
  mid-session and a probe child that skipped the headings produced no system
  message, consistent with hooks being snapshotted at session start. Re-run
  the probe from a fresh session: spawn `implementer` with "reply `probe done`
  only" and expect a report-contract system message.
- [ ] **Junior context diet (added 2026-09-19).** Junior files now restrict
  `tools:`, set `omitClaudeMd: true`, and carry `agents/JUNIOR-FACTS.md`.
  A zero-tool probe of `implementer` in the session that made the change
  still cost 41,477 tokens with 22 tools in its prompt snapshot: the harness
  kept the agent definition it had loaded earlier, so frontmatter edits do
  not hot-reload. From a fresh session spawn `implementer` with "reply
  `probe done` only" and read the first-turn `input + cache_creation +
  cache_read` from its transcript; expect at most 19k (tools and rules
  dropped) or at most 11k (skill listing dropped too). Above 30k means a
  field did not take; check the snapshot's `tools` array length (was 22).
