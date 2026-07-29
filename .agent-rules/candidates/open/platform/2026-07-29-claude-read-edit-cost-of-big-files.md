---
id: 2026-07-29-claude-read-edit-cost-of-big-files
created: 2026-07-29
source_platform: claude
source_project: /home/itec/emanuele/presley
axis: platform
status: open
summary: In Claude Code, editing a file requires having read it, and a plain Read pulls up to 2000 lines — so a large doc costs its full token weight on every write, and past ~25k tokens cannot be read in one call at all.
suggested_action: check whether other platforms (cursor, antigravity, codex, copilot) have the same read-before-edit coupling and per-call caps; if they do, the shared rules can carry a file-size guidance line instead of a Claude-only note
verify_platforms: [cursor, antigravity, codex, copilot]
---

## The mechanic (observed on Claude Code, 2026-07-29)

Three harness behaviours compose into a cost that is invisible until a file
gets big:

1. **`Edit` refuses unless the file was read in this conversation.** So every
   write is preceded by a read.
2. **`Read` with no `offset`/`limit` reads up to 2000 lines** — i.e. the whole
   file for anything realistic. This is the default an agent reaches for.
3. **There is a per-call token cap (~25k) on the result.** Past that, `Read`
   returns a truncated page and tells you to paginate. A 1008-line / 67 KB
   markdown file hit this.

Consequence: a 67 KB doc cost ~17k tokens **per session that touched it**, and
again after each compaction. Appending one line to the end paid for the whole
file.

## The escape hatch, and why nobody uses it

A *partial* read (`offset`/`limit`) satisfies the read-before-edit precondition
fine. So the cost is avoidable in principle. In practice nobody does it, because
a monolithic file gives no way to know which offset is the right one — there is
no index. The fix is therefore structural (index + section files), not a
discipline note telling agents to paginate.

## Why this belongs on the platform axis

The *project*-axis lesson (split long-lived knowledge files) is filed
separately and is tool-agnostic. What is platform-specific is **why the cost
exists at all**: the read-before-edit coupling plus the per-call cap. Another
agent with different tool semantics — one that can append without reading, or
that chunks automatically — would not have the same pressure, and the shared
rules should not assert a Claude-shaped cost as universal.

**Unverified for other platforms.** Someone working in cursor / antigravity /
codex / copilot should check whether their edit tools require a prior full read
and whether they cap per-call reads. If the answer is yes across the board, this
can be promoted into `AGENTS.md` as a general "keep agent-read files under N
lines" rule; if it is Claude-only, it stays in `harness/claude.md`.
