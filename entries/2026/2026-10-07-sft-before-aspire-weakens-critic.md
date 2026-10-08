---
id: 2026-10-07-sft-before-aspire-weakens-critic
title: SFT before ASPIRE has no reliable effect on the critic; run-to-run critic variance dominates (3 seeds)
date: 2026-10-07
kind: finding
relevance: watch
fields: [machine-learning, training, evaluation]
tags: [aspire-si, sft, lora, critic, representation-drift, qwen2.5, planted-errors, seed-variance, null-result]
---

## Summary

The aspire-si runs on 2026-10-07 asked whether supervised fine-tuning (SFT) a
student on teacher answers *before* ASPIRE training changes how well ASPIRE's
learned critic separates strong answers from copies with one planted error.

Seed 42 suggested SFT made the critic much worse. Under the pre-registered rule
(three seeds, mean drop ≥ 0.10), **there is no reliable difference**:
- with the composite teacher, the mean drop was 0.06;
- with the local teacher, it was 0.008.

The finding that held is about variance, not the treatment. One configuration's
critic ranged from 0.425 (below chance) to 0.866 across three seeds. The
representation-drift result does replicate: ASPIRE has a repeatable drift direction
that runs against SFT on teacher answers.

The entry keeps its original id so links still resolve; the original claim is
marked `[wrong]` below.

## Key points

- **Setup:**
  - Qwen2.5-1.5B student, LoRA r16, critic head on the last hidden layer;
  - teachers: Qwen2.5-32B (local), or Qwen + Gemma-4-31B (composite);
  - 32 training prompts;
  - judge set: 127 pairs, each a strong answer and the same answer with one
    planted error.
- **Pairwise accuracy** on the 127 pairs:

  | teacher | arm | seed 42 | seed 43 | seed 44 | mean |
  |---|---|---|---|---|---|
  | composite | control (ASPIRE only) | 0.866 | 0.803 | 0.425 [0.333, 0.516] | 0.698 |
  | composite | SFT then ASPIRE | 0.646 | 0.504 | 0.764 | 0.638 |
  | local | control | 0.724 | 0.543 | 0.638 | 0.635 |
  | local | SFT then ASPIRE | 0.638 | 0.732 | 0.512 | 0.627 |

  Mean drops: composite 0.06 and local 0.008, both under the pre-registered 0.10.
- **Critic variance dominates.**
  - The composite control critic spanned 0.425 to 0.866 across seeds.
  - The local control spanned 0.543 to 0.724.
  - Single-run critic comparisons at this scale are meaningless.
- **Training loss is not a guide.** Seed 44's best critic had *rising* critic
  training loss.
- **The drift trajectory replicates across all three seeds:**
  - the fine-tune's drift points the same way every time (cosine 0.98), with
    magnitude 20–23;
  - ASPIRE after SFT opposes it in all 6 runs (cosine −0.49 to −0.77);
  - control ASPIRE, without SFT, also opposes the SFT direction (−0.57 to −0.75)
    and aligns with ASPIRE-after-SFT (+0.67 to +0.81).

  So ASPIRE has a repeatable drift direction, across seeds and teachers, that runs
  against supervised fine-tuning on teacher answers.
- **The fine-tune itself barely paid off:** at 1024 tokens it improved held-out
  answers by +0.11 (paired CI [+0.016, +0.203]), under the pre-registered 0.2 bar.

## Studio relevance

- **No evidence against "SFT first, then preference or critic training".** Don't
  avoid it on the strength of seed 42.
- **Treat learned-critic numbers as distributions.**
  - At 32 prompts, budget at least three seeds per arm and pre-register the
    decision rule.
  - Never select a critic by its training loss.
  - The same discipline applies to the planted-defect detector program
    ([[2026-10-07-planted-defects-program-for-sung-mixes]]) and to any LLM judge
    ([[2026-10-07-qwen32b-judge-position-bias]]).
- **The drift result is the durable one.** ASPIRE pulls representations in a fixed
  direction opposite to SFT on teacher answers. That is a mechanistic lead worth
  following before scaling either step.
- **The method worked.** A pre-registered three-seed rule caught a one-draw
  "finding" before it shaped a design. It is filed here as a correction, not
  deleted.

**Follow-up (2026-10-08):** quadrupling the prompts to 128 lifted every seed's
critic by 0.10–0.13 but left the spread between seeds unchanged (range 0.181);
see [[2026-10-08-more-prompts-raise-the-aspire-critic-s-accuracy-but-not-its-]].

## Claims

- [wrong] SFT before ASPIRE makes the learned critic worse at separating strong answers from planted-error copies. (via: aspire-si seeds 43 and 44 under the pre-registered three-seed rule; mean drops 0.06 composite and 0.008 local, under the 0.10 bar; reported by session A 2026-10-07)
- [verified] Seed 42 on 127 planted-error pairs: control-composite 0.866 [0.787, 0.929] against SFT-then-ASPIRE 0.646 [0.559, 0.732], one run each. (via: aspire-si run report 2026-10-07-sft-then-aspire.md, reported by session A 2026-10-07)
- [verified] Across seeds 42/43/44, mean pairwise accuracy was 0.698 vs 0.638 (composite control vs SFT) and 0.635 vs 0.627 (local), below the pre-registered 0.10 drop. (via: aspire-si seeds 42–44, reported by session A 2026-10-07)
- [verified] ASPIRE's composite control critic ranged from 0.425 to 0.866 pairwise accuracy across three seeds with 32 training prompts. (via: aspire-si seeds 42–44, reported by session A 2026-10-07)
- [verified] Critic training loss did not predict judge accuracy: seed 44's best critic had rising loss. (via: aspire-si seed 44, reported by session A 2026-10-07)
- [verified] The SFT drift direction replicated across seeds (cosine 0.98, magnitude 20–23). ASPIRE's drift opposed it in all 6 SFT-then-ASPIRE runs (cosine −0.49 to −0.77), and control ASPIRE also opposed it (−0.57 to −0.75) while aligning with ASPIRE-after-SFT (+0.67 to +0.81). (via: aspire-si seeds 42–44 drift analysis, reported by session A 2026-10-07)
- [verified] The SFT improved held-out answers by +0.11, paired CI [+0.016, +0.203], under the pre-registered 0.2 bar. (via: aspire-si run report, 2026-10-07)

## Sources

- [rig] aspire-si training runs, seeds 42–44, on 2026-10-07, measured by session A
- [primary] https://github.com/mcp-tool-shop-org/aspire-si/pull/30 — correction PR (docs; open at filing)
- [primary] https://github.com/mcp-tool-shop-org/aspire-si/blob/main/docs/runs/2026-10-07-run-1-seeds.md — run 1 report, seeds 42–44 (on main once #30 merges)
- [primary] https://github.com/mcp-tool-shop-org/aspire-si/blob/main/docs/runs/2026-10-07-sft-then-aspire.md — run report (seed 42; carries a correction note after #30)
- [primary] https://github.com/mcp-tool-shop-org/aspire-si/blob/main/docs/runs/2026-10-07-runs-2-3.md — runs 2–3
- [primary] https://github.com/mcp-tool-shop-org/aspire-si/blob/main/docs/runs/2026-10-07-next-runs-plan.md — next-runs plan
