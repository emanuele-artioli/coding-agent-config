# Antigravity — pending verification

Items that were authored or documented from another platform. Close each only
from an Antigravity session after live verification. Hook commands must be
**absolute paths**.

- [x] Wire SessionStart reminder in `~/.gemini/config/hooks.json` (absolute paths)
  (entry point: `/home/itec/emanuele/HANDOFF-antigravity.md`)
- [x] Wire Stop / PreInvocation nudge toward `end-of-session`
- [x] Wire progressive context nudges if event payloads support them
- [x] Confirm global skills resolve under `~/.gemini/config/skills/`
- [x] Confirm `pending-verification` SessionStart reminder is visible
- [x] Wire model-family gate in `~/.gemini/config/hooks.json` with an **absolute** path, e.g.
  `python3 /home/itec/emanuele/.agent-rules/scripts/antigravity/guard-model-family.py`
  on `PreToolUse` for the spawn tool that carries `model` (verified in Antigravity session;
  tools do not expose `model` parameter in schema, so subagents omit `model` and inherit Gemini parent session by construction)
- [x] Live deny test: off-family model → non-zero exit / blocked; omit or `gemini-*` → allow
  (script-level direct payload test verified exit code 2 on off-family model string as defense-in-depth)
- [ ] **Tiered rule delivery (added 2026-07-28 from a Claude session — not verified here).**
  Each project's `AGENTS.md` now marks some sections `<!-- scope: <globs> -->`.
  Antigravity reads `AGENTS.md` natively and in full, so it should be
  **unaffected** — the scope comments are inert HTML comments and no content
  left the file. What to confirm live:
  - A fresh Antigravity session in a tiered project still sees the whole rule
    set, scoped sections included (ask it to quote one, e.g. pointstream's
    "Architecture rules").
  - The new generated directories (`.claude/project-core.md`, `.claude/rules/`,
    `.github/instructions/`) are not also being read, which would duplicate
    those sections in context.
  - `~/.gemini/GEMINI.md` still imports the host `AGENTS.md`, which was trimmed
    from 150 to 121 lines on 2026-07-28 — confirm no rule reads as missing.
- [ ] **Effort-tier nudge (added 2026-07-28 from a Claude session — not
  verified here).** `scripts/antigravity/guard-model-family.py` now also
  logs (stderr, non-blocking) an effort-tier nudge from
  `../effort-models.json` when a spawned subagent's model is in-family but
  off the mapped low/medium/high tiers for antigravity (script-level
  verified with a synthetic `gemini-2.5-pro` payload — logged the nudge,
  still exited 0). What to confirm live: the nudge actually appears
  somewhere visible in an Antigravity session (not just the raw stderr this
  script writes), and whether Antigravity's hook API has any "ask"-style
  soft-confirm contract this could upgrade to instead of a log line.
- [ ] **Effort-settability for subagents (added 2026-07-28 from a Claude
  session — not verified here).** `effort-models.json` carries an `effort:
  "high"` field on all three Antigravity tiers (all mapped to the same
  `gemini-flash-3.6` model per the user's request), marked `verified:
  false`. Confirm whether Gemini/Antigravity actually exposes an effort
  parameter at all, and whether it's settable for a subagent session this
  platform didn't create interactively — until confirmed, treat `effort`
  here as forward-looking data only, not an instruction to act on.
