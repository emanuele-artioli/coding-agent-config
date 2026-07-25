# Global environment notes

Host-wide rules for every project and session on this host. **This file holds
no rules of its own** — it exists to import the two files that do, because
Claude Code reads `CLAUDE.md` and nothing else at the user level.

@/home/itec/emanuele/.agent-rules/AGENTS.md
@/home/itec/emanuele/.agent-rules/harness/claude.md

Edit those files, never this one:

- `.agent-rules/AGENTS.md` — tool-agnostic host rules, shared verbatim with
  every other agent on this host. **The register of things that have gone
  wrong more than once**: if a mistake happens twice, it belongs there,
  phrased as the rule that prevents it rather than the story of the failure.
- `.agent-rules/harness/claude.md` — mechanics that only make sense for Claude
  Code (`Bash`, `Monitor`, `ScheduleWakeup`, `run_in_background`, where
  Claude's own skills/agents/hooks live).

Both live in the `coding-agent-config` repo checked out at
`/home/itec/emanuele`. `.agent-rules/README.md` explains how the same content
reaches Cursor, Antigravity, Copilot and Codex.
