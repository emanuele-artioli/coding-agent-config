# Knowledge candidates queue

Central queue for knowledge surfaced from any project × platform cell.
Evaluation happens asynchronously in a coding-agent-config session
(`evaluate-candidates` skill). **Write a candidate only when there is
something to surface** — an empty `open/` tree means nothing is pending.

## Layout

```
candidates/
  open/project/     # axis: project — other projects may want this
  open/platform/    # axis: platform — other platforms may need this
  done/             # applied or discarded (audit trail)
  pending-verification/   # per-platform checklists
```

One pipeline for both axes. Browse dirs separate scanning only; status
machine and skills are shared. Branch on `axis` at apply time.

## Candidate file format

YAML frontmatter + body. Filename: `YYYY-MM-DD-<short-slug>.md`.

```yaml
---
id: 2026-07-27-example
created: 2026-07-27
source_platform: cursor   # cursor | claude | antigravity | copilot | codex
source_project: /home/itec/emanuele/pointstream   # or "." for this repo
axis: project             # project | platform (must match open/<axis>/)
status: open              # open | applied | discarded | needs_verification
summary: One-line description
suggested_action: lift to foundation skills / copy to projects X / …
verify_platforms: []      # e.g. [claude, antigravity] when live configs need checks
---

The knowledge itself — enough that evaluation does not need the chat.
```

## Status machine

1. **open** — waiting in `open/<axis>/`
2. **applied** / **discarded** — moved to `done/` with final status in frontmatter
3. **needs_verification** — product touches another platform’s live config; also
   listed under `pending-verification/<platform>.md` until that platform closes it

## Who writes / who evaluates

- Any session may write into `open/` by absolute path
  (`/home/itec/emanuele/.agent-rules/candidates/...`).
- `end-of-session` considers both axes and writes only when warranted.
- `evaluate-candidates` (coding-agent-config) applies, discards, or defers.
- Platform write-ownership: shared SoT edits are fine; live platform configs
  and verification claims belong to that platform.
