---
id: 2026-11-19-when-the-class-can-be-read-off-which-pair-is-asked-about-a-r
title: When the class can be read off which pair is asked about: a root-cause study of a balanced benchmark
date: 2026-11-19
kind: finding
relevance: act
fields: [evaluation, benchmarks]
tags: [d5c, shortcut-audit, contrast-sets, benchmark-design, consult, harvest]
---

## Summary

The d5c benchmark gives a judge model a short list of timing facts and one claim, and asks for supported, unsupported
or cannot tell. Its shortcut audit fails on a pool built from public seeds: 44 of about 600 tests are must-fix, and the
bar is zero. This entry records where those 44 come from, what an outside model said when asked how to remove them, and
what R&D measured when it checked that advice. The work is interim. No design has been chosen and nothing is built.

The cause is simple once seen. A triad is one fact set with three claims, one per class, and the three claims ask about
three different pairs of events. So the class is tied to which pair is asked about, and a pair's place in the fact graph
predicts it. The first fix R&D proposed (ask about one pair, with three numbers) turned out to move the cue into the
claim number, where it is visible without reading the facts at all.

## Key points

- **What was measured (public seeds, counts only).** In all 1,056 triads of a 3,168-item pool, the three claims are
  about three different event pairs. A lookup from a pair's position to the class beats chance: by about +0.05 for the
  rank of the two events and for the kinds of fact near them in ordinary cells, and by +0.11 to +0.21 in the smaller
  "shared" cells (lookup accuracy above one third, minus the same lookup on shuffled labels; in-sample, so sizes are
  upper bounds).
- **It is a design effect.** For 8 of the 12 structural features examined, the most skewed value favours the same
  class in all 11 parts of the pool (for two more it does not, and for two the value is too rare per part to tell). Shuffling labels inside triads and inside part and cell give the same null, so the audit's test is
  not the problem.
- **Why balancing afterwards did not work.** The generator swaps whole triads to balance about 20 features. The one
  target examined, the rank distance between the two events, is balanced exactly (it sits below chance). Swapping cannot
  balance features with about 100 to 300 values, and no swap helps when
  every triad carries the same skew.
- **The shared cells are worst** because their recipes give each class its own chain depth and graph family, with six
  triads per part to balance with. Whole feature values hold a single class there.
- **First proposal: one pair, three numbers.** If a triad asks about one pair with three claim numbers, every feature
  of the facts and the pair is identical across classes, listed or not. In every fact set at least six ordered pairs
  could carry all three classes, so it is feasible.
- **What the consult added.** Asked without being told our preference, Gemini 4 Carbon (AI Studio, High thinking)
  agreed on the cause and pointed out that the one-pair design cannot have a zero cue in the claim number: within a
  triad the supported number is always the smallest (for "at least" claims) and the unsupported the largest. It gave a
  formula: a lookup on the number alone gains about the spread of the three numbers divided by three times the range of
  the lower bound across triads.
- **R&D checked that on the pool.** Putting three numbers on each of today's 3,144 usable claim pairs gives a
  claim-number lookup +0.127 above its null. Our lower bounds span -8 to 38 units and the median gap per cell is 3 to 14
  units, so the wide range the formula asks for is out of reach. The proposal would have added a failure larger than
  most of the ones it removed (the largest structure cues measured were about +0.2, in the shared cells).
- **The consult's alternative: one claim, three number-assignments.** Keep the pair, the direction and the claim number
  fixed, and move the bounds across the claim by changing fact numbers. R&D simulated it: one changed number can never
  reach all three classes (it moves one bound), but two numbers reach all three in 936 of 1,056 claims. Where both
  changed facts touch neither event of the claim (203 claims), the feature with the largest lookup in this study
  (where the claim number sits among the numbers of facts touching the two events) is exactly zero, because those
  numbers do not change. Where at least one changed fact touches an event (733 claims) it is +0.12. A new cue appears in the sum of all numbers (+0.08 to +0.17 in this crude
  simulation) and would have to be offset.
- **A prototype, run through the audit's own gate.** R&D retrofitted the one-claim design onto the public pool and ran
  the gate on the result. With no extra rule, the audit's permutation scheme stops being valid (two of the features it
  blocks on are number comparisons the design now varies). A within-triad test then flags 104 tests when any two
  numbers may change, and 57 when only interior numbers change and a third number is offset to hold the total. One rule fixes
  that: **an edited number never crosses the claim number.** Then every single-number comparison with the claim is the
  same inside a triad. The best variant (any facts may change, a third number offsets the total, the never-cross rule applies) built 704
  of 1,056 triads and had 15 must-fix tests on 2,112 items, against 44
  on 3,168 for today's pool (the smaller pool detects less, so the two counts are not like for like). The 15 are two
  signals: the sum of lower-bound numbers along the shortest chain against the claim (+0.03 to +0.06) and the mean of
  upper-bound numbers along it (+0.02 to +0.04). No structure feature is flagged in any variant.
- **Where the prototype fails.** In the small shared cells only 15 of 264 triads could be built (6%), and none of the
  132 in the two cells where the claim's pair shares an "at most" fact. Today's skeletons there have too few numbers that can move without crossing the claim.
- **A Latin square does not rescue the one-pair design.** Three pairs per fact set, each carrying all three classes,
  with copies rescaled by up to 13 times, still leaves a claim-number cue of +0.07 to +0.10.
- **Recorded depth is nearly always right.** 25 of 2,112 decided items (1.2%) can be proven by a shorter chain than the
  tight one.
- **Every construction moves the cue somewhere.** The useful question is where it lands: in something visible without
  the facts (the claim number), or in the fact numbers on the deciding chain, which is the computation itself.
- **Where the line is.** The consult argued that "where the claim number sits among the numbers next to the two
  events" is the task itself when the deciding chain has one or two facts (every fact on such a chain touches one of the
  two events) and a shortcut when the chain has three or four. That implies an audit bar that depends on depth, which
  ours does not have.
- **Other points from the consult.** Checked by arithmetic: 3,168 items detect about +0.03 overall but only about
  +0.12 inside one 198-item cell, which is its case for auditing the generator on a pool ten times the scored one (not
  run). Partly checked in code: rejecting single claims after classes are assigned can re-create the bias, and our two
  readings do differ on lower bounds only. Not checked: its advice to report an all-three-correct rate per triad and to
  cluster errors by triad.

## Studio relevance

### What it contradicts in our design (read first)

| Finding | d5c today | Decision |
|---|---|---|
| Class is tied to the pair asked about | Three claims on three pairs per fact set; classes get their own depth targets | Open. No more patches to the balancing step until a construction is chosen |
| One pair with three numbers creates a claim-number cue (+0.127 measured) | R&D proposed exactly this on the morning of 2026-11-19 | Withdrawn as a stand-alone fix |
| The shared-cell recipes are class-specific | `_shared_cell_config` in the generator | To be replaced whatever construction is chosen |
| One flat bar treats endpoint-number features alike at every depth | The pre-registration sets one bar of zero | Open; a depth-conditioned bar is a pre-registration change |
| 3,168 items cannot see a moderate cue inside one small cell | The audit runs on the scored pool size | Open; a larger audit pool is cheap because generation is code |

### Decisions and actionables

1. The feasibility study was run the same day (above). What it leaves is one decision, not yet taken: adopt one-claim
   triads; decide whether sums along the chain are a shortcut or the computation being tested; audit on a pool ten
   times the scored one.
2. If chain sums stay in the gating family, no construction tested here reaches zero.
3. Shared cells need purpose-built skeletons before the design can be judged there.
4. The benchmark will not be sealed in the current window.

### What went wrong on our side

The count of 44 was in the audit's own summary for two days while work went into smaller gates. And the first fix was
proposed before anyone measured the cue it would create. Both are recorded here because the bench keeps its errors.

## Claims

- [verified] In all 1,056 triads of the public pool the three claims ask about three different event pairs of one fact set (via: R&D counts-only script on the pool rebuilt from public seeds, 2026-11-19)
- [verified] For 8 of the 12 structural features examined (rank, degree, incidence and fact-kind features), the most skewed value favours the same class in all 11 parts; two others do not and two could not be assessed per part (via: part 1 of R&D's counts-only study scripts on the same pool, 2026-11-19)
- [verified] A one-pair, three-number design on today's fact sets gives a claim-number lookup 0.127 above its within-triad null (via: R&D simulation on 3,144 claim pairs, 2026-11-19)
- [verified] If triads use numbers (m, m+s, m+2s) with m uniform over M positions, a lookup on the number alone scores 1/3 + 2s/(3M) (via: R&D re-derivation of the consult's formula, 2026-11-19)
- [verified] Changing two fact numbers reaches all three classes for a fixed claim in 936 of 1,056 claims; changing one never does (via: R&D simulation, numbers 0 to 60 units, both readings agreeing, 2026-11-19)
- [verified] A retrofit of the one-claim design with the never-cross rule builds 704 of 1,056 triads and has 15 must-fix tests under the audit's scheme S with 2,000 permutations, all on two short-chain sum or mean features (via: R&D prototype script calling the audit's gate functions on the public pool, 2026-11-19)
- [verified] The same retrofit builds 15 of 264 shared-cell triads (via: same script, 2026-11-19)
- [verified] With three pairs per fact set each carrying all three classes and copies rescaled by 1, 2, 3, 5, 8 and 13, a claim-number lookup stays 0.074 to 0.099 above its null (via: R&D simulation, 2026-11-19)
- [verified] 25 of 2,112 supported or unsupported items in the public pool can be proven by a chain with fewer edges than the tight chain (via: R&D hop-limited bound script, 2026-11-19)
- [unverified] Where the deciding chain has three or more facts, a cue from numbers next to the two events is a shortcut and can be suppressed by putting the variation in interior facts (the consult's argument; our simulation supports the second half on 203 claims)
- [unverified] Presenting premises in a shuffled order instead of proof order changes LLM deductive accuracy by over 30% (Chen et al. 2024, as cited by the consult; not read by R&D)
- [unverified] Treating items that share a fact set as independent understates standard errors (Miller 2024, as cited by the consult; not read by R&D)

## Sources

- [aggregator] https://aistudio.google.com/ — AI Studio consult, Gemini 4 Carbon (High thinking, search grounding), 2026-11-19: constructions that remove a class-tied-to-pair cue
- [primary] https://aclanthology.org/2020.findings-emnlp.117/ — Gardner et al. 2020, Evaluating Models' Local Decision Boundaries via Contrast Sets (cited by the consult; not read)
- [primary] https://arxiv.org/abs/1909.12434 — Kaushik, Hovy and Lipton 2020, Learning the Difference that Makes a Difference with Counterfactually-Augmented Data (cited by the consult; not read)
- [primary] https://aclanthology.org/D19-1341/ — Schuster et al. 2019, Towards Debiasing Fact Verification Models (cited by the consult; not read)
- [primary] https://arxiv.org/abs/2402.08939 — Chen et al. 2024, Premise Order Matters in Reasoning with Large Language Models (cited by the consult; not read)
- [primary] https://arxiv.org/abs/2411.00640 — Miller 2024, Adding Error Bars to Evals (cited by the consult; not read)
