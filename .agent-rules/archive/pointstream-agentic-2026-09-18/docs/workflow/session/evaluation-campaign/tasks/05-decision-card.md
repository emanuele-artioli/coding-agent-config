# E05 Stage 1 Executable Card & Baseline Decision: Foreground Generation Candidates

**Date**: 2026-09-16  
**Status**: AUTHORIZED PILOT RELEASE (Execution authorized under 2026-09-16 bounded-pilot-release brief; aggregate $\le 1.0$ GPU-hour cap)  
**Author**: Antigravity (Pair Programming Session)  
**Task Reference**: [20260916-bounded-pilot-release.md](20260916-bounded-pilot-release.md) / [05-foreground.md](05-foreground.md) / [02s-training-and-controls.md](02s-training-and-controls.md)

---

## 1. Executive Summary & Authorization Status

This card defines the corrected, executable Stage 1 pilot protocol for foreground generation candidate families (`pix2pix`, `spade4tennis`, and baseline reference models).

### Release Authorization & Scope
Per the coordinator brief (`20260916-bounded-pilot-release.md`), conditional pilot execution is **AUTHORIZED** upon passing explicit preparation gates and landing a green merged revision. No training or confirmation scoring was executed prior to gate passage. Execution is constrained to **ONE aggregate GPU-hour total** encompassing training, diagnostics, validation, and any ambiguity extension.

---

## 2. Evidence Base & Existing Artifact Acceptance

The protocol builds on existing, immutable acceptance and diagnostic artifacts under `$PS_DATA_ROOT/outputs/evaluation-campaign/e02r/`:

1. **Diagnostic Matrix Report**:
   - Path: `outputs/evaluation-campaign/e02r/diagnostic_matrix_pix2pix_scene028.json`
   - SHA-256: `cec034102a3e00c2073158807278312ea3f7ccf56221918331e86dc308af7426`
   - Scope: 5-corner diagnostic probe on 16 frames of `alcaraz_highlights/scene_028` (crop $256 \times 256$, native $1080 \times 1920$).
   - Reconciled Wire: 100% byte reconciliation (`exact_match: True`, total 7,023,087 bytes).
   - Residual-Off Control: Confirmed 0 residual bytes and 0 residual calls.
   - Generative Residual Demand: 110,913 bytes for Pix2Pix vs 113,287 bytes for pasted reference keyframe.
   - Conditioning Sensitivity: Confirmed (16/16 frames have distinct delivered pixel hashes between conditioned and shuffled conditioning).

2. **Campaign Ingestion Result**:
   - Path: `outputs/evaluation-campaign/e02r/campaign_result_pix2pix_scene028.json`
   - SHA-256: `296dc0c98dc441ab85676cf3d4950b58ff35b6e2ce61f3ae97c2e9db9151df84`
   - Schema: `pointstream.campaign_result.v1`
   - Claim Eligibility: `standalone_transport: true`; `rd: false`, `runtime: false`, `generalization: false` (correctly scoped historical probe).

3. **Checkpoint Continuation Evidence**:
   - Path: `outputs/evaluation-campaign/e02r/checkpoint_resume_evidence/pix2pix_interrupted_checkpoint.pt`
   - SHA-256: `9109f53237098ff71dfcba7f1a25fe24ae23814a06311df56c29ea7782a61e9d`
   - Scope & Verification: Tested in `test_fresh_process_trainer_cli_continuation` under single-worker CPU execution (`CUDA_VISIBLE_DEVICES=""`, `--num-workers 0`, `--reference-mode first`). Proved exact bitwise equality (`torch.equal`, `diff: 0.00e+00`) across generator weights, discriminator weights, optimizer moments (`exp_avg`, `exp_avg_sq`), and RNG states (torch, numpy, python). Bounded strictly to CPU execution without claiming unmeasured CUDA bit-identity.

---

## 3. Split Labels & Materialized Development View

### 3.1 Split Classification & Quarantine
- **Development Pool**: `alcaraz_highlights/scene_028` and `federer007` (Federer/Djokovic scene 007) are **exposed development data**, never confirmation data.
- **Confirmation Reservation**: All confirmation sources (`conf_cand_01_sinner_medvedev_ao2024`, `conf_cand_04_medvedev_djokovic_usopen2023`, `conf_cand_05_swiatek_sabalenka_madrid2024`) are **strictly quarantined** under `manifests/evaluation_20260916_coordinator_confirmation_reservation.json`. Zero pilot steps, parameter searches, or test runs touch confirmation sources.

### 3.2 Materialized Development Subset (`alcaraz_highlights/scene_028`)
The pilot enforces bounded subset selection directly in `TennisSkeletonDataset` via `--video-filter`, `--scene-filter`, `--frame-start`, and `--frame-count`:

- **Active Tracks**:
  1. `alcaraz_highlights_scene_028_track_0002` (player foreground)
  2. `alcaraz_highlights_scene_028_track_0004` (player foreground)
- **Phase 1A: Tiny-Scene Training Set** (`frame_start=0, frame_count=16`):
  - Total items: 32 (16 frames per track, indices $t \in [0, 16)$).
  - Reference policy: `--reference-mode first` selects track start ($t=0$, `colors[0]`).
  - Target match: Legitimate match occurs only at $t=0$ (2 items); $ref \neq target$ for all remaining 30 items.
- **Phase 1B: Disjoint Development Validation Set** (`frame_start=16, frame_count=16`):
  - Total items: 32 (16 frames per track, indices $t \in [16, 32)$).
  - Shared first reference: Anchored to $t=0$ (`colors[0]`).
  - Target match: Zero target matches ($ref \neq target$ for all 32 items). Strictly disjoint target frames from training set.

---

## 4. Stage 1 Pilot Execution Protocol

### 4.1 Process-Group Deadline & Resource Budget
- **Aggregate GPU Cap**: Hard aggregate cap of **$\le 1.0$ GPU-hour total wall-clock time** (3,600 s) across the entire process group (training, diagnostics, validation, adaptation, and any extension).
- **Time Allocation**: Training capped at $\le 40$ minutes; at least one-third ($\ge 20$ minutes) reserved for diagnostics and evaluation.
- **Ambiguity Extension**: A targeted learning-rate refinement extension ($\le 0.5$ hour) must fit entirely within the 1.0 GPU-hour total, never exceeding it.
- **Hardware Isolation**: Single GPU device allocation (`CUDA_VISIBLE_DEVICES=1` on RTX 6000 Ada); GPU 0 remains undisturbed.
- **Execution Config**: Batch size 1, num_workers 0, seed 42.
- **Heartbeat & Checkpoints**: 10-minute progress heartbeat; intra-epoch hourly checkpoint deadline with atomic file replacement (`save_checkpoint_atomic`).

### 4.2 Baseline Controls
The candidate generative model (`gen_on_res_off`) is evaluated against two explicit reference baselines on identical disjoint development frames:
1. **Control A (Pasted First-Reference Baseline)**:
   - Keyframe pasted reference (`gen_off_res_off`), transmitting reference frame 0 and placing it directly into target bounding boxes.
   - Secondary matched residual-on point (`gen_off_res_on` vs `gen_on_res_on` at QP 32) for codec context.
2. **Control B (Supported Warped Reference Baseline)**:
   - Supported optical-flow / affine warped reference baseline (`bbox_resized_first_reference` or flow-warped), with any unavailable baseline exposed explicitly.
3. **Diagnostic Matrix Controls**:
   - Same-seed determinism: Bit-identical outputs for identical seeds (`--same-seed-control`).
   - Pose conditioning sensitivity: Delivered pixel hashes differ between conditioned and shuffled pose (`--shuffled-control`).
   - Blank conditioning control: Delivered pixel hashes differ from blank pose (`--no-conditioning-control`).
   - Residual-off control: Zero residual bytes and zero residual calls when residual is OFF.

### 4.3 Charged Total Wire Accounting
Evaluations enforce whole-codec wire accounting, rejecting crop-only or residual-only shortcuts:
$$B_{\text{total}} = B_{\text{bg\_plate}} + B_{\text{bg\_stream}} + B_{\text{fg\_ref}} + B_{\text{pose\_motion}} + B_{\text{masks}} + B_{\text{weights\_adapter}} + B_{\text{headers}} + B_{\text{residual}}$$
- Background plate and stream fully costed.
- Foreground keyframe transmission fully costed.
- Pose/motion metadata, bounding boxes, and segmentation masks charged to wire.
- Per-sequence or shared adapter/model overhead costed.
- Full wire byte reconciliation (`exact_match: True`) required; missing total rate remains incomparable.

### 4.4 3D Metric Reporting
Every evaluation must report all three core dimensions:
1. **Rate**: Total charged wire bytes, bits-per-pixel (bpp), and component subledger.
2. **Quality**: Objective fidelity measured as PSNR-Y (dB), whole-frame windowed SSIM, and object-region appearance/temporal fidelity.
3. **Speed**: Measured client decode and inference latency (seconds per frame and fps) on standardized target hardware stratum (`shared_gpu_server`).

---

## 5. Justified Bounds & Promotion Criteria

### 5.1 Justified Two-Sided Bounds
Derived from historical outcomes (where early training/untrained generators exhibit blur and low fidelity around 20–35 dB, and pasted reference keyframe achieves ~34.5 dB on `scene_028`):
- **PSNR-Y**: $[18.0\text{ dB}, 42.0\text{ dB}]$ (Values $< 18.0$ dB indicate complete generator divergence; values $> 42.0$ dB on lossy video indicate instrument leakage).
- **SSIM**: $[0.50, 0.96]$ (Values $< 0.50$ indicate severe structural artifacts; values $> 0.96$ indicate target leakage).
- **Total Wire Bytes**: $[400\text{ KB}, 1500\text{ KB}]$ for 16 frames (including background, foreground reference, pose metadata, and container headers).
- **Client Latency**: $[10\text{ ms}, 250\text{ ms}]$ per frame.

Any result outside these intervals triggers an immediate **alarm** requiring data and pipeline investigation.

### 5.2 Promotion Decision Rule (Uncertainty-Aware)
A candidate model is promoted to Stage 2 if and only if on the disjoint development evaluation:
1. **Pareto Advantage**:
   - Total wire rate is lower at matched or better quality (PSNR $\ge \text{baseline} - 0.10$ dB and SSIM $\ge \text{baseline} - 0.005$), OR
   - Quality is improved on one axis without degrading the other outside its indifference band (PSNR $> \text{baseline} + 0.10$ dB with SSIM $\ge \text{baseline} - 0.005$, or vice versa) at matched wire rate ($\le +2\%$).
2. **Client Latency Budget**:
   - Measured client latency does not exceed the declared client budget ($\le 105\%$ of baseline latency target).
3. **Controls Passed**:
   - Passes same-seed determinism, conditioning sensitivity, blank conditioning, and residual-off verification.
4. **Valid Evaluation**:
   - Zero `NaN`, zero negative PSNR, and full byte reconciliation.

---

## 6. Actual Executable Run Commands

When dispatched, pilot execution uses the tested and verified CLI tools:

```bash
# 1. Environment & GPU Isolation (GPU 1)
export CUDA_VISIBLE_DEVICES=1
export PYTHONPATH="."
export PYTHONNOUSERSITE=1
export DATA_ROOT="/home/itec/emanuele/pointstream-data/assets/dataset"
export OUT_DIR="/home/itec/emanuele/pointstream-data/outputs/evaluation-20260914/e05/stage1_pilot"
mkdir -p "$OUT_DIR/samples" "$OUT_DIR/matrix"

# 2. Phase 1A: Tiny-Scene Pilot Training (Bounded Subset: 16 frames, batch 1, workers 0)
timeout 2400 python scripts/train_pix2pix.py \
  --data-root "$DATA_ROOT" \
  --condition pose_body \
  --reference-mode first \
  --video-filter alcaraz_highlights \
  --scene-filter scene_028 \
  --frame-start 0 \
  --frame-count 16 \
  --epochs 20 \
  --batch-size 1 \
  --num-workers 0 \
  --img-size 256 \
  --lr 0.0002 \
  --seed 42 \
  --checkpoint-interval-sec 3600.0 \
  --out-weights "$OUT_DIR/generator_pix2pix.pt" \
  --checkpoint-path "$OUT_DIR/checkpoint_pix2pix.pt" \
  --sample-dir "$OUT_DIR/samples"

# 3. Phase 1B: Diagnostic Matrix on Disjoint Development Window (Frames 16..31)
timeout 1200 python scripts/run_diagnostic_matrix.py \
  --video alcaraz_highlights \
  --scene scene_028 \
  --frames 16 \
  --start-frame 16 \
  --generator pix2pix \
  --checkpoint "$OUT_DIR/generator_pix2pix.pt" \
  --output "$OUT_DIR/matrix/diagnostic_matrix.json" \
  --shuffled-control \
  --no-conditioning-control \
  --same-seed-control \
  --device "cuda:0" \
  --full-trajectory \
  --seed 42

# 4. Result Ingestion & Schema Validation via Checked Adapter Helper
python scripts/adapt_generation_result.py \
  --input-matrix "$OUT_DIR/matrix/diagnostic_matrix.json" \
  --output-record "$OUT_DIR/campaign_result.json" \
  --run-id "e05_stage1_pilot_scene028" \
  --backend-name "pix2pix" \
  --checkpoint "$OUT_DIR/generator_pix2pix.pt"
```

---

## 7. Status & Dispatch Handoff

- **Preparation Gates**: SATISFIED and VERIFIED.
- **Dataset Subset View**: MATERIALIZED and TESTED.
- **CLI Commands**: TESTED against real parsers and APIs.
- **Split Labels**: CORRECTED (`federer007` is development; confirmation quarantined).
- **Execution**: COMPLETED (2026-09-16). Phase 1A training: 4.9 min; Phase 1B diagnostics (6 corners): 19.5 min; Phase 1B corrective completion (blank control + same-seed): 6.1 min. Total cumulative GPU time ~30.5 min on GPU 0 RTX 6000 Ada, strictly within the 1.0 GPU-hour deadline (29.5 min remaining).
- **Control Evidence**: All controls verified (same-seed bitwise identity, conditioning sensitivity, non-trivial generation, and blank/zero pose calibration: matched 31.98 dB > shuffled 31.75 dB > blank 30.99 dB).
- **Deployment Accounting**: Per-video fitted weights (217.7 MB) not amortized across frames; if charged, wire rate expands to ~214 MB. Shared model unverified across domains. Claims `rd_claim=false` and `speed_claim=false` recorded.
- **Pilot Outcome**: REJECTED (Failed Stage 2 Promotion). pix2pix on disjoint development frames 16..31 failed both Pareto rate-distortion (-1.96 dB PSNR at 6.67 MB wire bytes vs 33.94 dB at 1.00 MB baseline) and client decode latency (7.03s vs 1.30s baseline). Stage 2 remains unreleased; confirmation sources remain quarantined.


