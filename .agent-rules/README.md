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
- `scripts/<name>.{sh,py}` — canonical hook/enforcement logic. Each agent's
  own hook config calls this script by absolute path. Event names and
  matchers stay in each agent's own settings file — those are inherently
  tool-specific (Claude's PreToolUse/PostToolUse vs. Antigravity's
  onWrite-style triggers) and can't be unified, only the invoked logic can.
  Advisory (never-block) scripts are made directly executable (`chmod +x`,
  invoked without a `python3`/interpreter prefix) so a missing file hits
  Claude Code's real "command not found" fail-open path, rather than
  `python3 <missing path>`, which runs fine and exits 2 — a blocking error
  on some hook events (notably `Stop`, where exit 2 means "prevents Claude
  from stopping," turning a missing advisory script into a hung session).
  Safety-guard scripts (`guard-rm.py`, `guard-wait-loop.py`) are invoked via
  `python3 <path>` deliberately, so a missing file fails *closed* (blocks
  the whole Bash call) instead of silently letting the thing they guard
  against through.

### Exception: `sync_agent_rules.py` is vendored, not referenced centrally

Every script above is invoked by an absolute path pointing back into this
directory. `scripts/sync_agent_rules.py` can't work that way: it's invoked
by CI in both pointstream and presley (and by pointstream's local
pre-commit), and CI runners have no access to `~/.agent-rules/` at all — a
central reference would break every push. Instead, `scripts/sync_agent_rules.py`
is the one hand-edited canonical copy, and
`scripts/vendor-sync-agent-rules.sh` physically copies it into
`pointstream/tools/` and `presley/tools/` whenever it changes. Run the
vendor script after editing the canonical copy; there's no automated check
that the vendored copies stay current (CI can't do that check either) — the
same trust model `tools/host_rules_snapshot.md` already operates under in
each project.

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

No cross-agent skill exists yet (still groundwork, per the `skills/` section
above). `scripts/` is real, in active use since 2026-07-23: `session-status.py`,
`guard-rm.py`, `paper-sync-reminder.py`, and `guard-wait-loop.py` were
consolidated out of duplicated copies in pointstream and presley;
`sync_agent_rules.py` follows the vendor-copy model explained above.
