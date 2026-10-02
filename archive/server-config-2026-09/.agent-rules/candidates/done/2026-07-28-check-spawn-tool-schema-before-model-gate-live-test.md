---
id: 2026-07-28-check-spawn-tool-schema-before-model-gate-live-test
created: 2026-07-28
source_platform: claude
source_project: .
axis: platform
status: applied
summary: Before chasing a live hook-level deny test for the model-family gate, check whether the platform's own spawn-tool schema already restricts the model field.
suggested_action: From an Antigravity session, inspect the spawn tool that carries `model` (whatever it's called there) for a schema-level enum/restriction on allowed values, the same way Claude Code's `Agent` tool restricts `model` to `sonnet|opus|haiku|fable`. Record the finding in candidates/pending-verification/antigravity.md before attempting the live deny test.
verify_platforms: [antigravity]
---

Two platforms turned out to differ in a way worth checking explicitly rather
than assuming:

- **Claude Code**: the `Agent` tool's JSON schema itself restricts `model` to
  `sonnet|opus|haiku|fable`. An off-family value never reaches the
  PreToolUse `guard-model-family.py` hook — it's rejected by
  `InputValidationError` at the tool-call-validation layer first. The "live
  deny test" for this platform is therefore structurally unreachable, not
  merely unverified — closed as N/A in
  `candidates/pending-verification/claude.md`. The hook still runs and was
  confirmed correct via direct script invocation with synthetic payloads,
  but it's redundant defense-in-depth here, not the primary gate.
- **Cursor**: by contrast, `Task`'s schema does *not* restrict `model` — an
  off-family string (`claude-sonnet-5-thinking-high`) was actually accepted
  by the tool call and only then denied by the `before-task.py` hook
  (confirmed live 2026-07-27, see `candidates/pending-verification/cursor.md`).
  There the hook is load-bearing, not redundant.

Antigravity's `pending-verification/antigravity.md` still has the live deny
test listed as fully open, written from a guess ("adapter authored from
Cursor — unverified"). Before spending effort trying to force a live
hook-level deny, check which situation Antigravity is actually in: if its
spawn tool schema already enum-restricts `model` the way Claude Code's does,
the live deny test should be closed the same way (schema is the enforcement,
hook is defense-in-depth) instead of staying open indefinitely waiting for a
test that schema validation makes impossible to trigger.

## Resolution (2026-07-28)
Inspected Antigravity tool schemas. Native subagent spawn tools in Antigravity
(`browser_subagent`, `run_command`, `manage_task`, etc.) do not expose a `model`
or `subagent_model` field in their tool schemas — subagents always omit `model`
and inherit the parent Gemini session model by construction. Direct script
invocation with synthetic payloads (`claude-3-5-sonnet`) confirmed
`guard-model-family.py` exits code 2 as redundant defense-in-depth. Finding
recorded in `candidates/pending-verification/antigravity.md` and candidate closed as applied.
