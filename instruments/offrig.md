---
id: offrig
title: offrig — big models on rented RunPod GPUs
date: 2026-10-09
kind: instrument
relevance: reference
fields: [studio-tooling, gpu-computing]
tags: [instrument]
instrument_status: shipped
invoke: "offrig CLI (on PATH) or MCP tools mcp__offrig__*; start with offrig_status"
when: "A research task needs a model too big for the 5090, or a GPU job that should not run locally."
where: "E:/AI/offrig · github.com/mcp-tool-shop-org/offrig"
---

## Summary

Prices a session before spending, launches pods, feeds handoffs, and keeps project memory. Spending is capped by the Director.

## Studio relevance

Costs money: price with offrig_plan and confirm before launching.

## The verifier and `verify calibrate` (updated 2026-10-09)

R&D's calibration work, together with the Publisher's PRs reviewed by R&D, shaped calibrate on 2026-10-09:
- **`--num-predict`** sets the reply budget (in the manifest and the resume identity). The chain's 4096 starved
  gemma4:31b's thinking.
- **Quote rule 2** (offrig#47): comment and diff markers are stripped per line, and a short quote counts when
  it's a whole line. Every verdict pins `quote_rule`; a verdict without the pin came from a pre-#47 binary,
  which means rule 1.
- **`--keep-thinking`** (#48) writes `thinking.jsonl` in the run directory, untrusted and never scored. Keep it
  out of public commits unless it's been scanned.
- **Repeated failures on one claim** (#46, #49): a 5xx or a dropped reply twice on the same claim counts against
  the model **only if** a health probe shows the server still answers. A server that's down charges nothing.
- **Adaptive context, `--num-ctx auto`** (#53, approved and merging):
  - the window is sized from a measured probe band;
  - one resolved window per run;
  - `shift:false` and `truncate:false` on every request;
  - `context_overflow` is offrig's sizing failure, never charged to the model;
  - a reply that used its whole `num_predict` is always `truncated`.
- **Per-provider and account-wide budget caps** (#51, #52): an unreadable cap fails closed, and manual pods are
  shown as uncounted.

**Calibrate what is served:** a model's calibration holds for one engine and one set of settings (model digest,
think, `num_predict`, `num_ctx`, quote rule). A served engine or settings change means a new calibration, never
a rescore. Results and protocols are in `experiments/verifier-gold/calibration/`.

**Rig caveat:** the VRAM/temperature watchdog (`E:/AI/training/_watchdog.ps1`) doesn't guard Ollama's runner.
A breach from an Ollama run kills nothing. Runs on the 5090 Ollama keep their own temperature/VRAM watch and
unload the model themselves.
