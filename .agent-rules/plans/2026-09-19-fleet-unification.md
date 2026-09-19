# Fleet unification plan

Prepared 2026-09-19. Planning only: no production stubs, runtime config changes,
merges, or branch deletions are part of this review.

## Decision

Keep PR #23 as the foundation. Repair its installer and validation gaps before
merging it, then land two independently revertible changes: lean junior context,
and reliable completion-boundary knowledge capture. Keep PointStream #136 as a
downstream consumer check. Do not merge every old branch into the current branch.

Use **gpt-5.6-luna / max** for Codex juniors throughout implementation. The parent
keeps interface, scope, integration, and evidence decisions. Other harnesses keep
their in-house model families; this request does not replace them with Luna.

## Reviewed state and findings

Fresh origin/master: `70e429492272976536df05970a2808b394cba1ce`.
PR #23 / org-roles-dispatch: `454b817c432cfb8e5ffc6b316f5be3f3f16ff18d`,
eight commits ahead, open, policy CI successful. It is the repository's only open
PR. The home checkout was clean.
PointStream #136 / host-config-only is open with lint, typecheck, and tests green.
These are snapshots, not guarantees about later heads.

1. **Installer conflict protection is broken for generated Codex files.**
   `scripts/install.py:539-571` writes over any differing regular file, including
   user-owned AGENTS.md or a same-name custom role. A temporary-directory probe
   classified a custom role as stale and then replaced it. Require known ownership
   and an unchanged last-installed digest; preserve edited/unowned files and report
   a conflict. Check mode must not mutate. Also replace the broad “any symlink into
   HOST is ours” test with exact managed destinations/targets.
2. **Role portability currently means text delivery, not equal behavior.**
   `render_codex_agent()` emits name, description, body, model, and effort only.
   Claude's tools, omitClaudeMd, and maxTurns are not translated. Cursor,
   Antigravity, and Copilot receive the same Claude-frontmatter files by symlink,
   including `model: opus`; their handling of those fields must be established.
   Generate native wrappers from shared role content and each platform's rung map.
   Unsupported controls must be visible, not silently described as enforced.
3. **The facts block overclaims guard coverage.** Its statement that hooks deny
   off-family spawns is not established on Codex; its harness explicitly says no
   model-family adapter yet. Pending hook trust/firing cannot support an enforcement
   claim. Keep short behavioral constraints even when a hook also enforces them.
4. **Green CI does not cover all new behavior.** The current workflow checks
   policies, adapter parity, rule generation, dated claims, and guardlib tests.
   It does not run the new lessons/installer/paper-marker suites or verify_roles.
   Extend CI with real collection and nonzero failure exit codes. In particular,
   test_install_plugin.py's direct entry point uses unittest.main(exit=False)
   and then prints “ok”; use a test runner, not that print as evidence.
5. **The closeout trigger is still voluntary.** The session skill says to call
   end-of-session “when the user is done”; that skill says nudges never auto-run it.
   The user’s implicit final-report boundary is therefore not covered.
6. **The workflow documents disagree about composition and authority.** A project
   session skill “wins”, but PointStream delegates common behavior to the host
   session skill. Define extension/composition explicitly. Its area-based handoff
   should not acquire an unwanted root HANDOFF.md. End-of-session's blanket
   ask-before-push also conflicts with existing user authorization; remove the
   redundant approval rule, while retaining genuine platform permission gates.
7. **The context/cost numbers are historical, not acceptance evidence.** Claude's
   fresh-session reduction is still pending. The 100k/five-turn break-even estimate
   came from a specific model and workload; it is not a Luna max routing law.

Checks rerun during this review: verify_roles (22 files, zero failures),
sync_host_rules --check (four files current), installer unittest collection
(two tests), lessons (eight tests), report contract (13 tests). System Python lacks
pytest, so this is not a claim that the whole suite ran locally. No production
installer was run. A new read-only audit was dispatched with explicit Luna/max;
this does not verify generated named-role loading after installation.

## Branch disposition

| Branch/ref group | Evidence | Action |
|---|---|---|
| org-roles-dispatch | Eight unique commits; PR #23 is the only open config PR | Foundation for this plan; repair, validate, then merge. |
| archive/pointstream-agentic-2026-09-18 | One unique archive commit, e8ca1f0; paths are under the restore archive | Preserve as restore-only; do not merge archived project policy into active config. |
| docs/harness-subagent-capabilities | 9c00ca8 and 155b2a8 are not ancestry/patch-id merged; current post-merge hook is byte-identical to 155b2a8. Parallel dispatch is retained in shared policy/harnesses; candidate is explicitly discarded with a recorded rationale | No wholesale merge. Keep evidence. Explicitly document Claude's parallel dispatch in the capability matrix if useful; do not restore stale weaker-model advice. |
| fix/pycache-prefix-in-guard-scripts | Four guard scripts are byte-identical to 9c22b2a; corrected candidate text is byte-identical to e8b7a0e | Functional work preserved; no merge needed. |
| host/multihost-and-shell-startup | Bootstrap preserved and extended; host facts moved into host.md. db55afb's env-based hook delivery is replaced by the later direct-Python plus sys.pycache_prefix mechanism | No merge needed. Preserve the corrected mechanism and host/portable split. |
| Already ancestors of origin/master | antigravity/subagent-ladder-harness; antigravity/verify-and-fix-worktree-cleanup; codex/codex-harness-wiring; cursor/subagent-ladder-harness; fix/cursor-imported-claude-hook-args; fix/multihost-and-login-shell-cost; fix/multihost-local-dirs; lift-portable-fleet; rules/pointers-not-copies; verify/cursor-host-2026-08-31 | Already integrated; no content to merge. Remote branches remain untouched. |
| Local 2026-09-18-orchestrator-and-host, antigravity/subagent-ladder-harness, cursor/subagent-ladder-harness, master | All are ancestors of origin/master; master equals origin/master | No unique local work found. Retain unless separately retired under the branch policy. |

The three historical branches above show `+` in git cherry; they are not exact
whole-commit patch matches. “No functional merge needed” rests on targeted diffs
and moved/replaced-hunk evidence, not on branch age. Do not call them merged or
delete them. No active feature was found that requires merging these old tips.

## Junior context: what to remove and what to retain

Aim for **a small role contract plus a complete task brief**, not literally only
the parent's prompt. System instructions, managed policy, permissions, and required
tool schemas remain. A prompt telling an agent to ignore already-loaded context
does not recover tokens. A shell-only agent is also not a filesystem sandbox.

| Harness | Established control | Plan / uncertainty |
|---|---|---|
| Claude Code | omitClaudeMd omits user/project/local rules; tools limits the tool surface; skill preloads are explicit | Fresh-process probe is required. Managed policy remains. Keep Skill and irrelevant MCP tools out of bounded roles; verify what catalog remains. |
| Codex | This task's spawn API supports fork_turns=none; native role files can configure skills and MCP settings | No-history is not no-AGENTS. Probe project_doc_max_bytes and other documented controls in an isolated child configuration; do not claim a universal omitAGENTS switch. Preserve parent config and mandatory instructions. |
| Cursor | Fresh child conversation and native model/readonly controls are documented | Do not equate a fresh conversation with absence of user/project rules. Do not assume Claude frontmatter controls the tool surface. Native-app and SDK controls are separate capabilities. |
| Antigravity / Copilot | Shared files are delivered by the installer | Require native schema and live discovery/control probes; retain normal context when omission is unsupported. Do not infer capabilities from Claude. |

The senior assembles the brief from canonical rules, scoped to allowed paths and
the task. Include: outcome and exclusions; exact checkout; allowed files; interface
invariants; relevant project constraints; environment/test command; evidence and
acceptance criteria; budget; report and stuck contracts. Relevant rules include
dependency management, sqlite-before-torch, external data locations, paper evidence
requirements, or checkpoint/resume requirements only when the task needs them.

Always retain: respect allowed paths and concurrent work; no child git operations;
do not invent results; stop and report missing inputs or conflicting requirements;
do not relax guards/permissions to make a check pass. If unexpected files are
needed, return the gap to the senior. Removing project instructions without carrying
their applicable invariants is a correctness regression, not an optimization.

Generate compact shared core and optional host/task facts from canonical sources.
Do not maintain an expanding hand-copied universal facts block in every role, or
make the parent reconstruct safety rules from memory. Do not send senior-only
planning, promotion, PR, and session-management procedures to a bounded child.

Reuse a successful child for analysis then implementation in the same area, at the
same model/effort, with an explicit scope/budget extension. Start fresh for a new
area or an escalation after failure. The existing skill does not yet encode this
reuse rule even though Claude's report recommended it.

### Savings and measurement decision

Claude's reported baseline was roughly 40–42k initial tokens, with 47% in schemas
and 15% in imported rules. As arithmetic on that report, those categories total
about 25–26k tokens; they cannot all disappear because some tools and constraints
remain. The recorded <=19k target, or <=11k if the skill catalog also disappears,
is an unverified hypothesis. Do not transfer it to Codex or count cached input as
free context. Do not promise “prompt only” or a universal savings percentage.

Before measuring, register these expectations: initial context stays positive;
lean/control ratio plausibly 0.25–1.10, with any increase investigated and <=0.50
only an aspirational Claude target. Quality remains within [0,1] and every mandatory
constraint fixture must pass. End-to-end time and total tokens may worsen through
extra reads/retries; record them and reject an optimization that merely shifts
startup savings into rework. Out-of-range readings are alarms, not successes.

Compare fresh normal-role and lean-role sessions on identical small tasks; change
one control at a time (history, rules, tools/MCP, skills, task brief). Include an
unchanged-control repeat and harmless marker rules to detect whether omitted text
still arrives. Record harness/build, actual model/effort, loaded tools/skills/rule
sources, uncached/cached input separately, task tokens, accepted outcome, violations,
retries, and elapsed time. Sum provider fields only according to that provider's
usage semantics. Report unavailable telemetry as unavailable.

Start with a smoke pair per available harness. Broader cost/quality claims require
at least eight paired representative tasks, all observations, and uncertainty;
reuse existing artifacts only if configuration identities match. No quality winner
or fixed junior break-even from a handful of successful probes. Prefer the least
context that passes the task and constraint checks, not the smallest token count.

## Who records lessons and when

Today the **parent session** writes candidates when it invokes end-of-session;
lessons.py searches/updates them, reminders count them, and evaluate-candidates
applies/discards/defers them. Neither reminders nor the ledger discover lessons.
Keep the parent responsible for semantic judgment. Juniors return potential lessons
as evidence; they should not race to write the shared queue themselves.

Keep one candidate ledger, including first observations. Add a small deterministic
CLI for storage and lifecycle bookkeeping, using lessons.py rather than creating a
second knowledge database. Keep a short skill for deciding what was learned. Use
verified hooks as a backstop; a hook should not launch a separate LLM to interpret
every reply or silently promote rules.

### Proposed end-of-session behavior

1. **Recognize a boundary before the final report.** Explicit wrap-up, requested
   handoff, completed work with a closing report, or a deliberate blocked transfer
   triggers capture. Progress updates, ordinary factual replies, clarification
   questions, approval waits, compaction, and child reports do not close the task.
   A planned subtask finishing is not completion of the user's larger objective.
2. **Snapshot current state once.** Record branch/commit, relevant dirty paths,
   checks, unresolved decisions, and owned running jobs. Never infer idle resources
   from elapsed time or kill jobs during capture.
3. **Review only the uncaptured work.** Parent considers project and platform
   lessons. Match the ledger, inspect candidate matches, then record a first
   observation or a new occurrence with evidence and provenance. No lesson is a
   legitimate outcome; record a lightweight closeout receipt, not an empty candidate.
4. **Make capture idempotent.** Key the receipt by repo identity, session/task ID,
   and completion boundary/revision. Use a stable event ID for each observation.
   Repeated Stop/handoff calls for the same event must not increment occurrences.
   A later independent incident must increment them, even in the same task.
5. **Diagnose recurrence before promotion.** Was the lesson unapplied, never
   loaded, stale, ineffective despite loading, or actually a different problem?
   Preserve previous status and application provenance. Promote only when evidence
   supports it. Keep project-only knowledge local until cross-project applicability
   is established; prefer deterministic enforcement when feasible.
6. **Persist continuation where the project expects it.** Update existing area
   state/handoff conventions. Use HANDOFF.md only where appropriate. Handoff and
   end-of-session call the same capture routine without recursive invocation.
7. **Finish authorized repo actions separately.** Capture grants no new authority.
   Commit only session-owned changes and use existing push/PR authorization. Do
   not stage all files, auto-merge because Stop fired, retire a possibly paused
   worktree, or make changes to another harness's live config.
8. **Report the result.** Say what is complete, checked, still running or open;
   mention lesson capture only when useful. The final report remains the user's
   deliverable, not an extra administrative report.

On a supported Stop event, check for an uncaptured completion boundary and request
at most one recovery continuation. Guard re-entry and concurrent events. Stop is
normally a turn boundary, not proof of session completion. Unsupported hooks stay
explicitly unsupported; the senior's pre-final procedure is the portable baseline.
On crash or forced termination, leave a pending receipt for the next session to
review. Do not fabricate lessons from missing context. SessionEnd can flush existing
state where supported, but cannot reliably ask a terminated model to reflect.

The audit found that lessons.py record unconditionally increments an occurrence,
selects the first matching ID, and writes the destination without locking or
collision protection (scripts/lessons.py:139-173). Replaying two identical record
calls against a temporary first-observation candidate produced occurrences: 3.
Existing eight tests pass but do not cover this replay. Concurrency and interrupted
writes are design risks identified from the implementation, not reproduced live
failures. Add event identity, duplicate-ID/axis validation, collision rejection,
serialized atomic updates, and crash recovery before enabling automatic capture.

## Interfaces to settle before implementation

Write signatures/docstrings in actual source files only when implementation begins.
Freeze these contracts before juniors fill bodies:

- Role rendering: shared role + harness capabilities + rung + scoped facts ->
  native artifact and explicit unsupported-control diagnostics. Installation checks
  ownership/digest and does not replace user modifications.
- Dispatch brief validation: required seven fields plus relevant constraints under
  read-first/goal; fail with named missing fields. Validation cannot establish that
  an LLM selected all semantic constraints; the senior owns that review.
- Observation storage: candidate identity + event ID + project/platform provenance
  + evidence -> created/recorded/already-recorded result. Atomic locked updates,
  stable identity across renames, deterministic duplicate handling, recoverable
  migration of legacy files, no silent duplicate-ID selection.
- Closeout: boundary input + task state + proposed observations -> receipt and
  pending/completed status. Mark complete only after all writes succeed. Retry
  after interruption must not lose or double-count observations. Keep operational
  receipts separate from candidate content and outside automatically loaded rules.
- Hook adapter: real harness payload -> normalized event -> shared policy result;
  unsupported fields/events produce diagnostics, not invented capability claims.

## Implementation waves

Each writer gets its own branch/worktree. Coordination docs land on the shared
integration branch before dispatch. Every prompt supplies the session skill's
seven fields, exact ownership, runnable check, and a bounded budget. No child git
operations. Budget initial lanes to 12 minutes/15 tool calls, then deliberately
split or extend a successful same-area child if needed. No blind retry loops.

| Wave | Owner and allowed area | Work and acceptance |
|---|---|---|
| 0: foundation | Senior | Refresh PR heads; freeze interfaces and capability statuses. Keep #23 as base. Record branch dispositions. Amend shared contracts and the test list before dispatch. |
| 1A: safe installation | Luna max, scripts/install.py and its tests | Preserve unowned/modified role/rule files, exact link ownership, atomic write and check-only behavior. Run installer tests against temporary homes and both host/no-host configurations. |
| 1B: ledger correctness | Luna max, scripts/lessons.py and its tests | Stable event dedup, status history, scope-aware matching, concurrency/recovery, first observation insertion. Run lessons tests, including replay and concurrent writers. Independent of 1A. |
| 1 integration | Senior | Re-run both suites. Wire role/installer/lessons/paper-marker checks into CI with managed test dependencies. Fix #23 claims and documentation. Merge #23 only after this foundation is green; do not wait for speculative context targets. |
| 2A: lean native roles | Luna max, role wrappers, generator extension and role tests | Generate each supported harness wrapper from common role text; Codex Luna/max. Distinguish supported from unverified/unsupported controls. Snapshot/parse outputs and run strict role validation. Depends on 1A. |
| 2B: completion core | Luna max, new closeout module/tests | Deterministic boundary receipts, observation transaction, no-lesson receipt, replay/recovery. Run completion behavior/misuse tests. Depends on 1B. Independent of 2A. |
| 3A: lifecycle adapters | Luna max, stop/continuity adapters and adapter tests | Wire completion core only into verified event contracts, with recursion/rate limits. Payload fixtures plus live owned-harness probe. Depends on 2B. |
| 3B: policy and workflow | Senior | Compose project/host session behavior; update session/end-of-session/handoff/evaluate-candidates and dispatch reuse rules. Update JUNIOR-FACTS sourcing, README, enforceable register, generated docs. Resolve shared-file overlap after 2A. |
| 4: evidence and rollout | Senior, bounded Luna max measurement helper if useful | Fresh-process model/context probes, constraint fixtures, matched acceptance/time/token evidence. Install only the current harness's owned config; other harness owners close their own pending-verification rows. |
| 5: downstream and retirement | Senior | Recheck PointStream #136 preconditions and area-workflow composition, then evaluate its merge separately. Re-read status docs after merges. Retire merged clean worktrees only when not paused; retain restore archive and do not delete remote branches. |

The plan has three logical delivery units: repaired #23 foundation, lean roles,
and automatic closeout. Use one PR per independently revertible unit, not per
junior or per file. Context and closeout units may proceed in parallel after the
foundation. Never let a child directly rewrite a shared interface.

### Required test cases

- Installer: unowned file, modified generated file, known/unknown symlink, stale
  managed artifact, no-op rerun, check mode, missing target directories, portable
  generated output, host overlay absent, valid TOML with quotes/backslashes.
- Roles: correct family/model/effort per harness, Luna max rather than silent xhigh
  fallback, no stale legacy shadowing, omitted unsupported keys, relevant facts
  retained, generated output drift caught. Runtime discovery is a separate check.
- Ledger: create first observation; repeat same event; independent repeat; reopened
  applied/discarded/pending entry with previous state retained; same symptom in
  different scopes; duplicate IDs; malformed legacy metadata; concurrent updates;
  interrupted rename/write; match ties. Review semantic matches rather than choosing
  the largest lexical score automatically.
- Closeout: explicit end, implicit completed report, requested handoff, blocked
  transfer, no lessons, continued work after completion, repeated Stop, child report,
  progress reply, user question/approval wait, abrupt exit, pending jobs, hook re-entry,
  failure between recording lessons and receipt completion, unavailable hooks.
- Deliberately not tested: third-party model internals, byte-exact natural-language
  summaries, hypothetical unreachable errors, or a universal token floor. Behavioral
  fixtures validate our contracts; live probes establish actual harness behavior.

Do not mark a wave retired while its worktrees remain unaccounted for. Preserve a
worktree that hosts paused work and report why; human confirmation is required for
its removal. Never use force, rm -rf, or remote deletion for cleanup.

## PointStream boundary

Keep #136 separate. Its deletion of redundant roles is sensible once host roles
are demonstrably usable. Green codec tests do not prove Cursor's User Rule or
Codex global role discovery. Confirm both preconditions from the PR, plus a real
spawn in a session with no project role table. Do not remove legacy global roles
until that check succeeds. This review does not certify the archive's byte identity;
verify its manifest before any future destructive retirement. Keep paper-marker
failures outside this config plan except as explicitly tracked downstream work.

## Sources

- [Config PR #23](https://github.com/emanuele-artioli/coding-agent-config/pull/23)
- [PointStream PR #136](https://github.com/emanuele-artioli/PointStream/pull/136)
- [Claude subagents](https://code.claude.com/docs/en/sub-agents): rule omission,
  tool access, inherited context, and skill loading.
- [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents):
  native role schema, override precedence, skill/MCP settings.
- [Codex configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference):
  project_doc_max_bytes is a byte cap, not proof of complete rule omission. Its
  public effort enum lags this task's max-capable spawn API; verify the installed
  parser and actual runtime before claiming generated Luna max profiles are live.
- [Cursor subagents](https://cursor.com/docs/subagents): fresh contexts, native
  fields, inherited tools. This does not establish omitClaudeMd support.

All external capability sources were opened on 2026-09-19. Pending native behavior
must be measured in that harness; sharing a Markdown file is not proof of parity.
