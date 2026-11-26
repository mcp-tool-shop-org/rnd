---
id: 2026-11-26-when-should-a-model-reason-adaptive-reasoning-for-local-word
title: When should a model reason? Adaptive reasoning for local worders and judges
date: 2026-11-26
kind: finding
relevance: act
fields: [machine-learning, evaluation]
tags: [rdlab, adaptive-reasoning, deep-research]
---

## Summary

A Deep Research run surveyed when explicit reasoning helps a model's answer and when it doesn't. It also covered
methods for reasoning adaptively, and how to measure what skipping reasoning costs on items with proven keys. Read
against rdlab's code, the main finding is a gap in what has been measured, not in what has been built.
- The paired, triad-clustered statistics the report recommends already exist in the judge scorer.
- But rdlab has never compared thinking on and off, for the judges or for the writers.
- Its thinking models run greedy (temperature 0) on the Ollama path. The report argues against that for thinking
  models.

## Key points

- **Thinking is fixed on.** The bake-off judge adapter turns thinking on in code (`enable_thinking=True`), so there is no
  non-thinking arm to compare against.
- **Temperature.** The Ollama path sends temperature 0 to every model, thinking ones included. The cloud-GPU judge runs
  at 1.0. The two paths differ, and the report says thinking models should not run greedy.
- **What the evidence suggests.** Explicit reasoning tends to help multi-step deduction more than reading-and-judging or
  verbalising tasks, and it can hurt through overthinking. This is direction only: several headline numbers in the
  report were not on the cited abstract pages.
- **Item counts.** A 2-point accuracy difference with about 10% disagreement needs about 2,000 unclustered items
  (a hand check of the report's power figure). rdlab's 1,260 items, clustered in triads, resolve about 3–4 points.
  More distinct items help more than more repeats of the same items.
- **Model mix.** The report's compute tables assume dense models. rdlab's models are mostly mixture-of-experts, so those
  tables don't transfer.

## Studio relevance

`act`, in this order:
1. **Free, done first.** Mine the existing results for answers stopped by length, unparseable answers, and
   thinking-length against correctness, split by class and difficulty.
2. **Cheap local A/B:** the writer with thinking off, and a sweep of the reader-thinking flag on a slice.
3. **A non-thinking twin of the judge,** paired on the same items with the existing scorer. It needs a new adapter and
   a booked GPU window, and the maintainer's answer on whether a non-thinking arm may enter the bake-off record.

The temperature question (keep 0 for reproducibility, or follow each model card) is also with the maintainer.

## Claims

- [verified] The bake-off judge adapter calls the chat template with `enable_thinking=True`. (via: rdlab source at
  origin/main adf5843, read 2026-11-26)
- [verified] The Ollama path sends `temperature: 0` in its options. (via: rdlab source at adf5843, read 2026-11-26)
- [verified] The judge scorer already computes paired, triad-clustered statistics. (via: a clerk read of the scorer at
  adf5843, 2026-11-26)
- [unverified] Specific effect sizes the report gives, such as a confidence-based stopper losing 56–70 points and a 2.15×
  median sample-size saving, were not on the cited abstract pages.

## Sources

- [aggregator] https://gemini.google.com/ — Gemini Deep Research (Gemini 4 Carbon), seed 66, 2026-11-26: report on when models should reason (kept verbatim in the lab's private
  notes, with a harvest read against the code). Six cited arXiv abstracts were opened, and all exist: 2606.00206,
  2609.09989, 2605.30315, 2608.01631, 2409.12183, 2505.11423.
