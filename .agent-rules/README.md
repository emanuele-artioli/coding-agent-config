# Cross-agent shared rules and tools

Single source of truth for configuration shared across coding agents on this
host: Claude Code, Google Antigravity/Gemini CLI, and GitHub Copilot
(CLI/cloud agent — not the older VS Code Copilot Chat instructions model,
which has no comparable global-config surface). Each agent's own native
config is either a symlink into this repo or a thin wrapper pointing here —
edit content only in this directory, never in a per-agent copy.

All paths below were verified against each platform's current docs and
against what actually exists on disk on this host — not carried over from
memory, since Antigravity in particular moved its global config path (see
"Antigravity's global path moved" below).

## Layout

- `shared.md` — host-wide prose rules and conventions. Imported directly via
  `@` syntax from `~/.claude/CLAUDE.md` and `~/.gemini/GEMINI.md` (both
  tools natively support `@/absolute/path` imports) — an edit here is live
  in both immediately, no sync step, no drift. Copilot has no import syntax,
  but its coding agent/code-review now read a repo's `AGENTS.md` natively
  (alongside `CLAUDE.md`/`GEMINI.md` directly, per GitHub's own changelog),
  and `scripts/sync_agent_rules.py` (see below) already generates `AGENTS.md`
  from each project's `CLAUDE.md` — so Copilot gets host-wide rules
  transitively through that generated file, no separate mechanism needed.
- `skills/<name>/SKILL.md` and `agents/<name>.agent.md` — canonical
  **global** tools, real files (not pointer files — skills/agents have no
  import syntax, so the content itself must be present at the path each
  platform scans). Made available on each platform via the **symlink farm**
  (below). Use these for a tool that is genuinely generic — no project-name,
  no project-specific path, no project-specific metric baked in.
- `skills/<name>/SKILL.md` is *also* used for the **skeleton + thin-wrapper**
  pattern: a handful of skills (`test-design`, `update-paper`,
  `reviewer-response`, `results-report`) turned out to exist independently in
  both `pointstream` and `presley` with the same shape but real
  project-specific bodies (different paper repo hashes, different metric
  names, different conventions) — not copy-paste duplication. For these, the
  file here holds the generic procedure, and each project keeps its own
  `.claude/skills/<name>/SKILL.md` shrunk to its own required `description`
  frontmatter (must stay project-specific — it's what triggers invocation)
  plus one line — "Read `/home/itec/emanuele/.agent-rules/skills/<name>/
  SKILL.md` and follow it" — plus that project's own specifics. **This is not
  a guaranteed system-level import** the way `shared.md`'s `@` is — it relies
  on the agent actually complying with the instruction. Test a new one once
  for real before trusting it for anything that matters. Same pattern for the
  `paper-editor` and `gpu-job-runner` agent skeletons.
- `scripts/<name>.{sh,py}` — canonical hook/enforcement logic. Each
  platform's own hook config calls this script by absolute path. Event names
  and matchers stay in each platform's own config — those are inherently
  tool-specific and can't be unified, only the invoked logic can (see the
  event-name table below; the three platforms don't even agree on
  capitalization). Advisory (never-block) scripts are made directly
  executable (`chmod +x`, invoked without a `python3`/interpreter prefix) so
  a missing file hits Claude Code's real "command not found" fail-open path,
  rather than `python3 <missing path>`, which runs fine and exits 2 — a
  blocking error on some hook events (notably `Stop`, where exit 2 means
  "prevents Claude from stopping," turning a missing advisory script into a
  hung session). Safety-guard scripts (`guard-rm.py`, `guard-wait-loop.py` —
  the ones that can actually deny a call) are invoked via `python3 <path>`
  deliberately, so a missing file fails *closed* (blocks the whole Bash
  call) instead of silently letting the thing they guard against through.
  `guard-long-run.py` is advisory, not a safety guard — it only ever prints
  a note and exits 0 — so despite living in the same directory it follows
  the advisory convention above (`chmod +x`, direct exec, no `python3`
  prefix).

### Exception: `sync_agent_rules.py` is vendored, not referenced centrally

Every script above is invoked by an absolute path pointing back into this
directory. `scripts/sync_agent_rules.py` can't work that way: it's invoked by
CI in pointstream, presley, moq3dgs and TIGAS (and by local pre-commit in
each), and CI runners have no access to `~/.agent-rules/` at all — a central
reference would break every push. Instead, `scripts/sync_agent_rules.py` is
the one hand-edited canonical copy, and `scripts/vendor-sync-agent-rules.sh`
physically copies it into each project's `tools/` dir whenever it changes.
Run the vendor script after editing the canonical copy; there's no automated
check that the vendored copies stay current (CI can't do that check either)
— the same trust model `tools/host_rules_snapshot.md` already operates under
in each project.

## Global tool locations per platform

| | Claude Code | Antigravity / Gemini CLI | GitHub Copilot (CLI/cloud agent) |
|---|---|---|---|
| Global skills | `~/.claude/skills/<name>/SKILL.md` | `~/.gemini/config/skills/<name>/SKILL.md` | `~/.copilot/skills/<name>/SKILL.md` (also reads `~/.agents/skills/`) |
| Project skills | `.claude/skills/<name>/SKILL.md` | `.agents/skills/<name>/SKILL.md` | reads `.github/skills`, `.claude/skills`, **or** `.agents/skills` |
| Global agents | `~/.claude/agents/<name>.md` | `~/.gemini/config/agents/<name>.md` (or `<name>/agent.md`) | `~/.copilot/agents/<name>.agent.md` |
| Project agents | `.claude/agents/<name>.md` | `.agents/agents/<name>.md` | `.github/agents/<name>.agent.md` |
| Global hooks | `~/.claude/settings.json`, keyed by event | `~/.gemini/config/hooks.json` | `~/.copilot/hooks/*.json` (CLI only) |
| Project hooks | `.claude/settings.json` | `.agents/hooks.json` | `.github/hooks/*.json` |
| Hook event names | `PreToolUse`/`PostToolUse`/`UserPromptSubmit`/`Stop`/`SessionStart`/… | `PreToolUse`/`PostToolUse`/`PreInvocation`/`PostInvocation`/`Stop` | `preToolUse`/`postToolUse`/`sessionStart`/`sessionEnd`/`userPromptSubmitted`/`agentStop`/`subagentStop`/`errorOccurred` (lowerCamel, different set) |
| Prose rules | `~/.claude/CLAUDE.md` / `CLAUDE.md` | `~/.gemini/GEMINI.md` / `.agents/rules/*.md` | `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md` (glob-scoped via `applyTo` frontmatter), plus reads `AGENTS.md`/`CLAUDE.md`/`GEMINI.md` directly |
| Custom commands | `.claude/commands/` (merged into skills) | `~/.gemini/commands/<name>.toml` | n/a |

Notes:

- **Antigravity's global path moved.** Docs and disk both now say
  `~/.gemini/config/{skills,agents,hooks.json}` — `~/.gemini/antigravity/skills/`
  and `~/.gemini/antigravity/global_workflows/`, previously documented here,
  do not exist on disk and are stale. `~/.gemini/config/` does exist and
  already holds a vendor plugin's skills in exactly this shape, which is what
  caught the staleness.
- **No platform's global folder is shared verbatim by another** — each wants
  the file at its own exact path (and, for agents, its own extension:
  `<name>.md` vs `<name>.agent.md`). Since these are plain files, not
  directories with generated content, a **symlink farm** works: the real file
  lives under `.agent-rules/skills/` or `.agent-rules/agents/`, and each
  platform's global directory gets a symlink into it, named whatever that
  platform requires. Content is authored once, live everywhere, no drift —
  the same effect `shared.md`'s `@import` gets for prose, achieved
  differently because skills/agents have no import syntax.
- **Copilot's project-level skills overlap with the other two "for free."**
  It reads `.claude/skills` or `.agents/skills` directly — no copy needed.
  Antigravity's project-level path is `.agents/skills`; Claude's is
  `.claude/skills`. Projects here keep one real directory (`.claude/skills`)
  and symlink `.agents/skills` → `.claude/skills`, so all three platforms
  read the same project-level files with one symlink, not three copies.
- **Copilot's agentic workflows** (`.md` files compiled to a hardened
  `.lock.yml` GitHub Actions workflow) are repo-only by design — they run in
  Actions, committed to the default branch. No global equivalent exists,
  nothing to unify there.
- **Copilot's plugins** (a manifest bundling agents+skills+hooks+MCP+LSP,
  installable via `~/.copilot/settings.json` user-level or
  `.github/copilot/settings.json` repo-level) are a Copilot-specific
  packaging format with no Claude/Antigravity equivalent. Out of scope here
  — the symlink farm already gets the cross-platform reuse a plugin would,
  without adopting a Copilot-only format that the other two can't read.
- `~/.copilot/` exists on this host but the `copilot` CLI binary is not
  currently on `PATH` — the global dirs are created and populated anyway so
  they're ready the moment it is installed. **`~/.copilot/hooks/wait-loop.json`
  is wired to `guard-wait-loop.py` on the same assumption Claude's wiring
  uses (tool-call JSON on stdin, `tool_name`/`tool_input.command` keys) —
  this is unverified**, since Copilot's docs describe the hook *config*
  schema but not the exact payload/output contract a `preToolUse` command
  receives and must return. Test for real the first time Copilot CLI is
  actually installed and used here, per the general skill/hook testing rule
  above — don't trust this wiring blindly until then.

`scripts/` is real, in active use since 2026-07-23: `session-status.py`,
`guard-rm.py`, `paper-sync-reminder.py`, `guard-wait-loop.py`, and
`guard-long-run.py` were consolidated out of duplicated/missing copies in
pointstream and presley; `sync_agent_rules.py` follows the vendor-copy model
explained above.

`guard-wait-loop.py` is additionally wired into `~/.claude/settings.json`
(tracked in this repo) as a `PreToolUse`/`Bash` hook, and into
`~/.copilot/hooks/wait-loop.json` as a `preToolUse` hook, so it protects
every Claude Code and Copilot CLI project on this host automatically, not
just pointstream and presley — confirmed that Claude Code merges hooks
across user- and project-level settings files (both fire) rather than the
more specific level overriding, so this doesn't conflict with a project's
own copy of the same hook.
