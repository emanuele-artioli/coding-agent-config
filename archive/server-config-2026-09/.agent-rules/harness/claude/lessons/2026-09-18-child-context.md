# 2026-09-18 — child context and spawn delay

A new agent file is not spawnable at once: on 2026-09-18 `implementer`
appeared in the `Agent` tool about ten minutes after `install.py` linked
it, without a restart.

Of a ~40k-token floor measured on the 2026-09-18 children, ~17k was tool
schemas the child never used and ~6k was the imported rules. Junior and
escalation files restrict `tools:`, set `omitClaudeMd: true`, and carry
`agents/JUNIOR-FACTS.md` instead.

A 1008-line / 67 KB markdown file cost ~17k tokens per session that
touched it (`Edit` requires a prior `Read`; a plain Read pulls up to
2000 lines). Past ~25k tokens `Read` truncates.
