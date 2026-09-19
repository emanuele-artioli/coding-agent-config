---
name: paper-outline
description: The senior researcher's procedure for outlining paper text before any writer is dispatched. Use for a new section, a rewrite, or a reviewer item that needs new text. Produces GOAL and HOLE markers in the .tex, each naming the evidence path and the numbers a paragraph may cite, plus dispatched writers on disjoint files. Ends with checked numbers, a passing marker lint, and a paper commit naming the ids.
---

# Outlining a section before anyone writes

You are the senior. The judgment about what the paper claims and which
number backs it is yours and stays yours. Juniors write prose into
markers you placed. Dispatch follows the seven-field contract in the
`session` skill; do not restate it here.

## When to run this

A new section or a rewrite. A reviewer item that needs new text. Always
before the first writer is dispatched.

## Procedure

1. **Gather, as the senior only.** Juniors never read these.
   - The paper repo's own `AGENTS.md` or `CLAUDE.md`, for the marker
     syntax and the revision macros such as `\rev{}` and `\del{}`.
   - The open markers:
     `grep -n '^% *\(STATUS\|GOAL\|HOLE\|NOTE\|NEXT\|CLAIM\)(' *.tex`
   - The research log's standing results and its superseded registry.
   - The reviewer checklist, if there is one.

2. **Write the outline as markers in the `.tex`.** One `GOAL(id)` per
   paragraph, saying what that paragraph must convince the reader of and
   which evidence path it will cite. A `HOLE(id)` wherever the evidence
   does not exist yet. Every number a paragraph will cite is named here,
   with its source path. A writer picks words, never numbers.

3. **Dispatch `paper-editor` juniors**, one per marker group, on
   disjoint `.tex` files, with:
   - the marker ids they own,
   - the evidence paths, and the numbers with their sources,
   - the revision convention from step 1,
   - check: `scripts/paper-markers-lint.py <paper-dir>` when the project
     has it, else a balanced braces and environments check on the edited
     files.

4. **Intake.** Read the produced paragraphs. The text is the product, so
   this is one of the cases where you do read the work. Check each cited
   number against the source path you handed over. Run the lint yourself.

5. **Before submission** run `referee` on the manuscript and
   `paper-structure` for the page budget.

6. **Commit the paper repo separately from the code**, naming the marker
   ids in the message.

## Never

- Let a junior choose which number to cite.
- Clear a `HOLE` without landing its data.
- Hand a junior the research log or the reviews to interpret.
