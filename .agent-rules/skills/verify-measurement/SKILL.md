---
name: verify-measurement
description: Check that a measurement can be believed before reporting it — calibrate the instrument against known anchors, run the null control, and report the effect with its uncertainty. Use before stating that one arm/model/configuration beats another, before publishing any metric number, and whenever a result is surprisingly good.
---

# Verifying a measurement before you report it

A number is not evidence. A number produced by a checked instrument, next to its
null, with its uncertainty, is evidence.

**Use this when:** you are about to say X beats Y; you are about to quote a
metric value; a component underperforms and you are about to blame it; or a
result came out better than expected. That last one is the most important and the
easiest to skip.

## 1. Has the instrument been calibrated?

Score inputs whose answer you already know, and check the **whole curve**:

| Anchor | What it must show |
|---|---|
| identical | the metric's perfect value |
| mild perturbation | clearly better than severe |
| severe degradation | clearly worse than mild |
| unrelated input | at the published far end of the scale |

Two failures that look identical to a smoke test, and both shipped:

- **No dynamic range.** A metric scored an unrelated image at 0.083 and a good
  reconstruction at 0.085. Perfectly monotonic, perfectly ordered, useless.
  Only the **absolute scale** against the published range exposes this.
- **Wrong direction over part of the domain.** A wiring fault scored a blurred
  clip at 100 and an identical one at 97. Additive noise was monotonic; only a
  **blur** anchor caught it. Include both noise and smoothing — they are
  different failure directions.

Two traps in building the anchors themselves:

- **Do not use white noise as "unrelated".** Two noise images are perceptually
  *similar* to a learned metric — real LPIPS puts them at 0.13 against 0.57 for
  structured content. Use structured or natural content.
- **Do not assume severe and unrelated are orderable.** Heavy blur drives content
  toward flat grey, which can sit further from the reference than an unrelated
  image. Assert identical → mild → severe, and mild → unrelated, separately.

Also check the tool's own preconditions: libvmaf refuses regions under 32 px and
is meaningless on flat content, so it cannot score a small crop at all.

## 2. Is the comparison scoped the same way on both sides?

Region-scoped on one metric and whole-frame on another is not a comparison.
This produced a false "best on perceptual quality" claim: object-masked PSNR was
tabulated beside whole-canvas LPIPS.

State the scope with every number.

## 3. Where is the null?

**Run the control in the same session, before reporting.** Pick the one that
isolates the claim:

| Claim | Null |
|---|---|
| "the model uses input Z" | same model, **wrong** Z (shuffled/foreign) |
| "the model helps" | no model — copy, passthrough, or nearest baseline |
| "retraining improved it" | the **un**retrained checkpoint, same harness |
| "this component pays for itself" | the component disabled |

A control that reproduces the effect means the effect is not what you think.
That is how a "retraining worked" claim was caught: the un-retrained model scored
+0.86 where the retrained one scored +0.98.

## 4. Is the effect bigger than the noise?

Report **n, the mean difference, and the standard error**. Pair the arms on the
same items so item-to-item variance cancels.

- under ~1 standard error → inside noise, name no winner
- 1–2 → suggestive, not a result on its own
- over ~2 → clear
- fewer than ~8 items → underpowered, report the effect and claim no direction

A +0.98 dB effect over 12 items with per-item sd of 2.0 is ~1.7σ. It was reported
as a finding.

## 5. Was the thing invoked the way it is meant to be?

Before concluding a component is weak, confirm it is being driven correctly. A
temporal video model was evaluated one frame at a time for three rounds; its
native clip path improved it by 2.76 dB. The single-frame path existed, ran, and
passed its tests.

## What to write down

- the number, **with the instrument's range beside it**
- the scope (region? whole frame? which mask?)
- the null, and what it scored
- n and standard error, and the verdict from §4
- the seed, checkpoint, and any offset

## The asymmetry

These checks get applied to disappointing results and skipped on exciting ones.
**When the news is good, add a check rather than stopping.** Every wrong
conclusion this skill exists to prevent was a pleasing result reported before its
control was run.
