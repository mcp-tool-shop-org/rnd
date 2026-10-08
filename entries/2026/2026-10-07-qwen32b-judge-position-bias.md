---
id: 2026-10-07-qwen32b-judge-position-bias
title: Qwen2.5-32B as a judge of planted errors — ties, total position bias, and how to plant errors
date: 2026-10-07
kind: finding
relevance: reference
fields: [evaluation, machine-learning, local-llm]
tags: [llm-as-judge, position-bias, pairwise, qwen2.5-32b, planted-errors, aspire-si]
---

## Summary

Measured by aspire-si on 2026-10-07 with Qwen2.5-32B-Instruct judging 127
strong/flawed answer pairs, where each flawed answer carries one planted error.

- **Absolute scores** mostly tie.
- **Pairwise judging** shows total position bias in one order.
- **Generating the planted errors** works only when the model returns a
  structured edit that code applies, not a rewrite.

## Key points

- **Absolute 0–10 scores:** whole-number scores tied 89 of 127 pairs. When the
  judge did separate a pair, it was right 31 of 38 times.
- **A/B at temperature 0:**
  - with the strong answer as A, it picked A for all 127 pairs;
  - with the strong answer as B, it picked the strong answer only 49 of 127
    times.
  - That is total position bias in one order, so both orders are required, and
    "separable" effectively means "it picks the right answer when it comes
    second".
- **Making planted errors:**
  - "rewrite the answer with one error" made the 32B paraphrase everything,
    sometimes labelling its own error;
  - "copy the answer with one change" returned it unchanged 84 of 128 times;
  - what worked: ask for JSON `{original sentence, edited sentence}`, apply the
    edit in code, retry on failure.

## Studio relevance

Applies to every LLM-as-judge in the studio, including the Qwen3-Omni second
rater proposed in [[2026-10-07-single-rater-labels-and-ai-listener]]:

- always score both orders;
- prefer forced choice over absolute scores;
- generate controlled defects by structured edits, never by asking a model to
  rewrite.

**Confirmed (aspire-si PR #36):** score both orders and average the option
probabilities.
- On 149 fresh pairs, Qwen2.5-32B Q4 went from 0.685 on single choices (A chosen
  82%) to 0.886 averaged over both orders, and 0.898 on the 127 pairs here.
- Kev-4B went from 0.547 to 0.973.
- The bias sits on top of a real, consistent preference; averaging over both
  orders recovers it ([[2026-10-07-open-jev-style-decision-models]]).

readouts' training KB holds the AlpacaEval `is_randomize_output_order` protocol
(`rnd readouts alpacaeval`).

## Claims

- [verified] Qwen2.5-32B-Instruct picked position A for all 127 pairs when the strong answer was A, and the strong answer only 49/127 times when it was B. (via: aspire-si judge measurement, reported by session A 2026-10-07)
- [verified] Whole-number 0–10 absolute scores tied 89 of 127 strong/flawed pairs. (via: aspire-si judge measurement, 2026-10-07)
- [verified] Averaging the A/B log-probabilities over both orders lifted Qwen2.5-32B Q4 to 0.886 on 149 fresh planted pairs and 0.898 on the 127 here, from 0.685 on single choices. (via: aspire-si PR #36 confirmation run, reported by session A 2026-10-07)

## Sources

- [rig] aspire-si judge measurements on 2026-10-07, measured by session A
- [primary] https://github.com/mcp-tool-shop-org/aspire-si/blob/main/docs/runs/2026-10-07-sft-then-aspire.md — run report
