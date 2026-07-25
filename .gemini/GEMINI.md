# Antigravity — global agent constraints

This file holds no rules of its own. It imports the tool-agnostic host rules
and the Antigravity-specific ones, so that both stay single-sourced in the
`coding-agent-config` repo at `/home/itec/emanuele`.

@/home/itec/emanuele/.agent-rules/AGENTS.md
@/home/itec/emanuele/.agent-rules/harness/antigravity.md

Edit `.agent-rules/AGENTS.md` for anything that should apply to every agent on
this host, and `.agent-rules/harness/antigravity.md` for Antigravity's own
mechanics or a deliberate override of a host-wide rule (Antigravity resolves
conflicts in `GEMINI.md`'s favour over `AGENTS.md`).

`~/.gemini/AGENTS.md` is a symlink to the same host rules file, for the native
`AGENTS.md` support added in v1.20.3 — it is the same content by construction,
not a second copy to maintain.
