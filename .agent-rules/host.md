# This machine only

Lab GPU host overlay. **Do not copy this file into a project.** Other
clones of coding-agent-config skip it. This host's `~/.claude/CLAUDE.md`
and `~/.gemini/GEMINI.md` import it next to the portable `AGENTS.md`.
Cursor has no user-level rules file: add the User Rule in Settings, or
open this repo. Shared portable rules stay in `AGENTS.md`.

## The host

Shared remote Linux **GPU server, no root/sudo/apt**, headless. Home is
`/home/itec/emanuele`. Install extra tooling with conda (Miniconda at
`/usr/local/miniconda3`) into a *separate* env — never a project's pinned
env, since several forked third-party models are version-sensitive and a
stray `pip install` silently breaks them. Headless: save media and plots
to disk, `cv2.imshow()`/`plt.show()` never works.

**`import sqlite3` before `import torch`.** conda's `libicui18n` needs
`CXXABI_1.3.15`, which the system `libstdc++` that torch pins does not
export. It bites at *runtime* when the sqlite3 import is deferred inside
a function, and CI will not reproduce it. Put `import sqlite3` at the top
of the package's `__init__.py` so no submodule can reintroduce it.

## The home is NFS: `open()` costs, and one at a time costs most

Every home here is an export of one server, `data3`. Measured 2026-08-31:
**serial `open()` runs at 2.4–4.3/s, `stat()` on the same files at
~13,000/s, local `/tmp` (ext4) at 15,774/s.** Bulk throughput is fine
(174 MB/s) and retransmissions are 4 in 1.64 billion RPCs, so this is
per-request round-trip latency on the NFSv4 OPEN, not the network and not
server saturation.

- **Parallelism is the fix, and it is dramatic.** The same copy went
  1.7 → 23.3 opens/s at `-P 24`, a 14× speedup; 10,578 files took 6 min
  instead of an hour. Any bulk read/copy of many small files here gets
  `xargs -P 24` or better. What you cannot parallelise — a
  single-threaded indexer, `mypy`, one `cp` — pays the full serial rate.
- **Walking is cheap; opening is not.** `find`, `du`, `git status` and an
  editor's file watcher only `readdir`+`stat`, at thousands per second.
  Indexers, language servers, `grep -r` and `mypy` open every file. So
  `search.exclude` earns its keep and `files.watcherExclude` mostly does
  not.
- **Tree size is a multiplier, not a cause.** ~0.3 s × files opened,
  identical for every project: 1,400 files is 7 min, 17,000 is 1.4 h.
- **Keep regenerable caches on local disk** — `.mypy_cache`,
  `.pytest_cache`, `.ruff_cache`, `__pycache__`, coverage, tool downloads.
  Reading one worktree's 8,311-file mypy cache is ~40 min. Namespace per
  checkout (`MYPY_CACHE_DIR=/tmp/mypy-$(basename "$PWD")`) or worktrees
  collide on module-name keys.
- **A path on local disk must be created on every host you use.** `$HOME`
  is one NFS export; `/var/tmp` is local. `scripts/bootstrap-hostlocal.sh`,
  sourced from **both** `~/.profile` and `~/.bashrc`, creates them.
- **A login shell runs before every agent shell call.** After fixing conda
  hook and nvm, ~0.34–0.98 s. `export PYTHONNOUSERSITE=1`.
- **Keep the editor's own server off NFS.** `.cursor-server` on `/var/tmp`.
- **Batch work into long-lived processes**, and open **one worktree** as
  the editor folder, never the parent.
- **A `du`, `find` or `git status` that seems hung is usually neither.**
  Check `wchan` for `nfs_wait_bit_killable`.

## GitHub CLI (gh)

At `~/emanuele/bin/gh`, on `PATH`, authenticated as `emanuele-artioli`.
**Use it after every push to a repo with CI**: `gh run list --branch <b>
--limit 3`, then `gh run watch <id>`, then **`gh run view <id>
--log-failed`**. `gh run watch` can flake with transient "Bad
credentials"; a following `gh run view` still shows the real status.

## Worktree cleanup

Do not run a project script that `rm -rf`s worktrees. Merged-and-clean
trees: `git-clean-merged-worktrees` on PATH. Ask first if a session may
be paused there.

## Cursor User Rule (this machine)

Cursor does not read `~/.cursor/rules/`. Paste:

    Before anything else, read /home/itec/emanuele/.agent-rules/AGENTS.md,
    /home/itec/emanuele/.agent-rules/host.md, and
    /home/itec/emanuele/.agent-rules/harness/cursor.md, and follow them.
