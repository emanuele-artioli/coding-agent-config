---
name: compute-preflight
description: Establish correctness and select an efficient configuration before an expensive GPU or multi-hour computation.
---

Read the project's compute adapter and scientific protocol. Define the target,
representative inputs, candidate configurations, stage budgets and promotion
criteria before examining outcomes. Preserve the production entry point and
processing path; mock inputs or materially different quality settings cannot
validate a production configuration.

Run a bounded smoke test for output validity, metrics, memory and relevant
checkpoint/resume behavior. Then compare a small justified set of configurations
in a bounded pilot. Select the lowest measured cost meeting the target. Add
scale confirmation when the pilot cannot establish full-scale behavior; state
the basis and uncertainty of extrapolations.

Use `agentctl run` with a compute specification so the supervisor records and
checks evidence before full execution. Relevant code, configuration, input,
environment or hardware changes invalidate evidence. Stop on failed checks,
nonfinite/missing metrics, unattainable targets or budget exhaustion; explain
what must change before spending the full budget. Do not expand the search or
use paid compute beyond the assigned authority.
