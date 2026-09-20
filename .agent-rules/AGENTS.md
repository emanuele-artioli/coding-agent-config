# Agent rules — portable fleet

Edit **this file** for anything that should apply to every agent using this
repo, on any machine. Tool names and per-agent config paths belong in
`harness/<agent>.md`. Lab GPU / NFS facts belong in `host.md` (this
machine only).

It is **the register of things that have gone wrong more than once** —
if a mistake happens twice it belongs here, phrased as the rule that
prevents it, not the story of the failure.

**A project does not need its own AGENTS.md, skills, or agents** for this
fleet to work. Discover the repo from its README, `pyproject.toml`, and
tests. If a `PLAN.md` or `docs/areas/` exists, use them; do not require
them. Do not inline these rules into a project — that becomes a second
source of truth.

**Keep it short.** Every line is loaded by every agent in every session —
prose costs adherence.

## Write in plain words

Simple everyday language, short sentences, common word over the fancy
one, cut words that add nothing. Keep technical terms that carry meaning
(QP, worktree, checkpoint); drop decorative ones. Chat, commits and
comments; paper text keeps its academic register.

<!-- scope: pyproject.toml, environment.yaml, requirements*.txt, setup.py, setup.cfg, scripts/**, tools/** -->
## Python dependency management

Manage packages through `pyproject.toml`, not ad-hoc `pip install`.
`environment.yaml` only for bootstrapping heavy CUDA/GPU binaries. Never
fall back to `requirements.txt`.

**In a git worktree, a helper script run from outside it imports the MAIN
checkout.** Python puts the *script's own directory* on `sys.path[0]`,
not the cwd. Keep helper scripts inside the worktree, or set
`PYTHONPATH`.

## Git — reversible is yours to do, irreversible is not

**Work on a branch, and do not ask permission for anything you can undo.**
Commit, push the branch, open the PR, and merge it when you are confident
— a wrong merge is a revert.

**Stop at the operations nothing can recover**: a force push
(`--force-with-lease` included), deleting a remote branch or tag, `push
--mirror/--prune`, `reflog expire`, `gc --prune=now`, and `git clean -f`.
Those are a human's to run. Enforced by `guardlib/destructive_git.py` on
agent shells. An editor's git panel talks to git itself and is not that
hook.

- **Read a branch before deleting it** — `git log origin/main..<branch>`
  and `git diff origin/main...<branch> --stat`. If it is not empty, `git
  tag archive/<branch>` and push the tag *before* deleting.
- **Compare against `origin/main` (or `origin/master`), not a stale local
  default branch.**
- **A worktree with uncommitted changes never gets `--force`d away.**
- **"Superseded" needs proof** — `git patch-id`, or a diff.
- **A branch alone does not isolate a session.** Two agents in one
  checkout share one HEAD. One live session → one worktree → one branch.
  The primary checkout is not for parallel children. If this tree is
  dirty, do not `git checkout` another branch here — add a worktree.
- **A merge can silently keep the stale half of a status file.** After
  any merge touching a plan or status doc, re-read the lines describing
  *current* state.
- **Do not `rm -rf` a worktree.** Git's refusal is the warning. A project
  script that discards uncommitted work is forbidden. Merged-and-clean
  trees: host `git-clean-merged-worktrees` only. Ask first if a session
  may be paused there.

## No project files required

Ordinary edits need no dispatch ceremony. For multi-step work the senior
(the parent session) reads the repo as it is (README, tests, existing
docs), then dispatches juniors with the seven-field prompt from skill
`session` and re-runs their check instead of reading their work. A successful
child may continue from analysis into a fix in the same area, with the same
model and an explicit scope extension; start fresh for a new area or an
escalation. Close with `end-of-session`.

<!-- scope: tests/**, **/tests/**, **/test_*.py, **/*_test.py, conftest.py, **/conftest.py -->
## Research code — tests are a failsafe, not a formality

Cover envisioned behavior and plausible misuse of code we own. Skip
unreachable branches, third-party behavior, and errors a caller cannot
produce. **A test that exists only to raise a coverage number is a
defect.** If the project has a paper, tests that pay for themselves check
*the claim*: an experiment whose result violates what the paper asserts
should fail loudly.

## A flag is not a feature

An option that the code accepts can still be ignored. Before relying on
a capability, drive it and measure that the output changed in the way
claimed.

## Experiment results — bound before believing

Before launching a run or reading headline metrics, state a **plausible
worst- and best-case** for each *before* looking at the number. A result
outside that range is an **alarm**. Procedure: `verify-measurement` /
`results-report`. Reuse existing artifacts; a newer code fix does not
certify old evidence. Launch the smallest probe that fills a documented
gap.

When you report a result, carry **size, quality, and time** if those
axes exist — not two of three. Detail in `verify-measurement`.

**Old numbers do not become new because the code changed.** Reuse
artifacts; rescore if the question is the same. Missing timing is not a
reason to rerun a finished rate/quality measurement.

If the work has a paper, **scope headline claims to the regime where
they hold.** Finding that regime is part of the method.

**When the news is good, add a check rather than stopping.**

## Long jobs must checkpoint at least hourly

Any job over an hour checkpoints every 60 minutes of wall clock, with
its resume path verified *before* it is relied on, and appends a
progress line at least every 10 minutes. Launch detached. Do not invent
a periodic agent poll loop; wake on actionable events.

**A batch runner that tolerates per-entry failures exits 0 when every
entry failed.** Compare results produced against entries submitted;
never read exit 0 as "the wave completed".

## Seniority follows model size

Stay on this platform's in-house family. Three rungs in
`effort-models.json` (this author's map — edit it for your bill): junior
for bounded children, senior for the parent session, escalation for a
fresh child after `STUCK: out of ideas.` or a failed check. The senior
holds context and judgment; a junior holds one task, a runnable check,
and a budget. Verify the claim, not the work: re-run the check, do not
re-read the diff. Never resume a stuck child to change its model, never
loop, never spawn another vendor's model. Dated API chart: repo README.

A junior needs a runnable check, a page-long prompt, and five or more turns
of work; below that, work in the senior's own context. Build that prompt from
the task, the relevant canonical rules, and scoped host facts. Do not send
senior-only planning, promotion, PR, or session-management procedures, an
unrelated skill catalog, or a copied universal facts block. Mandatory
platform instructions, permissions, and tool schemas still apply. A second
senior, on its own worktree and branch, is for a piece needing repo-wide
judgment, no check, or a talk with the human: it re-reads the repo, and you
talk twice.

## Plan mode: split complex plans into parallel-agent waves

When a plan has independent pieces, split into workstreams, hand each to
a subagent in its own git worktree, and group them into **waves**. Skip
it for one file or one clear order (`skipped: sequential/small`).

**Coordination docs land on the shared branch immediately.** A wave is
finished when its worktrees are gone, not when its PRs merge. **Ask the
user first** before removing a worktree that may be a paused session.

## One PR per independently revertible change

Over-splitting burns review budget; under-splitting keeps default stale.

## Knowledge loop — crossed axes

If this checkout is your SoT, surface knowledge into
`.agent-rules/candidates/` (`open/project/`, `open/platform/`) only when
there is something to file. The parent decides what was learned; the
deterministic closeout tool records the boundary and event IDs so retries do
not duplicate it. Close out with `end-of-session`; apply with
`evaluate-candidates`.

<!-- host-rules:start — GENERATED by tools/sync_agent_rules.py.
     A pointer, deliberately: host rules are not copied into projects,
     because a copy goes stale silently. Everything above this marker
     is this project's own, hand-edited. -->

# Host-wide rules

These are **not** reproduced here. They live in one file on this
machine, which is the only place they are edited:

`/tmp/cac-policy-home/.agent-rules/AGENTS.md`

Follow it for every session. Claude Code and Antigravity load it
automatically; if it is not already in your context, read it with your
file-reading tool before doing anything else. Harness-specific
mechanics are beside it in `/tmp/cac-policy-home/.agent-rules/harness/`.

@/tmp/cac-policy-home/.agent-rules/AGENTS.md

<!-- host-rules:end -->
