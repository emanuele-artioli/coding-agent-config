# W5 — PointStream vs host SoT alignment

Read `README.md` in this folder first. Wait to **write** PointStream until
W1 (and ideally W2) have landed host policy. You may **read** PointStream
immediately.

## Job

PointStream’s project guidelines already describe an orchestrator: parent
plans, bounded children, acceptance checks, escalate on a **fresh** child,
parent keeps integration. That is closer to the 2026-09-18 user intent
than coding-agent-config’s last session (`review-fix` everything).

The **ladders** are not aligned with the locked model facts:

| Place | PointStream today | Locked 2026-09-18 |
|---|---|---|
| Cursor | Composer 2.5 → Grok 4.6 **low** | Grok 4.6 always; medium default; optional high |
| Antigravity | Flash **low** → Flash **high** | Flash **medium**; optional high |
| Codex | Luna/medium → Terra/medium → Sol/medium | Sol parent; Luna **xhigh** children; rare Astra |
| Claude (session skill) | haiku/sonnet, avoid opus | Opus 5 medium; do not use Sonnet |

Also: PointStream forbids `scripts/cleanup_merged_worktrees.sh` until
`INFRA-ACT-01`. Host now has `git-clean-merged-worktrees`. W3 owns the
safety question; you apply the project-side pointer once W3 reports.

## Read first (PointStream)

- `AGENTS.md` (host pointer + Subagents section)
- `docs/workflow/session/SKILL.md`
- `.cursor/agents/budget-default.md`, `expert-retry.md`
- `.agents/agents/` copies
- `.codex/config.toml` profiles
- `docs/workflow/session/subagent-ladder-trial.md` (trial profiles are
  **not** the production ladder — do not promote them to the host)
- Paper repo `67a9ea6275d3d9785ce57026/AGENTS.md` only if a host rule
  duplicated paper science (it should not)

Host side after W1/W2:

- `.agent-rules/effort-models.json`
- `skills/model-routing/SKILL.md`
- `harness/*.md` subagent sections
- host `AGENTS.md` orchestrator paragraph

## Alignment direction

- **Host learns structure from PointStream** (dispatch prompt: goal, allowed
  files, acceptance check, stuck rule; parent does not hold child traces).
- **PointStream learns model facts from host** (slugs, no Composer rung, no
  Sonnet-as-default, Codex Sol/Luna/Astra).
- Do not copy PointStream science, PLAN.md, or area docs into the host.
- Do not copy host NFS essays into PointStream; it already `@`-imports
  host `AGENTS.md`.

## Conflict to resolve in the write-up before editing

PointStream “cost-first” means start cheap, escalate after a failed
check. User now wants the **parent** on the capable default (Sol / Grok /
Flash medium / Opus) and children on the volume model (Luna xhigh / Grok /
Flash), with Astra only when stuck. That is not the same as
budget-default → expert-retry. Rename or retarget those profiles so names
still match what agents spawn, or replace the two-rung files with
task-class files. Do not leave both stories in `AGENTS.md`.

## Touch these when applying

PointStream only:

- `AGENTS.md` § Subagents
- `docs/workflow/session/SKILL.md` harness capability bullets
- profile files / `.codex/config.toml`
- maybe a one-line pointer to host `model-routing` instead of duplicating
  the procedure

Host only if you find a PointStream rule that all projects need: file
`candidates/open/project/` — do not silently lift.

## Done when

PointStream’s dispatch story and the host’s `effort-models.json` name the
same models and the same escalate-when-stuck rule. Trial profiles remain
clearly trial-only. No second host-rules copy inside PointStream.
