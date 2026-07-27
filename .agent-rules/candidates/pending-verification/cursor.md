# Cursor — pending verification

Checklist of items this platform must verify live. Unchecked `- [ ]` lines
trigger a SessionStart reminder.

- [x] SessionStart candidate / pending-verification reminders (sample payload + script probe 2026-07-27)
- [x] Progressive context nudges: beforeSubmitPrompt / stop / preCompact adapters (sample payloads; medium at stop 20; soft after warm; preCompact user_message)
- [x] `hooks.json` wired for sessionStart, beforeSubmitPrompt, stop, preCompact
- [x] Confirm live SessionStart fires after Cursor reloads `hooks.json` (2026-07-27 fresh chat `b90833db-…`: `~/.cursor/session-start.log` has real `session_id` + payload keys; `additional_context` also reached the agent via hooks_context)
- [x] Confirm whether live `stop` / `beforeSubmitPrompt` payloads include undocumented `context_usage_percent` (2026-07-27: `stop-probe.log` shows `has_fill: false` — stop has token counts / `loop_count` but **not** fill %; keep stop-count proxy in `context_nudge.py`)
- [x] Re-probe `beforeShellExecution` after hooks.json change (`rm -rf __guard_probe__` denied live 2026-07-27; probe log + failClosed deny)
