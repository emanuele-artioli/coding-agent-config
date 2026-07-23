# Cross-agent shared rules and skills

Single source of truth for configuration shared across coding agents on this
host (currently Claude Code and Google Antigravity/Gemini CLI). Each agent's
own native config file is a thin wrapper pointing here — edit content only
in this directory, never in the per-agent copies.

## Layout

- `shared.md` — host-wide prose rules and conventions. Imported directly via
  `@` syntax from `~/.claude/CLAUDE.md` and `~/.gemini/GEMINI.md` (both
  tools natively support `@/absolute/path` imports) — an edit here is live
  in both immediately, no sync step, no drift.
- `skills/<name>.md` — canonical procedure for a skill shared across agents.
  Each agent's own skill file keeps its own required frontmatter (name,
  description — genuinely tool-specific schema) but its body is just one
  instruction: "Read `/home/itec/emanuele/.agent-rules/skills/<name>.md`
  and follow it." **Unlike `shared.md`, this is not a guaranteed system-level
  import** — it relies on the agent actually complying with that
  instruction. Test a new skill once for real before trusting it for
  anything that matters.
- `scripts/<name>.sh` — canonical hook/enforcement logic. Each agent's own
  hook config calls this script by absolute path. Event names and matchers
  stay in each agent's own settings file — those are inherently
  tool-specific (Claude's PreToolUse/PostToolUse vs. Antigravity's
  onWrite-style triggers) and can't be unified, only the invoked logic can.

## Known skill/hook locations per agent

- Claude Code skills: `~/.claude/skills/<name>/SKILL.md` (user-level) or
  `.claude/skills/<name>/SKILL.md` (project-level)
- Claude Code hooks: `~/.claude/settings.json` (user-level) or
  `.claude/settings.json` (project-level), keyed by event
  (PreToolUse/PostToolUse/UserPromptSubmit/Stop/etc.)
- Antigravity skills: `~/.gemini/antigravity/skills/<name>/SKILL.md`
  (global scope)
- Antigravity global workflows: `~/.gemini/antigravity/global_workflows/<name>.md`
- Gemini CLI custom commands: `~/.gemini/commands/<name>.toml`
- Gemini CLI / Antigravity hooks: `~/.gemini/settings.json`, triggered on
  events like `onWrite`

None of the above existed on this host as of 2026-07-23 — this is
groundwork for whenever the first cross-agent skill or hook actually gets
written, not a migration of existing content.
