---
name: paper
description: Canonical marker spec for paper .tex, plus short literature, figure, outline, update, structure, reviewer, and measurement procedures. Dispatch through `session`.
---

# Paper markers and research

Dispatch through the `session` skill. This file is the canonical marker
spec, not AGENTS.md.

## Markers

Comments in `.tex`: `STATUS` / `GOAL` / `HOLE` / `NOTE` / `NEXT` /
`CLAIM(anchor)` with `src=` and `date=`.

- One `GOAL` per paragraph: what it must convince the reader of.
- `HOLE` where evidence is missing. Never clear a HOLE without landing
  its data.
- When data lands, write the `CLAIM` line in the same edit:
  `CLAIM(id): src=<path> date=YYYY-MM-DD`.
- Writers pick words, never numbers. Every number comes from a source
  path the senior named.

## Literature

State the question and screening criteria first. Dispatch `paper-screener`
juniors against that list. You select what to cite, implement, or ignore.

## Figure

Name the figure and pre-state bounds before reading numbers. Dispatch
`data-condenser` with the figure spec, data shape, run list, and bounds.
Close every alarm before a number is used.

## Outline

Place markers in the `.tex` before anyone writes. Dispatch `paper-editor`
on disjoint files with the marker ids, evidence paths, and numbers.

## Update

Fold findings into the hole that asked for them. Clear the `HOLE` and
write its `CLAIM` together. Check citability before citing a run.

## Structure

Venue page limit is hard. No section ~40% of body words; no stretch of
prose longer than ~2 pages without a float. Measure section balance and
float density; cut whole results, not adjectives.

## Reviewer

Work the checklist entry, then land the change. Dispatch `referee`
before submit. "Done" means the text or experiment is in place, never a
plan.

## Measurement

State plausible best/worst bounds before looking at observed values.
Alarm if a value is outside those bounds; do not report it until the
alarm is closed. Report size, quality, and time together. A number is
evidence only after the instrument is checked against known anchors.
