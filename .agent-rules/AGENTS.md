# Host-wide agent rules — single source of truth

Edit **only this file** for anything that applies to every agent on this host.
Keep it tool-agnostic: tool names, invocation syntax and per-agent config paths
belong in `harness/<agent>.md`. It is **the register of things that have gone
wrong more than once** — if a mistake happens twice it belongs here, phrased as
the rule that prevents it, not the story of the failure.

Nothing copies this file; agents import or symlink it (routing table in
`README.md`). Do not inline it into project files — that becomes a second
source of truth. Cloud agents on other machines will not see it; accepted.
Rollout TODO: `candidates/open/platform/2026-08-23-pointer-not-inline-host-rules.md`.

**Keep it short.** Every line is loaded by every agent in every session on every
project — prose costs adherence, so compress rather than accumulate.

## Write in plain words

Simple everyday language, short sentences, common word over the fancy one, cut
words that add nothing. Keep technical terms that carry meaning (QP, worktree,
checkpoint); drop decorative ones. Applies to chat, commits and comments; paper
text keeps its academic register.

## The host

Shared remote Linux **GPU server, no root/sudo/apt**, headless. Home is
`/home/itec/emanuele`. Install extra tooling with conda (Miniconda at
`/usr/local/miniconda3`) into a *separate* env — never a project's pinned env,
since several forked third-party models are version-sensitive and a stray
`pip install` silently breaks them. Headless: save media and plots to disk,
`cv2.imshow()`/`plt.show()` never works.

**`import sqlite3` before `import torch`.** conda's `libicui18n` needs
`CXXABI_1.3.15`, which the system `libstdc++` that torch pins does not export.
It bites at *runtime* when the sqlite3 import is deferred inside a function, and
CI will not reproduce it. Put `import sqlite3` at the top of the package's
`__init__.py` so no submodule can reintroduce it.

## The home is NFS: `open()` costs, and one at a time costs most

Every home here is an export of one server, `data3`. Measured 2026-08-31:
**serial `open()` runs at 2.4–4.3/s, `stat()` on the same files at ~13,000/s,
local `/tmp` (ext4) at 15,774/s.** Bulk throughput is fine (174 MB/s) and
retransmissions are 4 in 1.64 billion RPCs, so this is per-request round-trip
latency on the NFSv4 OPEN, not the network and not server saturation.

- **Parallelism is the fix, and it is dramatic.** The same copy went 1.7 → 23.3
  opens/s at `-P 24`, a 14× speedup; 10,578 files took 6 min instead of an hour.
  Any bulk read/copy of many small files here gets `xargs -P 24` or better.
  What you cannot parallelise — a single-threaded indexer, `mypy`, one `cp` —
  pays the full serial rate.
- **Walking is cheap; opening is not.** `find`, `du`, `git status` and an
  editor's file watcher only `readdir`+`stat`, at thousands per second.
  Indexers, language servers, `grep -r` and `mypy` open every file. So
  `search.exclude` earns its keep and `files.watcherExclude` mostly does not.
- **Tree size is a multiplier, not a cause.** ~0.3 s × files opened, identical
  for every project: 1,400 files is 7 min, 17,000 is 1.4 h. A project that
  "works" here is not on a faster path, only a shorter one.
- **Keep regenerable caches on local disk** — `.mypy_cache`, `.pytest_cache`,
  `.ruff_cache`, `__pycache__`, coverage, tool downloads. Reading one worktree's
  8,311-file mypy cache is ~40 min, the whole gap between a 15–25 min local run
  and 3m30s on CI. `.gitignore` does not help; it stops git tracking them, not a
  tool reading them. Namespace per checkout
  (`MYPY_CACHE_DIR=/tmp/mypy-$(basename "$PWD")`) or worktrees collide on
  module-name keys.
- **Keep the editor's own server off NFS too** — `.cursor-server` measured
  58,495 files, 3.4× a whole checkout, so a cold connect spends hours before
  touching any project. `/var/tmp` here is local and not age-cleaned;
  `/local/users/<you>` if an admin grants one. Same for a conda env, worth
  copying only for a run of many short processes.
- **Batch work into long-lived processes**, and open **one worktree** as the
  editor folder, never the parent — that pulls in every sibling worktree plus
  `.conda` (3M inodes) and every dataset.
- **A `du`, `find` or `git status` that seems hung is usually neither.** Check
  `wchan` for `nfs_wait_bit_killable`. Contention is often not yours: a
  co-tenant's editor `grep` has sat in `D` state for 13 hours on this mount, and
  a measurement taken during that is not a measurement of your project.

## Python dependency management

Manage packages through `pyproject.toml`, not ad-hoc `pip install`.
`environment.yaml` only for bootstrapping heavy CUDA/GPU binaries. Never fall
back to `requirements.txt`.

**In a git worktree, a helper script run from outside it imports the MAIN
checkout.** Python puts the *script's own directory* on `sys.path[0]`, not the
cwd, so a scratchpad script plus an editable install resolves to the main tree —
the worktree's edits are invisible and new modules look missing. Keep helper
scripts inside the worktree, or set `PYTHONPATH`. Otherwise a stream silently
tests code it did not write.

## GitHub CLI (gh)

At `~/emanuele/bin/gh`, on `PATH`, authenticated as `emanuele-artioli`.
**Use it after every push to a repo with CI** rather than assuming the push
landed or guessing from job names: `gh run list --branch <b> --limit 3`, then
`gh run watch <id>`, then **`gh run view <id> --log-failed`** — that last one is
the actual fix for CI debugging, because the unauthenticated REST API gives only
names and conclusions and 403s on logs. `gh run watch` can flake with a
transient "Bad credentials" on the annotations call; a following `gh run view`
still shows the real status. Same for `gh pr view` / `issue view` / `pr create`.

## Git — never destroy work you have not read

Several agents work these repos at once, and unmerged work has genuinely been
lost here: a complete HNeRV baseline once sat in a forgotten worktree.

- **Read a branch before deleting it** — `git log main..<branch>` and
  `git diff main...<branch> --stat`. If it is not empty, `git tag
  archive/<branch>` and push the tag *before* deleting. Tags are free and make a
  triage mistake recoverable.
- **Compare against `origin/main`, not a local `main`.** A local `main` dozens
  of commits stale makes every merged branch read as far *ahead* — 52 commits of
  drift made six merged branches look like 34 commits of unmerged work.
- **A worktree with uncommitted changes never gets `--force`d away.** Commit
  onto its own branch, tag, then remove. A refusal from `git worktree remove` is
  a warning, not an obstacle to route around.
- **"Superseded" needs proof** — `git patch-id`, or a diff. A branch whose
  commit message matches one on main may still hold changes main never got.
- **A branch alone does not isolate a session.** Two agents in one checkout
  share one HEAD; isolation needs a worktree *and* a branch.
- **A merge can silently keep the stale half of a status file.** Conflict
  resolution picks one side per hunk and the older side usually still reads
  plausibly. After any merge touching a plan or status doc, re-read the lines
  describing *current* state and check each against reality. One status line
  here announced a finished workstream as still blocked — twice.

## Research code — tests are a failsafe, not a formality

Cover envisioned behavior and plausible misuse of code we own. Skip unreachable
branches, third-party behavior, and errors a caller cannot produce — this is
research code and boilerplate slows the iteration that matters. **A test that
exists only to raise a coverage number is a defect**: it makes the gate lie. If
deleting padding drops the gate, lower the gate to the honest number and ratchet
it back up. The tests that pay for themselves check *the paper's claim*: an
experiment whose result violates what the paper asserts should fail loudly and
be marked uncitable, not be caught later by a human reading a table.

## Experiment results — bound before believing

Before launching a run or reading its headline metrics, state a **plausible
worst- and best-case** for each (one-line basis: prior runs, paper baselines,
metric bounds, trivial baselines), *before* looking at the number. A result
outside that range is an **alarm**: investigate implementation / eval / data
bugs first, and do not report or cite it until the alarm is closed or the bounds
are revised with a reason. Procedure in `results-report` / `gpu-job-runner`.

Make the band **two-sided** when the bound is on the very quantity the
experiment exists to generalize past — a one-sided band derived from the
incumbent cases encodes the assumption under test as if it were a bound. Check a
bound at the operating point its own wording names ("at matched rate" is not "at
fixed QP"). **To close a fired alarm cheaply, run the new analysis path over old
data and see whether it reproduces an already-published number**; if it does,
the tool is not the explanation and the alarm is a finding.

## Control the instrument, then the result

A measurement is not evidence until the thing that produced it has been checked
on inputs whose answer is already known. Two metrics here passed "identical
scores well, degraded scores badly" while measuring nothing usable — one could
not tell a good reconstruction from an unrelated image, the other scored a
blurred clip above a perfect match. Rankings were published on both.

- **Calibrate against known anchors before trusting any ranking**: identical,
  mild, severe, unrelated — and check the *absolute* scale against the published
  range, not just the ordering. A metric can be perfectly ordered and still
  uninterpretable.
- **A control is part of a measurement, not a follow-up.** No "X beats Y"
  without the null in the same session: unrelated input, no model, shuffled
  condition.
- **A "fraction of the oracle/ceiling/headroom" metric has a floor well above
  zero.** Random selection already captured 0.402 of an oracle here, so 0.833 is
  not "83% of the way there" — the earned credit is the difference. Compute the
  null (milliseconds, over values you already have) and report it beside the
  number. Pre-registered bounds do not catch this: a band around a mis-scaled
  quantity is still mis-scaled.
- **Quote the instrument's range with the number.** "0.067" means nothing;
  "0.067, where an unrelated image scores 0.645" means something.
- **Report n and the standard error.** A difference under ~2 standard errors is
  not a finding, and one measured on a handful of items is not a direction.
- **When a component underperforms, check it is being invoked the way its
  architecture intends** first. A temporal video model was evaluated one frame at
  a time here for three rounds.

**The asymmetry to watch:** these checks get applied to disappointing results and
skipped on exciting ones. **When the news is good, add a check rather than
stopping.**

## Long jobs must checkpoint at least hourly

SSH here drops a couple of times a day. Any job over an hour checkpoints every
60 minutes of wall clock — independent of its epoch/step cadence — with its
resume path verified *before* it is relied on, and appends a progress line at
least every 10 minutes so a silent hang shows in minutes. Launch detached.

**A batch runner that tolerates per-entry failures exits 0 when every entry
failed.** The per-entry handling is right — one bad config should not abandon a
multi-hour wave — so the check belongs with the caller: compare results produced
against entries submitted, and never read exit 0 as "the wave completed". A
clean 50/50 split in what succeeded points at a config-shape bug, not GPU
flakiness.

## Plan mode: split complex plans into parallel-agent waves

When a plan has independent pieces, split into workstreams, hand each to a
subagent in its own git worktree, and group them into **waves** ordered by
dependency: a wave starts only once everything it depends on has reported back.
Validated on a multi-part refactor — it surfaced cross-workstream issues at each
boundary instead of at the end. Worth it for genuinely multi-part, multi-file
work; skip it for one file or one clear order, and say so in the plan
("skipped: sequential/small").

**Coordination docs land on the shared branch immediately.** A prompt, wave
plan, brief or status table — anything written *for another agent to read* — is
invisible behind an unmerged PR, which is exactly the audience it exists for.
Only code waits for review. Two waves here launched against docs the workers
could not see, and one brief was readable only inside the worktree that wrote it.

**A wave is finished when its worktrees are gone, not when its PRs merge.** A
worktree outliving its branch is a silent-revert hazard: a resumed session
re-applies its version of a file a later session already changed, and nothing
about the output looks wrong. Remove per the git rules above, and **ask the user
first** — a session may be paused in one.

## One PR per independently revertible change

Over-splitting burns the Copilot review budget — measured: it stops analysing
PRs after a few days of heavy splitting. Under-splitting keeps `main` stale and
leaves parallel sessions rebasing onto old code.

## Knowledge loop — crossed axes

Platforms and projects form a **grid**, not a stack: every platform can work on
every project. Surface knowledge on either axis into `.agent-rules/candidates/`
— `open/project/` for what other projects may want, `open/platform/` for what
other platforms may need — writing only when there is something to surface.
Close out with `end-of-session` (commits on invoke, asks before push); apply or
discard from a coding-agent-config session with `evaluate-candidates`. Live
platform configs and "this works on X" claims belong to platform X; cross-writes
become `needs_verification` tickets under `candidates/pending-verification/`.
