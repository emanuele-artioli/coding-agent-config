# Prompt — fix the host's slowness, then close out the knowledge queue

Run from `/home/itec/emanuele` (the coding-agent-config checkout).

**The two halves are in this order for a reason, and the order is not optional:
the investigation produces evidence that two queued candidates are about.**
Evaluating them first would mean ruling on rules whose evidence is about to be
confirmed or overturned.

---

You have two jobs this session. Both must land. If the first runs long, **stop
it and do the second anyway** — the queue has been unevaluated since
2026-07-29 and that is the failure this session exists to end.

## Part 1 — why can no editor open PointStream on this host?

**The detailed brief, with every measurement already taken, is
`/home/itec/emanuele/pointstream/plans/prompts/nfs-editor-slowness.md`. Read it
first; do not re-derive its numbers.** In short: across eight PointStream
worktrees there are 79,738 inodes, ~85% of which is `.mypy_cache` duplicated
per worktree, against ~750 inodes of actual tracked source; the home mount
serves ~6 file opens/second; `/tmp` is local ext4 while home is `nfs4`.

**Treat the inode count as a hypothesis, not a diagnosis.** The brief names the
two checks that would confirm or kill it — what folder the editor actually opens
(one worktree, or the parent, which also contains ~565,000 data files), and why
VS Code reportedly works on TIGAS on this same host. A wrong hypothesis closed
out is a result, and saying so is worth more than a fix that treats the wrong
thing.

**Box it.** If you have not established the cause after a reasonable effort,
write down what you ruled out and move to Part 2. Do not let this consume the
session.

**Two things to check with the user before doing:** removing merged worktrees
(a session may be paused in one — as of 2026-08-31 all six wave-8 branches were
0 commits ahead of main), and anything that touches another user's processes. A
co-tenant's VS Code server had a recursive `grep` running 11 h 52 m on this
mount; it is not yours to kill.

## Part 2 — evaluate the whole candidate queue

Use the **`evaluate-candidates`** skill. There are **11 open candidates** — 6
project, 5 platform — the oldest from **2026-07-29**, plus three
`pending-verification` checklists and a stale `candidates/HANDOFF.md` from
2026-07-27 that should be read and then retired if it is spent.

Apply, discard or defer each one. Respect platform write-ownership: live config
claims about a platform belong to that platform, and a cross-write becomes a
`needs_verification` ticket rather than an edit.

**Two of the open candidates are Part 1's subject**, so do them last and let the
investigation decide them:

- `open/platform/2026-08-31-caches-on-nfs-dominate-the-walked-tree.md` — argues
  regenerable caches belong on local disk, not an NFS checkout. If Part 1 shows
  the cache was not the cause, this candidate is weaker than it reads and should
  say so rather than being applied on its own authority.
- `open/project/2026-08-31-clean-up-a-wave-when-it-merges.md` — argues a wave is
  finished when its worktrees are gone, not when its PRs merge. Part 1's
  worktree findings bear on this directly.

## A third item, if there is room

A PointStream session on 2026-08-31 proposed three additions to
`.agent-rules/AGENTS.md` and deliberately did **not** make them, because that
file governs every session on this host. They are the two candidates above, plus
one on **PR granularity**: one PR per independently revertible change — over-
splitting burns the Copilot review budget (measured: it stops analysing PRs
after a few days of heavy splitting), while under-splitting keeps `main` stale
and leaves parallel sessions rebasing onto old code. Decide these with the user
rather than unilaterally.

## Done when

The editor symptom is attributed to a named cause with a measurement behind it
(or explicitly not attributed, with what was ruled out); `candidates/open/` is
empty or every remaining file has a stated reason for staying; and any
`AGENTS.md` change was agreed rather than assumed.
