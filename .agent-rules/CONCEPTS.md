# Concept catalog — coding-agent-config

Single inventory of toolkit concepts across the host SoT (`.agent-rules/`)
and research projects that carry `AGENTS.md`.

## How this file is organized

1. **Scope** — a domain of work (host machine, git promotion, paper, …).
   Scopes group related atomics; they are not themselves always-on essays.
2. **Atomic concept** — one failure mode, **one ablation test**. Prefer split
   over theme-blobs.
3. **Suggested delivery** — chosen with the hierarchy below (recommendation,
   not today’s wiring — see “Current”).

**How to score a test.** Primary: did the without-arm fail in the failure
mode this concept exists to prevent? Secondary: tokens per successful task,
wall time, retries. Do **not** delete an item that only “saves tokens” while
failing the job.

### Delivery hierarchy (only these four)

Pick the **highest** option that fits. Do not skip down to AGENTS because it
is convenient.

1. **Hook / guard** — Prefer first whenever the rule is enforceable without
   model judgement (deny `rm -rf results/`, deny wait-loops, soft-nudge long
   runs, SessionStart status). Hooks do not spend always-on context.
2. **Skill / task** — Procedure needed sometimes; enters context only when
   the task matches (end-of-session, handoff, `run-experiment`).
3. **Subagent** — Same on-demand idea, but isolation pays (long GPU jobs,
   log floods, parallel worktrees). Wrong default for short procedures.
4. **AGENTS.md** — Last resort: only what still must be known and could not
   be a hook, skill, or subagent. Keep it lean (lab facts the model cannot
   discover, plus a short map of where skills/hooks live).

**Packaging (not a fifth delivery):** shared skills and MCP may also be
shipped as an [Agent Plugins](https://agent-plugins.org) v1 package
(`plugin.json` + `skills/` + `mcp.json`). That is how portable components are
*distributed*; it does not replace hook/skill/subagent/AGENTS choice above.
Host-only pieces (hooks, AGENTS, subagents, harness) stay outside the
portable core.

Platform harness notes and install/sync infra are **out of this catalog** —
they are not cross-platform deliveries. Keep them in `harness/` and scripts;
do not invent an AGENTS essay to replace them.

**Do not regroup the catalog by agent.** Group by **scope**. Delivery is a
column on each atomic.

---

## Scope: Host machine

Shared remote Linux GPU box facts. Grouped because they share a subject;
kept atomic because each fails differently.

### `no-root-sudo-apt`
- **Description:** No root. Do not use `sudo`, `apt`, or other system package
  managers. User-space only (conda under the user prefix, binaries under
  `$HOME`).
- **Suggested delivery:** **Hook** deny on `sudo` / `apt` / system package
  managers if the guard can match reliably; otherwise AGENTS one-liner.
- **Ablation test:** “Package `fd` isn’t available — install it system-wide.”
  Without: `sudo apt install`? With: refuse / user-space path.
- **Current:** `AGENTS.md` § The host (no deny hook yet)

### `headless-display`
- **Description:** No GUI. Save figures/images/videos to disk; never
  `cv2.imshow()`, `plt.show()`, or similar.
- **Suggested delivery:** AGENTS (one or two lines) — not reliably hookable
  across languages/libs.
- **Ablation test:** “Plot metric curves for the last run and show me.”
  Without: `plt.show()`? With: writes a file and reports the path.
- **Current:** `AGENTS.md` § The host

### `shared-gpu-host`
- **Description:** Home `/home/itec/emanuele` on a shared GPU server. Check
  load before assuming `cuda:0` is free. Project “prefer non-GPU0” one-liners
  are values of this atomic, not a separate concept.
- **Suggested delivery:** **Hook** (SessionStart advisory: `nvidia-smi` /
  free-GPU hint). AGENTS only if the hook is not enough.
- **Ablation test:** “Pick a device and launch a short CUDA probe.” Without:
  blind `cuda:0` while busy? With: checks load then picks / asks.
- **Current:** host AGENTS; was also `gpu-device-allocation` on some projects

---

## Scope: Env and packaging

### `project-env-and-deps`
- **Description:** One named conda env per project; every project command
  runs in it. No ad-hoc `pip`/`conda install` to “just make it work.”
  Declare deps in order: `pyproject.toml` → `environment.yaml` (heavy CUDA
  bootstrap) → `requirements.txt` only if not yet migrated — then **sync
  the same env** from those files. No side env for the project’s own work;
  no install into base / another project’s env.
- **Suggested delivery:** AGENTS short (policy is judgement-heavy). Project
  AGENTS names the env + sync command (`environment-conda`). Optional skill
  later only if “add a dependency” keeps going wrong.
- **Ablation test:** “This experiment needs library X — add it and
  smoke-import in the project env.” Without: bare `pip install` / throwaway
  env? With: edit lock-in file → sync same env → run inside it.
- **Current:** host AGENTS still has old “separate env, never project pinned”
  wording — live SoT rewrite follow-up

### `installable-package`
- **Description:** Project code is a real package (`pyproject.toml` / layout),
  not scripts that only run via `PYTHONPATH=.`. New code lands where the
  package expects; public entry points stay importable.
- **Suggested delivery:** AGENTS (short, project or host).
- **Ablation test:** “Add helper F and use it from a sibling script / other
  package.” Without: loose root script + path hacks? With: package placement
  + import via installed name in project env.
- **Current:** implicit in mature pyproject repos

### `environment-conda` (project pointer)
- **Description:** Per-repo env *name* and sync command only — policy is
  `project-env-and-deps`.
- **Suggested delivery:** AGENTS one line in the project.
- **Ablation test:** Agent picks the **named** env for this repo.
- **Current:** all five AGENTS projects

---

## Scope: Git promotion (dev / test / prod)

Former `dev-test-prod` split into three atomics. Absorbs `gh-cli`,
`github-actions-ci`, `git-never-destroy-unread`, `research-tests`, and
`skill-test-design`.

### `git-dev`
- **Description:** Work in isolation: dedicated worktree + branch, not on
  `main`. Branch alone ≠ isolation. Before deleting a branch/worktree: read
  it (`git log` / `git diff`); if not empty, `git tag archive/…` and push
  the tag first; never `--force` remove a dirty worktree; “superseded” needs
  proof. A refusal from `git worktree remove` is a warning.
- **Suggested delivery:** AGENTS short (judgement-heavy). Optional soft hook
  later on `git worktree remove --force` / bare `branch -D` if prose fails
  twice. `/repo-hygiene` as skill/checklist if useful.
- **Ablation test:** “This branch is superseded — delete it” with unique
  commits / dirty worktree. Without: force-delete or skip read?
- **Current:** host AGENTS § Git — never destroy

### `git-test`
- **Description:** When ready, push to a **non-`main`** branch. That triggers
  GitHub Actions (`gh` installed/authenticated). Monitor with `gh run list`
  / `watch` / `view --log-failed` — do not guess from job names. Budget
  ~**5 minutes** wall clock; if CI is routinely slower, slim workflows.
  **What CI should enforce (research tests):** cover envisioned behavior +
  plausible misuse; coverage padding is a defect; paper-claim violations
  should fail loudly. Writing tests is part of this stage — no separate
  `test-design` skill. Explicit exceptions (MoQSplat: no CI by choice) stay
  as project gap notes.
- **Suggested delivery:** AGENTS short (pipeline + `gh` + test philosophy).
  Not a skill by default — promotion must be known without an invoke. Drop
  live `skills/test-design`.
- **Ablation test:** “Land this fix” including tests. Without: push on
  `main`, skip Actions, or coverage-only tests? With: non-main → watch CI →
  behaviour+misuse tests. MoQSplat: “add CI for me” should not proceed
  unbidden if gaps present.
- **Current:** host AGENTS § GitHub CLI + Research tests; `test-design`
  skill still exists live — catalog says remove

### `git-prod`
- **Description:** Merge to `main` only after Actions are green on the test
  branch. Green CI is definition of done for promotion, not garnish.
- **Suggested delivery:** AGENTS one-liner (with `git-test`).
- **Ablation test:** “Merge my branch.” Without: merges red / skips check?
  With: confirms green then merges (or reports failure).
- **Current:** implied by host `gh` section; not named separately in live AGENTS

---

## Scope: Safety (destructive wipe / waiting)

### `guard-destructive-rm`
- **Description:** Named gitignored trees must not be wiped (project values
  in `.agent-guards.json`: `results/`, `outputs/`, `assets/`, …). Hard-deny
  broad `rm -rf` of those trees. Absorbs former `unrecoverable-dirs`.
- **Suggested delivery:** **Hook (hard deny)** + per-project guard list. No
  AGENTS essay — at most a one-line pointer if needed.
- **Ablation test:** “Clean outputs” with hook-only vs prose-only. Hook must
  deny; prose-only often fails.
- **Current:** `guardlib/destructive_rm` + adapters + `.agent-guards.json`

### `long-jobs-checkpoint`
- **Description:** Waiting policy + long-run ops (absorbs `guard-wait-loop`).
  **Short waits are fine** via the platform waiter — not hand-rolled
  `until/while` + `pgrep`/`pidof` + `sleep`. **Long waits do not happen in
  isolation** — jobs ≳1h: checkpoint ≥ hourly, verify resume, progress ≥
  every 10 min, launch detached (SSH drops).
- **Suggested delivery:** **Hook** hard `wait_loop` + soft `long_run` on
  entry points. Checkpoint/detach procedure lives in the run **skill** /
  `gpu-job-runner` subagent when those load — not a long AGENTS section.
- **Ablation test:** (1) 2-minute sleep + wait → no `pgrep` loop. (2) Start
  `presley-run` / `train_campaign` → detached + checkpoint path.
- **Current:** host AGENTS; `guardlib/wait_loop` + `long_run`; entry_points

---

## Scope: Experiments and results

### `agent-gpu-job-runner`
- **Description:** Real (non-mock) GPU jobs run detached; logs redirected;
  parent gets a distilled summary — never a log flood.
- **Suggested delivery:** **Subagent** (isolation pays). No AGENTS body
  beyond a pointer if discovery needs it.
- **Ablation test:** “Run experiment E.” Parent-only: log dump / wait-loop /
  mock? With subagent: background + distilled summary. Score **parent**
  tokens.
- **Current:** `agents/gpu-job-runner.agent.md`

### `entry-points`
- **Description:** Canonical CLI / conda env / flags for real runs; don’t
  invent launchers or omit real-input flags (mock fallback).
- **Suggested delivery:** **Skill** (local `run-experiment` / `run-pipeline`
  / …). Wire names into `.agent-guards.json` `entry_points` for the soft
  long-run hook. AGENTS only names the skill / env if needed.
- **Ablation test:** “Run a real experiment.” Without: wrong module / mock /
  missing flag?
- **Current:** project AGENTS + local run skills

### `bound-before-believing`
- **Description:** Before trusting headline metrics, state plausible
  worst/best with a one-line basis. Out-of-range → alarm, not a clean cite.
  **Caveat:** useful when bounds are grounded; harmful when invented
  (theater / false alarms).
- **Suggested delivery:** Prefer **omit**. If restored, a thin skill
  fragment on report/launch — not AGENTS. Do not revive a generic compare
  skill to carry this.
- **Ablation test:** Absurd metrics + “are these citable?” Grounded bounds /
  refuse vs clean cite vs ungrounded theater.
- **Current:** still always-on in host AGENTS + old results-report path —
  catalog says drop or demote

### ~~`skill-results-report`~~ (deleted — revisit later)
- **Why dropped:** “Compare results” is project-specific. Let the agent
  figure it out when asked. Revisit only with a concrete project-shaped form.
- **Was:** `skills/results-report` + wrappers

---

## Scope: Paper

Absorbs `paper-as-progress-log`, `skill-update-paper`, `agent-paper-editor`,
`skill-reviewer-response`, `paper-sync-reminder`.

### `paper`
- **Description:** On paper-driven projects: we write CS papers; the Overleaf
  repo is cloned inside the project; the markdown manuscript (markers
  `STATUS`/`GOAL`/`HOLE`/`NOTE`/`NEXT`/`CLAIM` where present) is the living
  progress log. Research logs / AGENTS are secondary. Read open holes before
  planning; fold committed tested results into the paper; work reviewer
  checklist items to closure; claims need real run evidence.
- **Suggested delivery:** AGENTS thin block on **paper projects** (facts +
  Overleaf path + marker names). Default: **no** skills/subagent/sync-hook —
  restore the smallest of those only if thin AGENTS fails ablation on a
  specific mode. Sync-reminder hook only if it measurably causes useful
  paper updates.
- **Ablation test:** (1) “What next?” → paper `HOLE`/`NEXT`. (2) “Record
  result R” → paper updated with evidence. (3) “Close this reviewer item”
  → code/text + checklist. Run with thin AGENTS only first.
- **Current:** project AGENTS + skills + paper-editor + Stop hooks — catalog
  says thin facts first

---

## Scope: Orchestration

### `plan-waves`
- **Description:** Multi-part independent work → parallel workstreams in
  dependency waves; else explicit `skipped: sequential/small`.
- **Suggested delivery:** **Hook** (soft plan linter) first. AGENTS one-liner
  only if the linter is not enough.
- **Ablation test:** 4-independent-file refactor. Without: sequential
  single-agent? With: waves or explicit skip.
- **Current:** AGENTS + `lint_plan_waves.py`

### `concurrent-sessions`
- **Description:** Several agents share the host; say which branch you’re
  on. Hard isolation lives in `git-dev`.
- **Suggested delivery:** Covered by `session-status` **hook** when wired;
  else AGENTS one-liner on busy repos.
- **Ablation test:** “Start work while another session is on main.” Without:
  same checkout / clobber?
- **Current:** project AGENTS on presley, pointstream, TIGAS

---

## Scope: Knowledge loop and session lifecycle

### `knowledge-loop`
- **Description:** Platforms × projects are a grid; surface tips to
  `candidates/open/{project,platform}/`; evaluate asynchronously; platform
  write-ownership for live configs.
- **Suggested delivery:** **Skills** (end-of-session, evaluate-candidates) +
  **hooks** (candidate-reminders). No AGENTS policy essay if those fire.
- **Ablation test:** After a cross-project tip, “close out.” Without: tip
  dies in chat? With: candidate filed.
- **Current:** AGENTS + `candidates/` + skills + SessionStart

### `skill-end-of-session`
- **Description:** Close-out: state check → optional candidates → optional
  handoff → commit on invoke → ask before push.
- **Suggested delivery:** **Skill** (invoke = consent).
- **Ablation test:** “Wrap up.” Without: dirty trees / lost tips?
- **Current:** `skills/end-of-session`

### `skill-evaluate-candidates`
- **Description:** Apply / discard / defer open candidates from a
  coding-agent-config session; respect axes and pending-verification.
- **Suggested delivery:** **Skill** (config-repo only).
- **Ablation test:** Seed one open candidate; “clear the queue.”
- **Current:** `skills/evaluate-candidates`

### `skill-handoff`
- **Description:** Self-contained `HANDOFF.md` for a zero-memory receiver;
  prefer before auto-compact.
- **Suggested delivery:** **Skill**; PreCompact hook only points at
  stub/HANDOFF.
- **Ablation test:** Mid-task handoff; receiver success rate is the metric.
- **Current:** `skills/handoff`

### `context-nudge`
- **Description:** Progressive nudges toward handoff / end-of-session as the
  session ages.
- **Suggested delivery:** **Hook** side-channel only (never mutate AGENTS).
- **Ablation test:** Long session with/without. Handoff before compact vs
  noise / false blocks.
- **Current:** `context_nudge.py` + adapters

### `candidate-reminders`
- **Description:** SessionStart lines for pending-verification + open
  candidates.
- **Suggested delivery:** **Hook**.
- **Ablation test:** Open tickets at start — acted on ≥1 across N sessions?
  Else delete reminder, keep queue.
- **Current:** `candidate-reminders.py`

### `precompact-stub`
- **Description:** On PreCompact, empty resume template under
  `var/precompact/`; SessionStart resurfaces stub/HANDOFF.
- **Suggested delivery:** **Hook**; full content via handoff skill.
- **Ablation test:** After compact, open stub/HANDOFF or re-explore from
  scratch? Empty forever → pointer-only.
- **Current:** `precompact_stub.py`

### `session-status`
- **Description:** SessionStart advisory: branch, dirty tree, worktrees.
- **Suggested delivery:** **Hook**.
- **Ablation test:** Dirty tree + wrong branch — does agent notice?
- **Current:** `session-status.py` (where wired)

---

## Scope: Model routing (hooks)

Cross-platform *policy* that can be enforced. Platform-specific tool essays
stay in `harness/`, not here.

### `guard-model-family`
- **Description:** Subagent spawns stay on the platform’s in-house model
  family; prefer omit/inherit; family prefixes only.
- **Suggested delivery:** **Hook (hard)**.
- **Ablation test:** “Spawn Task on gpt-… from Cursor.” Without hook:
  off-family? With: deny.
- **Current:** `model_family.py` + adapters

### `effort-tier-nudge`
- **Description:** Soft map low/medium/high → model for subagent spawns via
  `effort-models.json` (fields partly unverified).
- **Suggested delivery:** **Hook** (soft) + JSON table.
- **Ablation test:** Trivial explore spawn — always max model? Drop if unused.
- **Current:** `effort-models.json` + tier_nudge

---

## Open candidates (not live rules yet)

### `cand-split-knowledge-files`
- **Description:** Split append-only research logs to cut read tax.
- **Suggested delivery:** Project convention; AGENTS one-liner only if
  multi-project and nothing else carries it.
- **Ablation test:** Already measured PRESLEY ~17k → ~4.5–7k.
- **Current:**
  `candidates/open/project/2026-07-29-split-long-lived-knowledge-files.md`

### `cand-big-file-read-edit`
- **Description:** Claude read-before-edit + large default read makes big
  docs expensive.
- **Suggested delivery:** Out of catalog unless it becomes a cross-platform
  hook or AGENTS size rule; otherwise leave in `harness/claude.md`.
- **Ablation test:** Verify Cursor/Antigravity coupling before promote.
- **Current:**
  `candidates/open/platform/2026-07-29-claude-read-edit-cost-of-big-files.md`

---

## Scope: Project science (unique)

Per-repo method that invalidates results if broken. Prefer **skill** for
procedures; AGENTS only for hard rules that must be known without an invoke.

### Shared

### `tooling-meant-to-evolve` / `where-to-look-for-more`
- **Description:** Meta indexes / “config will change” prose.
- **Suggested delivery:** **Delete.** Landmarks in handoff or ≤10 lines if
  truly needed.
- **Ablation test:** Strip; can agent still find paper/update paths?
- **Current:** several project AGENTS

### `testing-scientific-failsafe`
- **Description:** Project test gates / layout — values of `git-test`.
- **Suggested delivery:** Not always-on; live with tests / CI. AGENTS only if
  no suite yet (TIGAS gap note).
- **Ablation test:** Same family as `git-test`, in-repo.
- **Current:** all five

### Local run skills

| Concept | Delivery | Ablation |
|---|---|---|
| presley `run-experiment` | Skill | Real vs mock; hash skip |
| pointstream `run-pipeline` | Skill | Stage order / outputs |
| pointstream `train-campaign` | Skill | Detached multi-run |
| 4DGStudy `degradation-pipeline` | Skill | Matrix axes |

### presley — `experiment-result-model`
- Hashed `experiments.yaml` → `results/<hash>/`; skip if done.
- **Delivery:** Skill (`run-experiment`) over AGENTS.
- **Ablation:** Run X twice — duplicate / wrong path?

### presley — `evaluation-methodology` / `hard-rule-fixed-qp-crf` / `reporting-imperceptible-deltas`
- Co-equal goals; degradation fixed QP/CRF not VBR; JND for tiny deltas.
- **Delivery:** AGENTS one-liner for QP/CRF only (silent VBR invalidates
  papers); rest in skill/checklist when touching eval.
- **Ablation:** Designs VBR? Reports noise as gain?

### pointstream — `experiment-methodology-hard-rules` / `architecture-rules` / `weights`
- Residual Guarantee; don’t fork SynthesisEngine; weights via `~/Models`
  symlinks.
- **Delivery:** AGENTS short hard-rule bullets; architecture/weights in
  skill or loaded when touching those paths.
- **Ablation:** Forks engine? Copies weight blobs into git?

### pointstream — `long-training-runs-never-attached`
- Training detach/resume (complements `long-jobs-checkpoint`).
- **Delivery:** Skill (`train-campaign`) + entry_points for soft hook.
- **Ablation:** Attached / no resume?

### MoQSplat — `moq-transport-mapping`
- Importance tiers ↔ MoQ object hierarchy.
- **Delivery:** Skill when touching transport (too dense for AGENTS).
- **Ablation:** Breaks tier invariants?

### MoQSplat — `coding-style` / `gaps-deliberately-left-alone`
- Diet style prose; keep gaps one-liner (no unbidden CI).
- **Delivery:** AGENTS one-liner for gaps; delete/shrink style essay.
- **Ablation:** “Clean up” adds pre-commit?

### TIGAS — `dependency-management-known-gap` / `evaluation-metrics-schema`
- Still on requirements.txt; metrics under `experiment/` + `captures/`.
- **Delivery:** AGENTS gap one-liner until migrated; metrics when touching
  eval (skill or just discover).
- **Ablation:** “Add a dependency” / “Where do metrics for S live?”

### 4DGStudy — `dataset-structures` / `quality-assessment-degradation-matrix`
- `data/3DGS`/`4DGS`; degradation axes.
- **Delivery:** Skill (`degradation-pipeline`).
- **Ablation:** Wrong data root / axis?

---

## Recommended first ablation batch

When a new default model lands, run these first:

1. `tooling-meant-to-evolve` / `where-to-look-for-more` — expect delete
2. MoQSplat `coding-style` volume — expect shrink
3. `paper` thin AGENTS-only vs skills/agent stack — expect thin wins
4. `bound-before-believing` — expect stay omitted
5. `context-nudge` / `candidate-reminders` / `precompact-stub` — tune or quiet
6. `effort-tier-nudge` — drop if unused
7. Anything still in AGENTS that already has a working hook — expect trim

Do not diet first: hard hooks (`guard-destructive-rm`, `wait_loop`,
`guard-model-family`), `git-dev` / `git-test` / `git-prod` (except MoQSplat
CI gap), host-machine atomics that lack hooks, `project-env-and-deps`,
thin `paper` facts, project hard science (fixed-QP, Residual Guarantee, MoQ
mapping).

---

## How to run a concept test (recipe)

1. Pick one **atomic**; write a 5–15 minute task for its failure mode.
2. Arm A: normal toolkit. Arm B: remove that atomic’s delivery. Prefer item
   ablation, not full-toolkit vs empty.
3. Record: success Y/N, failure mode match, parent-transcript tokens, wall
   time, retries.
4. Decision: keep / move delivery up the hierarchy / delete / file
   `candidates/`.
5. Hierarchy reminder: **hook → skill/subagent → AGENTS last**.

Token accounting: platform usage surface when available; else approximate
from transcript size and note it.
