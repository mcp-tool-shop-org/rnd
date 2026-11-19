---
id: 2026-11-19-one-claim-three-number-assignments-a-purpose-built-generator
title: One claim, three number-assignments: a purpose-built generator passes the shortcut gate, and judges fail at finding the chain
date: 2026-11-19
kind: finding
relevance: act
fields: [evaluation, benchmarks]
tags: [d5c, shortcut-audit, contrast-sets, benchmark-design, difficulty-pilot, local-judges]
---

## Summary

This follows the entry "When the class can be read off which pair is asked about". That entry found why the d5c
benchmark's shortcut audit failed (44 must-fix tests against a bar of zero) and ended with a retrofit that half worked.
Here R&D built the alternative from scratch, as a prototype outside the real generator: every triad is one set of
events and facts with ONE claim, and the three classes come from three assignments of numbers. On pools of 3,168 items
from public seeds the audit's own gate finds 0 must-fix tests and 0 significant ones, with the bar unchanged. A small
pilot on local judge models then asked whether the new items still test reasoning. They do: the strongest judge mostly
fails by summing the wrong chain of facts, not by adding wrongly.

The construction has been adopted for the next build. The real generator, the learned probe, the planted-cue controls
and a larger pool are still to come, so the zero is a prototype result and not yet a verdict on a sealed set.

## Key points

- **The rules that make it work.** One skeleton and one claim per triad. Facts that name either claim event are the
  same in the three items; only "interior" facts are redrawn. No number on the deciding chain is on a different side of
  the claim number in different items. The width of the feasible range is drawn from one distribution for all three
  classes. The fixed facts carry a share of the bound drawn from almost none to almost all. The totals of all lower and
  of all upper numbers stay clear of the claim number. Every item is solved under both readings of "after" and must
  give exactly its target bounds.
- **A law that explains the leftovers.** A statistic that leaves out a part of the bound whose spread is M sees the
  class with a lift of about shift / (1.5 × M), where shift is how far the bound moves between classes. Small ends and
  small claim numbers therefore leak; large claim numbers with narrow ranges do not.
- **The listed gate.** With the rules above, 292 of the audit's 304 gate features are identical inside every triad, and
  the other 12 differ in at most 2.7% of triads. The gate reports 0 must-fix and 0 significant under both of its
  permutation schemes, on a one-family pool, on a sixteen-shape pool and on a twenty-shape pool.
- **What the listed gate cannot see.** Because almost everything listed is constant inside a triad, the gate has nothing
  left to test. What remains lives in plain statistics of the numbers. R&D measured 13 of them outside the audit
  (lookup accuracy by cell, minus the same lookup with labels shuffled inside triads): up to +0.19 in the first
  prototype, +0.027 once claim numbers were 200 to 500 with widths of 5 to 7, and at most +0.010 on the final pool.
  Those 13 statistics now join the audit's gated list, and its planted-cue controls will plant on them, since the old
  controls have no feature left to bite on.
- **Variety had to be rebuilt.** One skeleton family passes the gate but is thin. The final prototype has twenty
  shapes: chains of four or five facts with one of three decoys (a 2-fact chain, a 3-fact chain, a branch off the
  chain), shared-cell chains with a loose direct fact, an interior edge sometimes written as two facts, and a "fork"
  family in which the two claim events sit on two branches from one root, so the bounds are a difference of two chains.
- **Two older variety rules failed until the fork family existed.** Every chain claim runs along its chain, so the
  share of claims with zero or backward distance in the stage order was 0 against floors of 8% and 6% of items. With
  forks it is 18 to 27% and 16 to 24% per part. Events per item rose from the old "5 or 6" to 5 to 8; that rule was
  amended, with the amendment recorded as made after seeing the data.
- **Decoys are redundant on purpose.** A decoy chain or a loose direct fact changes no bound; it is there so that the
  shortest or most obvious route is not the deciding one. The older rule "every fact is needed" becomes "every deciding
  fact is needed, and every other fact is tagged and verified redundant".
- **The difficulty pilot (180 items, three local judges, temperature 0, thinking off).** The strongest judge, a
  27B-class model, was right on 48 of 90 items with claim numbers 30 to 90 and on 54 of 90 with 200 to 500. Chance is
  30. A 4B model scored 43 and 40. A third judge's run is not usable: half its answers were cut off by the output limit.
- **Where the errors come from.** For the strongest judge, a bound that is the sum of no chain in the facts (plain
  arithmetic or misreading) accounts for 15 and 6 of 90 items. Bounds that are real sums from the facts but from the
  wrong chain (a decoy or the loose fact) account for 53 and 45. Three-digit numbers were not harder: both bounds were
  exact on 34 of 90 items against 20 with two-digit numbers. With the deciding bound right, the label was wrong on 2
  and 3 items.
- **Right for the wrong reason.** 23 and 17 of the strongest judge's correct answers rested on wrong bounds, nearly all
  "cannot tell" reached from a loose fact. So the benchmark gains a second score beside label accuracy: an answer is
  "grounded" when the label is right and the bound that decides the item is exact. On the pilot that is 25 and 37 of 90
  against 48 and 54. Asking a judge for bounds changes the wording it sees, so it runs as a new arm with its own row.

## Studio relevance

- **Act:** the next d5c build uses this construction. The build must reproduce the zero inside the real generator and
  then pass what the prototype never ran: the learned probe (given the same weight as the gate), both corruption
  probes, the planted-cue controls and a pool ten times larger, which is what it takes to see effects near +0.01.
- **A method worth keeping:** when balancing after the fact keeps failing, look for the unit that carries the label. Here
  it was the event pair; holding the pair and the claim fixed removed several hundred features at once, where swapping
  triads had been balancing them one at a time.
- **A caution for any contrast-set benchmark:** making listed features constant inside a set also blinds the audit that
  lists them. The audit has to move to whatever still varies, and its controls have to be planted there.
- **For judge evaluation generally:** label accuracy on a three-way task overstates a judge that never does the work.
  Asking for the intermediate quantity and scoring it separates the two at almost no cost.
- Limits: prototype pools, public seeds, one range of claim numbers and widths; a 13-item list of unlisted statistics
  that is R&D's own; a pilot with one prompt wording, no fork items and thinking off.

## Claims

- [verified] On a 3,168-item prototype pool with twenty skeleton shapes, the audit's main gate reports 0 must-fix and 0 family-wise significant tests under schemes S and W (608 tests each, 2,000 permutations) (via: R&D script calling the audit's gate functions on the pool, public seeds, 2026-11-19)
- [verified] The same gate reports 44 must-fix tests on the current public selected pool (via: the audit run recorded in the earlier entry, 2026-11-19)
- [verified] 292 of 304 gate features take one value inside every triad of the prototype pool; the most variable of the rest differs in 2.7% of triads (via: R&D script over the featurised pool, 2026-11-19)
- [verified] Thirteen number statistics outside the listed features have lookup lifts of at most +0.010 above their within-triad shuffle null on the twenty-shape pool; the largest was +0.027 on the one-family pool and up to +0.19 in the first prototype (via: R&D lookup script, 200 shuffles, 2026-11-19)
- [verified] Per part of 96 triads the twenty-shape pool has 51 to 78 zero-distance and 45 to 69 backward claims of 288 items, 31 to 38 distinct directed skeletons, and 5 to 8 events per item (via: R&D script using the generator's own parsing and skeleton functions on 11 parts, 2026-11-19)
- [verified] A 27B-class local judge scored 48/90 and 54/90, and a 4B judge 43/90 and 40/90, on 180 prototype items at temperature 0 with thinking off (via: R&D pilot through a local Ollama daemon, every completion kept, 2026-11-19)
- [verified] For the 27B-class judge, bounds that are sums of no chain in the facts occur on 15 and 6 of 90 items, and bounds that are real chain sums but not the tightest on 53 and 45 (via: R&D script enumerating every chain between the claim events, 2026-11-19)
- [verified] 23 and 17 of that judge's correct labels rest on a wrong deciding bound; counting only answers with the deciding bound exact gives 25/90 and 37/90 (via: R&D analysis of the pilot's raw outputs, 2026-11-19)
- [unverified] A statistic that omits a part of the bound with spread M sees the class with lift about shift / (1.5 × M) (R&D's working rule from four prototype rounds; fits the measured cases, not derived in general)
- [unverified] The construction will pass a learned probe and the planted-cue controls (not run on any pool of this construction)
- [unverified] Three-digit claim numbers do not make the items an arithmetic test (one judge, 180 items, direction only)

## Sources

- [user] https://github.com/mcp-tool-shop-org/rnd — R&D's own prototype generator, gate runs and difficulty pilot, 2026-11-19 (scripts and raw outputs held in the lab's private working tree; counts reported here)
- [primary] https://aclanthology.org/2020.findings-emnlp.117/ — Gardner et al. 2020, Evaluating Models' Local Decision Boundaries via Contrast Sets (the family of designs this belongs to; cited by the earlier consult, not read)
- [primary] https://arxiv.org/abs/2411.00640 — Miller 2024, Adding Error Bars to Evals (clustered items; cited by the earlier consult, not read)
