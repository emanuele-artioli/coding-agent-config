# 2026-09-20 — Antigravity native roles and global discovery

Live audit 2026-09-20:
- Antigravity scans `~/.gemini/config/agents/*.md` for global subagents at startup.
- Roles require `subagent: true` in YAML frontmatter to appear under available subagents.
- Symlinks to shared `.agent-rules/agents/*.agent.md` carry Claude frontmatter (`model: opus`)
  which triggers family denials or fails discovery.
- `install.py` generates native markdown copies under `~/.gemini/config/agents/` with
  `model: flash`, `effort`, `reasoningEffort`, and `subagent: true`.
- Native Stop payloads do not carry closeout boundaries; ordinary Stop is a no-op in
  the closeout adapter (`harness/antigravity/stop.py`), while explicit closeout receipts
  are written only on genuine closeout commands.
