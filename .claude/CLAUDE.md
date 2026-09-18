# Global environment notes

Host-wide rules for every project and session on this host. **This is the
only Claude user-level rules file** — there is no `~/CLAUDE.md`. It holds
no rules of its own; it exists to import the two files that do, because
Claude Code reads `CLAUDE.md` and nothing else at the user level.

@/home/itec/emanuele/.agent-rules/generated/claude-host-core.md
@/home/itec/emanuele/.agent-rules/host.md
@/home/itec/emanuele/.agent-rules/harness/claude.md

Edit those files, never this one:

- `.agent-rules/AGENTS.md` — portable fleet rules (shared with other
  machines). Generated `claude-host-core.md` is that file minus `scope:`
  sections.
- `.agent-rules/host.md` — this GPU/NFS machine only.
- `.agent-rules/harness/claude.md` — Claude mechanics.

Both live in the `coding-agent-config` repo checked out at
`/home/itec/emanuele`. `.agent-rules/README.md` explains how the same content
reaches Cursor, Antigravity, Copilot and Codex.
