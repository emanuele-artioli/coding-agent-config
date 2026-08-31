# Host-wide agent rules — single source of truth

Edit **only this file** for anything that applies to every agent on this host.
It stays strictly tool-agnostic — tool names, invocation syntax and per-agent
config paths belong in `harness/<agent>.md`, so every consumer can take these
bytes as-is. It is also **the register of things that have gone wrong more
than once**: if a mistake happens twice it belongs here, phrased as the rule
that prevents it rather than the story of the failure.

Nothing copies this file. Local agents import it (`~/.claude/CLAUDE.md`,
a project's `@` import / Read pointer, Cursor `alwaysApply` rule) or
symlink it (`~/AGENTS.md`). Do not inline it into project files — that
needs a sync script and becomes a second source of truth. Cloud agents
on other machines will not see it; that is accepted for work on this
host. Rollout TODO:
`.agent-rules/candidates/open/platform/2026-08-23-pointer-not-inline-host-rules.md`.
Routing table in `README.md`.

Keep it short. Every line here is loaded by every agent in every session, on
every project — prose costs adherence, so compress rather than accumulate.

## Write in plain words

Use simple, everyday language. Short sentences. Pick the common word over the
fancy one, and cut words that add nothing. Keep the technical terms that carry
real meaning (QP, worktree, checkpoint) — drop the decorative ones. This
applies to chat replies, commit messages, and comments; paper text keeps its
own academic register.

## The host

Shared remote Linux **GPU server, no root/sudo/apt**, headless. Home is
`/home/itec/emanuele`. Install extra tooling with conda (Miniconda at
`/usr/local/miniconda3`) into a *separate* env — never into a project's pinned
env: several forked third-party models are version-sensitive and a stray
`pip install` silently breaks them. Headless means save media and plots to
disk; `cv2.imshow()`/`plt.show()` never works here.

**`import sqlite3` before `import torch`.** conda's `libicui18n` needs
`CXXABI_1.3.15`, which the system `libstdc++` that torch pins does not export,
so torch-first breaks `sqlite3`. It bites at *runtime* when the sqlite3 import
is deferred inside a function, and CI will not reproduce it. Put `import
sqlite3` at the top of the package's `__init__.py` so no submodule can
reintroduce it.

## The home directory is NFS, and `open()` is what costs

Every home here is an export of one server, `data3`. Measured 2026-08-31:
**`open()` runs at 2.4–4.3 calls/second, while `stat()` on the same files runs
at ~13,000/s and local `/tmp` (ext4) does 15,774 opens/s.** Bulk throughput is
fine (174 MB/s). Retransmissions are 4 in 1.64 billion RPCs, so this is
server-side latency on the NFSv4 OPEN, not the network, and page cache barely
helps.

- **The cost is per file opened, and identical for every project.** Tree size is
  the multiplier, not the cause: ~0.3 s × however many files something opens.
  1,400 files is 7 minutes; 17,000 is 1.4 hours. A project that "works" here is
  not on a faster path, only a shorter one.
- **Walking is cheap; opening is not.** `find`, `du`, `git status` and an
  editor's file watcher do `readdir`+`stat` and run at thousands per second.
  Indexers, language servers, `grep -r` and `mypy` open every file and do not.
  So `search.exclude` earns its keep and `files.watcherExclude` mostly does not.
- **Batch work into long-lived processes.** A conda env here is tens of
  thousands of files, so every fresh Python process pays a two-to-three minute
  import tax. Ten short scripts cost half an hour of nothing.
- **Keep regenerable caches on local disk**, not in an NFS checkout:
  `.mypy_cache`, `.pytest_cache`, `.ruff_cache`, `__pycache__`, coverage, tool
  downloads. Reading one worktree's 8,311-file mypy cache is ~40 min, which is
  the whole gap between a 15–25 min local `mypy` run and 3m30s on CI.
  `.gitignore` does not help — it stops git tracking them, not a tool reading
  them. Namespace per checkout (`MYPY_CACHE_DIR=/tmp/mypy-$(basename "$PWD")`):
  worktrees sharing one cache dir collide on module-name keys.
- **The editor's own server is usually the biggest tree in the path.**
  `.cursor-server` measured 58,495 files — 3.4× a whole project checkout — so a
  cold connect spends hours before touching any project. Keep it off NFS
  (`/var/tmp` here is local and not age-cleaned; `/local/users/<you>` if an
  admin grants one). Same reasoning for a conda env, which is worth copying only
  for a run of many short processes — measure before paying it.
- **Keep editors out of data directories**, and open **one worktree** as the
  folder rather than the parent that contains all of them: the parent pulls in
  every sibling worktree plus `.conda` (3M inodes) and every dataset.
- **A `du`, `find` or `git status` that seems hung is usually neither.** Check
  `wchan` for `nfs_wait_bit_killable` before debugging the tool. Contention is
  often not yours — a co-tenant's editor `grep` has sat in `D` state for 13
  hours on this mount, and a measurement taken during that is not a measurement
  of your project.

## Python dependency management

Manage packages through `pyproject.toml`, not ad-hoc `pip install`.
`environment.yaml` is only for bootstrapping heavy CUDA/GPU binaries (drivers,
PyTorch wheels, compiled packages). Never fall back to `requirements.txt`.

**In a git worktree, a helper script run from outside it imports the MAIN
checkout.** Python puts the *script's own directory* on `sys.path[0]`, not the
cwd, so a scratchpad script plus an editable install resolves the package to the
main tree — the worktree's own edits are invisible and new modules look missing.
Measured: script in scratchpad → main; script inside the worktree, `python -c`
from it, or `PYTHONPATH=<worktree>` → the worktree. Keep helper scripts inside
the worktree, or set `PYTHONPATH`. Otherwise a stream silently tests code it did
not write.

## GitHub CLI (gh)

Installed at `~/emanuele/bin/gh`, on `PATH` in every shell, authenticated as
`emanuele-artioli`. Available in every project — install/auth never needs
repeating.

**Use it after every push to a repo with CI.** Don't assume a push landed
cleanly or guess at failures from job and step names:

- `gh run list --branch <branch> --limit 3` — find the run
- `gh run watch <run-id>` — wait for it. It can flake with a transient "Bad
  credentials" on the annotations call; a following `gh run view <run-id>`
  still shows the real status, so that crash is not a failed run.
- `gh run view <run-id> --log-failed` — **the actual fix for CI debugging.**
  The unauthenticated REST API exposes only names and conclusions and 403s on
  log downloads even for public repos, which means guessing at root causes.
  Authenticated `gh` gives the failing line immediately.

Same applies to `gh pr view`, `gh issue view`, `gh pr create` — not CI-only.

## Git — never destroy work you have not read

Several agents work these repos at once, and unmerged work has genuinely been
lost here: a complete HNeRV baseline once sat in a forgotten worktree.

- **Read a branch before deleting it** — `git log main..<branch>` and
  `git diff main...<branch> --stat`. If it is not empty,
  `git tag archive/<branch> <branch>` and push the tag *before* deleting.
  Tags are free and make a triage mistake recoverable.
- **A worktree with uncommitted changes never gets `--force`d away.** Commit
  onto that worktree's own branch, tag, then remove. A refusal from
  `git worktree remove` is a warning, not an obstacle to route around.
- **"Superseded" needs proof** — `git patch-id`, or diff against `main`. A
  branch whose commit message matches one on main may still hold changes main
  never got.
- **A branch alone does not isolate a session.** Two agents in one checkout
  share one HEAD; isolation needs a worktree *and* a branch.
- **A merge can silently keep the stale half of a status file.** Conflict
  resolution picks one side per hunk and the older side usually still reads
  plausibly. After any merge touching a plan or status doc, re-read the lines
  that describe *current* state and check each against reality. One status line
  here announced a finished workstream as still blocked — twice.

## Research code — tests are a failsafe, not a formality

Cover envisioned behavior and plausible misuse of code we own. Skip
unreachable branches, third-party behavior, and errors a caller cannot
produce — this is research code and boilerplate slows the iteration that
matters. **A test that exists only to raise a coverage number is a defect**:
it makes the gate lie. If deleting padding drops the gate, lower the gate to
the honest number and ratchet it back up as real tests land.

The tests that pay for themselves check *the paper's claim*, not just that the
code runs: an experiment whose result violates what the paper asserts should
fail loudly and be marked uncitable, rather than being caught later by a
careful human reading a table.

## Experiment results — bound before believing

Before launching a run or reading its headline metrics, state a **plausible
worst-case and best-case** for each (one-line basis: prior runs, paper
baselines, metric bounds, trivial baselines). Write the bounds *before*
looking at the number. A result outside that range is an **alarm**:
investigate implementation / eval / data bugs first; do not report it as a
clean finding or cite it until the alarm is closed or the bounds are
explicitly revised with a reason. Procedure lives in `results-report` /
`gpu-job-runner`.

Make the band **two-sided** whenever the bound is on the very quantity the
experiment exists to generalize past — a one-sided band derived from the
incumbent cases encodes the assumption under test as if it were a bound, and
points the alarm text at the wrong thing. Check a bound at the operating point
its own wording names ("at matched rate" is not "at fixed QP"). **To close a
fired alarm cheaply, run the new analysis path over old data and see whether it
reproduces an already-published number**; if it does, the tool is not the
explanation and the alarm is a finding. That beats auditing the new code, and
validates the tool at the same time.

## Control the instrument, then the result

A measurement is not evidence until the thing that produced it has been checked
on inputs whose answer is already known. Two metrics here passed
"identical scores well, degraded scores badly" while measuring nothing usable —
one could not tell a good reconstruction from an unrelated image, the other
scored a blurred clip above a perfect match. Rankings were published on both.

- **Calibrate a metric against known anchors before trusting any ranking from
  it**: identical, mild, severe, unrelated — and check the *absolute* scale
  against the published range, not just the ordering. A metric can be perfectly
  ordered and still be uninterpretable.
- **A control is part of a measurement, not a follow-up.** No "X beats Y"
  without the null in the same session: unrelated input, no model, shuffled
  condition. Run it *before* reporting, not after being asked.
- **A "fraction of the oracle/ceiling/headroom" metric has a floor well above
  zero.** Random selection already captured 0.402 of an oracle here, so 0.833 is
  not "83% of the way there" — the earned credit is `0.833 − 0.402`. Compute the
  null (a Monte Carlo over values you already have, milliseconds) and report it
  beside the number. Pre-registered bounds do not catch this: a band around a
  mis-scaled quantity is still mis-scaled.
- **Quote the instrument's range with the number.** "0.067" means nothing;
  "0.067, where an unrelated image scores 0.645" means something.
- **Report n and the standard error with any comparison.** A difference under
  ~2 standard errors is not a finding, and one measured on a handful of items is
  not a direction.
- **When a component underperforms, check it is being invoked the way its
  architecture intends** before concluding anything about the component. A
  temporal video model was evaluated one frame at a time here for three rounds.

**The asymmetry to watch:** these checks get applied to disappointing results and
skipped on exciting ones. **When the news is good, add a check rather than
stopping.**

## Long jobs must checkpoint at least hourly

SSH here drops a couple of times a day. Any job expected to run over an hour
checkpoints at least every 60 minutes of wall clock — independent of its
epoch/step cadence — and its resume path is verified *before* it is relied on.
Long scripts also append a progress line at least every 10 minutes, so a
silent hang is visible in minutes rather than hours. Launch detached; never
attached to a shell an SSH drop takes with it.

**A batch runner that tolerates per-entry failures exits 0 when every entry
failed.** The per-entry handling is right — one bad config should not abandon a
multi-hour wave — so the check belongs with the caller: compare results produced
against entries submitted, and never read exit 0 as "the wave completed". A
clean 50/50 split in what succeeded points at a config-shape bug, not GPU
flakiness.

## Plan mode: split complex plans into parallel-agent waves

When a plan has multiple pieces that don't share state, don't execute it
linearly. Split into workstreams, hand each to a subagent in its own git
worktree, and group them into **waves** ordered by dependency: a wave starts
only once every workstream it depends on has reported back, and all
workstreams in a wave launch together.

**Why:** validated on a multi-part refactor — it surfaced cross-workstream
issues at each wave boundary instead of at the end, and kept parallel agents
from clobbering each other.

**How to apply:** worth it for genuinely multi-part, multi-file tasks with
largely independent pieces. Skip it for small or sequential work — one file,
one clear order — where waves are pure coordination overhead. If you skip,
say so explicitly in the plan (“skipped: sequential/small”).

**Coordination docs land on the shared branch immediately.** A prompt, a wave
plan, a brief, a status table — anything written *for another agent to read* —
is invisible behind an unmerged PR, which is exactly the audience it exists for.
Only code waits for review. Two waves here launched against docs the workers
could not see.

**A wave is finished when its worktrees are gone, not when its PRs merge.** A
worktree that outlives its branch is a silent-revert hazard: a resumed session
re-applies its own version of a file a later session already changed, and
nothing about the output looks wrong. Removal follows the git rules above — but
compare against **`origin/main`**, not a local `main` that may be dozens of
commits stale and will make every merged branch look unmerged — and **ask the
user before removing**, because a session may be paused in one.

## One PR per independently revertible change

Over-splitting burns the Copilot review budget — measured here: it stops
analysing PRs after a few days of heavy splitting. Under-splitting keeps `main`
stale and leaves parallel sessions rebasing onto old code. The unit is what you
would want to revert on its own.

## Knowledge loop — crossed axes

Platforms and projects form a **grid**, not a stack: every platform can work
on every project. Surface knowledge on either axis into `.agent-rules/candidates/`
(write only when there is something to surface) — `open/project/` for what
other projects may want, `open/platform/` for what other platforms may need.

Close out with the `end-of-session` skill (considers both axes, commits on
invoke, asks before push). Apply or discard from a coding-agent-config session
with `evaluate-candidates`. Live platform configs and “this works on X” claims
belong to platform X; cross-writes become `needs_verification` tickets under
`candidates/pending-verification/`.
