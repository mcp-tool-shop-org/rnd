---
title: The card is full
description: E5 finishes. Each local model's largest context window on the 5090 is now measured, and two of them came out far larger than the first run could show. Plus two NVIDIA tools read against our own, and three new instruments for the bench.
issue: 5
date: 2026-10-13
highlights:
  - "<strong>E5 is complete:</strong> four local models hold their full trained context window on the 5090; gemma4:31b holds 86,016 tokens and granite4.1:30b 43,008."
  - "<strong>The first run's two lower bounds were a predictor's fault, not the card's:</strong> once it learned from measured loads, gemma's figure rose six-fold."
  - "<strong>Two NVIDIA tools, read against our own:</strong> NeMo Relay for tracing agents, and PAIR, a router for the machines on a home network."
  - "<strong>Three new instruments:</strong> a licence probe, an exact-word search, and a weekly watch on the sources the studio depends on."
---

Every claim below links to the record it came from. Interim results are labelled as interim.

## E5: how much context each model holds

E5 asks a router's most practical question about a local model: how long a prompt can it take before it no longer
fits on the graphics card? Past that point the model spills into system memory and slows sharply. For each model,
interlock's harness raised the context window step by step and filled it with a real prompt. It recorded the largest
window that stayed on the card, under a 30,500 MiB ceiling, with no spill.

| Model | Largest window on the card | Trained window |
|---|---|---|
| llama3.1:8b | **131,072** | 131,072 |
| gemma4:31b | **86,016** | 262,144 |
| granite4.1:30b | **43,008** | 131,072 |
| qwen3:14b | **40,960** | 40,960 |
| qwen3:8b | **40,960** | 40,960 |
| mistral-small:24b | **32,768** | 32,768 |

Measured with Ollama 0.35.1, an f16 KV cache with flash attention, and Q4_K_M weights on an idle card.

**How the edges were found.**
- **gemma4:31b is bounded by a measurement.** The next step, 88,064 tokens, peaked 44 MiB over the ceiling. Neighbouring
  readings vary by a couple of hundred MiB, so the true edge lies somewhere between the two.
- **granite4.1:30b is bounded by a forecast and a measurement.** The next step was forecast over the ceiling from the
  measured growth per token, and the step after that was measured over.

**Why the first run fell short.** The first full run, earlier the same day, stopped gemma at 14,336 and granite at
30,720. Both stops came from a safety predictor that assumed every layer's memory grows with the window. gemma uses
sliding-window attention and granite is a hybrid model, so their memory grows far more slowly. After a dated
amendment, the predictor learned from measured loads instead. The same run also fixed a spill rule that had
misfired on llama3.1:8b, which in fact holds its full window with gigabytes to spare.

**Three small defects in the receipt.** None changes a result, and they're queued as one fix:
- a label names the wrong reason for gemma's stop;
- one reading probably caught the previous load still freeing memory;
- a decode rate reads a million tokens a second, because each check generates a single token.

→ [E5: the card, the rulings and the defects](https://github.com/mcp-tool-shop-org/rnd/blob/main/entries/2026/2026-10-13-e5-fill-card.md)
· [the trimmed records](https://github.com/mcp-tool-shop-org/rnd/tree/main/experiments/e5)

## Two NVIDIA tools, read against our own

- **NeMo Relay** records what an AI agent actually did: each model call, tool call and decision, in open trace
  formats. It can wrap Claude Code without changes to it. We've added it to the toolset as a planned instrument: if
  a trial confirms the transparent mode, it could trace our agent experiments.
  → [How do we see what an agent actually did?](/rnd/briefs/agent-tracing-nemo-relay/)
- **PAIR** joins the computers on a home network into one model service and sends each request to a machine that
  holds the model. Its own documentation lists what its scheduler can't see: whether a model is already loaded, how
  much context fits, and how jobs differ in size. interlock measures exactly those things on one machine, and E5 is
  one of them.
  → [Where should this request run? NVIDIA PAIR and interlock](/rnd/briefs/pair-and-interlock/)

## New on the bench

- **`rnd probe <url>`** answers the first questions about a tool or model from each source's own records: its
  licence, latest release, gating, and any code mentioning telemetry. A source it can't reach is reported as unknown,
  never guessed.
- **`rnd search --exact`** finds whole words in the same case, so a search for PAIR finds the product, not every pair.
- **`rnd watch`** checks a list of sources for anything new since the last look. The list covers NVIDIA's blog and
  models, the CUDA toolkit, and the releases of Ollama, OpenVINO, PyTorch, ComfyUI, llama.cpp and Claude Code. Once
  a week a scout reads what's new and writes a short ranked report: what to try, what to file and what to skip.

→ [rnd's README: probing a tool, watching sources](https://github.com/mcp-tool-shop-org/rnd#probing-a-tool-before-a-trial)

## New: the weekly watch

The watch now has its own page every Monday: what changed in the tools and models the studio runs on, what it
means for our work, and what we did about it. The first edition caught a Claude Code fix that closes a gap in our
own experiment's sandbox.

→ [The watch: week of 13 October](/rnd/watch/2026-10-13/)
