# Wave 2 development pilots (after Wave 1 gates)

> Historical dispatch, superseded on 2026-09-12 by [evaluation handoff](evaluation-handoff.md).
> Its GPU assignment and automatic matrix/ladder sequence are not current authorization.

Do not launch until Wave 1 integration gates hold. GPU 1 on this host is assigned (`CUDA_VISIBLE_DEVICES=1`). GPU 0 hosts an unrelated process (`mitraba` `app.py` :7860, ~528 MiB) and must be left alone.

Superseded Wave 2 artifacts remain at `outputs/development-recovery/`; write new outputs beside them, never overwrite.

## Predeclared display-fidelity targets

VMAF approximately 75, 85, 90, 95. Adjust only through a preserved decision record. Never extrapolate. Do not compute BD-rate unless measured overlap satisfies the existing 50% / 10-point-span rule.

## Diagnostic matrix (first)

Two development scenes from `manifests/development_recovery.json`:

- `alcaraz_highlights` / `scene_000`
- `federer_djokovic` / `scene_007`

16 frames, pix2pix immutable checkpoint, then SPADE4Tennis-lite only if its repaired readiness smoke passes.

Corners: gen off/on × residual off/on, plus shuffled-conditioning generation null.

Acceptance: generator-on hashes differ from paste and shuffled; no source fallback; checkpoint/config/source identity; compact mask accounting; exact wire reconciliation; per-source size/quality/runtime.

If generation still does not alter delivered frames, stop. Do not train around a no-op.

## Overlap-capable residual ladder (second)

Wave 2 residual-HF (H0–H3, QP 42/35/28/20) sat at VMAF 94.77–96.33 (Alcaraz) and 87.24–91.18 (Federer) while native VVC topped out at 87.03 / 83.76. AV1 overlap was 17.3% on Alcaraz and a 3.9 VMAF span on Federer. Those comparisons stay unscorable.

After compact masks, extend:

- PointStream residual **down** (coarser QPs, optional gating/downscale) into VMAF ~75–90.
- VVC **up** with QPs 35/31/27 in addition to 63/55/47/39.
- AV1 similarly where the high-quality endpoint is still insufficient; retain native and 0.5/0.25 adaptive arms.

Two sources only. Development-only. No Gate B, no confirmation sources, no paper claims.
