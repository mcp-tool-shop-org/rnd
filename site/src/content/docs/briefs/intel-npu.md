---
title: What can the Intel NPU carry?
description: The rig's Intel NPU runs small embedders about 3–10× faster than the CPU at batch 1, with matching outputs. Batching on it can hang the device, which now gets recorded as a result.
date: 2026-10-09
status: measured
shelf: pending (readouts-internal model-knowledge)
---

## The question

The rig's Core Ultra 9 285K has an Intel NPU (AI Boost) sitting idle beside the RTX 5090. Could it carry the
studio's small, always-on models (embedders, cross-encoders), so the 5090 stays free for the big ones?

## What we found

- **Embedders at batch 1 are much faster on the NPU.** bge-small is 3× faster than the CPU and bge-base about
  10×, and the NPU's outputs match the CPU's (cosine ≥ 0.99999).
- **A small NLI cross-encoder (DeBERTa) runs at CPU speed on the NPU,** with the same answers.
- **Batching can hang the NPU.** DeBERTa at batch 8 hung it once, and switchyard's first E1 run lost the device
  at nomic-embed 8×1024 (the driver reset it). bge at batch 8 ran cleanly. Until the cause is known, batch
  sizes above 1 run last, in their own block, and a device loss is recorded as a result instead of ending the
  run.
- **When the NPU seemed to disagree with the CPU, the bug was ours.** In switchyard's E1 run, 19 arms missed
  the output-matching check. Kimi traced every one to a single input the adapter never fed (`token_type_ids`).
  OpenVINO then read leftover memory, different in each compiled model. With that input fed, every comparison
  matches at 1.00000000. The NPU and iGPU never miscomputed. The same stale input may also explain the two
  nomic crashes, so the E1 re-run gives that arm one diagnostic try, alone and last.
- **Windows logs nothing when the NPU resets.** The driver's error code is the only evidence.
- **Health checks after each loss passed** (79 s and 66 s): all three models back at their earlier speeds, outputs
  matching.

![Intel NPU vs CPU](/rnd/charts/npu-vs-cpu.svg)

## Caveats

- One probe run per cell, median of the timed calls. The CPU's batch-8 medians are noisy.
- The NPU advertises 13.1 int8 TOPS but measured about 2.4, because moving data to it is the bottleneck.

## Receipts

`mcp-tool-shop-org/rnd`, `experiments/npu-probe/results/2026-10-09-probe.json` and
`2026-10-09-health-after-e1-loss.json`, plus `instruments/intel-npu.md`. The switchyard E1 incident record is
`mcp-tool-shop-org/switchyard`, `experiments/e1/incident-2026-10-09.md`.
