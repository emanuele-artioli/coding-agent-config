---
name: test-design
description: Propose, then write, the tests for a component you added or changed — behaviour cases, plausible-misuse cases, and an explicit list of what is deliberately not tested. Use after writing or modifying anything under a project's source tree, and as the test step of a refactor PR. Surfaces the proposed list for approval before writing any test code.
---

# Designing tests for a component

The goal is a small number of tests that would actually fail if the code
broke, not coverage. On research code especially, a test that cannot fail is
worse than no test — it makes the suite look like it is watching something it
is not. If the project's `CLAUDE.md` names a coverage gate or a threshold,
read it before starting — the workflow below assumes there is one and that it
exists to catch untested code arriving unnoticed, not as a target.

## Workflow

1. **Read the change.** `git diff` for uncommitted work, or read the module.
   Identify what the component promises: its inputs, its outputs, and the
   invariants a caller relies on.

2. **Draft the list, in three groups.** Most components deserve 3–8 tests.

   - **Behaviour** — the envisioned cases, with expected values you can state
     by hand. A closed-form computation gets a hand-computed case; a mapping
     gets its boundary values.
   - **Plausible misuse** — what a caller in *this* repo could realistically
     do wrong (an empty/malformed input, a mismatched dimension, a config key
     naming a backend that doesn't exist). Prefer mistakes that would produce
     a *plausible-looking wrong number* over ones that just raise — only the
     first kind survives to be silently cited later.
   - **Deliberately not testing** — say what you're leaving out and why:
     unreachable branches, third-party library behaviour, errors a caller
     cannot produce, and anything whose only effect would be moving the
     coverage number.

3. **Show the list to the user before writing any test code.** Number the
   items so they can say "drop 3, add one for X." Don't skip this even when
   the list looks obvious — the user knows failure modes the code doesn't
   show.

4. **Write only the approved tests**, then run the project's test command and
   report the result and the coverage delta.

## What makes a test worth writing

Ask: *what would have to break for this test to fail, and could that
plausibly happen?* If the answer is "nothing realistic," drop it.

The category worth hunting for is the **silent wrong answer**, not the crash
— a result that looks fine, passes review, and gets cited, while actually
violating whatever the project's core claim or invariant is (check
`CLAUDE.md`/`RESEARCH_LOG.md`/equivalent for what that invariant is on this
project — e.g. a payload-size accounting that doesn't sum, a quality metric
of `null` passing as a real result, two code paths that could disagree when
they're required not to).

## Which tier the test belongs in

If the project defines test tiers (check `CLAUDE.md`/`pytest.ini`/CI config),
use them; a common shape that has worked well across projects on this host:

- **Unit** — pure logic, mocks for anything heavy, CPU only. Runs on every
  push, no marker.
- **Integration** — needs real weights, a dataset, or a GPU. Marked and
  excluded by default.
- **Stage contract** — "this stage's own output is well-formed" is not a
  test, it's a validator. Put it on the data model so it fires during every
  real run, and unit-test the validator itself.
- **Goal invariant** — "this run supports the claim the project/paper makes."
  Belongs in a dedicated invariants module so the verdict gets written into
  the run's own output record. A run whose invariant check fails should never
  be citable in a report or paper — that's the point of writing it there
  instead of only in prose.

The last two matter most: a rule that lives only in `CLAUDE.md` prose can't
stop a bad run being cited three weeks later; a rule that writes its verdict
into the run's own output can.

## The living-test rule

Every diagnosed bug and every newly imagined edge case gets a test in the
same session it's diagnosed — the dead-end/regression-log entry and the
regression test are written together. Deleting a test requires saying why its
failure mode is now impossible.

## Coverage

The gate exists to stop untested code arriving unnoticed, not as a target.
If the project keeps a coverage-omit list, treat it as a debt ledger: when a
split makes part of an omitted module testable, remove its entry in the same
change. Never add an entry to raise a number, and never write a test whose
only purpose is to raise one — if deleting padding drops the gate, lower the
gate to the honest number and ratchet it back up as real tests land.
