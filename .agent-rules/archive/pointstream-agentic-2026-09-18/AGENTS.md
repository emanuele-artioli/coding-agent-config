# POINTSTREAM — Rules of Engagement

PointStream is an object-centric semantic video codec where every component is a config choice. The encoder transmits each salient object's appearance and motion plus a reusable background model and an optional corrective residual; the client reconstructs frames generatively or from references. Target: an ACM TOMM submission, **30 September 2026**.

## Host Rules

This file is the single source of truth for this project's agent rules. Host-wide rules are not copied here; they live in one file on this machine:

@/home/itec/emanuele/.agent-rules/AGENTS.md

Follow that file for every session. Harness-specific mechanics:
- Cursor: `@/home/itec/emanuele/.agent-rules/harness/cursor.md`
- Antigravity: `@/home/itec/emanuele/.agent-rules/harness/antigravity.md`

The paper lives in `67a9ea6275d3d9785ce57026/`, a **separate git repo** with its own `AGENTS.md`. Commit there when you change manuscript text.

---

## Where Things Are

| Need | Read | Write / Update |
|---|---|---|
| Current assignment | [PLAN.md](PLAN.md) and one linked area | That area's state/actions; [PLAN.md](PLAN.md) only if summary changes |
| Gate dependency | [docs/roadmap.md](docs/roadmap.md) | [docs/roadmap.md](docs/roadmap.md) only when dependency or pass criteria changes |
| Prior decision / failure | Area evidence links, history indexes, PR discussion | PR for session detail; [docs/history/findings.md](docs/history/findings.md) for validity |
| Component behavior | `src/contracts/` and relevant code/tests | Code/contracts/tests in the owned scope |
| Human setup / run | [docs/setup.md](docs/setup.md); [README.md](README.md) for user flow | [README.md](README.md) / [docs/setup.md](docs/setup.md) alongside behavior changes |
| Research evidence | Area protocol and immutable outputs | Run records; area verdict; PR provenance |
| Paper claim | [docs/areas/paper.md](docs/areas/paper.md) and paper `AGENTS.md` | Separate paper commit; evidence references back in paper area |
| Dispatch / report / closeout | [docs/workflow/session/SKILL.md](docs/workflow/session/SKILL.md) | Prompt in response; PR report; durable area update |

---

## Rules That Code Cannot Enforce

- **The paper's headline claims must land where PointStream wins.** A codec paper whose central result is "we lose to the anchor everywhere" is not a submission. Finding and naming the regime where an object-centric codec beats conventional coding is part of the work. Scope headline claims to the regime where they hold.
- **Searching for the winning configuration is the method, not a compromise.** Run the axes, observe the numbers, and locate where PointStream wins. The obligation is to report the search transparently: say which axes were tried, what each gave, and where the claim boundary lies.
- **Bound before believing.** Before reading any measured result, write down a plausible best and worst case with rationale. A result outside that range is an alarm: investigate the measurement instrument before reporting the number.
- **A flag existing is not a feature working.** Encoders accept options and ignore them. Before relying on any capability, drive it and measure that the output changed in the way claimed.
- **Every result carries all three dimensions: size, quality, and speed.** Not two of them. A configuration that is cheaper and better but ten times slower to encode is a different result from one that is as fast; a table omitting runtime cannot distinguish them.

---

## Task Completion and Setup

For dispatch, completed work, or handoff, read and follow the [session workflow](docs/workflow/session/SKILL.md). It owns PR reporting, area updates, validation, and worktree retirement; ordinary replies do not require a closeout.

Use [docs/setup.md](docs/setup.md) before environment setup or experiment runs, and its verification section before merging. Host-wide cache and import-order rules remain in the host rules above.

Project constraints: data must stay outside the code tree (no `assets/` or `outputs/` symlinks); record the exact native encoder/decoder paths and versions with each run so comparisons are reproducible. Do not run `scripts/cleanup_merged_worktrees.sh` (`INFRA-ACT-01`: its `rm -rf` fallback can discard uncommitted work). Merged-and-clean worktrees: host `git-clean-merged-worktrees` only.

## Subagents

The parent coordinator delegates bounded parallel lanes by default. It keeps
integration, shared-contract changes, and the hardest scientific or
architectural judgment. It does not use demo trial profiles for codec,
evaluation, paper, GPU, or shared-contract work.

Children get a goal, allowed paths, and a success check they can run alone.
They return a short report. If they are out of ideas they return
`STUCK: out of ideas.` plus what they tried. Escalate on a **fresh** child;
do not resume to change model. Verify the runtime model (and, on Codex,
effort and permission metadata) before accepting a child result.

**Codex** — profiles in `.codex/config.toml`: `budget_default` (Luna /
extra-high) for ordinary children; `expert_retry` (Astra / low) only after
`STUCK` or a failed check. Trial `trial_a_*` profiles stay trial-only.
Pass both model and `reasoning_effort`.

**Cursor** — profiles in `.cursor/agents/`: `budget-default` (Grok 4.6
medium) then `expert-retry` (Grok 4.6 high) after stuck/failed check.
Spawn by `subagent_type` and omit `model`. Grok effort is the slug
(`cursor-grok-4.6-medium` / `-high`).

**Antigravity** — profiles in `.agents/agents/`: `budget-default` (Gemini
3.8 Flash / medium) then `expert-retry` (Flash / high). Spawn by
`TypeName`. There is no 3.8 Pro.

**Claude** — `Agent` children use Opus medium. Do not pick Sonnet.

Host slug map: `/home/itec/emanuele/.agent-rules/effort-models.json` and
skill `model-routing`. Do not run `scripts/cleanup_merged_worktrees.sh`.
Merged-and-clean linked worktrees: host `git-clean-merged-worktrees`
(refuses dirty trees). Ask before removing a worktree that might be a
paused session. `INFRA-ACT-01` still applies to any script that can
discard uncommitted work.

For eligible real demo tasks, follow the automatic two-day, 24-card randomized
trial in [subagent-ladder-trial.md](docs/workflow/session/subagent-ladder-trial.md).
