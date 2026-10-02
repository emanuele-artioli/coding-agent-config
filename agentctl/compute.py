"""Validate supervisor-observed stage evidence before expensive execution."""

import math
from pathlib import Path

from .common import Refused, digest, identifier, read_json


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def validate(protocol, budget):
    if not isinstance(protocol, dict):
        raise Refused("GPU production and multi-hour jobs require a compute protocol")
    targets = protocol.get("targets")
    if not isinstance(targets, dict) or not targets:
        raise Refused("define measurable targets before running")
    for bounds in targets.values():
        if not isinstance(bounds, dict) or not bounds or set(bounds) - {"min", "max"}:
            raise Refused("metric targets require min and/or max")
        if not all(finite(value) for value in bounds.values()):
            raise Refused("metric bounds must be finite")
        if bounds.get("min", -math.inf) > bounds.get("max", math.inf):
            raise Refused("metric bounds are reversed")
    if not protocol.get("representative_input") or not protocol.get("runtime_environment") or not protocol.get("hardware"):
        raise Refused("record representative inputs, environment and hardware")
    candidates = protocol.get("candidates")
    if not isinstance(candidates, list) or not 1 <= len(candidates) <= 12:
        raise Refused("provide 1–12 explicit candidate configurations, not an open-ended search")
    if len({candidate.get("name") for candidate in candidates}) != len(candidates):
        raise Refused("candidate names must be unique")
    for candidate in candidates:
        if not candidate.get("name") or not isinstance(candidate.get("parameters"), dict):
            raise Refused("each candidate needs a name and parameter configuration")
        identifier(candidate["name"])
        if set(candidate["parameters"]) & {"output", "candidate"}:
            raise Refused("candidate parameters cannot override output or identity")
    stages = protocol.get("stages", {})
    scaling = protocol.get("scale_arguments", {})
    if not isinstance(scaling, dict) or any(not isinstance(flag, str) or not flag.startswith("--") or not isinstance(reason, str) or not reason.strip() for flag, reason in scaling.items()):
        raise Refused("scale_arguments must declare option names and their extrapolation basis")
    def signature(argv):
        result = []
        index = 0
        while index < len(argv):
            if argv[index] in scaling:
                if index + 1 >= len(argv) or "{" in argv[index + 1]:
                    raise Refused("scale arguments cannot override selected production parameters")
                index += 2
            else:
                result.append(argv[index])
                index += 1
        return result

    required = ["smoke", "pilot", "full"]
    if protocol.get("confirmation_required", True):
        required.insert(2, "confirmation")
    elif not protocol.get("confirmation_waiver"):
        raise Refused("explain why scale confirmation is unnecessary")
    total = 0
    for name in required:
        stage = stages.get(name, {})
        argv = stage.get("argv")
        if not isinstance(argv, list) or not argv or not all(isinstance(arg, str) for arg in argv):
            raise Refused(f"{name}: argv must be a nonempty list of strings")
        seconds = stage.get("seconds")
        if not finite(seconds) or seconds <= 0:
            raise Refused(f"{name}: positive finite budget required")
        if not stage.get("metrics_file"):
            raise Refused(f"{name}: metrics_file required")
        if not stage.get("entrypoint") or stage.get("entrypoint") != stages.get("full", {}).get("entrypoint"):
            raise Refused("all stages must declare the same production entrypoint")
        if stage["entrypoint"] not in argv:
            raise Refused("declared production entrypoint is absent from stage argv")
        if signature(argv) != signature(stages.get("full", {}).get("argv", [])):
            raise Refused("preflight changes production arguments; declare only justified input/scale differences")
        for candidate in candidates:
            if any("{" + parameter + "}" not in "\0".join(argv) for parameter in candidate["parameters"]):
                raise Refused("every stage must use every selected production parameter")
        if not stage.get("production_path", False) or stage.get("mock", False):
            raise Refused("preflight must exercise the real production path")
        total += seconds * (len(candidates) if name == "pilot" else 1)
    if total > budget:
        raise Refused("staged worst-case runtime exceeds task budget")
    preflight = protocol.get("preflight_seconds")
    if not finite(preflight) or preflight <= 0 or total - stages["full"]["seconds"] > preflight:
        raise Refused("stages exceed the explicit preflight budget")
    return required


def meets(observed, targets):
    return all(bounds.get("min", -math.inf) <= observed["metrics"][name] <= bounds.get("max", math.inf)
               for name, bounds in targets.items())


def metrics(path, targets, require_target=True):
    observed = read_json(path)
    if not isinstance(observed, dict) or observed.get("valid") is not True:
        raise Refused("stage did not attest valid real outputs")
    values = observed.get("metrics", {})
    for name, bounds in targets.items():
        value = values.get(name)
        if not finite(value):
            raise Refused(f"missing or nonfinite metric: {name}")
        if require_target and (value < bounds.get("min", -math.inf) or value > bounds.get("max", math.inf)):
            raise Refused(f"target not met: {name}={value}")
    if not finite(observed.get("cost")) or observed["cost"] <= 0:
        raise Refused("stage must record positive measured cost")
    return observed


def fingerprint(revision, changes, protocol, environment, hardware):
    return digest({"revision": revision, "changes": changes, "protocol": protocol,
                   "environment": environment, "hardware": hardware})


def admissible(evidence, identity, required):
    if evidence.get("fingerprint") != identity:
        raise Refused("preflight evidence is stale for this code/config/input/environment/hardware")
    for name in required:
        if name == "full":
            continue
        if evidence.get("stages", {}).get(name, {}).get("passed") is not True:
            raise Refused(f"{name} evidence missing or failed")
    if not evidence.get("selected_candidate"):
        raise Refused("no configuration demonstrated to meet the target")


def render(stage, candidate, output):
    values = {"output": str(output), "candidate": candidate["name"], **candidate["parameters"]}
    try:
        return [arg.format_map(values) for arg in stage["argv"]]
    except KeyError as error:
        raise Refused(f"missing candidate parameter {error}") from error
