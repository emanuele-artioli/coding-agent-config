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

Work in a worktree on a branch. The primary checkout stays on
`origin/master` (or `origin/main`), clean.

Undoable git: just do it (commit, push the branch, open the PR, merge).
A wrong merge is a revert.

Irreversible git is a human's to run: force push (`--force-with-lease`
included), deleting a remote branch or tag, `push --mirror/--prune`,
`reflog expire`, `gc --prune=now`, and `git clean -f`. Enforced by
`guardlib/destructive_git.py` on agent shells. An editor's git panel
talks to git itself and is not that hook.

<!-- scope: tests/**, **/tests/**, **/test_*.py, **/*_test.py, conftest.py, **/conftest.py -->
## Research code — tests are a failsafe, not a formality

Cover envisioned behavior and plausible misuse of code we own. Skip
unreachable branches, third-party behavior, and errors a caller cannot
produce. **A test that exists only to raise a coverage number is a defect.**
If the project has a paper, tests that pay for themselves check the claim.

## A flag is not a feature

An option that the code accepts can still be ignored. Before relying on
a capability, drive it and measure that the output changed in the way
claimed.
