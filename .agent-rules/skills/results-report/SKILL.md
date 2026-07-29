---
name: results-report
description: Summarize or compare a project's run/experiment results (metrics, size/cost accounting, timings) under its results directory. States plausible best/worst bounds before trusting headline numbers and alarms on out-of-range values. Use when the user wants a table, comparison, or analysis of runs rather than raw JSON.
---

# Summarizing results

## Check the citability verdict before reporting anything

**A run/result whose citability check fails (or whose `invariant_failures`-
style field is non-empty) is not citable.** That field records that the run
itself is unsound, not that its numbers merely look odd — a fallback to mock
data, an evaluation that didn't complete, an accounting that doesn't sum, a
transported/output size larger than the source. Such a run still writes a
perfectly well-formed summary, which is exactly why the check exists.

Exclude those runs from tables and comparisons, and say which ones you
dropped and why, rather than silently omitting them.

A run with **no** verdict field at all predates the check and has never been
evaluated — treat a missing verdict as unverified, not as clean. If the
project has a backfill command for this, run it before relying on older
runs.

## Bound the headline metrics before believing them

Citability catches *recorded* methodology failures. It does not catch a
plausible-looking wrong number from a broken metric path. Before reading or
tabulating headline metrics:

1. State a **plausible worst-case and best-case** for each headline metric,
   with a one-line basis (prior runs on this project, paper / published
   baselines, hard metric bounds like [0,1], or a trivial baseline such as
   encode-nothing / random / identity). Prefer bounds carried from the
   launch prompt or an earlier message over inventing them after the fact.
2. **Write the bounds before looking at the observed values.** Post-hoc
   "that's still plausible" is the failure mode this check exists to stop.
3. If any observed value falls **outside** that range: treat it as an
   **alarm**, not a finding. Say so explicitly, exclude the run from clean
   tables/comparisons (or mark the cell as out-of-range), and investigate
   implementation / eval / data bugs before anything else. Do not fold the
   number into the paper via `update-paper` until the alarm is closed or the
   bounds are explicitly revised with a reason.
4. If the launch never stated bounds and you are only summarizing old runs,
   derive them from the project's standing results / research log / prior
   comparable runs *before* opening the new summary JSON — and say that you
   did.

## Where results live

Check the project's `CLAUDE.md` (or equivalent) for the results directory
layout and the output record's schema — field names and the headline metrics
differ per project (this convention has independently reinvented itself with
different specifics per project on this host: payload-size accounting vs.
perceptual-quality metrics vs. something else entirely). Whatever the
project's headline claim is, that's the number to lead with, not whatever
happens to be first in the JSON.

## Workflow

1. State worst/best-case bounds for the headline metrics (see above) *before*
   opening the run summaries you are about to trust.
2. If the project has a comparison/report helper (a CLI command, a notebook,
   a `compare`-style module) that already encodes the project's
   citability/JND/significance rules, use it instead of hand-rolling a
   comparison — those rules are usually more specific than they look, and
   re-deriving them by eye is a common source of a misleading table.
3. Otherwise, enumerate candidate runs and their config/metadata, and build a
   comparison table yourself: run identifier, the config delta being
   compared, headline metric(s), any accounting fields, wall time. Use a
   script (python/jq), not eyeballing raw JSON.
4. Drop or flag citability failures and out-of-range alarms before stating a
   verdict. State the verdict in terms of the project's actual claim (e.g.
   "does this component pay for itself," "is this quality difference
   perceptible"), not just "the numbers went up." Note anything that limits
   comparability (a smoke-test-sized run compared against a full run, a
   null/missing metric).
5. Compare like with like — same input, same major settings, same seed if
   the project uses one — and say explicitly when you can't guarantee that
   from the summaries alone.
6. Plots/media go to disk (this host is headless) — never assume a display
   is available.
7. If the finding matters beyond this conversation, fold it into the paper
   via the `update-paper` skill, and check the research log's superseded
   registry before citing any pre-existing number. Never cite an open
   out-of-range alarm.
