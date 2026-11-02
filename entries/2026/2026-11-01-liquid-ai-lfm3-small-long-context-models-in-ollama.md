---
id: 2026-11-01-liquid-ai-lfm3-small-long-context-models-in-ollama
title: "Liquid AI LFM3: small long-context models in Ollama"
date: 2026-11-01
kind: release
relevance: watch
fields: [local-models]
tags: [lfm3, ollama, licence]
---

## Summary

LFM3 is Liquid AI's third model family, published on Hugging Face in October 2026. It includes:
- a 1.7B text model aimed at tool calling and structured output, with a long context window;
- a base model;
- 2B vision-language, audio and "omni" models.

Ollama 0.40.12 added support for the family; 0.40.13 added it on Windows. All the checkpoints carry Liquid AI's own licence, the LFM Open License v1.0, which limits commercial use by company size.

## Key points

- **The licence is custom.** Commercial use is licensed only to a company with annual revenue under 10 million US dollars.
- **The checkpoints are small** enough to run anywhere on the rig, including as a possible router or tool-calling rung.
- **Official GGUF and MLX builds** exist beside the full-precision checkpoints.

## Studio relevance

`watch`. LFM3 is a try candidate for **research only**: a small tool-calling model to measure in interlock's routing experiments.

Because of the revenue clause, it never ships in a studio product and never generates data for one. Re-read the licence before any trial.

## Claims

- [verified] LFM3-1.7B and LFM3-Omni-2B are licensed "lfm1.0", and the model card links the LFM Open License v1.0. (via: `rnd probe` on both Hugging Face repos, and the 1.7B model card, 2026-11-02)
- [verified] The LFM Open License v1.0 defines a threshold of 10 million US dollars in annual revenue, says commercial use by an entity that exceeds it is not licensed, and exempts non-commercial or research use by qualified non-profits from it. (via: the LICENSE file in LiquidAI/LFM3-1.7B, read 2026-11-02)
- [verified] Ollama 0.40.12 and 0.40.13 list LFM3 support; .13 adds it on Windows. (via: the Ollama release bodies read by the weekly watch, 2026-11-02)
- [unverified] The 1.7B model's 256K context length and tool-calling strengths, as stated in Ollama's release notes. Not measured here.

## Sources

- [primary] https://huggingface.co/LiquidAI/LFM3-1.7B — model card and LICENSE
- [primary] https://huggingface.co/LiquidAI/LFM3-Omni-2B — model card
- [primary] https://github.com/ollama/ollama/releases/tag/v0.40.13 — Ollama release notes
