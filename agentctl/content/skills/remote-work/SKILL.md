---
name: remote-work
description: Dispatch and monitor an authorized coding task or bounded command on a registered local or SSH machine using agentctl.
---

Use `agentctl doctor --host HOST` before first dispatch. Read the project's
execution constraints and the machine profile; PointStream permits command
dispatch but prohibits remote agent sessions.

Create a task specification containing the revision, explicitly selected
changes, runtime/resource limits, checks, and output locations. Use the native
harness chosen for the task and its existing subscription. `agentctl run SPEC`
creates an isolated checkout and detached supervisor. Unattended execution
must pass the sandbox probe; otherwise use attended execution.

Inspect `status` and bounded `logs` on the same task after disconnects. Never
resubmit an unknown task. `continue` resumes its recorded native session;
changing harnesses requires `handoff` and a fresh task. `cancel` retains work.
Successful remote coding tasks publish a branch and draft PR unless the project
restricts publication. Do not merge or deploy without explicit authority.

Use `agentctl --help` and the installed package's README for the task contract.
