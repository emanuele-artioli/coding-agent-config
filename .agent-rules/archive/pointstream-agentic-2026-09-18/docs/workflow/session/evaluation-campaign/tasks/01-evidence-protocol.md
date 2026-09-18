# E01 — Evidence reuse and frozen experiment interfaces

Owner: Cursor. Area: [evaluation](../../../../areas/evaluation.md), with data
protocol changes explicitly included. Ready in parallel with E02.
Scope: manifests, result inventory/adapters, experiment protocol and plot ingestion
interfaces, related tests, evaluation/data areas. Do not edit generator/backdrop
implementations. Publish the proposed contract early for E02; implementations
follow after coordinator acceptance. Budget: initial 4 worker hours; no full runs.

## Work

1. Inventory existing indexes/classifications before inventing one. Inspect
`manifests/candidate_inventory.json`, `manifests/development_recovery.json`,
`manifests/bp46_long_tennis_scenes.json`, `manifests/gate_b_confirmation.json`,
external outputs and `results/` if present, campaign metadata and code readers.
Read structure/provenance first; set bounds before examining headline metrics.
Bounded planning inventory found campaign/bp/timestamp folders, scattered
validity records and superseded reports, but no universal eligibility index.
`candidate_inventory.json` is a backend roster, not a result index; bp26's
classification is config wiring, not evidence validity. Also inspect
`outputs/bp29-panorama/`, `outputs/bp30-background/` mode-comparison and per-video
stream sweeps, and `outputs/bp52-background-crf/background-search.json`; related
bp53 scale/bp56 effort code may cover requested axes. BP30 modes refer to plate
reference policies, not necessarily the three requested representations.
Create a question-to-artifact map: anchors, background removal off/on, generator
trajectories, residual, timing, sources. For each mark reuse, rescore, repair or
new run, with the exact incompatibility. PR #96 introduced the background probe;
#98 is generator diagnostics; #101 repaired the probe. Current probe explicitly
uses a cleaned/filled stack: establish actual saved removal policy before reuse.

2. Preserve immutable evidence and existing classifications. Archive only where
needed for plot discovery, with verified checksums/path mappings and repaired
references; a filter over the existing index may suffice. Separate validity by
claim (RD, runtime, standalone transport, generalization), not one blanket flag.
Missing timing does not invalidate otherwise valid RD evidence. Repaired code
cannot retroactively certify old wire precision or outputs.

3. Freeze source exposure and a development/validation/confirmation manifest.
Audit seven old development sources and the already-scored two confirmation
candidates. Group replays/excerpts by match. Prefer six fresh matches, select the
largest feasible set within deadline, prospectively record a lower count and
small-sample limits. Planning target three; two is restricted confirmation, one
case study. Use `required_matches` in `experiments/tier/protocol.py` through a
versioned policy; inspect callers for hardcoded six before updating. No final
score access during selection. Coordinate exact selected count here before freeze.

4. Specify high/low resolution, fps, valid colour paths, source timestamps,
duration and reconstruction policies from the campaign plan. Define learning
crop resolution separately from displayed output resolution. Include easy and
hard camera/occlusion regimes using metadata, at least one scene per selected
video, preferably multiple separated scenes. Avoid quality-based scene selection.
Register a sustained live/playback test duration beyond initialization, temporal
context and several refresh cycles, with backlog-over-time measurements. Freeze
metric priorities, practical quality floor and latency criterion on
development evidence before evaluating winners; report them here for acceptance.

5. Extend existing result schema with claim eligibility and timing-evidence
references. Record per-host profiling strata and sample counts, uncertainty,
exclusions, timestamps and cold/warm scope. Design reusable plotting ingestion
that emits exclusion reasons, not silent drops; E03/E08 implement the plots.
Provide concrete JSON examples using actual field names, validators and commands,
and a minimal decode/metric/ledger control requirement. Coordinate common runner
interfaces with E02 without editing its files.

## Acceptance

Deliver a compact checked-in reuse/split/protocol manifest with immutable artifact
pointers and per-question gaps; a prospectively configurable source-count gate;
exact operating-point/quality/timebase contracts; and an E03/E04 input manifest.
Demonstrate that a usable old row is retained, invalid evidence is excluded from
the relevant claim, and a missing-timing RD row remains available without gaining
a speed claim. No new benchmark required just to populate a fresh directory.

## Start, validation and return

Read [campaign plan](../plan.md), your named area, and the project
[session workflow](../../SKILL.md). Follow its worktree, ownership, reuse-first,
bounds, per-stage budget, scheduling and return contract. Output root is
`$PS_DATA_ROOT/outputs/evaluation-20260914/<task-id>/<unique-run-id>/`; job records
are under `$PS_DATA_ROOT/jobs/`. These paths are proposed destinations, not
existing evidence. Commit code/docs, run relevant behavior tests and setup
verification plus CI; native paths require a real encode/decode control.
Documentation-only work uses link checks and `git diff --check`. Report exact
validation commands actually run; do not invent working CLI flags in dispatches.
Return here after the bounded assignment; wait for the coordinator's next task.
