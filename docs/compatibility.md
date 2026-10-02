# Harness compatibility

| Harness | Guidance | Skills | Execution / limitations |
|---|---|---|---|
| Codex | Effective `CODEX_HOME/AGENTS.md`, project `AGENTS.md` | `~/.agents/skills`, project `.agents/skills` | `exec --json`, native session resume; isolated subscription profile for unattended work |
| Claude | `~/.claude/CLAUDE.md`; project `@AGENTS.md` compatibility shim | `~/.claude/skills` | `-p --output-format stream-json --resume`; attended until isolated auth/tool profile is verified |
| Cursor | Project `AGENTS.md`; managed `.cursor/rules/agentctl.mdc` | `~/.agents/skills` | Native `agent` CLI required; editor CLI alone is insufficient |
| Antigravity | `~/.gemini/config/AGENTS.md`, project `AGENTS.md` | Desktop/IDE config skills; CLI `~/.gemini/antigravity-cli/skills` | `agy -p --output-format stream-json --conversation`; attended until isolated auth/tool profile is verified |

The installer creates a Cursor user-rule artifact when no project is specified.
It does not pretend to set the UI's global user rules. Paste that artifact into
Cursor User Rules or use `install --project PATH --harness cursor` in each project.
Existing project instructions are preserved. Existing unmanaged symlinks or
edited managed files produce conflicts requiring review.

Claude's directly documented `AGENTS.md` discovery requires 2.1.277+. Earlier
versions use a shim; native discovery can be suppressed by legacy Claude
instruction files. Keep compatibility until a native-session loading check
establishes that it is unnecessary. Skills use native discovery paths rather
than assuming all harnesses search the same locations.

Hooks use one policy library but different native payloads and response formats.
Codex/Claude event buckets, Cursor `preToolUse` with `failClosed`, and Antigravity
named top-level definitions are rendered separately. Unknown or malformed
covered calls are denied. These checks are focused on shell and mutation tools;
they are not universal parsers or complete security boundaries.

For unattended Codex, create a fresh HOME, copy only subscription OAuth tokens
and model preferences, disable external apps/plugins/browser/computer tools,
and supply immutable hook configuration. The entire process tree is contained
by a scoped OS sandbox. Remove the copied auth file when the task stops.
Native model rejection, authentication failure or quota exhaustion yields an
attention state. There is no automatic alternative model or API fallback.

Mac Seatbelt file isolation is verified separately from process lifetime. The
macOS kernel rejects `kqueue` descendant `NOTE_TRACK` with errno 45, so local
unattended jobs are refused. Use attended local runs or eligible Linux SSH
workers. Linux admission tests double-fork/new-session cleanup inside the PID
namespace rather than assuming that file isolation proves budget containment.

GPU passthrough is not admitted unattended until device isolation has been
verified. Use the attended, budgeted project dispatcher. No live training or
multi-hour GPU run is a package acceptance test.

Gemini CLI can configure `context.fileName` to include `AGENTS.md` and supports
Agent Skills. Copilot has its own custom-instruction and hook discovery paths.
These are documented compatibility targets, not v1 orchestration adapters.

## Primary references

- [Codex instructions](https://learn.chatgpt.com/docs/agent-configuration/agents-md), [skills](https://learn.chatgpt.com/docs/build-skills), [hooks](https://learn.chatgpt.com/docs/hooks), [headless execution](https://learn.chatgpt.com/docs/non-interactive-mode)
- [Claude memory](https://code.claude.com/docs/en/memory), [skills](https://code.claude.com/docs/en/skills), [hooks](https://code.claude.com/docs/en/hooks), [headless execution](https://code.claude.com/docs/en/headless)
- [Cursor rules](https://cursor.com/docs/rules), [skills](https://cursor.com/docs/skills), [hooks](https://cursor.com/docs/hooks), [headless execution](https://cursor.com/docs/cli/headless)
- [Antigravity rules](https://antigravity.google/docs/rules), [skills](https://antigravity.google/docs/skills), [hooks](https://antigravity.google/docs/hooks), [headless execution](https://antigravity.google/docs/cli/headless)
- [Gemini instructions](https://geminicli.com/docs/cli/gemini-md/), [Copilot customization](https://docs.github.com/en/copilot/reference/customization-cheat-sheet), [Agent Skills specification](https://agentskills.io/specification)

Claude rendering respects `CLAUDE_CONFIG_DIR`. Doctor reports Cursor CLI config
overrides (`CURSOR_CONFIG_DIR`, Linux `XDG_CONFIG_HOME`) separately from the
documented desktop hook location. See [Claude environment variables](https://code.claude.com/docs/en/env-vars)
and [Cursor CLI configuration](https://cursor.com/docs/cli/reference/configuration).
