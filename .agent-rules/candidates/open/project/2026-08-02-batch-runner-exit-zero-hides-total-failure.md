---
id: 2026-08-02-batch-runner-exit-zero-hides-total-failure
created: 2026-08-02
source_platform: claude
source_project: /home/itec/emanuele/presley
axis: project
status: open
summary: A batch runner that catches per-entry errors exits 0 even when every entry failed — verify result count against entry count, never the exit code
suggested_action: lift into AGENTS.md near the long-jobs/checkpoint rule; applies to any project with a queue-driven runner (presley-run, training sweeps, backfills)
verify_platforms: []
---

Half of an experiment wave (16 of 32 cells) failed with a config error.
`presley-run` caught the error per entry, printed
`Error running experiment <hash>`, continued to the next one, and **exited 0**.
A chained job then ran its evaluation and LPIPS-backfill passes over the
half-empty set and also exited 0. Nothing downstream complained.

The per-entry error handling is *correct* — one bad config should not abandon a
multi-hour wave — so the check cannot live in the runner. It has to live with
the caller.

**The rule:** after any batch run, verify the number of results produced
against the number of entries submitted. Never treat exit 0 as evidence that a
wave completed.

```
grep -c 'Error running experiment' <log>     # errors, directly
# and compare: entries in the run-file vs result.json files on disk
```

In this incident the only signal was arithmetic: 32 `Running …` lines in the
log against 16 `result.json` files on disk. Both counts were easy to get and
neither was checked until the analysis tool reported an implausible "everything
is missing".

**Why it generalizes:** any project where a runner iterates a queue and
tolerates individual failures has this shape — training sweeps, evaluation
backfills, data-ingest jobs. The more robust the runner is to one bad item, the
more completely a systematically bad *batch* disappears into a clean exit code.
A wave that fails 100% looks identical to one that succeeds 100% from the
outside.

**Corollary that made this one systematic rather than flaky:** the failure was
a config-shape error (an argument valid for one component passed to another),
so it hit every entry of one kind and none of the other. A clean 50/50 split in
what succeeded is a strong hint of a config bug rather than resource flakiness
— worth checking the split before blaming the GPU.
