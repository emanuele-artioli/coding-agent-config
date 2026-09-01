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
- [ ] **PreToolUse `command` is a python3 string, no `args` (added 2026-09-01
  from Cursor).** Cursor imports these hooks and drops `args`, so
  `"command": "/usr/bin/env"` plus an args array ran bare `env` and
  fail-closed every Cursor Shell call. `~/.claude/settings.json` now uses
  `/usr/bin/python3 /path/guard-*.py`. Confirm from a live Claude session
  that Bash PreToolUse (wait-loop, irreversible git, protected rm) and
  `Agent|Task` (model-family) still fire. Do not restore `command`+`args`
  through `/usr/bin/env`. See `done/2026-09-01-cursor-drops-claude-hook-args.md`.
