---
id: 2026-07-27-living-architecture-diagrams
created: 2026-07-27
source_platform: cursor
source_project: .
axis: platform
status: open
summary: Keep README mermaid diagrams generated from filesystem + hook/install configs so they do not drift
suggested_action: Add scripts/render_architecture.py writing marked regions in .agent-rules/README.md; gate with --check
verify_platforms: []
---

# Living architecture diagrams (deferred implementation)

## Problem

Hand-updated mermaid graphs in the README will drift the same way prose rules
do. Structure and skill/hook interactions should stay mapped automatically.

## Proposed shape

1. **`scripts/render_architecture.py`** walks `.agent-rules/` and emits mermaid
   into fenced regions in `.agent-rules/README.md` marked e.g.
   `<!-- arch:tree:start -->` … `<!-- arch:tree:end -->` and
   `<!-- arch:flows:start -->` … `end`.
2. **Diagram kinds:**
   - **Tree:** skills / agents / workflows / harness / scripts / candidates.
   - **Flows:** SessionStart → reminders; end-of-session → candidates →
     evaluate; hooks → guardlib; install symlink farm (from `install.py`
     `plan()` + parsed hook command paths).
3. **Freshness gate:** `install.py --check` or the renderer’s `--check` fails
   if committed README regions ≠ regenerated output.
4. **Optional interaction edges** that cannot be inferred live in a tiny
   manifest YAML; keep that list short.
5. **v1 scope:** host `.agent-rules/README.md` only; projects opt in later.

Agents may invoke the tool after structural edits; they should not freehand
the SoT diagram.
