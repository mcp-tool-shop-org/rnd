# 3A: the B-2 36-cell quantisation matrix

Source: Antigravity reply, 2026-11-13 08:55 UTC (03:55 ET), final window `jam-b2-qmat-g4-4`.
`[unverified]`: no record here re-ran or audited these figures.

## Setup

- Base: `Qwen/Qwen2.5-7B-Instruct` at a pinned revision, with each of the 5 frozen B-2
  selected LoRA seeds (13, 42, 271, 512, 1024) merged, plus the base itself: 6 models.
- Rungs: `F16`, `Q8_0`, `Q6_K`, `Q5_K_M`, `Q4_K_M`, `IQ4_XS` (no importance matrix) from one
  pinned `llama.cpp` revision: 36 cells.
- Evaluation: greedy (temperature 0) `llama-server` completions on the inner validation
  slices (jam tools, grounding, abstention, transfer), 285 prompts per cell, 10,260
  completions in all. The sealed holdout was not read or exported (the reply's statement).
- Final window: `G4` Standard, 5,739.889 s, 16.023857 units; earlier bring-up windows are in
  the table below.

## Five-seed mean by rung

| Rung | File size | Base composite | 5-seed mean composite | Delta vs F16 | 41-tool jam exact | 9-tool grounding | prose calibration (abstain / answerable) | transfer |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| F16 | 15.24 GB | 0.4250 | 0.7656 | +0.0000 | 0.4940 | 0.9610 | 0.8417 (0.933 / 0.750) | 0.1917 |
| Q8_0 | 8.10 GB | 0.4111 | 0.7680 | +0.0024 | 0.5000 | 0.9623 | 0.8417 (0.933 / 0.750) | 0.1917 |
| Q6_K | 6.25 GB | 0.4271 | 0.7667 | +0.0011 | 0.4960 | 0.9623 | 0.8417 (0.933 / 0.750) | 0.1750 |
| Q5_K_M | 5.44 GB | 0.4091 | 0.7657 | +0.0001 | 0.5040 | 0.9597 | 0.8333 (0.933 / 0.733) | 0.1583 |
| Q4_K_M | 4.68 GB | 0.4056 | 0.7440 | -0.0216 | 0.4920 | 0.9483 | 0.7917 (0.900 / 0.683) | 0.1917 |
| IQ4_XS | 4.25 GB | 0.4130 | 0.7636 | -0.0019 | 0.4960 | 0.9532 | 0.8417 (0.933 / 0.750) | 0.2250 |

## Per-model composite across the 36 cells (delta vs F16 in brackets)

| Model | F16 | Q8_0 | Q6_K | Q5_K_M | Q4_K_M | IQ4_XS |
|---|---:|---:|---:|---:|---:|---:|
| base | 0.4250 | 0.4111 (-0.0139) | 0.4271 (+0.0022) | 0.4091 (-0.0158) | 0.4056 (-0.0193) | 0.4130 (-0.0119) |
| seed 13 | 0.7648 | 0.7648 (+0.0000) | 0.7670 (+0.0022) | 0.7626 (-0.0022) | 0.7464 (-0.0184) | 0.7648 (+0.0000) |
| seed 42 | 0.7787 | 0.7830 (+0.0043) | 0.7787 (+0.0000) | 0.7808 (+0.0022) | 0.7626 (-0.0161) | 0.7808 (+0.0022) |
| seed 271 | 0.7325 | 0.7392 (+0.0067) | 0.7347 (+0.0022) | 0.7392 (+0.0067) | 0.7260 (-0.0065) | 0.7282 (-0.0043) |
| seed 512 | 0.7776 | 0.7787 (+0.0011) | 0.7787 (+0.0011) | 0.7715 (-0.0061) | 0.7327 (-0.0449) | 0.7789 (+0.0013) |
| seed 1024 | 0.7744 | 0.7744 (+0.0000) | 0.7744 (+0.0000) | 0.7744 (+0.0000) | 0.7522 (-0.0221) | 0.7655 (-0.0088) |

## What the reply concludes

1. `Q8_0`, `Q6_K` and `Q5_K_M` are lossless relative to `F16` at this resolution (mean
   deltas +0.0024, +0.0011, +0.0001).
2. `Q4_K_M` shows a consistent cliff: -0.0216 on the mean, negative in all 5 seeds, worst
   -0.0449 (seed 512). The damage is localised to abstention prose calibration (0.8417 to
   0.7917, -5.00 points) and secondarily grounding (0.9610 to 0.9483, -1.27 points); the
   41-tool exact match barely moves (0.4940 to 0.4920).
3. `IQ4_XS` (433 MB smaller than `Q4_K_M`) recovers most of the cliff: 0.7636, with
   prose calibration back to 0.8417 and jam exact 0.4960. The reply's figure is "91%" of
   the cliff removed (recomputed here: (0.0216 - 0.0019) / 0.0216 = 91%, which matches).
   Its explanation (non-linear 4.25 bits-per-weight grids and automatic higher-precision
   protection of the first FFN-down tensors at that `llama.cpp` revision) is a reading of
   the quantiser's source, not something measured here.
4. **Receipt parity note:** the P4 receipt exact-match check was false for all 5 seeds. The
   reply attributes this to the adapter merge running in `bfloat16` on the Colab GPU
   (RTX PRO 6000 Blackwell, CUDA 13.0) before conversion, which differs by ordinary
   cross-device rounding from the local rig's merge. All 36 GGUF digests and sizes are in the
   summary file kept on the rig.

## Windows and units

| Window | Card | Elapsed (s) | Units | Outcome |
|---|---|---:|---:|---|
| `jam-b2-qmat-cpustub-1` | CPU high-mem | 40.326 | 0.002912 | uploads and bundle download verified; a manifest folder-prefix mismatch fixed |
| `jam-b2-qmat-cpustub-2` | CPU high-mem | 182.855 | 0.013206 | install and build verified; a missing host-RAM readout in the vitals emitter fixed |
| `jam-b2-qmat-cpustub-3` | CPU high-mem | 516.556 | 0.037307 | ok; full dry matrix passed |
| `jam-b2-qmat-g4-1` | G4 | 553.969 | 1.546497 | input hash mismatch on the adapter manifest (a pin prefix); pin fixed |
| `jam-b2-qmat-g4-2` | G4 | 886.544 | 2.474937 | `llama-server` flash-attention flag now needs an explicit `on`; eval script patched |
| `jam-b2-qmat-g4-3` | G4 | 1,150.878 | 3.212869 | 210 of 285 baseline prompts ran; 41-tool prompts exceeded the per-slot context; total context raised |
| `jam-b2-qmat-g4-4` | G4 | 5,739.889 | 16.023857 | ok; 36 of 36 cells, 10,260 completions |

Total 23.311585 units (recomputed here), of which the three pre-final `G4` windows, a
tooling-fix sequence, cost 7.234303.

## Kept on the rig (not filed)

The summary JSON (27,364 bytes, sha256 `65c0703aec16648d5625313d7ae32206bb6839845471f58c51688ea6f3cb2156`),
the per-cell JSONL.gz (19,546 bytes, sha256 `5627920a690164b2b566e4c5bb1326552327816fbd4c72472dab7d08684925a9`),
the per-item JSONL.gz (464,347 bytes, sha256 `316ac80e69d9643a44b1f34a4998e0d1cb5c916ae9b667d73ddecbe65cae2a25`), and the
GGUF files.
