---
name: literature-review
description: The senior's procedure for turning a research question into a screened, selected reading list. Use when the human names a research question or goal, when a related-work section has an open HOLE, or when a new method needs state-of-the-art baselines. Produces a candidate table screened by juniors and a selected list the senior wrote. The output says which papers to implement as baselines, which to cite, and which to ignore.
---

# Literature review: screen wide, select yourself

You are the senior. Juniors read papers against criteria you wrote and
fill a table. They never decide what matters. Dispatch through the
`session` skill's seven-field contract.

## Procedure

1. **State the question in one sentence**, and the decision it serves:
   which baseline to implement, which claim to make, which method to
   cite. A question with no decision behind it is a reading habit, not a
   review. Write both lines down before searching.

2. **Write the screening criteria before you search.** Venue list and
   year floor. Public code required. Public weights and public dataset
   required too when the decision needs you to run the method. Scope
   keywords that a paper must hit. Exclusions, named. These criteria go
   into every dispatch verbatim, not summarized.

3. **Build the candidate list.** Three to six search queries, each
   phrased differently. Run them against Google Scholar, arXiv,
   Semantic Scholar, and Papers With Code, then walk the citation graph
   of one or two anchor papers, both directions. Dedupe by DOI or arXiv
   id. Cap the list at the budget below.

4. **Dispatch `paper-screener` juniors in parallel**, at most eight
   papers each, writing to disjoint files
   `docs/literature/<topic>/screen-<k>.md`. `docs/literature` lives in
   the project repo, or in the paper repo when the project keeps a
   separate one. Each dispatch carries: that junior's paper list, the
   criteria verbatim, its own output path, the column layout every part
   file shares, and the rule that any id already in `candidates.md` is
   skipped.

5. **Intake.** For each junior, open two of its papers at random and
   check the code, weights, and data fields against the source. One
   wrong field rejects that junior's whole batch, and the batch is
   re-run, not patched. Then concatenate the accepted part files into
   `docs/literature/<topic>/candidates.md`.

6. **Select.** Read only the verdict, reason, and summary columns. Write
   `docs/literature/<topic>/selected.md`: one line per kept paper with
   why it is kept and the next action, which is implement as baseline,
   cite, or ignore with the reason. The senior selects. Juniors never
   do, at any step.

7. **Land it.** Citations and comparisons go into the paper through
   `paper-outline` markers. A paper that changes the project plan
   becomes a knowledge candidate or a plan update, in the same pass.

## Budget

At most 30 candidates per pass, at most eight papers per junior. A wider
question is two passes, not one bigger one.

## Never

- Cite a screener's summary in a paper without opening the paper
  yourself for that claim.
- Let a junior select, rank, or drop a paper on its own judgment.
- Re-screen ids that are already in `candidates.md`.
