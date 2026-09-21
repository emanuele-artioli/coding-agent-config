# This machine only

Lab GPU host overlay. **Do not copy this file into a project.** Other
clones of coding-agent-config skip it. This host's `~/.claude/CLAUDE.md`
and `~/.gemini/GEMINI.md` import it next to the portable `AGENTS.md`.
Shared portable rules stay in `AGENTS.md`.

## The host

Shared remote Linux **GPU server, no root/sudo/apt**, headless. Home is
`/home/itec/emanuele`. Install extra tooling with conda (Miniconda at
`/usr/local/miniconda3`) into a *separate* env — never a project's pinned
env. Headless: save media and plots to disk; `cv2.imshow()`/`plt.show()`
never work.

**`import sqlite3` before `import torch`.** conda's libstdc++ bites at
runtime otherwise. Put `import sqlite3` at the top of the package's
`__init__.py`.

**Ensure a free GPU before experiments.** Check GPU availability on the
machine (e.g. `nvidia-smi`) before running an experiment. If no GPU is
free, stop and report this immediately rather than launching onto an
occupied GPU.

## NFS

`open()` is expensive on this export. Keep editor servers on `/var/tmp`.
Evidence: `archive/FINDINGS-nfs-editor-slowness.md`.

## GitHub CLI (gh)

At `~/emanuele/bin/gh`, on PATH, authenticated as `emanuele-artioli`.

## Worktree cleanup

Merged-and-clean trees: `git-clean-merged-worktrees` on PATH. Ask first
if a session may be paused there.
