---
title: Can one claim with three sets of numbers remove a benchmark's shortcuts?
description: In a prototype, the audit's listed tests find nothing, and a small pilot suggests the hard part becomes finding the right chain of facts. Not a verdict on a sealed set, and everything the audit does not list is unproven.
date: 2026-11-19
status: interim
shelf: not yet (the real build exists and is under audit; no pass yet)
---

## The question

d5c is the studio's test for comparing local models as judges on three-way verification: is a claim supported by
the facts, ruled out by them, or impossible to tell? Its items come in triads, one per answer. The benchmark's
shortcut audit failed on a pool built from public seeds: 44 tests were must-fix, and the bar is zero.

An earlier study found the cause. A triad was one set of facts with three claims about three different pairs of
events, so the answer could be read off which pair was asked about. The question here: if a triad instead keeps ONE
claim and changes only numbers in the facts, do the shortcuts go, and is what is left still a reasoning test?

## What we found

- **The audit's listed tests find nothing.** On a 3,168-item prototype pool the audit's gate reports 0 must-fix and
  0 significant tests under both of its permutation schemes (608 tests each), with the bar unchanged. Today's pool:
  44. This is a prototype result on the listed tests, not a verdict on a sealed set.
- **The rules that do it.** One skeleton and one claim per triad. Facts that name either claim event are the same
  in all three items. No number on the deciding chain changes side of the claim number. The width of the feasible
  range is drawn the same way for all three answers. Totals stay clear of the claim number.
- **Making listed features constant blinds the audit that lists them.** 292 of the audit's 304 features are now
  identical inside every triad, and the other 12 differ in at most 2.7% of triads. What is left lives in plain
  statistics of the numbers. R&D measured 13 of them
  outside the audit: the largest lift was +0.194 in the first prototype, +0.027 with claim numbers of 200 to 500
  and narrow ranges, and +0.010 on the final pool. The studio has decided to add those 13 to the audit's list.
- **A working rule for the leftovers (unverified).** A statistic that leaves out a part of the bound whose spread is
  M sees the answer with a lift of about shift / (1.5 × M), where shift is how far the bound moves between answers.
  It fits the cases measured and is not derived in general. Nothing makes the lift exactly zero.
- **Variety had to be rebuilt.** One skeleton family passes the gate but is thin. The final prototype has twenty
  shapes, including a "fork" in which the two claim events sit on two branches from one root, so the bounds are a
  difference of two chains. Without forks, two older variety rules (claims with zero or backward distance in the
  stage order) could not be met.
- **A small pilot points at chain-finding, not adding. Direction only.** 180 items of the one-family version,
  thinking off, working capped at 80 words: 90 items with claim numbers 30 to 90 and 90 with 200 to 500. The
  strongest local judge was right on 48 and 54 of 90, where chance is 30. On 53 and 45 items both its bounds were
  real sums from the facts, a single fact's number or missing, but not the tightest; on 15 and 6 at least one bound
  was the sum of no chain at all. For a smaller judge, three-digit numbers did make it worse: its no-chain bounds
  rose from 23 to 36 of 90. This is a direction from one judge, not a measured property of the benchmark.
- **Right for the wrong reason.** 23 and 17 of the strongest judge's correct answers rested on a wrong deciding
  bound. The studio has decided to add a second score, "grounded": the label is right and the deciding bound is
  exact. On the pilot that is 25 and 37 of 90.

## What changed because of it

- The construction was adopted for the next d5c build, and the rule changes were written into the
  pre-registration before any real pool is drawn: one claim per triad, the fork family, 5 to 8 events per item
  (amended after seeing the data, and recorded as such), decoy facts tagged and verified redundant, the 13 number
  statistics in the audit's list, and the grounded score as a secondary score with its own arm.
- **The real build now exists and is under audit (added the evening of 2026-11-19).** The construction was built in
  the real generator the same day. On its public-seed pools the audit's main gate reports no must-fix test: 0 on each
  of the three pool types and 0 on a pool ten times larger. That zero has no measured detection margin on the number
  statistics yet: the audit's planted-cue controls were designed for the old items and cannot plant a visible cue in
  the new ones, so they are being redesigned. The learned probe's result is not valid as run (its permutation null is
  biased for this design) and it is being rerun. On the larger pool the gate as coded flagged one residual: one number
  statistic (the sum of all lower numbers minus the claim number) predicts the answer with a lift of +0.0056, under
  the +0.02 floor. Six other number-statistic tests reach p = 0.0125 under a plain min-p rule, which the gate's way of
  scaling its tests masks. The pool-level figure is small because the cue is rare, not because it is weak: in about
  2% of triads, those whose smallest total sits just above a cut-off the construction applies, that statistic gives a
  lift of +0.26 (of 80 "at least" items in the lowest two bins, 0 are supported and 74 are unsupported). The cut-off
  rule is ours and is being
  changed. So there is no pass yet. This brief is the state as of the evening of 2026-11-19; later findings go in
  a follow-up entry, not here.

## Caveats

- **The findings above are from the prototype.** Public seeds, calibration-size parts, one range of claim numbers and widths. Only the
  audit's listed gate was run. The prototype does not enforce the benchmark's rule that half the supported items
  have zero slack.
- **The list of 13 statistics is R&D's own.** A cue nobody listed is what the learned probe is for; it
  did not run on the prototype, and its run on the real build is not valid.
- **The pilot is small:** 180 items of the one-family version, two usable judges, one prompt wording, thinking
  off, working capped at 80 words, no fork items. It gives a direction, not a measured property of the benchmark.
- **The first drafts of the library entry and of this brief overclaimed.** An independent review by a model from
  another family failed each; the entry's corrected text passed on its third round.
- The scripts and raw outputs are in the lab's private working tree; this brief and the entry report counts.

## Receipts

`mcp-tool-shop-org/rnd`:
- `entries/2026/2026-11-19-one-claim-three-number-assignments-a-purpose-built-generator.md`, with every claim marked
  verified or unverified and every source tier-tagged.
- The study it follows: `entries/2026/2026-11-19-when-the-class-can-be-read-off-which-pair-is-asked-about-a-r.md`.

## Shelf status

Not promoted. It becomes a knowledge-base candidate when the real build has passed its full audit.
