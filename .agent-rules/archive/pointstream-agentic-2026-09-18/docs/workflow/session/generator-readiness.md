# Worker C — identify and validate a useful generator

> Historical repair brief. For new work use [parallel probes](parallel-probes.md).
> Its retired-evaluator status and old training budget below are superseded;
> they are not standing authorization to launch training.

Assignment: GEN-ACT-04. Follow overnight-recovery.md. Own src/components/generation/, scripts/train_campaign.py and focused generator/training tests. Do not edit the runner owned by A or evaluator owned by B; agree interfaces through the coordinator.

The audited Gate A/B runs use no generator. Registered backends and historical fine-tunes are candidates, not proof of readiness. Inventory actual available checkpoint paths/hashes, architecture, training provenance, licensing constraints already recorded, required conditioning and native temporal calling convention. Distinguish installed, loadable, successfully invoked and scientifically validated. Do not download large models or alter the pinned environment casually.

Inspect existing ControlNet/IP-Adapter/Animate-Anyone/pix2pix/SPADE adapters before selecting one candidate with real weights and a plausible codec benefit. The Animate-Anyone adapter references a tennis fine-tune profile; verify files and inference rather than assuming it is ready. scripts/train_campaign.py currently has an evaluate_checkpoint function that raises because its old decoder was retired: do not launch it unchanged or report its old ranking proxy as total codec rate–distortion.

Run a tiny inference smoke test using the architecture's intended sequence input, real reference/pose conditioning where required, and repeated fresh-process output checks. Compare with pasted references and shuffled/wrong conditioning. Confirm generation actually executes and changes the reconstructed output; source-frame fallbacks invalidate the test. Reserve GPU time through the coordinator.

A bounded training pilot does not require the generation-free baseline to win. It does require a functioning current-runner evaluator and a measured baseline. Restore checkpoint evaluation against full reconstructed clips, total transmitted bytes and encode/decode runtime; preserve model and split provenance. Video-specific fitted weights must be counted if needed by the client. Improvements in crop realism alone are insufficient: evaluate temporal error and residual byte demand at matched final fidelity.

Authorized tests: checkpoint/config identity reaches evaluation; missing checkpoints fail explicitly; temporal input reaches a temporal backend as a sequence; the actual selected checkpoint is invoked; evaluator uses held-out development scenes and current-runner results; unsuccessful evaluation cannot select a winning checkpoint. Use small owned-code fixtures, not tests of third-party internals.

Deliver the verified candidate inventory, one real smoke command, and either a working bounded pilot command or a precise blocker. Training is capped at two hours within the coordinator's eight-hour budget and begins only after A/B integration supports credible scoring. No confirmation-source tuning or multi-day campaign. Coordinator updates generation policy and reports results.
