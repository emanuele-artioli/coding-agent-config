---
id: 2026-08-02-pre-registered-bounds-two-sided-and-how-to-close-an-alarm
created: 2026-08-02
source_platform: claude
source_project: /home/itec/emanuele/presley
axis: project
status: applied
summary: Pre-registered bounds must be two-sided on the quantity under test, and the cheapest way to close a fired alarm is to reproduce a landed number with the new analysis path
suggested_action: amend the existing "Experiment results — bound before believing" rule in AGENTS.md with both points; they are refinements of a rule that already exists and already paid off
verify_platforms: []
---

Two refinements to the existing host-wide **"bound before believing"** rule,
both learned from a wave where three of four pre-registered bound sets fired.

## 1. Do not pre-register a one-sided band on the quantity under test

A bound was written as `−25 … +5%` with the alarm text *"< −40% (too good;
suspect a rate-accounting error)"* — i.e. it anticipated only the failure mode
where the method looks **better** than expected. The measurement came back at
**+34%**, off the other end, and the pre-registered alarm text pointed at the
wrong thing to check.

The band had been derived from the two subjects the experiment existed to
generalize *past*. It therefore encoded the assumption under test as if it were
a bound, which is exactly backwards: the experiment's whole purpose was to find
out whether that assumption held.

**Rule:** when the bound is on the very quantity the experiment exists to
generalize, write it **two-sided and wide**, or leave it un-banded and say why.
Bounds derived from the incumbent cases are fine for *sanity* (orders of
magnitude, metric limits) but must not be narrow around the incumbent result.

## 2. Closing a fired alarm: reproduce a landed number with the new path

The rule says a fired bound is an alarm and implementation / eval / data bugs
must be investigated *before* the result is reported. It does not say how, and
the obvious approach — auditing the new analysis code — is slow and
inconclusive.

**The fast discriminator: run the new analysis path over the OLD data and check
it reproduces an already-published number.**

Here that closed two separate alarms in one command each. The new BD-rate tool
reproduced the paper's landed figures exactly (−28.87%, −16.1%, +80.9%,
+27.5%) on the incumbent videos, which ruled out the analysis in one step and
left the new measurement standing as a real result. A second cheap check —
billing the rate two different ways and getting identical answers — ruled out
the other suspected axis.

**Rule:** before doubting new data, reproduce a landed number with the new
tool. If it reproduces, the tool is not the explanation and the alarm is a
finding. This also has the side benefit of validating the tool for its intended
use at the same time.

## 3. Check a bound at the operating point its own text names

A bound specified *"at matched rate"* was first checked at fixed QP. Those are
different quantities — at fixed QP the two arms sit at different bitrates, so
the gap mixes the effect under test with whatever the treatment did to the rate
axis. Checked wrongly it read 0.88–1.20 (apparent alarm); checked correctly,
0.57–0.86 (inside the alarm threshold). Read the bound's own wording for the
operating point, and compute *that*.

---

## Resolution — 2026-08-31

**Applied** to `AGENTS.md` as a second paragraph under "Experiment results —
bound before believing", carrying all three points: two-sided bands when the
bound is on the quantity the experiment exists to generalize past; reproduce a
landed number with the new analysis path as the cheap way to close a fired
alarm; and check a bound at the operating point its own wording names.
