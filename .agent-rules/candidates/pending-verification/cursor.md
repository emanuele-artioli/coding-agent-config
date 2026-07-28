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
- [ ] **Tiered rule delivery (added 2026-07-28 from a Claude session — not verified here).**
  Each project's `AGENTS.md` now marks some sections `<!-- scope: <globs> -->`.
  Those sections stay in `AGENTS.md` in full, so Cursor should be **unaffected**:
  it reads the root `AGENTS.md` eagerly and gets everything, exactly as before.
  What to confirm live, in any of pointstream / presley / moq3dgs / TIGAS / 4DGStudy:
  - Cursor still picks up the root `AGENTS.md` and the scope comments are inert
    (they are HTML comments, so they should render as nothing and change no rule).
  - Cursor does **not** additionally load `.claude/rules/*.md`. It reads
    `.claude/` skills, and if it also reads `.claude/rules/` then every scoped
    section arrives twice — once from `AGENTS.md`, once from the rule file.
    That is the one real regression risk on this platform. Ask the agent to
    quote a scoped rule and see whether it cites one source or two.
  - `.cursor/rules/cursor-harness.mdc` is unchanged and still applies.
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
  session — not verified here).** `effort-models.json` carries an `effort`
  field on Cursor's medium/high (Grok 4.5) tiers, marked `verified: false`.
  Confirm whether Cursor/Grok exposes an effort parameter for a spawned
  `Task` subagent (vs. only for the interactive chat model picker), and
  whether Composer 2.5 has any tier concept at all — until confirmed, treat
  `effort` here as forward-looking data only.
