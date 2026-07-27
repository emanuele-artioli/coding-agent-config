# Cursor — pending verification

Checklist of items this platform must verify live. Unchecked `- [ ]` lines
trigger a SessionStart reminder.

- [x] SessionStart candidate / pending-verification reminders (sample payload + script probe 2026-07-27)
- [x] Progressive context nudges: beforeSubmitPrompt / stop / preCompact adapters (sample payloads; medium at stop 20; soft after warm; preCompact user_message)
- [x] `hooks.json` wired for sessionStart, beforeSubmitPrompt, stop, preCompact
- [ ] Confirm live SessionStart fires after Cursor reloads `hooks.json` (open a new chat; check `~/.cursor/session-start.log` and/or whether `additional_context` reached the agent — Cursor IDE has a known race that can drop it)
- [ ] Confirm whether live `stop` / `beforeSubmitPrompt` payloads include undocumented `context_usage_percent` (docs: field is on `preCompact` only; `stop` now appends keys to `~/.cursor/stop-probe.log` — check after this chat's stop)
- [x] Re-probe `beforeShellExecution` after hooks.json change (`rm -rf __guard_probe__` denied live 2026-07-27; probe log + failClosed deny)
