---
title: Mining an A/B run (ab_dataminer)
description: How rnd abmine reads a record of greedy generations with top-K log-probabilities and says where, and by how much, two arms of the same model differ.
sidebar:
  order: 5
---

When two arms of an A/B run produce different text from the same model, there are three questions. Where did they first part? By how much did the arms' numbers differ before that? Was it a near-tie or a real shift? `rnd abmine` answers them from the run's record, with no GPU and no server. It's the analysis half of the [A/B template](/rnd/handbook/ab-experiments/) for runs that compare backends, builds or settings of one model.

## What the record needs

JSON lines, with one `result` row per arm and prompt:

```json
{"kind": "result", "arm": "S2", "prompt": 0, "tokens": ["The", " sky"],
 "top": [[["The", -0.01], ["A", -4.6]], [[" sky", -0.02], [" color", -5.1]]],
 "prompt_eval_count": 27, "eval_count": 64, "eval_duration_ns": 352000000}
```

- **Greedy decoding** (temperature 0, a fixed seed) on the same prompts in every arm.
- **`top`:** per step, the top-K candidates with their log-probabilities, best first. Ollama returns them with `logprobs: true` and `top_logprobs: K`. In Ollama 0.40.4 they come from the full pre-sampling logits, so `top_k: 1` doesn't hide the runner-up.
- **The arm field** is `arm` (or `block`, as the first sandbox harness wrote it). Other rows are ignored.

## Δz: comparing logits across arms

At each step where both arms saw the same context (the matched prefix, and the fork step itself), with R the reference arm and T the test arm, and t1, t2 R's top two candidates:

    Δz = (ℓR(t1) − ℓR(t2)) − (ℓT(t1) − ℓT(t2))

Δz is the change in the gap between the reference's two best candidates. It doesn't depend on how each arm normalises its probabilities, so it compares the arms' logits directly. A positive Δz means the test arm thinks the two are closer, or flips them. A step is **censored**, and flagged rather than guessed, when t1 or t2 is outside T's top-K. A larger K censors less.

## What `analyze` reports

`rnd abmine analyze <record> [--arm A --arm B …] [--reference R] [--log ARM=PATH …] [--json]`

**For each pair of arms** (the first named is the reference) **and each prompt:**
- **the fork:** the first differing token, or "identical";
- **step-0 Δz,** the first token after prefill. A nonzero step-0 Δz means the arms already disagree after prefill: the difference isn't drift built up during decoding;
- **|Δz| over the matched prefix:** the mean, p95, maximum and count;
- **a drift slope per token,** a least-squares fit of |Δz| on the step;
- **the largest pre-fork spikes:** steps with |Δz| at least 0.1 and at least five times the prefix's median;
- **the fork in detail:** both arms' top candidates there, the token each chose, and Δz at the fork;
- **the chosen-token MAE:** the mean |ℓR − ℓT| of the token both arms chose, over the matched prefix.

**Across arms:** a count of identical prompts and the mean |step-0 Δz| for each pair.

**With `--reference`,** two more things:
- at each fork between two other arms, which way the reference went, where it saw the same context;
- each arm's chosen-token MAE against the reference.

**With `--log`,** what each arm's `OLLAMA_DEBUG` server log says it actually ran: the backend DLLs loaded, the device and compute capability, the FlashAttention setting and how it resolved, the KV cache types, CUDA graph reuse and each prompt's token count.

## Replay, for a GPU grant: `probe`

`abmine.probe` replays a generation as prefill and asks for one token. The input is the model's chat template, rendered exactly in raw mode and ending inside the assistant turn, followed by the generated tokens up to a position.
- Comparing the replay with the decode step, on one arm, separates the prefill path's numerics from the decode path's.
- The replay must first reproduce the recorded prompt token count and step-0 candidates on the same backend, or nothing after it is trusted.
- A later position whose token count doesn't grow by one per token has re-tokenised differently, and is flagged.
- The qwen3 rendering is pinned to its template's sha256, and refuses any other template.

It's a library function for a harness, not a command, because it needs a server, and a server needs a grant.

## The first use

The 2026-10-15 sandbox test of the studio's CUDA 13.4 Update 2 backend for Ollama: the record and its analysis are in [experiments/ollama-cuda-backend](https://github.com/mcp-tool-shop-org/rnd/tree/main/experiments/ollama-cuda-backend).
- It reproduced the outside reviewer's hand figures: Δz 0.770 and 1.345 at the two forks, and 1.294 for the step-14 runner-up shift.
- It showed the two builds disagreeing at step 0 on every prompt, which points at prefill numerics, not accumulated drift.
