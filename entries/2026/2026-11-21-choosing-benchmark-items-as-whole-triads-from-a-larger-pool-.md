---
id: 2026-11-21-choosing-benchmark-items-as-whole-triads-from-a-larger-pool-
title: Choosing benchmark items as whole triads from a larger pool: what a Deep Research report found (seed 43)
date: 2026-11-21
kind: finding
relevance: watch
fields: [evaluation]
tags: [benchmark-audit, seed-43, harvest]
---

## Summary

Our generated reasoning benchmark builds its items in triads: three claims about one set of facts, one claim per answer
class. After a generator repair, its audit still found one leaning slice: 21 of 33 items in one class. We asked a Gemini
Deep Research run whether choosing items at the pool level would balance cues better than another repair to the
generator. Pool-level choice here means picking whole triads from a larger generated set.

The report is `[aggregator]` AI output. A harvest clerk checked 13 of its claims at the source abstracts, and recomputed
the one simulation that bears on our audit.

## Key points

- **Select whole triads, never single items.** Item-level filters break the shared facts inside a triad, and fact-only
  accuracy can then rise above chance. That figure is the report's own simulation; it is plausible but unreproduced.
- **Pool-level selection is cheap at our sizes.** An integer program that picks whole triads to match named statistics
  solves in seconds, by the report's estimate (not measured by us).
- **Balancing named statistics can push the cue into unnamed ones.** The report's remedy is to audit with "canary"
  statistics that the selector never saw.
- **A fixed tail rule fires by chance.** The rule is: a class share of 7/12 or more on any slice of 30 or more items.
  The clerk's own simulation gives about 1.1% per scan under clean labels, so many scans together fire often. The report
  proposes a calibrated scan in its place, Berk-Jones style, with a null drawn by shuffling labels within triads.
- **An honest benchmark claim is bounded, not "cue-free":**
  - facts alone give exactly chance, by construction;
  - named probe families stay within a stated bound of chance;
  - the claim windows are disclosed.

## Studio relevance

### What it contradicts in our design (read first)

| Finding | Our design today | Decision |
|---|---|---|
| A tail audit over many statistics, tails and pools flags false leans often under clean labels | One tail failure was treated as a real lean, to repair or to disclose | We measured the audit's own false-alarm rates on our pools the same day (see the seed 44 entry). The observed tail is rarer than all but 2 of 2,000 label shuffles, so it is disclosed as real, not dismissed as noise |
| Choosing whole triads from a larger pool is cheap and keeps the shared-facts guarantee | Repairs are made only inside the generator, per item | A triad-selection pilot with canary audits is parked for a later benchmark. The current generator gets no second repair |
| Audit with held-out canary statistics | The audit uses the statistics the generator was tuned against | A candidate for future audits |
| Small released pools are too small for a standalone audit (the report's table, unchecked) | Pools of a few hundred to a few thousand items | A candidate rule: draw small pools from audited large ones |

### Decisions and actionables

1. No second generator repair. The current generator goes forward with a written disclosure.
2. Measure the audit's own false-alarm rate on our pools. This was done the same day; the results are in the seed 44 entry.
3. Triad-level selection with canary audits is parked for a later benchmark.

## Claims

- [verified] One tail scan (prefix slices of 30 or more items, a class share at or above 7/12) fires about 1.08% of the time under independent uniform three-class labels (via: the harvest clerk's Monte Carlo, 20,000 runs, 2026-11-21)
- [verified] Exact Berk-Jones statistics and their p-values can be computed efficiently for one-sided supremum statistics; applying them to triad-shuffled label scans is the report's own idea (via: abstract of Moscovich, Nadler and Spiegelman 2016, arXiv 1311.3190, read by the harvest clerk, 2026-11-21)
- [verified] Adversarial filtering of SNLI lowered model accuracy from 92% to 62%, and models trained on the filtered data generalized better out of distribution (via: abstract of Le Bras et al. 2020, arXiv 2002.04108, read by the harvest clerk, 2026-11-21)
- [verified] Jointly removing a reasoning dataset's statistical features was judged infeasible (via: abstract of Zhang et al. 2023, arXiv 2205.11502, read by the harvest clerk, 2026-11-21)
- [unverified] Forcing balance on measured covariates cut measured imbalance by 95% while raising unmeasured imbalance by 20% (the report's figures, from one scenario of Brooks and Ohsfeldt 2013, where the unmeasured increase ranged from about 4% to 2,200%)
- [unverified] An intact-triad selection over 10,000 triads solves in 17 seconds, and item-level selection moved fact-only accuracy from 33.3% to 55.8% (the report's own simulations; no code was given)

## Sources

- [aggregator] https://gemini.google.com/ — Gemini Deep Research (Gemini 4 Carbon, High), 2026-11-21: report on pool-level cue balancing for a generated benchmark
- [primary] https://arxiv.org/abs/1311.3190 — Moscovich, Nadler and Spiegelman (2016), exact Berk-Jones statistics and their p-values (abstract read)
- [primary] https://arxiv.org/abs/2002.04108 — Le Bras et al. (2020), Adversarial Filters of Dataset Biases (abstract read)
- [primary] https://arxiv.org/abs/2205.11502 — Zhang et al. (2023), on learning to reason from data (abstract read)
