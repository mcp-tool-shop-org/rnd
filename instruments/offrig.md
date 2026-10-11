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
- **GPU count on a pod** (#55, R&D review 2026-10-11: changes needed). `offrig_status` and `offrig_job` report
  the pod record's count, the plan's count and, in the job view, what `nvidia-smi` lists. A mismatch warns and
  never shuts the pod down. R&D's required changes:
  - the measured count drives `gpu_mismatch` too, with `gpu_mismatch_source` (record, measured or both);
  - a record without a count, with nothing measured, gives `gpu_mismatch: null` (unknown) and a warning, never
    `false`, which would read as confirmed;
  - `nvidia-smi` listing no cards against a plan above 0 is a mismatch, not "not measured";
  - one test per case. Merge on green after that, with no re-review.
- **Readiness and the host CUDA pin** (#56, for 1.1.0; R&D review 2026-10-11: pass with two changes).
  - **Why:** in pilot 3 an SGLang engine logged that startup finished, then deadlocked. `/health` stayed down while
    `/v1/models` answered, and the pod sat on a CUDA 13.2 host where the working pilots had run on 13.0.
  - **Ready now means one chat completion returned a choice,** tried twice.
  - **engine_hung:** the startup line followed by 3 minutes without `/health` is reported, with the pod left up.
  - **An exact `cuda_versions` pin** is sent as `allowedCudaVersions`, and refused alongside a floor.
  - **R&D's changes:**
    - two failed completions are also reported, never a shutdown, on every surface. A slow first request on a large
      engine would otherwise throw away the download, and the deadline watchdog already bounds the cost of waiting;
    - the startup line is detected by a count over the whole log, not a 40-line tail.
  - **The CUDA list:** RunPod's documented v1 values plus 13.1 and 13.2, which are observed but not documented.

**Calibrate what is served:** a model's calibration holds for one engine and one set of settings (model digest,
think, `num_predict`, `num_ctx`, quote rule). A served engine or settings change means a new calibration, never
a rescore. Results and protocols are in `experiments/verifier-gold/calibration/`.

**Rig caveat (updated 16:14):** the VRAM/temperature watchdog (`E:/AI/training/_watchdog.ps1`) has guarded Ollama's runner since 2026-10-09 16:14. Before that it didn't, and the rest of this paragraph describes that earlier state.
A breach from an Ollama run kills nothing. Runs on the 5090 Ollama keep their own temperature/VRAM watch and
unload the model themselves.
