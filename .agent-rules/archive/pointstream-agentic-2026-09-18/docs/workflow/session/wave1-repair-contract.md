# Wave 1 repair contract (coordinator-owned)

Base: `origin/main` `6199d3e`. Integration branch: `cursor/wave1-generation-transport-repair`.
Workers must not edit the same files. Coordinator merges and owns leftover interface glue.

## Shared wire contract

Generation intent is `ClientPlacement.is_generated` plus lattice `STAGE_GENERATION`. Never infer it from `supplied_crop is None`.

When `is_generated` is true:

- Appearance bytes are a generator condition (references), not a pasted crop.
- Pose/motion, mask, bbox, frame/schedule, generator identity, checkpoint SHA-256, and seed travel on the wire.
- Do not also emit a pasted placement for the same `(object_id, frame_index)`.

`generator_meta` (required whenever generation is on):

```json
{
  "name": "pix2pix",
  "seed": 1337,
  "params": {},
  "capabilities": [],
  "requires": [],
  "checkpoint_id": "path or logical id",
  "checkpoint_sha256": "64 hex chars or injected:<name>",
  "config_identity": "stable string"
}
```

Missing checkpoint identity, unknown generator name, or checkpoint mismatch must fail closed.

## File ownership

| Worker | Owns | Must not touch |
|---|---|---|
| A generated-client | `src/runner/run.py`; new tests under `tests/runner/`; optional `src/runner/generation_identity.py` | `src/runner/client.py`, `src/runner/accounting.py`, `scripts/run_diagnostic_matrix.py`, `experiments/tier/calibrate.py` |
| B compact-masks | `src/runner/client.py`, `src/runner/accounting.py`, new `src/runner/mask_wire.py`, transport/accounting tests | `src/runner/run.py`, `scripts/run_diagnostic_matrix.py` |
| C provenance | `scripts/run_diagnostic_matrix.py`, `experiments/tier/calibrate.py`, protocol/report helpers and their tests | `src/runner/run.py`, `src/runner/client.py` |

Worker A may add a clearly marked checkpoint-identity call in `reconstruct_serialized_client` only if `generation_identity.py` cannot be invoked from `run.py` alone. Worker B must preserve that generator-resolution block.

Worker B may add a `subledger` structure on `SizesBytes` and a helper that `ledger_from_bag` can call. If `src/runner/stages.py` `ledger_from_bag` must change, Worker B owns that function only; do not otherwise edit `stages.py`.

## Mask wire (Worker B)

Lossless compact representation. Initial design: per-frame sparse bounding rectangle plus packed binary bits; omit empty frames. RLE or a measured lossless image encoding is acceptable if declared and tested. Preserve exact mask semantics. Do not bbox-only approximate. Corrupt/truncated payloads fail closed.

## Accounting (Worker B)

`transport_total` equals `len(serialized_request)` exactly. Charge each class once. Subledger must distinguish at least: mask payload, pose/motion, placement/schedule headers, generator metadata, container/envelope overhead. Record the old raw-mask ~41.5 MB bound before measuring the compact result.

## Diagnostic report (Worker C)

Must record: code revision; source manifest and frame hashes; resolved config; generator backend and checkpoint SHA-256; seed/device/inference params and invocation count; delivered and base hashes per corner; byte subledger and wire-reconciliation verdict; encoder/client/eval timing; per-corner failures; pasted/no-generator/shuffled controls; whether generation changed delivered pixels and residual demand. Missing identity or a no-op generator invalidates generator comparison.

Calibration: identity > mild > severe and mild > unrelated, separately. Do not lower the 0.60 SSIM unrelated ceiling merely to pass. If natural unrelated SSIM cannot support 0.60, document the observed scale and propose a new preregistered policy. Do not treat shuffled-temporal high SSIM as a metric failure.
