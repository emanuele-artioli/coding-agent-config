---
name: paper-structure
description: Check a LaTeX manuscript's structural budget — page count against the venue limit, words per section, section balance, and float density (how far a reader goes without a table/figure). Use when a paper is over a page limit, when a section feels bloated, when deciding what to cut, or before submitting to a venue with a hard page budget.
---

# Paper structure and budget

A paper fails structurally in ways that are invisible while writing and obvious
to a reader: one section eats the paper, the conclusion outgrows the
introduction, the abstract becomes a results section, and the reader hits six
pages of unbroken prose. All of that is measurable. Measure it instead of
arguing about it.

**This skill does not judge writing quality.** It answers: is the paper the
right *size*, is it *balanced*, and is it *broken up* enough to be read.

## Do this first

Render the PDF and count pages for real. Estimating pages from word counts is a
fallback — it is calibrated to the paper's current float density, so it drifts
exactly when you start changing that density.

```bash
python <repo>/tools/paper_metrics.py --pages <rendered_page_count>
```

If the project has no such tool, the measurement is: prose words per `\section`,
excluding float bodies, captions, and any struck/deleted text (`\del{}`,
`\sout{}`) — none of that is prose a reader wades through. Count tables,
figures, algorithms and equations separately, per section.

## The rules

Heuristics for a full-length journal article, not laws. Override deliberately,
having seen the number — never by not looking.

**Hard (fix before submitting):**

- **Total pages ≤ the venue's limit.** Check whether the limit covers the main
  body only; many venues exclude references and appendices, which changes the
  strategy completely.
- **No section exceeds ~40% of body words.** Past that it is not a section, it
  is the paper, and everything else reads as preamble.
- **No stretch of prose longer than ~2 pages without a float.** This is the
  single best predictor of a reader getting lost.

**Soft (justify if you break them):**

- Every section is longer than the abstract. A section shorter than the abstract
  is a subsection wearing a hat.
- Conclusion ≤ introduction. A conclusion that outgrows the introduction is
  usually re-arguing the paper rather than closing it.
- ≥1 float per 2 pages overall.
- **Figures ≥25% of floats.** Tables carry values; figures carry *shape*. A
  reader skimming thirty tables learns nothing about shape. This is the most
  commonly violated rule in a results-heavy paper and the most damaging.
- Abstract 150–250 words. If it has a results section, it is too long.
- Rough section shares for an empirical paper: introduction 8–15%, related work
  8–15%, method 20–30%, evaluation 30–45%.

## Cutting to a page budget

When over budget by more than ~20%:

- **Cut whole results, not prose.** Compressing paragraphs produces a paper that
  is still too long *and* now unreadable. Removing a whole experiment and one
  sentence of justification is nearly free to read.
- **Merge tables that answer one question.** Several tables landed one-per-
  experiment usually collapse into one table plus a sentence each. The reader
  wants the finding, not the chronology of finding it.
- **Move provenance to an appendix** — per-item hashes, methodology ablations,
  metric audits. Keep the claim in the body, the evidence trail out of it.
- **Convert the biggest table into a figure.** It usually shortens the page *and*
  fixes the figure-ratio rule at the same time.

Do not start by trimming adjectives. That is the slowest path to a page and it
damages the writing.

## Things to check that a word count will not tell you

- **Duplicate `\label{}`s** — `grep -ohE '\\label\{[^}]+\}' *.tex | sort | uniq -d`.
  Commented-out duplicates are harmless; live ones make `\ref` silently wrong.
- **The bibliography actually resolves.** A malformed `.bib` entry can be
  tolerated by one toolchain and fatal in another; an entry with no citation key
  produces a citation that quietly renders as `?`.
- **Whether the venue counts references and appendices** in its limit. This is
  worth ten pages of strategy and takes one minute to check.

## Reporting

Report HARD failures and soft warnings separately, and always print the rules
being applied so the reader can disagree with a specific one. State the required
cut in both words and percent — "cut 9,800 words (49%)" is actionable in a way
that "the paper is too long" is not.
