# Host-wide agent rules — single source of truth

Edit **only this file** for anything that applies to every agent on this host.
It stays strictly tool-agnostic — tool names, invocation syntax and per-agent
config paths belong in `harness/<agent>.md`, so every consumer can take these
bytes as-is. It is also **the register of things that have gone wrong more
than once**: if a mistake happens twice it belongs here, phrased as the rule
that prevents it rather than the story of the failure.

Nothing copies this file. Local agents import or symlink it; cloud agents,
which have never seen this home directory, get it inlined into each project's
`AGENTS.md` by `scripts/sync_agent_rules.py`. Routing table in `README.md`.

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

## Python dependency management

Manage packages through `pyproject.toml`, not ad-hoc `pip install`.
`environment.yaml` is only for bootstrapping heavy CUDA/GPU binaries (drivers,
PyTorch wheels, compiled packages). Never fall back to `requirements.txt`.

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

## Long jobs must checkpoint at least hourly

SSH here drops a couple of times a day. Any job expected to run over an hour
checkpoints at least every 60 minutes of wall clock — independent of its
epoch/step cadence — and its resume path is verified *before* it is relied on.
Long scripts also append a progress line at least every 10 minutes, so a
silent hang is visible in minutes rather than hours. Launch detached; never
attached to a shell an SSH drop takes with it.

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
