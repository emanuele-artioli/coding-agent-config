---
id: 2026-08-31-clean-up-a-wave-when-it-merges
created: 2026-08-31
source_platform: claude
source_project: /home/itec/emanuele/pointstream
axis: project
status: applied
summary: Parallel-wave worktrees left behind after their branches merge become both a stale-edit hazard and the bulk of the NFS walk
suggested_action: add a cleanup step to the AGENTS.md parallel-agent-waves section
verify_platforms: []
---

The host rules describe how to *start* a wave — split into workstreams, one
worktree and branch each, grouped into dependency-ordered waves. They say
nothing about ending one, and the omission has a measurable cost.

Observed on PointStream, 2026-08-31, after wave 8: **all six wave-8 branches
were fully merged (0 commits ahead of main) and all six worktrees were still
present**, pinned to commits three merges behind. Two distinct harms:

**1. A stale worktree is a silent-revert hazard.** Wave 8's stream D owned
`src/runner/stages.py`. A later session changed `make_background` there to bind
its background model once per run rather than once per chunk — load-bearing,
because a stateful cross-scene stream that is rebound per chunk starts empty
every chunk and every scene pays a full keyframe, so the amortisation is
configured, reported in the ledger, and absent, with nothing about the output
looking wrong. If the wave-8 session resumes in its stale worktree and
re-applies its own version of that function, it reverts that silently. The
defence used was a test that greps the stage body, but the *cause* was a
worktree that outlived its branch.

**2. It is most of the NFS walk.** Seven leftover worktrees carried ~8,900
inodes each, ~85% of it duplicated tool cache — see the platform-axis candidate
`2026-08-31-caches-on-nfs-dominate-the-walked-tree`.

**Suggested rule:** a wave is not finished when its PRs merge; it is finished
when its worktrees are gone. Removal follows the existing safeguards — read the
branch first (`git log main..<branch>`), tag anything unmerged, never
`--force` away a worktree with uncommitted changes — and **ask the user before
removing**, because a session may be paused in one, which is exactly the state
found here.

---

## Resolution — 2026-08-31

**Applied on the first harm only. The second harm is disproved** — which is why
this candidate was held until the NFS investigation finished.

Harm 1, the stale-worktree silent revert, stands entirely on its own and is the
whole basis of the rule now in `AGENTS.md` under the parallel-agent-waves
section. A worktree that outlives its branch lets a resumed session re-apply its
version of a file a later session already changed, with nothing about the output
looking wrong.

Harm 2 — "it is most of the NFS walk" — does not survive measurement
(`FINDINGS-nfs-editor-slowness.md`). Walking is cheap here (~13,000 stats/s);
only `open()` is slow. And no PointStream worktree has ever been opened as an
editor folder, so leftover worktrees were never in any editor's scope. Removing
them is tidiness, not a performance fix, and the rule is worded that way.

One correction folded into the applied rule that the candidate did not have:
**compare against `origin/main`, not a local `main`.** Local `main` in the
PointStream checkout was 52 commits behind origin (last fetch 08-29), which made
every one of the six merged wave-8 branches read as 32–35 commits *ahead*. A
cleanup driven by the local comparison would have concluded that nothing was
safe to remove; one driven by a stale local `main` in the other direction could
have deleted unmerged work.
