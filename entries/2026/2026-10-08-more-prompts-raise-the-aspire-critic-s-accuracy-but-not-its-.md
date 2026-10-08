---
id: 2026-10-08-more-prompts-raise-the-aspire-critic-s-accuracy-but-not-its-
title: More prompts raise the ASPIRE critic's accuracy but not its spread between seeds
date: 2026-10-08
kind: finding
relevance: act
fields: [machine-learning]
tags: [aspire-si, critic, seed-variance, planted-errors, qwen2.5, pre-registered, rented-gpu]
---

## Summary

aspire-si's step 2 asked whether training the critic on more prompts would tame
the run-to-run variance that swamped the SFT-before-ASPIRE experiment
([[2026-10-07-sft-before-aspire-weakens-critic]]). It ran the control-local arm
(Qwen2.5-1.5B student, bf16 Qwen2.5-32B teacher) on 128 prompts instead of 32,
seeds 42, 43 and 44, and read the result under rules committed before the run
(aspire-si #35).

Four times the prompts lifted every seed's critic by 0.10 to 0.13, but the spread
between seeds stayed exactly the same: a range of 0.181 at both prompt counts.
Prompt count alone does not fix critic variance.

## Key points

- **Pairwise accuracy on the 127 planted-error pairs:**

  | seed | 128 prompts | 32 prompts |
  |---|---|---|
  | 42 | 0.827 | 0.724 |
  | 43 | 0.646 | 0.543 |
  | 44 | 0.764 | 0.638 |
  | mean | 0.745 | 0.635 |

- **Rule 1 (spread shrinks) fails:** a range of 0.181 at both prompt counts.
- **Rule 2 (level rises) passes:** the mean rose from 0.635 to 0.745, with every
  seed up by 0.10–0.13.
- **The seed order held:** 42 > 44 > 43 at both prompt counts. The variation
  follows the seed, not the prompt set. That points at something the seed
  fixes, such as critic-head initialisation or student sampling. Untested.
- **Reference judges on the same pairs:** pinned Kev-4B averaged over both orders
  0.976; the rnd Kev-4B judge fine-tune about 0.99
  ([[2026-10-07-open-jev-style-decision-models]]). Every critic is well below
  both.
- **Step 3** (the fine-tune follow-up) did not launch: its plan required rule 1 to
  pass.
- **Cost:** $8.03 for the run (offrig plan 19), plus $1.86 and $2.24 for two
  stopped attempts: a teacher download that was too slow, and a wrong time
  estimate.
- **Rented-GPU lessons:**
  - time a real model-shard download before planning, not a plain HTTPS stream;
  - ASPIRE generates epoch-1 dialogues online, about 1.67 min each with three
    runs side by side; epochs 2 and 3 take minutes. Plan time from epoch 1.

## Studio relevance

- **For aspire-si:** more prompts is worth having (+0.11 mean), but a single seed
  still cannot be trusted. Keep three seeds per arm and pre-registered rules. The
  next lever to test is the seed itself: fix the critic-head initialisation
  across seeds while varying sampling, and the reverse, to see which carries the
  0.18 spread. Session A has put it to the Director as the leading option;
  nothing is planned until he decides.
- **For anyone needing a judge of planted errors now:** use Kev-4B averaged over
  both orders, or the Kev judge fine-tune, not an ASPIRE critic.
- **For offrig planning:** the two lessons above go into how pod time is
  estimated. A stopped attempt cost more than a quarter of the run.

## Claims

- [verified] With 128 training prompts, control-local ASPIRE critics scored 0.827, 0.646 and 0.764 pairwise accuracy on the 127 planted-error pairs (seeds 42, 43, 44), against 0.724, 0.543 and 0.638 with 32 prompts: the mean rose by 0.11, the range stayed 0.181. (via: aspire-si step 2, offrig plan 19, read under #35; reported by session A 2026-10-08)
- [verified] The step 2 run cost $8.03, with $4.10 more spent on two stopped attempts. (via: offrig plan 19 and the stopped attempts, reported by session A 2026-10-08)
- [unverified] ASPIRE critic variance between seeds comes from critic-head initialisation or student sampling. (hypothesis from the unchanged seed order; untested)
- [unverified] ASPIRE epoch-1 dialogue generation takes about 1.67 min per dialogue with three runs side by side on the rented pod. (session A's measurement; one run)

## Sources

- [rig] aspire-si step 2, seeds 42–44 at 128 prompts, offrig plan 19, 2026-10-08, run and measured by session A; data at the aspire-si runs folder `2026-10-08-p128/plan19/`
- [primary] https://github.com/mcp-tool-shop-org/aspire-si/pull/42 — step 2 run report (docs/runs/2026-10-08-step-2.md)
- [primary] https://github.com/mcp-tool-shop-org/aspire-si/pull/35 — the rules committed before the run
- [user] Result relayed by session A (aspire-si), 2026-10-08
