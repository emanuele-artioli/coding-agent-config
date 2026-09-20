---
name: engineer
description: The senior's procedure for planning a change and designing its tests. Use for a feature or refactor larger than one file, any shared-contract change, and whenever the human asks for a plan. Produces stubbed signatures with docstrings, a three-group test list, and dispatched implementer juniors with runnable checks.
---

# Planning a change and its tests

You are the senior. The plan is the signatures and their docstrings, not
a prose document. Juniors fill bodies. Dispatch follows the seven-field
contract in the `session` skill; do not restate it here.

## When to run this

A feature or refactor that touches more than one file. Any change to a
shared contract or interface, however small. The human asking for a plan.

## Procedure

1. **Read what is there.** The current interfaces, the docs around them,
   and the tests that pin them. Write down the invariants callers rely
   on. If you cannot name them, you are not ready to plan.

2. **Write the plan as code.** Put the signatures in the real files,
   with type hints and a docstring each, and a body that is only
   `raise NotImplementedError`. The docstring says the purpose, the
   arguments, the return, what it raises, and the invariant a caller
   relies on. These docstrings are the documentation, written before any
   body exists.

3. **List the tests, per function**, in three groups. Most components
   deserve 3–8 tests.

   - **Behaviour** — the envisioned cases, with expected values you can
     state by hand. A closed-form computation gets a hand-computed case;
     a mapping gets its boundary values. Prefer a case that would produce
     a plausible wrong value over one that merely raises, because only
     the first kind survives to be cited later.
   - **Plausible misuse** — what a caller in this repo could realistically
     do wrong (empty or malformed input, a mismatched dimension, a config
     key naming a missing backend). Prefer mistakes that would produce a
     plausible-looking wrong number over ones that just raise.
   - **Deliberately not tested** — say what you are leaving out and why:
     unreachable branches, third-party library behaviour, errors a caller
     cannot produce, and anything whose only effect would be moving the
     coverage number.

   Show the list before writing tests when the user is in the loop.
   Number the items so they can say "drop 3, add one for X."

   Tests belong where the project says: `AGENTS.md` / `pytest.ini` /
   `README`. Never `CLAUDE.md`. A test that exists only to raise a
   coverage number is a defect.

4. **Dispatch `implementer` juniors**, one per disjoint file set, with:
   - read-first: the stubbed files and the test list for them,
   - allowed paths: that file set and its test files,
   - check: the project's test command for those tests, plus lint or
     type-check when the project has them,
   - a budget.

5. **Intake.** Re-run the check yourself. Green CI on a pushed branch is
   the definition of done. Do not read the diff. Read **Not verified**
   and **Assumptions** in each report, and take anything there that
   touches the goal as your own work.

6. **Docs.** Update the README or the architecture doc from the plan and
   the reports. The docstrings you wrote in step 2 are already the
   source; the junior's code is not.

## Never

- Let a junior change a signature or a shared contract. A junior that
  needs one reports it under **Not verified** and the senior decides.
- Dispatch without a runnable test. A check that cannot fail is not one.
- Write the docs by re-reading the junior's code.
