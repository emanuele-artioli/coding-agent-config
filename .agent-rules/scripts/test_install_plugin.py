#!/usr/bin/env python3
"""Smoke tests for Agent Plugins portable-core validation in install.py."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INSTALL = ROOT / "install.py"


def _load_install():
    spec = importlib.util.spec_from_file_location("cac_install", INSTALL)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["cac_install"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_validate_plugin_ok() -> None:
    mod = _load_install()
    rows = mod.validate_plugin()
    problems = [f"{label}: {status}" for label, status in rows if mod._plugin_row_is_problem(status)]
    assert not problems, "portable core invalid:\n  " + "\n  ".join(problems)
    labels = {label for label, _ in rows}
    assert "plugin.json $schema" in labels
    assert "plugin.json name" in labels
    assert any(label.startswith("skills/") for label in labels)


def test_load_catalog_from_mcp_json() -> None:
    mod = _load_install()
    catalog = mod.load_catalog()
    assert catalog == {}


if __name__ == "__main__":
    test_validate_plugin_ok()
    test_load_catalog_from_mcp_json()
    print("ok")
