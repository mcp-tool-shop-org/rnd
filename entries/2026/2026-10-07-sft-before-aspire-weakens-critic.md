---
id: 2026-10-07-sft-before-aspire-weakens-critic
title: Fine-tuning a student before ASPIRE made its critic worse at spotting planted errors (one seed)
date: 2026-10-07
kind: finding
relevance: watch
fields: [machine-learning, training, evaluation]
tags: [aspire-si, sft, lora, critic, representation-drift, qwen2.5, planted-errors]
---

## Summary

aspire-si run on 2026-10-07. A student was supervised fine-tuned (SFT) on
teacher-written answers before ASPIRE training. Its learned critic then
separated strong answers from planted-error copies much worse than a control
trained with ASPIRE alone. There is one training run per condition; seeds 43/44
are pending.

## Key points

- **Setup:**
  - Qwen2.5-1.5B student, LoRA r16, critic head on the last hidden layer;
  - teachers: Qwen2.5-32B (local), or Qwen + Gemma-4-31B (composite);
  - judge set: 127 pairs, each a strong answer and the same answer with one
    planted error.
- **Pairwise accuracy:**

  | teacher | control (ASPIRE only) | SFT-then-ASPIRE | CIs |
  |---|---|---|---|
  | composite | 0.866 [0.787, 0.929] | 0.646 [0.559, 0.732] | do not overlap |
  | local | 0.724 | 0.638 | overlap |

- **Representation drift:**
  - the fine-tune moved hidden states about 30× as far as ASPIRE does (shared
    direction 0.96);
  - ASPIRE's own drift then pointed against the fine-tune's (cosine −0.77);
  - no drift direction tracked teacher quality scores beyond a
    random-direction null.
- **The fine-tune itself barely paid off:** at 1024 tokens it improved held-out
  answers by +0.11 (paired CI [+0.016, +0.203]), under the pre-registered 0.2
  bar.

## Studio relevance

A watch item for any "SFT first, then preference or critic training" plan.
Treat as unconfirmed until seeds 43/44 land. Mechanistically it is plausible:
the SFT shift dominates the representation the critic reads, and ASPIRE spends
its updates pulling against it.

## Claims

- [verified] On 127 planted-error pairs, pairwise accuracy was 0.866 [0.787, 0.929] for control-composite against 0.646 [0.559, 0.732] for SFT-then-ASPIRE, one run each. (via: aspire-si run report 2026-10-07-sft-then-aspire.md, reported by session A 2026-10-07)
- [verified] The SFT improved held-out answers by +0.11, paired CI [+0.016, +0.203], under the pre-registered 0.2 bar. (via: aspire-si run report, 2026-10-07)
- [unverified] The effect replicates across seeds (43/44 pending).

## Sources

- [rig] aspire-si training runs on 2026-10-07, measured by session A
- [primary] https://github.com/mcp-tool-shop-org/aspire-si/blob/main/docs/runs/2026-10-07-sft-then-aspire.md — run report
- [primary] https://github.com/mcp-tool-shop-org/aspire-si/blob/main/docs/runs/2026-10-07-runs-2-3.md — runs 2–3
- [primary] https://github.com/mcp-tool-shop-org/aspire-si/blob/main/docs/runs/2026-10-07-next-runs-plan.md — next-runs plan
