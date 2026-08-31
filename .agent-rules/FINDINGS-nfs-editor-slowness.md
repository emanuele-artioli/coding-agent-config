# Findings — why no editor can open PointStream on this host

Measured 2026-08-31, `gpu5`, by the session driven from
`.agent-rules/PROMPT-host-slowness-and-queue.md`. Supersedes the hypothesis in
`pointstream-w8-e/plans/prompts/nfs-editor-slowness.md`.

## Verdict

**The inode hypothesis is wrong as an explanation, and right as a multiplier.**

The cause is not PointStream's layout. It is the NFS server `data3`
(192.168.33.10), which serves **`open()` at 2.4–4.3 calls per second** while
serving `stat()` at ~13,000/s on the *same files*. Every home on this host is
an export of that one server, so the cost is identical for every project.

## The measurements

Single-process Perl, `open()` + 1-byte read, 100–2000 files each.

| tree | inodes | opens/s |
|---|---:|---:|
| `TIGAS` (the project that "works") | 1,380 | **2.3** |
| `pointstream` (main checkout) | 17,033 | **2.4** |
| `pointstream-w8-a` (a worktree) | 8,894 | **2.7** |
| `/opt/local` — `data3:/x/opt`, a *different export* | — | **3.8** |
| `/tmp` — local ext4 | — | **15,774** |

`open()` against `stat()`, on the identical 100 files of a cold tree
(`web-splat`):

| operation | rate |
|---|---:|
| `readdir`+`stat` walk of 6,358 inodes | 2,957 inodes/s |
| `stat()` × 100 | 13,477/s |
| **`open()` × 100** | **3.5/s** |

Re-opening the same 100 files: 4.3/s, then 15.9/s. Caching helps a little and
never gets within three orders of magnitude of local disk.

`nfsstat -c`: **4 retransmissions in 1.64 billion RPCs**. The network is fine.
This is server-side latency on the NFSv4 `OPEN` operation — a stateful,
serialised call — not packet loss and not throughput.

## What this rules out

- **Inode count as the cause.** TIGAS is 12× smaller than `pointstream` and
  sits on the same 2.3 opens/s. It is not on a faster path; it is on a shorter
  one.
- **`files.watcherExclude` as the fix.** A file watcher does `readdir`+`stat`,
  which is ~3,850× faster than `open()` here. Excluding directories from the
  watcher buys almost nothing.
- **PointStream specifically.** `/opt/local`, a different export, is equally
  slow.

## What it explains

Inode count is the multiplier on a fixed ~0.3 s per file open. Anything that
opens every file in a tree costs:

| what is opened | files | at 3.5 opens/s |
|---|---:|---:|
| `TIGAS` | 1,380 | ~7 min |
| `pointstream` | 17,033 | ~1.4 h |
| one worktree's `.mypy_cache` | 8,311 | ~40 min |
| `.cursor-server` (the editor's own install) | **58,495** | ~4.6 h |
| `.vscode-server` | 28,615 | ~2.3 h |
| `/home/itec/emanuele` as the opened folder | millions | unbounded |

Three consequences follow, in order of how much they explain the symptom:

1. **The editor server's own installation is the biggest single tree involved.**
   `.cursor-server` is 58,495 files — 3.4× the whole PointStream checkout — on
   the stalled mount. A cold connect has to open a large share of them before
   any project is touched. This is a *connection* failure, not an indexing one,
   and it is independent of which project you open.
2. **Indexers, not watchers, pay the cost.** Cursor's `anysphere.cursor-retrieval`
   embedding index, Pylance, ripgrep search and mypy all `open()` every file.
   That is the 1.4 h for `pointstream`, and why TIGAS at ~7 min feels merely
   slow rather than broken.
3. **mypy's 15–25 min local run vs 3m30s on CI is fully accounted for.** Reading
   the 8,311-file `.mypy_cache` at 3.5 opens/s is ~40 minutes on its own.

## Which folder is actually opened

Recovered by matching `workspaceStorage` directory names against
md5(`vscode-remote://ssh-remote%2Bgpu5<path>`):

| when | editor | folder opened |
|---|---|---|
| 2026-08-31 09:31 (live) | Cursor | `TIGAS` |
| 2026-08-29, 08-27 ×2 | VS Code | `pointstream` |
| 2026-08-21, 08-20, 08-09 | Cursor | **`/home/itec/emanuele`** — the parent |
| 2026-07-31, 07-30 | Cursor | `presley` |
| 2026-08-05 | Cursor | `TIGAS` |

**No PointStream worktree has ever been opened as a folder.** So the 79,738-inode
"across eight worktrees" total in the brief was never what one editor walked.
The parent *was* opened three times, and that case is far worse than 79,738 —
it contains `.conda` (3,089,369 inodes), `.claude` (98,021), `pointstream-data`,
and every worktree.

Also found: **neither `.cursor-server/data/Machine/settings.json` nor
`User/settings.json` exists** — there are no remote-side excludes configured at
all.

## Contention, and what is not ours

`ayman`'s recursive `grep`, spawned by their editor, has now been in `D` state
(`nfs_wait_bit_killable`) for **13 h 01 m** against the same server — the same
process the brief recorded at 11 h 52 m the day before. The kernel's NFS state
manager for 192.168.33.10 was also in `D` during these measurements. This is
co-tenant load on a shared server and is not ours to kill. It means every
number above is an upper bound on how bad things are, not a clean measurement
of the server at rest — but the figure has now been reproduced on two separate
days (`~6/s` on 08-29, `2.4–4.3/s` on 08-31), so it is the normal operating
condition, not an episode.

## Fixes, re-ranked by the evidence

1. **Move the editor server off NFS.** `.cursor-server` / `.vscode-server` are
   the largest trees in the connect path and are pure cache. Relocating them to
   local disk (a symlink to `/tmp`, or `remote.SSH.serverInstallPath`) addresses
   the connection symptom directly. Nothing else on this list does.
2. **Move `.mypy_cache` off NFS**, one directory per worktree —
   `MYPY_CACHE_DIR=/tmp/mypy-$(basename "$PWD")`. Not a `cache_dir` in
   `pyproject.toml`: that gives every worktree the same path and they will fight
   over entries keyed by identical module names. Worth ~40 min per mypy run.
3. **Open one worktree, never the parent.** Costs nothing and removes the only
   unbounded case.
4. **`search.exclude`** (not `files.watcherExclude`) for caches and data.
5. **Remove merged worktrees** — real but modest, and it does not touch the
   connection symptom. See the branch state below.

## Worktree state, 2026-08-31

Local `main` was **52 commits behind `origin/main`** (last fetch 08-29), which
makes every wave-8 branch look 32–35 commits *ahead* until you compare against
the remote. Against `origin/main`:

| worktree | branch | ahead of origin/main | uncommitted |
|---|---|---:|---:|
| `pointstream-w6-b` | `wave8/coordination` | 0 | 0 |
| `pointstream-w8-a` | `wave8/plate-codec-sweep` | 0 | 0 |
| `pointstream-w8-b` | `wave8/intra-sidecar` | 0 | 0 |
| `pointstream-w8-c` | `wave8/low-rate` | 0 | 0 |
| `pointstream-w8-d` | `wave8/panorama` | 0 | 0 |
| `pointstream-w8-fix` | `wave8/weights-path` | 0 | 0 |
| `pointstream-w8-e` | `chore/mypy-experiments-gate` | **3** | 0 |
| `pointstream-w5-b` | — | — | **15 files** |

Six are merged and clean. **`pointstream-w8-e` holds 3 unmerged commits** — and
the brief this session was asked to read lives only there, invisible from the
main checkout. **`pointstream-w5-b` has 15 uncommitted files.** Neither may be
removed.

There is also a ninth worktree nested *inside* the main checkout at
`pointstream/.claude/worktrees/competent-rubin-96925a`, so opening `pointstream`
as a folder walks a worktree too.
