---
name: figure-first
description: The senior's procedure for building a results figure or table from the claim backwards, before any data is read. Use when a results subsection needs writing, when a HOLE names a figure or table, or when the human asks what the runs show. Produces a figure spec with pre-stated bounds, a condensed CSV with the script that made it, and a plot on disk. The decision rule is written before the numbers arrive, so a disappointing result still has an action.
---

# Figure first, data second

You are the senior. You name the figure and the bounds; juniors pull
numbers into the shape you named. Dispatch through the `session` skill's
seven-field contract.

## Procedure

1. **Name the figure before the data.** The claim it supports, in one
   sentence. Axes with units. Groups. The comparison it must make
   visible at a glance. If you cannot write the claim, there is no
   figure yet, only curiosity.

2. **Write the data shape.** Column names, what one row is, units per
   column, and n per group. This is the contract the junior fills.

3. **Inventory the evidence you already have.** Which run directories or
   result files could supply each column. Check citability or invariant
   verdicts where the project records them. Reuse and rescore before
   launching anything new: a newer code fix does not certify old
   evidence, and missing timing alone does not justify rerunning a
   finished rate or quality measurement.

4. **Pre-state bounds for every column**, each with a one-line basis:
   prior runs on this project, a published baseline, a hard metric
   range, or a trivial baseline. Write them into the dispatch. Juniors
   never invent bounds. See `results-report` for the bound procedure.

5. **Write the decision rule before the data.** What the figure shows if
   the hypothesis holds, what it shows if it does not, and the action
   for each case: pivot the claim, scope the claim to the regime where
   it holds, or run the smallest new probe with its own budget.

6. **Dispatch `data-condenser`** with: the figure spec, the data shape,
   the run list, the bounds, the output path for the CSV, and the output
   path for the script that produces it.

7. **Intake.** Re-run the junior's script yourself, one call. Every
   `ALARM` in its report is yours to close before the number is used
   anywhere. Run `verify-measurement` before stating that one arm beats
   another.

8. **Plot.** Write the plotting script yourself, or dispatch
   `implementer` with the CSV path and the figure spec. Plots are saved
   to disk; this host is headless and nothing renders to a screen.

9. **Land it** with `paper-outline` or `update-paper`, clearing the
   `HOLE` and writing its `CLAIM` line in the same edit, so the figure
   and the sentence it supports never drift apart.

## Never

- Read raw result JSON yourself to save a dispatch.
- Let a junior widen the run list beyond what you named.
- Treat a run with no citability verdict as clean.
- Launch a new run when a rescore of saved outputs answers the question.
