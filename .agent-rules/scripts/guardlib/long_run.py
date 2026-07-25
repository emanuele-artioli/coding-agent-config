"""Policy: advise when a long job may not be checkpointing or is attached.

SSH to this host drops a couple of times a day. A training or experiment run
that only saves at the end of an epoch can lose hours to a dropped connection,
and the loss is silent -- the job is simply gone.

Advisory only. Checkpoint cadence usually lives in a config file the command
line never names, so blocking here would be wrong far more often than right;
the real enforcement belongs in the training scripts themselves, which should
refuse to start without a writable checkpoint dir.
"""

from __future__ import annotations

import re

# Anything that plausibly names a checkpoint setting, in a flag or config path.
CHECKPOINT_HINTS = re.compile(
    r"checkpoint|ckpt|save[-_]?(every|steps|interval|freq)|resume|--out[-_]weights",
    re.IGNORECASE,
)

DETACHED = re.compile(r"\bnohup\b|\bsetsid\b|&\s*$|\bdisown\b")

# How to detach, in each agent's own vocabulary.
_DETACH_ADVICE = {
    "claude": "use run_in_background, or `setsid nohup ... < /dev/null &`",
    "cursor": "use Shell with block_until_ms: 0, or `setsid nohup ... < /dev/null &`",
}


def notes(command: str, entry_points: list[str], dialect: str = "claude") -> list[str]:
    """Advisory notes for a command launching a known long-running entry point."""
    if not command or not entry_points:
        return []
    if not any(entry in command for entry in entry_points):
        return []

    found = []
    if not CHECKPOINT_HINTS.search(command):
        found.append(
            "nothing on this command line names a checkpoint setting — confirm the "
            "config checkpoints at least hourly, and that resume has been tested"
        )
    if not DETACHED.search(command):
        advice = _DETACH_ADVICE.get(dialect, _DETACH_ADVICE["claude"])
        found.append(
            "this looks attached to the shell; an SSH drop would take the run "
            f"with it ({advice})"
        )
    return found
