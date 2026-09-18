# POINTSTREAM paper (ACM TOMM submission)

This is a separate git repo (Overleaf sync), nested inside the code repo but
independent of it — **different rules apply here than in the parent folder.**
Commit here, not in the parent. The manuscript goes to TOMM after an ACM MM
rejection, but it is a fresh submission rather than a rebuttal: `reviews.md`
holds ideas about what a future referee might object to, and nothing in it is
owed an answer.

*`CLAUDE.md` is a symlink to this file — Claude Code reads that name, Cursor and
others read this one. Keep them identical; do not delete either as a duplicate.*

## Build and page budget

Build with
`conda run -n tex --no-capture-output bash tools/build_pdf.sh`. It writes
`build/main.pdf` and fails if citation placeholders remain. The script uses
Tectonic for TeX and external BibTeX because this host's `tex` environment has
no working `pdflatex` format and Tectonic 0.17's embedded BibTeX fails on this
bibliography.

Measured 2026-09-04 after BP53 notes: **27 pages total**; body/references occupy
pages 1--22; appendices start on a fresh page (page 23) and span pages 23--27
(exactly 5 numbered pages).
The project budget is 23 pages including references plus at most 5 appendix
pages. Both the main body/references and the appendix span are now strictly
compliant with their respective limits following the companion-material move
and fresh-page appendix break. The body also needs rebalancing before final
evaluation results arrive. Re-check after every edit.

**The paper is the record.** There is no research log: what is worth keeping
lives in the manuscript, in a marker that states its fact inline, or in an
appendix.

## Marker convention (canonical spec)

One marker per comment line, uppercase keyword + parenthesized anchor + colon;
continuation lines are `%   ` (comment + two-space indent). Anchor = nearest
`\label` where one exists, else a stable slug.

| Marker | Meaning | Cleared when |
|---|---|---|
| `STATUS(file) date:` | Trust level of the file / a major section | Section reaches final form |
| `GOAL(id):` | What a section/table/figure must show | Element reaches final form |
| `HOLE(id):` | Concrete missing data — names the exact experiments needed | ONLY by the edit that lands that data, same pass |
| `NOTE(id):` | Caveat constraining how nearby text may be worded | When the caveat stops being true |
| `NEXT(id):` | Planned action, not yet a data gap | When done or superseded |
| `CLAIM(id):` | Provenance for the quantitative claims under `id` | Never deleted; updated when numbers change |

Discovery (run before planning any experiment or edit):

```
grep -rn '^% *\(STATUS\|GOAL\|HOLE\|NOTE\|NEXT\|CLAIM\)(' main.tex appendices/
```

Rules: anyone may write markers; a marker never delegates its content to
another file, it states the fact it needs; a `HOLE` is cleared only by the edit
that lands its data, citing an experiment path in a `CLAIM` line; markers are
comments, invisible to reviewers. **Camera-ready sweep:** before submission the
discovery grep must return only `CLAIM` lines.

## Claim discipline

- **The headline claim must land where PointStream wins.** A paper whose central
  result is "we lose to the anchor everywhere" is not a submission. Scope the
  main claim to the regime where it holds and state that boundary; secondary
  results may be negative and should stay that way. The full rule, including
  what it does *not* license — picking the configuration after seeing the
  numbers without saying so, or relaxing checks once the news is good — is in
  the code repo's `AGENTS.md`, which is the single source for it.

- **Every number traces to an experiment path** in the code repo via a `CLAIM`
  line. No path, no number — text, table or appendix alike.
- **The currency is BD-rate, not a byte count.** Two configurations never land
  at the same bitrate and never land at the same quality, so one operating
  point each compares nothing. Every configuration is swept across a rate
  ladder into a rate-distortion curve, and curves are compared by Bjontegaard
  delta rate against a common anchor, with the overlapping quality range
  reported. **A component is justified iff enabling it improves BD-rate against
  that anchor** -- not if it shrinks the payload at one point, and not because
  "it looks better". A single-point comparison is admissible only under
  dominance, where one arm is better on both axes. This is the definition in
  the code repo's `https://github.com/emanuele-artioli/PointStream/blob/bc09184d8707529f924a41d0dccc2b6f20e88d3e/plans/done/RESEARCH-HISTORY.md` section 5 and in Section~\ref{subsec:lattice} of the manuscript;
  the older "total payload at equal measured quality" wording it replaced was
  the right idea stated in a way that cannot actually be measured.
- **Quality is always measured, never assumed.** There is no guaranteed mode:
  the residual always carries some coarseness, and generative inference is
  statistical, so encoder- and client-side synthesis are not guaranteed
  identical. Symmetry is a design goal verified by measurement.
- **The residual is optional.** Conventional fallback is an explicit coded
  route. The all-disabled `SOURCE_PASSTHROUGH` diagnostic carries raw pixels,
  not conventionally compressed video; never report it as a compressed baseline.

## Appendix convention

One appendix per `.tex` file under `appendices/`, `\input` from the `\appendix`
block in `main.tex`. It holds what is worth preserving but not worth reading in
order to read the paper: tool surveys, negative results, reproducibility notes.
Rules in `appendices/README.md`.
