---
name: results-report
description: Summarize or compare a project's run/experiment results (metrics, size/cost accounting, timings) under its results directory. Use when the user wants a table, comparison, or analysis of runs rather than raw JSON.
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

## Where results live

Check the project's `CLAUDE.md` (or equivalent) for the results directory
layout and the output record's schema — field names and the headline metrics
differ per project (this convention has independently reinvented itself with
different specifics per project on this host: payload-size accounting vs.
perceptual-quality metrics vs. something else entirely). Whatever the
project's headline claim is, that's the number to lead with, not whatever
happens to be first in the JSON.

## Workflow

1. If the project has a comparison/report helper (a CLI command, a notebook,
   a `compare`-style module) that already encodes the project's
   citability/JND/significance rules, use it instead of hand-rolling a
   comparison — those rules are usually more specific than they look, and
   re-deriving them by eye is a common source of a misleading table.
2. Otherwise, enumerate candidate runs and their config/metadata, and build a
   comparison table yourself: run identifier, the config delta being
   compared, headline metric(s), any accounting fields, wall time. Use a
   script (python/jq), not eyeballing raw JSON.
3. State the verdict in terms of the project's actual claim (e.g. "does this
   component pay for itself," "is this quality difference perceptible"), not
   just "the numbers went up." Note anything that limits comparability (a
   smoke-test-sized run compared against a full run, a null/missing metric).
4. Compare like with like — same input, same major settings, same seed if
   the project uses one — and say explicitly when you can't guarantee that
   from the summaries alone.
5. Plots/media go to disk (this host is headless) — never assume a display
   is available.
6. If the finding matters beyond this conversation, fold it into the paper
   via the `update-paper` skill, and check the research log's superseded
   registry before citing any pre-existing number.
