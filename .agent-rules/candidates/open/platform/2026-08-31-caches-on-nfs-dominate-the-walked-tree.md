---
id: 2026-08-31-caches-on-nfs-dominate-the-walked-tree
created: 2026-08-31
source_platform: claude
source_project: /home/itec/emanuele/pointstream
axis: platform
status: open
summary: Tool caches, not source, are ~85% of what an editor walks per worktree on this NFS home — and they belong on local disk
suggested_action: lift into the AGENTS.md NFS section; applies to every project and every agent on this host
verify_platforms: []
---

Measured on PointStream, 2026-08-31, across eight git worktrees:

| location | inodes | of which `.mypy_cache` |
|---|---:|---:|
| main checkout | 17,028 | 9,444 |
| seven sibling worktrees | ~8,900 each | ~8,300 each |
| **total** | **79,738** | **~67,600 (85%)** |

Tracked source is about **750 inodes per checkout**. So the thing that makes a
project unwalkable here is not its code and not (since the data move) its
datasets — it is **per-worktree tool caches**, duplicated once per worktree, on
a mount serving ~6 file opens per second. A full walk of 79,738 inodes is
roughly 3.7 hours.

**`/tmp` on this host is local ext4** (`/dev/mapper/ubuntu--vg-ubuntu--lv`)
while `/home/itec/emanuele` is `nfs4`. Pointing cache directories there is
therefore two wins at once: the cache leaves the walked tree, and it stops
paying NFS metadata latency. Corroborating datapoint: a full local `mypy` run
took **15-25 minutes** against **3m30s for the same check on CI**, and a run
left going for 24 minutes had still not finished.

**The general rule this suggests:** on this host, any regenerable cache
(`.mypy_cache`, `.pytest_cache`, `.ruff_cache`, `__pycache__`, coverage data,
tool download caches) should live on local disk, not in an NFS checkout.
`.gitignore` does not help — it stops git tracking them, not a tool walking
them, which is the same trap the existing AGENTS.md note about editors and
`assets/` already describes.

**One trap when applying it:** several worktrees must not share a single mypy
cache directory, since entries are keyed by module name and would collide
across trees. Namespace per checkout.

**Also observed, and relevant to any timing measured here:** a co-tenant's
VS Code server (`ayman`) had a `find` plus recursive `grep -RIn` running for
11 h 52 m on the same mount. Contention on this host is not always yours, and a
measurement taken during it is not a measurement of your project.
