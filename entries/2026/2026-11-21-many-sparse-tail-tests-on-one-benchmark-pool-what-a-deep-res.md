---
id: 2026-11-21-many-sparse-tail-tests-on-one-benchmark-pool-what-a-deep-res
title: Many sparse tail tests on one benchmark pool: what a Deep Research report found (seed 44)
date: 2026-11-21
kind: finding
relevance: act
fields: [evaluation]
tags: [benchmark-audit, multiple-testing, seed-44, harvest]
---

## Summary

Our generated reasoning benchmark is audited for answer cues before release. The audit runs two rules:
- a **gate**: 144 kept tests, with family-wise control by single-step min-p over 4,999 label shuffles inside each triad;
- an **edge rule**: no class share of 7/12 or more on any slice of 30 or more items, across 156 tail families.

We asked a Gemini Deep Research run how to control errors across many sparse, nested tail tests like these. The report
is `[aggregator]` AI output. A harvest clerk checked four of its source claims (several other cited papers could not be
fetched) and recomputed its arithmetic. Then, the same day, we ran the measurement it recommended on our own pools: a
label-blind null of the whole gate.

## Key points

- **Permutation p-values are never zero.** Report (b+1)/(B+1), never b/B.
- **Empirical inner p-values put a floor under the family-wise p.** If each test's inner p is estimated from the same
  permutations, every permutation that is the strict maximum on some test ties the floor. The smallest family-wise p is
  then roughly the number of distinct "winning" shuffles divided by B+1. Exact inner p-values remove that floor.
  Under the within-triad null, a slice's count for one label is a fixed part from the triads wholly inside it, plus
  two binomial sums over the triads split across its boundary.
- **Nested tail slices act like one random walk looked at many times.** By the report's own simulation, which we did not
  check, the effective number of tests grows with the log of the slice-size range.
- **Report three pools together, not as "1 of 3 fired".** Give a pooled test plus a 2-of-3 partial-conjunction p, with
  the effect at a fixed cut in the other pools. Reading one firing out of three as "no replication" is the
  significant-versus-not-significant fallacy.
- **Calibrate the whole gate cheaply with a label-blind null.** Keep the real features and the triad structure, shuffle
  the labels, and put every shuffle through the gate.

## Studio relevance

### What it contradicts in our design (read first)

| Finding | Our design today | Decision |
|---|---|---|
| Empirical inner p-values create a floor in the family-wise p | The gate's min-p ranks each test inside the same 4,999 shuffles | Confirmed in our code. The acceptance pools' floors are 0.0158 / 0.0146 / 0.0160, and the one flagged test's family-wise p (0.0146) sits exactly at its pool's floor. The disclosure now says it means "as extreme as the test can resolve", not a measured 1.5% |
| The edge rule has no multiplicity control | Any trip among 156 families fails a pool | Measured with a label-blind null: 2,000 within-triad shuffles per acceptance pool, gate and edge rule exactly as coded. The edge rule fires on 2.25% / 1.75% / 0.90% of shuffles (cal / hold / ref), and on at least one pool in 4.85% |
| The gate's real false-alarm rate is unknown | Bounded at 5% by construction | The gate calls a must-fix on 0.35% / 0.30% / 0.20% of shuffles, and on at least one pool in 0.85%, every one through the tail rule |
| A real flag can be indistinguishable from noise at the floor | One hold tail was flagged at the floor | Against the same shuffles, a slice share as high as the hold tail's 0.636 appeared in 2 of 2,000 (0.1%). So the tail is very unlikely to be chance alone, and its effect stays small: answering "supported" on those items gains about 10 answers over chance across the hold pool's 31,680 items, about 1 answer per 3,000 (R&D's gate record) |
| Gate slices on discordant triads, not item count; report pooled plus 2-of-3 | Slices of 30+ items; per-pool reading | Candidates for future audits. A change to audit rules is the Director's decision, and it is not applied to the current benchmark |

### Decisions and actionables

1. The disclosure for the current benchmark carries the floor sentence, the null rates and the hold-tail sentence.
2. Exact inner p-values and discordant-triad gating are proposed for future benchmark audits, for the Director's
   decision. Nothing changes in the current audit.

## Claims

- [verified] Permutation p-values should never be zero, and the naive estimate understates them by about 1/m, for m permutations (via: abstract of Phipson and Smyth 2010, arXiv 1603.05766, read by the harvest clerk, 2026-11-21)
- [unverified] The valid estimate is (b+1)/(B+1), adding one to both counts (a standard result; the abstract read does not state the formula)
- [verified] With B = 2,000 permutations, 1/(B+1) = 0.0005, which is above a 156-family Bonferroni bar at alpha 0.05 (0.05/156 = 0.000321); 3,120 permutations is the smallest count that gets under it (via: recomputed by the harvest clerk, 2026-11-21)
- [verified] Modified Bonferroni and Holm procedures for discrete tests control the family-wise error under arbitrary dependence (via: abstract of Zhu and Guo 2019, arXiv 1711.08147, read by the harvest clerk, 2026-11-21)
- [verified] For independent pools at 20% single-pool power, exactly one firing in three pools has probability 0.384, and two or more 0.104; the report's Fisher 2-of-3 formula, p(2)p(3)(1 - ln(p(2)p(3))) with p(2) and p(3) the two largest of the three p-values, gives 0.28 on (1e-5, 0.2, 0.4) and 0.047 on (0.09, 0.09, 0.09) (via: recomputed by the harvest clerk, assuming independent pools, 2026-11-21)
- [unverified] That formula is Benjamini and Heller's partial-conjunction test (the source definition was not read)
- [verified] Under 2,000 within-triad label shuffles of each of our three acceptance pools, the edge rule fired on 2.25% / 1.75% / 0.90% of shuffles and on at least one pool in 4.85%; the gate's must-fix rate was 0.35% / 0.30% / 0.20% and 0.85% across pools; across all 2,001 rows (the real labels plus 2,000 shuffles), the share of rows at the gate's floor equalled the floor's own value (3.30% / 3.55% / 3.80% of the 2,000 shuffles alone, against floors of 0.03348 / 0.03598 / 0.03848) (via: R&D's null run, every sanity check passed, including an exact reproduction of the gate's decisions on the real labels, 2026-11-21)
- [unverified] The effective number of tests grows with the log of the slice-size range: 8.0 for 471 slices, 13.9 for 1,971, 44.1 for 14,971 (the report's own simulation)
- [unverified] Testing against a tolerated lean instead of zero cuts false alarms of a dual gate from 20.6% to 3.5% (the report's own simulation)

## Sources

- [aggregator] https://gemini.google.com/ — Gemini Deep Research (Carbon, High), 2026-11-21: report "Discrete Multiple Testing Benchmark Audit"
- [primary] https://arxiv.org/abs/1603.05766 — Phipson and Smyth (2010), Permutation P-values Should Never Be Zero: Calculating Exact P-values When Permutations Are Randomly Drawn (abstract read)
- [primary] https://arxiv.org/abs/1711.08147 — Zhu and Guo (2019), Familywise Error Rate Controlling Procedures for Discrete Data (abstract read)
