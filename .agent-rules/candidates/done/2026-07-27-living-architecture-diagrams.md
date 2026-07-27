---
id: 2026-07-27-living-architecture-diagrams
created: 2026-07-27
source_platform: cursor
source_project: .
axis: platform
status: applied
summary: Keep README mermaid diagrams generated from filesystem + hook/install configs so they do not drift
suggested_action: Add scripts/render_architecture.py writing marked regions in .agent-rules/README.md; gate with --check
verify_platforms: []
evaluated: 2026-07-27
---

# Living architecture diagrams (applied)

## Evaluation / apply (2026-07-27)

**Applied.** Decision on the open gate question: freshness is
`python3 .agent-rules/scripts/render_architecture.py --check` (standalone),
not folded into `install.py --check`.

## What landed

- `scripts/render_architecture.py` regenerates
  `<!-- arch:tree:* -->` (under Layout) and `<!-- arch:flows:* -->`
  (under Design principles) in `.agent-rules/README.md` from the filesystem.
- Agents should invoke the script after structural SoT edits; do not freehand
  those marked regions.
