---
id: 2026-11-21-reproducible-local-model-serving-for-game-evaluations-what-a
title: Reproducible local model serving for game evaluations: what a Deep Research report found (seed 45)
date: 2026-11-21
kind: finding
relevance: act
fields: [evaluation]
tags: [merchant-league, reproducibility, seed-45, harvest]
---

## Summary

Merchant League's evaluation runs open-weight models on one local GPU. It compares a seat's decision at frozen game states
under three arms, so the same request must give the same reply. We asked a Gemini Deep Research run:
- what still breaks bit-identical outputs in llama.cpp and vLLM serving;
- what a run must record;
- how large a pre-flight check must be.

The report is `[aggregator]` AI output. A harvest clerk checked 17 of its claims at source: server docs and source, issue
threads and paper abstracts. R&D re-checked the llama.cpp cache flags in its source.

## Key points

- **"Prefix caching off" is three settings, not one.** llama-server has:
  - a per-request prompt cache (`cache_prompt`, or `--no-cache-prompt` at launch);
  - a separate host-RAM prompt cache (`--cache-ram`, on by default at 8192 MiB);
  - idle-slot saving, on by default, which needs the RAM cache and a unified KV buffer.

  `--no-cache-prompt` leaves the host-RAM cache on, and `--cache-ram 0` leaves in-slot prefix reuse on, so turn each
  off explicitly.
- **With no prefix reuse and one slot, llama.cpp reproduces tokens.** One study, across two engines (llama.cpp among
  them) and four weight formats at batch size one, saw all ten serving configurations reproduce every token and
  log-probability without prefix reuse. A maintainer says bit-identical results come from a single slot with no prompt cache.
- **Prefix reuse moves outputs.** For one 7B model, the cache-hit and recompute paths diverged on 37.4% of multi-turn tool
  episodes at 16-bit and 82.5% at 4-bit. At 4-bit, run-to-run divergence came mainly from llama-server's own prompt cache:
  20.0 to 28.7% of episodes at its default across five random episode orders, and a 37.5-point shift under the canonical
  order.
- **vLLM guarantees reproducibility in online serving only in batch-invariant mode.** Drift between cold restarts is
  reported, from kernel autotuning. The report's proposed fix (a reduction-config flag) was not found in vLLM's source,
  and an issue comment shows drift even with an identical compile cache.
- **Record more than the settings you send.** That means the full effective sampler set (llama-server applies `min_p`
  0.05 unless told otherwise), the chat-template hash, a hash of each prompt's token ids, the GPU's identity and SM count,
  and the relevant environment variables. Compare token ids and top-5 log-probabilities, not reply text alone.
- **Size the pre-flight by the bound you want.** With zero failures in N independent states, each run twice, the 95%
  upper confidence bound on the per-state failure rate is 1 - 0.05^(1/N): 45% at N = 5, 26% at N = 10, 9.5% at N = 30.
  This assumes every state carries the same risk.

## Studio relevance

### What it contradicts in our design (read first)

| Finding | Our design today | Decision |
|---|---|---|
| "Prefix caching off" is three separate settings | The harness card refused to start only if "prefix caching is on" | Adopted in the harness card's addendum: the start check requires all three off, and each is recorded |
| The manifest must capture server and sampler state | Model hash, GPU name and driver, sampling parameters, cache setting, parallel slots | Added: batch and ubatch sizes, unified KV, flash attention, KV types, speculative decoding, context, threads, the full effective sampler set, the chat-template hash, per-request token-id hashes, a hashed GPU identity, SM count, CUDA/OS/WSL versions, and an environment snapshot that excludes anything secret-named |
| Reply text can hide a divergence that rejoins | Reply bytes compared | Token ids and top-5 log-probabilities are recorded per decision |
| vLLM is not bit-exact by default | vLLM allowed | A vLLM seat counts as "not shown bit-exact" until it passes a cold-restart check |
| A 10-state pre-flight bounds failure only near 26% | 10 states, run twice | Its size will be set by measurement on our own GPU. A failed pre-flight is a finding, never re-run until it passes |

### Decisions and actionables

1. The evaluation harness adopts the three-part cache check and the manifest fields. They are already written into its
   build plan.
2. The pre-flight size and a cold-restart check come later, measured on our own GPU.

## Claims

- [verified] llama-server's `--cache-ram` defaults to 8192 MiB, idle-slot saving defaults on and requires the RAM cache and a unified KV buffer, and `cache_prompt` defaults on (via: llama.cpp tools/server/README.md on master, read by the harvest clerk; R&D re-read the same defaults in llama.cpp's common/common.h:594-598 and common/arg.cpp:1363-1366 at tag b9333, commit 35c9b1f39, 2026-11-21)
- [verified] Without prefix reuse, ten serving configurations (two engines, four weight formats) at batch size one reproduced every token and log-probability over 80 episodes (via: abstract of Patodiya 2026, arXiv 2609.04748, read by the harvest clerk, 2026-11-21)
- [verified] For one 7B model, cache-hit and recompute paths diverged on 37.4% of episodes at 16-bit and 82.5% at 4-bit; at Q4_K_M the server-level prompt cache left 20.0 to 28.7% run-to-run divergence at its default under five random orders, and moved divergence by 37.5 points under the canonical order (via: abstract of Patodiya 2026, arXiv 2609.04748v3, re-read by R&D, 2026-11-21)
- [verified] vLLM's docs give no default reproducibility guarantee, and reproducible online serving only with batch invariance, a beta mode for compute capability 8.0 and up, on the same hardware and vLLM version (via: vLLM docs/usage/reproducibility.md and docs/features/batch_invariance.md on main, read by the harvest clerk, 2026-11-21)
- [verified] A llama.cpp maintainer states there are no batch-invariant CUDA kernels, but bit-identical results with a single slot and no prompt cache (via: llama.cpp pull request 16016 discussion, read by the harvest clerk, 2026-11-21)
- [verified] Zero failures in N independent state checks (each state run twice) give a one-sided 95% upper bound of 1 - 0.05^(1/N) on the per-state failure rate, if every state carries the same risk: 45.1% at N = 5, 25.9% at N = 10, 9.5% at N = 30 (via: recomputed by R&D, 2026-11-21)
- [unverified] The report's recipe for cold-restart stability in vLLM (a persisted compile cache plus a reduction-config flag); the flag was not found in vLLM's source

## Sources

- [aggregator] https://gemini.google.com/ — Gemini Deep Research (Carbon, High), 2026-11-21: report "Bitwise Reproducible Local LLM Serving"
- [primary] https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md — llama.cpp server documentation
- [primary] https://github.com/ggml-org/llama.cpp/pull/16016 — llama.cpp pull request discussion on batch invariance
- [primary] https://arxiv.org/abs/2609.04748 — Patodiya (2026), Same Request, Different Answer: Quantization Amplifies Cache-Induced Divergence in LLM Serving (abstract read)
- [primary] https://github.com/vllm-project/vllm/blob/main/docs/usage/reproducibility.md — vLLM reproducibility documentation
- [primary] https://github.com/vllm-project/vllm/blob/main/docs/features/batch_invariance.md — vLLM batch invariance documentation
- [primary] https://github.com/ggml-org/llama.cpp/issues/26128 — llama.cpp issue on the server prompt cache and `--no-cache-prompt` (body read)
