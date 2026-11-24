---
id: 2026-11-24-llamaindex-ocria-1-document-parser
title: LlamaIndex OCRia-1 — 4B page-image-to-Markdown parser on Qwen3.5-4B (restrictive RAIL-M licence)
date: 2026-11-24
kind: release
relevance: watch
fields: [vision, document-ai]
tags: [ocr, document-parsing, vlm, qwen3.5, ollama, llamaindex, licence, rail-m]
---

## Summary

LlamaIndex's OCRia-1 is a ~4B vision-language model fine-tuned from Qwen's Qwen3.5-4B that turns one page image into Markdown,
with tables and charts as HTML tables, diagrams as mermaid and formulas as LaTeX. It ships on Ollama as `llamaindex/ocria-1:bf16`
(about 10 GB) and on Hugging Face. **Its licence is not open source and restricts commercial use, competing services and use of
its outputs**; the Qwen base underneath is Apache-2.0. The benchmark numbers are self-reported on LlamaIndex's own benchmark, and
the card and the blog disagree on them.

## Key points

- **Licence chain** (LICENSE at HF revision 2b133ff8, read 2026-11-24; quotes are exact fragments, the rest paraphrased). [unverified]
  - **OCRia-1:** Hugging Face licence tag `ocria-1-license`. Title "OCRia-1 MODEL AND CODE LICENSE"; "Licensor: LlamaIndex, Inc.";
    "Based on the AI Pubs Open RAIL-M License, Version 0.1, March 2, 2023 (http://licenses.ai/), as modified below." It covers the
    weights and the `ocria_grounding` code, and §1A says "The Licensed Code is not open-source software."
  - **Acceptance by download:** the preamble binds anyone "BY DOWNLOADING, REPRODUCING, DISTRIBUTING OR USING THE MODEL".
  - **§1(o) Competing Service:** any product or service (API, hosted service or software) "that offers document parsing, optical
    character recognition, or extraction of text, tables, charts or fields from documents" and competes with the licensor's
    (LlamaParse and LlamaCloud are named).
  - **§1(n) Research Purposes** (three parts): "non-commercial research, teaching and study, including at academic and non-profit
    institutions"; evaluating or benchmarking the model, including publishing results; and internal R&D that does not use the
    model, its derivatives or its output in a product, service or production workflow for third parties or for the user's business
    operations.
  - **Attachment A 2(a)/(b):** if the user's organisation "generated more than two million US Dollars ($2,000,000) in gross revenue in
    the prior year" or "has raised more than two million US dollars ($2,000,000) in total equity or debt funding from any source", only
    personal use or Research Purposes.
  - **Attachment A 2(c):** no use "to provide, or as part of, a Competing Service, whatever Your revenue or funding, except for
    Research Purposes."
  - **§8 (share-alike, output):** "Output may not be used to create a Derivative of the Model", distillation included, except for
    Research Purposes. Use restrictions must pass to downstream users; attribution required.
  - Commercial licences: through LlamaIndex. Legal effect not assessed here.
  - **Base:** `Qwen/Qwen3.5-4B`, licence `apache-2.0` (also cited in the OCRia LICENSE's Attachment B). The OCRia card's text says it
    was fine-tuned from Qwen3.5-4B-Base; the LICENSE and the Ollama readme name Qwen3.5-4B. Not reconciled.
- **Where it runs.** The Ollama tag needs MLX: on our Windows/CUDA rig `ollama pull llamaindex/ocria-1:bf16` fails with
  "this model requires MLX support" (observed 2026-11-24), so the Ollama build is Apple-only. The official weights are one
  `model.safetensors` (10.35 GB, arch `qwen3_5`) on Hugging Face; the card says serve with vLLM 0.30+ and an image budget of about
  4.1 MP. A third-party GGUF (`prithivMLmods/OCRia-1-GGUF`, Q4_K_M 3.17 GB plus an mmproj) exists and is unvetted.
- **Size and memory.** One Ollama tag, `ocria-1:bf16`, 10 GB (readme: about 10.35 GB of weights). **VRAM: not stated** anywhere;
  the only tested hardware named is an Apple M4 Max (36 GB unified memory, MLX, Ollama 0.40.16). Context: the Ollama listing says
  256K (the base is 262,144 tokens natively); the Ollama readme default is 32,768 and the HF quickstart serves at
  `--max-model-len 32768`. [unverified]
- **Use.** One page image per request (PDFs rendered at 300 DPI first; the PDF text layer is not read). The card's own system prompt
  unchanged, no user text, **thinking off** (the format breaks otherwise), temperature 0, max_tokens 24,576.
- **Benchmarks (self-reported).** HF card: ParseBench 2 overall 85.24 (Text 87.87, Formatting 91.59, Tables 86.28, Charts 77.63,
  Visual grounding 85.96, Forms 82.09); ParseBench 1 overall 84.65; olmOCR-bench 90.5 (mean of the table and formula categories
  only); PulseBench-Tab 84; fr-bench-pdf2md 72.1 (technical report arXiv 2611.00092). The blog gives ParseBench overall 87.4 and
  olmOCR-bench 83.5 (all eight categories). ParseBench is maintained by LlamaIndex. The two ParseBench figures could not be reconciled.
- **Date.** The blog shows "Released Oct 22, 2026"; the Ollama tag and the HF LICENSE commit are about a day old as of 2026-11-24.

## Studio relevance

`watch`. **Not downloaded, by the Director's decision of 2026-11-24:** this entry is the licence analysis only. No pull, no terms
accepted (downloading is acceptance), no build card.
- **plain-sight (our public OCR / image-reading MCP tool): shipping OCRia-1 in it would likely fall under Attachment A 2(c).** A public
  tool that parses documents or extracts text and tables is a Competing Service by §1(o), and 2(c) applies whatever our revenue or
  funding. That rules it out for plain-sight as shipped.
- **Dataset work:** §8 bars using its output to create a derivative of the model (distillation included) outside Research Purposes,
  and Research Purposes part (iii) excludes output used in production workflows or business operations.
- **What it would allow:** evaluating or benchmarking it, and publishing the results, counts as Research Purposes (§1(n) part ii).
  Any such trial would still need the Director's go, a licence-registry entry with a snapshot, a GPU grant, and VRAM measured at the
  context sent.
- **Measure before trusting the numbers:** the benchmarks are the vendor's own and disagree between card and blog; VRAM is unstated.

## Sources

- [user] shared by the Director (relayed by the Publisher), 2026-11-24; the MLX-only pull failure and the weights facts checked by the Publisher on the rig, 2026-11-24
- [primary] https://huggingface.co/llamaindex/OCRia-1/raw/2b133ff86040704cec5dce1b3c99eec5c7268217/LICENSE — licence text, raw (read; no weights downloaded)
- [aggregator] https://huggingface.co/prithivMLmods/OCRia-1-GGUF — third-party GGUF, unvetted
- [primary] https://ollama.com/llamaindex/ocria-1 — Ollama listing and readme
- [primary] https://ollama.com/llamaindex/ocria-1/tags — tags and sizes
- [primary] https://huggingface.co/llamaindex/OCRia-1 — model card (licence tag, benchmarks, quickstart)
- [primary] https://huggingface.co/llamaindex/OCRia-1/blob/2b133ff86040704cec5dce1b3c99eec5c7268217/LICENSE — licence text at that
  revision
- [primary] https://huggingface.co/Qwen/Qwen3.5-4B — base model card (Apache-2.0)
- [primary] https://www.llamaindex.ai/blog/parse-ocria-1 — LlamaIndex announcement (self-reported numbers)
