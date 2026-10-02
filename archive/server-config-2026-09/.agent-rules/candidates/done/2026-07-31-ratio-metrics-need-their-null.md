---
id: 2026-07-31-ratio-metrics-need-their-null
created: 2026-07-31
source_platform: claude
source_project: /home/itec/emanuele/presley
axis: project
status: applied
summary: A "fraction of oracle/ceiling captured" metric has a floor well above zero — quoting it without its random-selection null overstates the method, and pre-registered bounds can miss this
suggested_action: add to the host-wide experiment-results rule (bound-before-believing section) as a companion to the plausible-range rule
verify_platforms: []
---

## The mistake, made twice in the same project

A selection method was scored by **capture ratio**: bits freed by the top-k items
*by the method's score*, over bits freed by the top-k *by a perfect oracle*. The
figure read 93–99%, and then 0.833 on a re-measurement, and in both cases was
described as how close the proxy is to optimal.

It is not. **Selecting k items at random already captured a mean 0.402** of the
oracle's bits, because the oracle's top-k and a random k overlap substantially
whenever the quantity is not concentrated in a few items. So:

- 0.833 is not "83% of the way to the oracle" — the usable range starts at ~0.40.
- The gap that a better model could close is `1.0 − 0.833`, but the credit the
  model has *earned* is `0.833 − 0.402`.
- On one of eight items the score was 0.510 against its own 0.436 null — i.e.
  **near chance**, while still reading as "51% of oracle", which sounds
  respectable. That item would have been reported as a mild underperformer
  instead of what it is.

## Why the existing discipline did not catch it

This host already has a bound-before-believing rule: state a plausible worst/best
case before looking at the number. That rule was followed here — bounds were
written and committed before any run existed — and it still missed this, because
**the bounds were stated on the metric itself** (`capture in 0.70..0.95`), and
the metric's floor was never questioned. A pre-registered band around a
mis-scaled quantity is still mis-scaled.

## The rule worth lifting

For any metric of the form *"fraction of the ceiling / oracle / upper bound
achieved"*, compute and report the **null**: what a trivial or random policy
scores on the same data. State the metric, the null, and the difference.

Cheap to compute — the random null above is a 2000-sample Monte Carlo over the
same per-item values already in hand, milliseconds — and it changes the reading
of the headline, so it belongs next to the number rather than in an appendix.

Applies beyond capture ratios: any "% of upper bound", "% of headroom claimed",
skill score, or hit-rate-at-k has the same property. A related instance already
recorded in this project: restoration methods were scored on "fraction of oracle
headroom captured", where the same question applies.

Implementation for reference: `tools/analyze_f1_oracle.py` in PRESLEY prints the
null and the margin per item, and flags any item whose margin is under 0.15 as
near-chance so it cannot be quoted as a success.

---

## Resolution — 2026-08-31

**Applied** to `AGENTS.md`, "Control the instrument, then the result", as a
bullet before the instrument-range one: a fraction-of-oracle metric has a floor
well above zero, the 0.402 random-selection null is quoted, the earned credit is
stated as the difference, and the point that pre-registered bounds do not catch
this is kept — that is the part that made the mistake repeatable.
