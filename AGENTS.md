# Working on coding-agent-config

Use Python 3.11+ and the standard library for runtime functionality. Run
`python3 -m unittest discover -s tests -v` for behavior changes.

This is a normal repository, not a home-directory checkout. Historical server
configuration is retained under `archive/`; it is inactive and must not be
installed or treated as current instructions.

The installer's safety contract is ownership, conflict detection, preservation
and rollback. Do not overwrite unrelated native configuration. Hooks are
advisory protection; unattended work requires an independently tested sandbox.
Compute admission must rely on supervisor-owned evidence, not agent assertions.

Preserve PointStream's project-specific dispatcher and prohibition on remote
agent sessions. Never run substantive GPU jobs as implementation tests.
