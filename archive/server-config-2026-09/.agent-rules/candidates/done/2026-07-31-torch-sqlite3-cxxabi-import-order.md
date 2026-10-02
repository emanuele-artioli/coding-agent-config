---
id: 2026-07-31-torch-sqlite3-cxxabi-import-order
created: 2026-07-31
source_platform: claude
source_project: /home/itec/emanuele/presley
axis: project
status: applied
summary: On this host `import torch` before `import sqlite3` breaks sqlite3 (CXXABI_1.3.15) — any project mixing torch with a SQLite store will hit it, at runtime
suggested_action: add to host-wide AGENTS.md environment notes; check pointstream/other torch projects that use sqlite3 or any lib pulling conda's libicu
verify_platforms: []
---

## The failure

```
ImportError: /usr/lib/x86_64-linux-gnu/libstdc++.so.6: version `CXXABI_1.3.15'
not found (required by <conda-env>/lib/python3.10/../../libicui18n.so.78)
```

`import sqlite3, torch` → fine. `import torch, sqlite3` → the above.

## Why

conda's `libicui18n.so.78`, which the stdlib `_sqlite3` extension links against,
requires `CXXABI_1.3.15`. Importing torch first pins the **system**
`/usr/lib/x86_64-linux-gnu/libstdc++.so.6`, which does not export that symbol, so
the later `_sqlite3` load fails. Once `sqlite3` is in `sys.modules` the ordering
stops mattering.

Verified on `/home/itec/emanuele/.conda/envs/presley` (Python 3.10). No root on
this host, so upgrading the system libstdc++ is not an option — ordering is the
fix.

## Why it is worth surfacing rather than leaving in one repo

It is a **property of this host's conda environments**, not of PRESLEY. Any
project here that (a) uses torch and (b) touches sqlite3 — directly, or through
any library that imports it — is exposed. It is also nastier than a normal import
error in two ways:

- **It can fail at runtime rather than at import time.** A module that imports
  torch at module scope and reaches sqlite3 from *inside a function* (a deferred
  import, common for avoiding circular imports or heavy deps) passes every import
  check and then dies mid-job.
- **CI can be green while the host is broken.** CI installed CPU torch from a
  different wheel and never reproduced it.

Concretely: it took out the evaluation pass of a finished ~6-hour GPU campaign
here. The runs themselves survived only because each writes its own output
directory as it completes.

## The fix that generalises

Import `sqlite3` at the top of the package's `__init__.py`, before anything can
reach torch. That immunises the whole package regardless of any submodule's
import order, which is more robust than fixing each site — new code cannot
reintroduce it.

```python
# <pkg>/__init__.py — load-bearing, not stylistic. See the CXXABI note.
import sqlite3  # noqa: F401
```

PRESLEY does this in `src/presley/__init__.py` with the full explanation inline,
plus `tests/test_import_order.py`, which asserts (i) sqlite3 is safe after torch,
(ii) the package is the *reason* — sqlite3 in `sys.modules` at package import and
torch not dragged in, (iii) every db-reaching module imports cleanly, and (iv) a
deferred in-function db import resolves. Those tests were confirmed to fail on
the unpatched tree.

---

## Resolution — 2026-08-31

**Applied** to `AGENTS.md`, "The host", compressed to the symptom, the cause,
the two properties that make it nasty (fails at runtime through a deferred
import; CI stays green), and the fix that generalises (`import sqlite3` at the
top of the package `__init__.py`).

Not verified beyond PRESLEY. Any torch project here that reaches sqlite3 —
directly or through a library — is exposed; PointStream has not been checked.
