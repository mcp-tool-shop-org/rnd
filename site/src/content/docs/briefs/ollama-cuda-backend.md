---
title: Can Ollama run the studio's CUDA 13.4 backend?
description: It's eligible. Its outputs differ from stock Ollama's, and the whole difference is the cuBLAS library. With only CUDA 13.4's cuBLAS swapped in, stock reproduces the studio build bit for bit, and neither build sits closer to a higher-precision reference.
date: 2026-10-15
status: measured
shelf: pending (readouts-internal)
---

## The question

The studio builds its own `ggml-cuda.dll` for Ollama on the RTX 5090, with CUDA 13.4 and machine code for this card
only. Before it replaces Ollama's stock CUDA 13.0 backend, does it give the same answers?

## What we found

**Not identical, but the difference is fully explained, and it isn't the studio's code.**
- The first sandbox test asked for identity with stock token for token, and the build failed it: two of three prompts
  forked.
- Its first generated token already disagreed on every prompt, which points at the prompt's prefill.

**A frozen, outside-reviewed harness then ran eight arms of qwen3:8b on 15 prompts, one arm at a time:**
- **Stock repeats itself** bit for bit across server starts.
- **Stock with only CUDA 13.4.3's cuBLAS swapped in** matches the studio build bit for bit: every token and every
  top-10 log-probability on all 15 prompts.
- **With cuBLAS held at 13.4, three different `ggml-cuda.dll` builds** change nothing at all: stock PTX compiled by
  the driver, the 13.4.1 build, and the 13.4.3 build with every FlashAttention quant.
- **Where cuBLAS runs.** The model keeps one weight in f16, the attention V projection in all 36 layers. While the
  prompt is read, that matmul goes to cuBLAS with f16 accumulation. Everything else runs in ggml's own kernels. A
  different cuBLAS kernel for that one GEMM changes the low bits from the first token on.
- **Neither build is closer to the qwen3:8b-q8_0 reference.** At the forks the reference sided with each build once,
  and the two builds' log-probability error against it differs by 0.003 nats.
- **The studio build had no task failures** on the 12 checked prompts.

So, by the rule set before the run, the build is eligible. Activating it is a separate decision, and stock CUDA 13.0
stays installed as a switchable fallback.

## Caveats

- One model (qwen3:8b Q4_K_M), 15 prompts, 64 greedy tokens. A model with more f16 or bf16 weights routes more work
  through cuBLAS, and could differ more.
- "Eligible" means different but no worse by this test. It doesn't mean better.
- The q8_0 reference failed two format checks that every Q4 arm passed. It measures closeness, not quality.
- The first run of the harness crashed at its first arm on a bug every review had missed, before anything loaded.
  The fix shipped with an offline dry run of the whole harness, which now runs in CI.

## Receipts

`mcp-tool-shop-org/rnd`, `experiments/ollama-cuda-backend/`:

- `diag-result-v6.md`: the result, the reading and the corrections;
- `diag-record-v6.jsonl` and `diag-analysis-v6.json`: the run's record and its ab_dataminer analysis;
- `diag/`: the frozen harness, byte for byte, and its tests;
- `sandbox-result-cu1343.md`: the failed sandbox test that started it;
- the build records for 13.4.1 and 13.4.3.
