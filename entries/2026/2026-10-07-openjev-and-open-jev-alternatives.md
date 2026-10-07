---
id: 2026-10-07-openjev-and-open-jev-alternatives
title: OpenJev and the other open "Jev" models — what each one is
date: 2026-10-07
kind: tool
relevance: watch
fields: [machine-learning, local-llm, ai-infrastructure]
tags: [jev, openjev, typesafe, decision-model, qwen, gguf, vllm, licence, sense-si]
---

## Summary

Jev (TypeSafe AI, launched 2026-09-15) is a hosted "System One" decision model.
It answers typed questions in one call, every answer a calibrated probability:
`choice`, `score`, and `noul` (a yes/no probability). Its weights are not public.
sense-si's decision layer calls the hosted Jev (`typesafe/jev-1.13`).

At least three unrelated open projects are called "OpenJev" or something close.
Only one of them is a near drop-in for the hosted API.

## Key points

- **`openjev/openjev`**, the model Runpod's deploy guide uses:
  - 27B, Qwen-based, fine-tuned "to select the correct option and stay
    consistent when the options are reordered";
  - API mirrors Jev: choice / score / noul, up to 52 options, a 16k-token
    prompt and one image;
  - served by vLLM 0.29 with a custom decision shim;
  - builds: BF16 (~54 GB), FP8 (~29 GB), MLX 8/4-bit, and four GGUF
    quantisations (16.5–28.6 GB, text only).
  - **Benchmark:** its authors' 10,000-question set from 34 public sources.
    The model card reports 84.0% against hosted Jev's 85.4%; Runpod quotes
    84.2% for the FP8 build.
  - **Licence:** weights CC BY-NC 4.0, so a commercial licence comes from the
    authors (support@loopai.com). The worker code is Apache-2.0.
  - **Hardware:** an 80 GB FP8 GPU is recommended. The GGUF builds fit a 32 GB
    card, but the decision API is the vLLM shim, so whether GGUF via llama.cpp
    reproduces it is untested.
- **`autotrust/JEV-27B`** (AutoTrust AI Lab), a distilled student of Jev 1.13:
  - built on Qwen3.8-27B plus a LoRA and a 24-slot decision head;
  - trained with KL loss on Jev's output distributions;
  - six-benchmark mean 84.07% against TypeSafe's 83.85%, self-reported, with
    one of the six benchmarks being OpenJev's own;
  - **weights Apache-2.0**, but the corpus (`SargeDev/jev-distill-corpus-v3`)
    contains about 498k hosted-Jev outputs. Whether TypeSafe's terms allow that
    is unresolved;
  - BF16 only (53.8 GB), no FP8 or GGUF, vLLM + `serve_decide.py`;
  - it mirrors Jev's mistakes: about 7% of 16-option answers change with option
    order alone, and it is weak at arithmetic, dates and counting.
- **`AlexWortega/openjev`** (MIT), later called SemIf:
  - a different design: a Qwen3.5 natural-language-inference cross-encoder at
    0.8B–35B, scoring a premise against a hypothesis;
  - 4B v5 is recommended (JevBench public 0.866, RAGTruth AUROC 0.932);
  - its card says v5 deliberately trained on the **test** splits of MMLU, ARC,
    GSM8K, HellaSwag, GPQA and others, so its scores on those are not
    comparable to anyone's;
  - it is not a choice/score/noul API.
- **Secondary coverage disagrees.** Some articles attribute different numbers
  (0.845 against 0.883 on 102 reconstructed rows) to "OpenJev". Only the model
  cards above are primary.

## Studio relevance

The value for sense-si / ai-jam-sessions is a **free, local Jev-shaped decision
model**. The research protocol in
[[2026-10-07-small-label-decision-learning]] needs many runs: serialisation
sweeps, evidence-family ablations and repeated CV folds. Against the hosted
API's $0.25 cap that is expensive; locally it is free.

**`openjev/openjev`** is the best fit: same question types, a GGUF build that
fits the 5090, and close benchmark parity.

**Gates, all for the Director:**

1. **Licence.** Non-commercial weights are fine for public research. Anything
   feeding a shipped product needs a licence from the authors.
2. **Download.** The GGUF builds are 16.5–28.6 GB.
3. **Rig.** The ai-jam-sessions listener (Qwen3-Omni, about 24 GB) and a 27B
   decision model cannot both be loaded at once on 32 GB.
4. **Serving.** The decision shim targets vLLM, so the first step is a test
   that GGUF serving reproduces the choice/score/noul probabilities. The
   alternative is the FP8 build on an offrig pod.

`autotrust/JEV-27B` has the friendlier weights licence, but its training-data
provenance is the open question, and it needs custom quantisation to fit 32 GB.

## Claims

- [unverified] openjev/openjev scored 84.0% (model card) / 84.2% FP8 (Runpod) on its authors' 10,000-question benchmark against 85.4% for hosted Jev.
- [unverified] autotrust/JEV-27B's six-benchmark mean is 84.07% against TypeSafe Jev 1.13's 83.85% (self-reported).
- [unverified] Whether TypeSafe's terms permit training on Jev outputs is unresolved; their terms were not found in this search.
- [unverified] AlexWortega/openjev v5 was trained on benchmark test splits, according to its own model card.

## Sources

- [primary] https://huggingface.co/openjev/openjev — OpenJev model card
- [primary] https://www.runpod.io/blog/how-to-deploy-openjev-on-runpod-serverless — Runpod deploy guide
- [primary] https://huggingface.co/autotrust/JEV-27B — AutoTrust AI Lab, JEV-27B model card
- [primary] https://huggingface.co/AlexWortega/openjev — AlexWortega, openjev / SemIf model card
- [secondary] https://letsdatascience.com/news/typesafe-ai-launches-jev-decision-model-889a38c0 — TypeSafe AI launches Jev
- [aggregator] https://apidog.com/kr/blog/openjev-open-source-jev-alternatives/ — open-source Jev alternatives roundup
- [user] Runpod newsletter pasted by the Director, 2026-10-07
