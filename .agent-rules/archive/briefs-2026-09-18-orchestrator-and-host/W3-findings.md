# W3 findings — multi-harness git (2026-09-18)

Inventory only; nothing deleted. Host CLI dry-run removed nothing.

## On disk (two snapshots in one session)

**coding-agent-config** (`/home/itec/emanuele`): one worktree, branch
`2026-09-18-orchestrator-and-host`, dirty (this wave). No child worktrees.
`~/.claude/worktrees/` empty.

**PointStream** (observed by W3, then gone without W3 deleting anything):

- First look: four trees — stale merged primary, dirty cursor-ladder
  worktree, merged-clean `e06`, plus a broken `pointstream-main` record —
  and unmerged local branches.
- Minutes later: extra trees gone; primary HEAD moved between
  `antigravity/starved-ladder-and-webp-anchors` and `main`.

That is **two live sessions on one checkout**, which is the failure mode
the merge-cleanup CLI does not cover (dirty tree, checkout fights,
unmerged leftovers). A later parent snapshot saw only `pointstream` on
`main` — do not treat a quiet `git worktree list` as “never happens.”

## INFRA-ACT-01 vs host CLI

- PointStream `scripts/cleanup_merged_worktrees.sh` stays **banned**
  (`rm -rf` fallback). `INFRA-ACT-01` is still open on that script.
- Host `git-clean-merged-worktrees` (`guardlib/worktree_cleanup.py`)
  refuses dirty, unmerged, and the primary checkout. Safe for
  **merged + clean** linked worktrees only. Different tool; do not
  rename them into each other (W5 note: naming collision).

## Practice (applied)

- Host `AGENTS.md`: one live session → one worktree → one branch.
- `end-of-session`: list worktrees (dirty / merged / unmerged); list
  unmerged branches vs `origin/main`; if this tree is dirty, do not
  `git checkout` another branch — add a worktree. Do not auto-delete.
- PointStream: keep the project-script ban; merged-clean cleanup is the
  host CLI.

## Note for W5

Do not run `pointstream/scripts/cleanup_merged_worktrees.sh`. Host
`git-clean-merged-worktrees` only, and only on clean merged trees.
The `.sh` name and the host CLI are easy to confuse — keep both names
in the project `AGENTS.md` line.
