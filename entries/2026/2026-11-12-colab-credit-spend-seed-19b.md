---
id: 2026-11-12-colab-credit-spend-seed-19b
title: Spending about 1,800 expiring Colab units: what the Deep Research report changed (seed 19b)
date: 2026-11-12
kind: finding
relevance: act
fields: [compute, colab]
tags: [colab, gpu, seed-19b, harvest, ban-risk, translation]
---

## Summary

The studio held about 1,800 Colab compute units that expired in about ten days, and asked a Gemini Deep Research
run how to spend them on useful batch GPU work. The report is AI search output, so all of it is `[aggregator]`. The
Publisher spot-checked at source only the claims a decision rests on: the Colab issue-tracker reports and the model
licences all held. The report's throughput numbers, an IFscore comparison, the idle-timeout wording and the pricing
table were not checked and are treated as estimates.

Its main value was six places where it contradicted the studio's own plan, most of them about risk to the paid
account and about assumptions the studio had never measured.

## Key points

- **Refused allocations are not free.** A tracker report describes a paying account blocked on 2026-11-06 after about
  ten user-directed 503 allocation attempts across four card types, on an account that had already been reinstated.
  The studio's A100 requests had been refused about fourteen times since that date.
- **Other tracker reports that held:** a G4 rate rise (2026-10-29), a paid runtime killed after about two hours with
  background execution on, G4 and H100 gating, and the Colab command-line tool losing track of submitted work after a
  connection blip (open on 2026-11-07).
- **The CLI's upload path** is a base64 `PUT /api/contents` request, which explains the upload size ceiling.
- **The tool's current version** on PyPI was 0.8.0.
- **A translation model built for constrained output** (Index-Translate-9B, Apache-2.0 in its Hub metadata, not
  gated, created 2026-09-28) was proposed in place of the Gemma-based translator. The report's claim that it follows
  placeholder instructions far better is unverified.
- **Estimates, not checks:** all five core workloads fit in under a third of the balance (the report's sizing), so
  units were not the binding constraint.
- **Things it confirmed and the studio kept:** G4 as the main card, booking each window at own rate times elapsed
  time, a CPU stub rung before any GPU window, short-lived tokens, a balance floor, Hub downloads for weights, and
  staying off the managed `colab run` and Drive-mount paths.

## Studio relevance

### What it contradicts in our design (read first)

1. **Retrying a refused card put the account at risk.** The "three tries, half an hour apart" rule treated a refusal
   as free; the tracker report shows the same pattern getting a paying account blocked.
2. **The detached-job design might leave the kernel idle.** The runner starts the job outside the kernel and polls;
   the report says background-execution protection only applies while a kernel execution is active. Whether short
   polls keep a VM alive for over an hour was unmeasured.
3. **The translation fix assumed the model was fine.** Every failure logged that day was a placeholder or
   instruction-following failure, so the model choice, not the pins, might be the cause. (Figure unverified.)
4. **The studio was optimising the wrong scarce thing.** Tuning 0.006-unit stubs while about 1,800 units expired; the
   binding limits were kit reliability and review time.
5. **Batching and bit-identical greedy output.** Batched decoding can change reduction order, so a batched
   temperature-0 pass may not reproduce an earlier unbatched pass bit for bit unless batch invariance holds.
6. **Silent card downgrades and a thread-count crash.** The kits checked the session shape but not the GPU's compute
   capability and memory; the report cites L4 or T4 handed out for G4 and an OpenMP crash in CUDA 13 wheels avoided
   by setting the thread count to 8. Neither guard existed.

### Decisions taken (the Publisher's rulings and changes sent to R&D, 2026-11-12)

- **Stop:** no more A100 allocation attempts in any lane. G4 is the GPU card; the L4 stays allowed for the caption
  lane. Allocations go only through a launcher with a circuit breaker: after two refusals in a day on one card type,
  stop that card for the day and report. No agent calls the allocation command directly.
- **Change:** the shared runner gains a boot assert (GPU compute capability and memory per card type; refuse and
  unassign otherwise) and sets the thread count before importing torch.
- **Measure, do not assume:** one CPU window runs the detached pattern for 75 minutes at the real poll cadence with a
  heartbeat file, capped at 0.5 units; if the job dies, the runner moves to a kernel-resident loop before any GPU
  pass over an hour. (The later ledger records the hold as completed with the kernel surviving 4,500 s; see
  `experiments/colab-campaign-2026-11`.)
- **Batching canary:** where an evaluation pass batches, it carries a batch-invariance canary (a few items at batch
  one against the same items inside a full batch, comparing token-id hashes) and reports before any adapter window.
- **Translation A/B:** one capped G4 window of the proposed model against the Gemma translator on the two failing
  READMEs, licence read on the model card first. **Superseded:** the Colab translation lane was closed the same
  afternoon, so this was not run as written.
- **Spend:** the largest sink was the evaluation lane, then volume rendering, then a LoRA lane; the target was three
  G4s kept busy.

Open for the Director and not decided here: object storage as a data plane, and how to use surplus units.

relevance: `act`, and mostly done. The next paid window should still use the launcher and boot assert.

## Claims

- [verified] A Colab tracker report (colabtools #6206) describes a ban on 2026-11-06 after about ten user-directed 503 allocations across G4, H100, L4 and A100 on an already-reinstated account (via: the issue read at source, the Publisher, 2026-11-12)
- [verified] colabtools #6194 (G4 rate rise, 2026-10-29), #5979 (paid runtime killed after about two hours with background execution on) and #6076 (G4 and H100 gated) exist and say what the report says (via: the issues read at source, the Publisher, 2026-11-12)
- [verified] google-colab-cli issue #220 exists: the CLI loses track of submitted work after a connection blip, opened 2026-11-07 and still open (via: the issue read at source, the Publisher, 2026-11-12)
- [verified] The CLI's file-management doc confirms `PUT /api/contents` with `format: base64`; PyPI shows google-colab-cli 0.8.0 (via: the doc and PyPI read at source, the Publisher, 2026-11-12)
- [verified] IndexTeam/Index-Translate-9B exists on the Hub with an Apache-2.0 licence tag, created 2026-09-28, not gated; google/metricx-24-hybrid-xl-v2p6 is Apache-2.0 (via: Hub metadata, the Publisher, 2026-11-12)
- [unverified] TranslateGemma's placeholder-keeping is far worse than a constrained-output translation model's (the report's arXiv:2609.40181 IFscore figures were not checked)
- [unverified] The five core workloads together fit under a third of the unit balance, and the render lane runs at about 200 images per hour per G4 (the report's estimates)
- [unverified] Batched greedy decoding changes the reduction order and so the output (the report, citing a 2025 batch-invariance write-up and the vLLM docs; not opened)
- [unverified] Colab's background-execution protection applies only during an active kernel execution (the report's reading of the FAQ; the wording was not checked, and idle-kernel survival is for the measurement window to settle)

## Sources

- [aggregator] https://gemini.google.com/app/e07081f2f1fc21bc — Gemini Deep Research report "Turning 1,800 Expiring Colab Compute Units into Commercial Studio Output" (seed 19b, 2026-11-12; account-private chat)
- [primary] https://github.com/googlecolab/colabtools/issues/6206 — Google Colab tracker (ban report)
- [primary] https://github.com/googlecolab/colabtools/issues/6194 — Google Colab tracker (G4 rate rise)
- [primary] https://github.com/googlecolab/colabtools/issues/5979 — Google Colab tracker (paid runtime killed)
- [primary] https://github.com/googlecolab/colabtools/issues/6076 — Google Colab tracker (G4 and H100 gated)
- [primary] https://pypi.org/project/google-colab-cli/ — PyPI (version 0.8.0)
- [primary] https://huggingface.co/IndexTeam/Index-Translate-9B — IndexTeam (Apache-2.0 tag)
