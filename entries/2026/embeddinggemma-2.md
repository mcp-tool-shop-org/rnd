---
id: embeddinggemma-2
title: EmbeddingGemma 2 — a multimodal embedder for studio retrieval
date: 2026-10-14
kind: tool
relevance: act
fields: [studio-tooling]
tags: [embeddings, retrieval, gemma]
---

## Summary

EmbeddingGemma 2 is Google DeepMind's open embedding model. It maps text and code, images, video and audio into
one 768-dimension space, and the vectors can be cut to 512, 256 or 128 dimensions. The text model is 270M
parameters. A vision encoder (170M) and an audio encoder (300M) load only when asked for. It reads 8,192 tokens,
takes short task prefixes, and must run in bfloat16 or float32: in float16 its activations overflow, and it returns
NaN or silently degraded vectors. Apache-2.0, not gated. The studio has it installed for a CPU benchmark against
offrig's current embedder, nomic-embed-text.

## Key points

- **Sizes.** The full model is 740M parameters, and text-only is 270M (a 130M backbone plus a 140M embedding table
  over a 262K vocabulary). Text and image is 440M, and text and audio is 570M. One 1.49 GB `model.safetensors`
  carries all of it.
- **Truncation.** Matryoshka dimensions are 768, 512, 256 and 128. Re-normalize after cutting, and give queries and
  documents the same dimension. 256 keeps nearly all text and code quality. 128 costs multimodal quality.
- **Prefixes.** `task: search result | query: …`, `task: code retrieval | query: …` and `title: {t} | text: {c}` for
  documents. `prompt_name="Document"` silently writes `title: none`. Images, audio and video take no prefix.
- **One space across encoders.** A text-only index can gain image or audio vectors later without re-embedding
  (the developer guide).
- **Runtimes.** The developer guide names vLLM, Transformers, sentence-transformers ≥ 6.1, SGLang, MLX, Ollama,
  LM Studio and LiteRT. Ollama's library builds are MLX tensor builds. On this Windows rig, Ollama 0.40.4 refuses
  them ("requires MLX support"), so Ollama can't serve it here yet.
- **Fine-tuning.** The cookbook has text and multimodal notebooks: sentence-transformers, `(anchor, positive,
  negative)` triplets, MultipleNegativesRankingLoss. The example is three triplets, so it shows the recipe, not a
  gain. The guide also points to Unsloth.

## Studio relevance

- **act: benchmark it against offrig's embedder.** offrig's index embeds with nomic-embed-text on a CPU-only Ollama.
  The design is `experiments/embeddinggemma-2/design.md`, and it runs on the CPU with no card grant. If
  EmbeddingGemma 2 wins, adopting it needs an Ollama-compatible embedding endpoint on the CPU, the way npu-serve
  serves the NPU, because Ollama can't serve it on Windows.
- **Not the NPU.** The Intel NPU computes in FP16, and the model card rules FP16 out. The probe was skipped on
  precision (outside review, 2026-10-15). An earlier R&D argument about a host-pinned vocabulary table came from
  gemma4 on the 5090, not from the NPU, and doesn't support the skip.
- **Later: canon search across modalities.** style-dataset-lab art and its prose, or vocology audio, in one index.
  That waits until text has won.
- **Later: fine-tuning on studio pairs,** which the intel-npu entry already lists as the next step for embedders.

## Claims

- [verified] The text-only model loads on the rig's CPU in float32, with 271M parameters, and returns 768-dimension vectors without NaN. Four short texts encode in 0.21 s after a 2.5 s load. (via: R&D smoke run, sentence-transformers 6.1.0, transformers 5.19.0, torch 2.14.1+cpu, 2026-10-15)
- [verified] `model.safetensors` (1,488,915,288 bytes) matches its blob sha256 `197a3296…3d79` in the HF cache. (via: R&D sha256 check, 2026-10-15)
- [verified] Ollama 0.40.4 on Windows refuses `embeddinggemma-2:270m-bf16-text` with "this model requires MLX support", and every library tag is a tensor build. (via: R&D `ollama pull` and the registry manifests, 2026-10-15)
- [unverified] MTEB multilingual v2 61.36, MTEB English v2 68.46 and MTEB code v1 78.68 at 768d. EmbeddingGemma 1 scores 61.15 and 68.76 on the multilingual and code sets. (model card)
- [unverified] At 256d: MTEB English v2 67.78, code 76.18. (model card)
- [unverified] Activations exceed float16's range, giving NaN or silent degradation in float16. (model card)

## Sources

- [primary] https://huggingface.co/google/embeddinggemma-2 — the model card, Google DeepMind
- [primary] https://developers.googleblog.com/embeddinggemma-2-the-developer-guide/ — the developer guide, Google
- [primary] https://github.com/google-gemma/cookbook — `docs/embeddinggemma/` notebooks (inference, multimodal,
  text and multimodal fine-tuning), Google
- [primary] https://ollama.com/library/embeddinggemma-2 — the Ollama library tags (MLX tensor builds)
- [primary] https://github.com/ollama/ollama/releases — v0.40.0 notes: MLX on Apple Silicon by default; MLX support
  for embeddinggemma-2
