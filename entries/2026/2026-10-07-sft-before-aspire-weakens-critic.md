---
id: 2026-10-07-sft-before-aspire-weakens-critic
title: Fine-tuning a student before ASPIRE made its critic worse at spotting planted errors (interim, 2 of 3 seeds)
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
trained with ASPIRE alone. Seed 42 showed it; seed 43 reproduces the composite
drop but flips the local direction. Seed 44 is running, and the pre-registered
rule needs all three seeds before a verdict.

## Key points

- **Setup:**
  - Qwen2.5-1.5B student, LoRA r16, critic head on the last hidden layer;
  - teachers: Qwen2.5-32B (local), or Qwen + Gemma-4-31B (composite);
  - judge set: 127 pairs, each a strong answer and the same answer with one
    planted error.
- **Pairwise accuracy** on the same 127 pairs:

  | seed | teacher | control (ASPIRE only) | SFT-then-ASPIRE | change |
  |---|---|---|---|---|
  | 42 | composite | 0.866 [0.787, 0.929] | 0.646 [0.559, 0.732] | −0.22 (CIs do not overlap) |
  | 43 | composite | 0.803 [0.720, 0.874] | 0.504 [0.417, 0.602] | −0.30 (CIs do not overlap) |
  | 42 | local | 0.724 | 0.638 | −0.09 (CIs overlap) |
  | 43 | local | 0.543 [0.465, 0.625] | 0.732 [0.646, 0.817] | +0.19 |
  | 44 | both | running | running | — |

- **Seed noise is large:** the local control critic alone moved 0.18 between
  seeds 42 and 43 (0.724 → 0.543). With the local Qwen-32B teacher, one run per
  seed cannot resolve differences of that size.

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
Treat as unconfirmed until seed 44 lands. After two seeds, the composite-teacher
drop looks real and the local-teacher result looks like noise. The wider lesson
already holds: compare critics over several seeds, never one run each.
Mechanistically the composite drop is plausible:
the SFT shift dominates the representation the critic reads, and ASPIRE spends
its updates pulling against it.

## Claims

- [verified] On 127 planted-error pairs, pairwise accuracy was 0.866 [0.787, 0.929] for control-composite against 0.646 [0.559, 0.732] for SFT-then-ASPIRE, one run each. (via: aspire-si run report 2026-10-07-sft-then-aspire.md, reported by session A 2026-10-07)
- [verified] The SFT improved held-out answers by +0.11, paired CI [+0.016, +0.203], under the pre-registered 0.2 bar. (via: aspire-si run report, 2026-10-07)
- [verified] Seed 43 on the same 127 pairs: control-composite 0.803 [0.720, 0.874], sft-composite 0.504 [0.417, 0.602], control-local 0.543 [0.465, 0.625], sft-local 0.732 [0.646, 0.817]. (via: aspire-si seed 43 run, reported by session A 2026-10-07)
- [verified] ASPIRE's critic trained with the local Qwen-32B teacher varied by about 0.18 in pairwise accuracy between seeds (control-local 0.724 at seed 42, 0.543 at seed 43), one run per seed. (via: aspire-si seeds 42 and 43, reported by session A 2026-10-07)
- [unverified] The effect replicates across seeds. Interim after 2 of 3: the composite drop reproduces (−0.22, −0.30) and the local direction flips (−0.09, +0.19). The pre-registered verdict waits on seed 44.

## Sources

- [rig] aspire-si training runs on 2026-10-07, measured by session A
- [primary] https://github.com/mcp-tool-shop-org/aspire-si/blob/main/docs/runs/2026-10-07-sft-then-aspire.md — run report
- [primary] https://github.com/mcp-tool-shop-org/aspire-si/blob/main/docs/runs/2026-10-07-runs-2-3.md — runs 2–3
- [primary] https://github.com/mcp-tool-shop-org/aspire-si/blob/main/docs/runs/2026-10-07-next-runs-plan.md — next-runs plan
