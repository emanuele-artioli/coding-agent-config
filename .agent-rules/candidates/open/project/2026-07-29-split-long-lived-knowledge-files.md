---
id: 2026-07-29-split-long-lived-knowledge-files
created: 2026-07-29
source_platform: claude
source_project: /home/itec/emanuele/presley
axis: project
status: open
summary: An append-only research log becomes a per-session token tax; split into an index carrying entry TITLES plus per-section bodies, and drain landed entries.
suggested_action: offer the pattern to any project with a long-lived append-only knowledge file (RESEARCH_LOG, DECISIONS, TECHNICAL_REPORT); consider a line-count ceiling convention in the shared rules
verify_platforms: []
---

## The problem

PRESLEY's `RESEARCH_LOG.md` reached **1008 lines / 67 KB (~17k tokens)**. Every
session that *wrote* to it paid the full read cost, because editing requires
having read the file first and a plain read pulls the whole thing. The cost
repeats after every context compaction. It had also grown past the point where
it could be read in a single call at all, so even reading it needed pagination.

This is a general failure mode for any append-only knowledge file that agents
are told to consult. The file gets *more* expensive exactly as it gets more
useful, and nothing in the normal workflow ever shrinks it.

## What was done

1. **Split into an index + per-section bodies.** `RESEARCH_LOG.md` became a
   157-line index; bodies moved to `research-log/{hard-rules,standing-results,
   open-questions,bugs,dead-ends,operational}.md`.
2. **The index carries every entry TITLE, not just section names.** This is the
   load-bearing detail. "Has X been tried?" / "is there a rule about Y?" is
   answerable from the index alone; only a hit opens a body file. An index of
   section names would not have replaced the full read.
3. **Verified byte-exact reassemblable** — `cat`-ing the parts under the header
   reproduced the original exactly. Done as a content-only commit with the
   index added separately, so the move diff reads as a pure relocation.
4. **Pointers were updated to name the specific file** (`research-log/hard-rules.md`,
   not `RESEARCH_LOG.md`). Without this the split saves nothing: agents follow
   the pointer they are given.
5. **A line-count ceiling (300) plus a drain rule.** The "standing results"
   section was a queue meant to shrink as entries landed in the paper and never
   had; ~20 entries were duplicating `CLAIM(id)` markers that already carried
   *more* detail (hashes, operating point, caveats) and are never deleted.

## Results

- Typical session cost: **~17k tokens → ~4.5–7k** (index ~2.3k + one body file).
  Not the 10× that the raw line-count reduction suggests — the index is not free.
- Drain took `standing-results.md` from 298 → 225 lines.

## Caveats worth carrying

- **The saving comes from the pointers, not the split.** Budget the pointer
  sweep as part of the work (here: 11 files across two repos, plus regenerated
  agent-rule files).
- **Byte-exactness is a check on the move, not a standing invariant.** Say so in
  the index, or a later reader will treat a drifted file as corruption.
- **Draining requires verification, not just deletion.** Each removed entry was
  checked to have a live `CLAIM` in the paper carrying at least as much, and one
  "do not cite" warning was confirmed present in the manuscript before its log
  copy was dropped. A drain done by eye would silently lose retraction
  provenance.
- Keep entries explicitly marked as a wording/constraint source of truth even
  when the headline has landed.

Related: this is the same mechanism as `[[trust-data-over-docs]]` in the sense
that the file's *stated* purpose (be the secondary store) stayed right while its
*shape* quietly became the problem.
