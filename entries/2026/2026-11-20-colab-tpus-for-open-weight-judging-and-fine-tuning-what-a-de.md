---
id: 2026-11-20-colab-tpus-for-open-weight-judging-and-fine-tuning-what-a-de
title: Colab TPUs for open-weight judging and fine-tuning: what a Deep Research report found (seed 40)
date: 2026-11-20
kind: finding
relevance: reference
fields: [compute]
tags: [colab, tpu, seed-40, harvest]
---

## Summary

The studio's Google AI Ultra plan includes Colab compute units, which we had spent only on GPUs. We asked a Gemini Deep
Research run whether Colab's TPUs suit our work: batch judging with open-weight models (4B to 32B), small LoRA
fine-tunes, embeddings and reranking, with reproducibility before speed. The report is `[aggregator]` AI output. A
harvest clerk checked its load-bearing claims against Google documentation and GitHub issues; several of its numbers
could not be found at any primary source.

Its answer, which the checks support: not now. Colab offers only single-chip TPUs; our judges run through llama.cpp with
GGUF weights and llama.cpp has no upstream TPU backend; and the TPU route that does exist (vLLM's TPU backend) loads
different weights, so it would be a different judge.

## Key points

- **What Colab offers.** Single-chip v5e-1 and v6e-1 runtimes; the older v2-8 was retired in September 2025. A v6e
  chip has 32 GB of high-bandwidth memory, so a dense 32B model does not fit on one.
- **Software.** llama.cpp has no TPU backend upstream; an unofficial out-of-tree one supports only two quantisation
  types. vLLM's TPU backend is real and lists Qwen3 and Gemma models, but it loads safetensors weights, not GGUF.
  Moving a judge to it changes the judge.
- **Cost.** The report's TPU rates (about 2.9 and 4.1 units an hour) are user measurements; no Google page states them.
  Its per-unit speed-ups over GPUs rest on one blogger's benchmarks that could not be read, so they are unchecked.
- **Reliability.** Users report v6e-1 allocation failures this month, and an October rise in GPU unit rates.
- **Reproducibility.** It says run-to-run bit-identical results are reachable on one TPU type with single-chip XLA;
  plausible, not tested by us.
- **Terms.** Colab's terms say nothing that separates TPU from GPU use; "no difference" is an absence in the text, not
  a finding.
- **Its first experiment.** A small vLLM batch-judging pilot on v6e-1 against a GPU control, gated on a 500-of-500
  identical replay and a net throughput-per-unit gain. We do not plan to run it now.

## Studio relevance

### What it contradicts in our design (read first)

| Finding | Our design today | Decision |
|---|---|---|
| A TPU judge would run on vLLM with safetensors weights | Judges are llama.cpp with GGUF weights; results are never pooled across hardware | No TPU judging; a TPU judge would be a new instrument, not the same judge on faster hardware |
| Colab TPUs are single-chip only | Our largest judges are 32B dense | They would not fit; no change |
| The command-line client once defaulted to a short run timeout (since fixed) | Some Colab kits rely on the client's defaults | Every Colab kit passes its timeout explicitly |

### Decisions and actionables

1. No TPU run before the current units expire: single-chip only, no llama.cpp backend, a different judge on vLLM-TPU,
   and the money at stake is small.
2. Colab hygiene, independent of TPUs: explicit timeouts in every kit, and cleanup of orphaned sessions after a
   refused allocation.
3. Not pursued now: offline vLLM batch judging on our GPU card (needs a decision on GGUF against safetensors judge
   numerics first), and Google's TPU Research Cloud programme (it exists; the terms the report gives for it are
   unconfirmed).

## Claims

- [verified] Colab's v2-8 TPU runtime was retired in September 2025 (via: colabtools issue 5566 read by the harvest clerk, 2026-11-20)
- [verified] A v6e TPU chip has 32 GB of high-bandwidth memory (via: Google Cloud TPU documentation read by the harvest clerk, 2026-11-20)
- [verified] llama.cpp has no TPU backend in its main repository, and an unofficial backend supports only Q4_0 and Q8_0 (via: GitHub pages read by the harvest clerk, 2026-11-20)
- [verified] vLLM's TPU backend lists Qwen3 and Gemma models and loads safetensors weights, not GGUF (via: vLLM TPU documentation read by the harvest clerk, 2026-11-20)
- [unverified] Colab TPU runtimes cost about 2.9 (v5e-1) and 4.1 (v6e-1) compute units per hour (the report's figures from user posts; no Google page found)
- [unverified] TPUs give 2.3 to 3 times more judging throughput per compute unit than Colab GPUs (the report's figures, from one blog that could not be read)
- [unverified] TPU inference can be made bit-reproducible run to run on one TPU type (the report's claim; not tested)

## Sources

- [aggregator] https://gemini.google.com/ — Gemini Deep Research (Gemini 4 Carbon, High), 2026-11-20: report on Colab TPUs for open-weight models
- [primary] https://github.com/googlecolab/colabtools/issues/5566 — Google Colab issue tracker: v2-8 TPU retirement
- [primary] https://cloud.google.com/tpu/docs — Google Cloud TPU documentation (v5e and v6e specifications)
- [primary] https://docs.vllm.ai/ — vLLM documentation, TPU backend and supported models
