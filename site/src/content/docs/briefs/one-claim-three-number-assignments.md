---
title: Can one claim with three sets of numbers remove a benchmark's shortcuts?
description: In a prototype, yes for every cue the audit lists, and the judges then fail at finding the right chain of facts. What is still unproven is everything the audit does not list.
date: 2026-11-19
status: interim
shelf: not yet (prototype only; the real build and its full audit are in progress)
---

## The question

d5c is the studio's test for comparing local models as judges on three-way verification: is a claim supported by
the facts, ruled out by them, or impossible to tell? Its items come in triads, one per answer. The benchmark's
shortcut audit failed on a pool built from public seeds: 44 of about 600 tests were must-fix, and the bar is zero.

An earlier study found the cause. A triad was one set of facts with three claims about three different pairs of
events, so the answer could be read off which pair was asked about. The question here: if a triad instead keeps ONE
claim and changes only numbers in the facts, do the shortcuts go, and is what is left still a reasoning test?

## What we found

- **The audit's listed tests find nothing.** On a 3,168-item prototype pool the audit's gate reports 0 must-fix and
  0 significant tests, with the bar unchanged. Today's pool: 44.
- **The rules that do it.** One skeleton and one claim per triad. Facts that name either claim event are the same
  in all three items. No number on the deciding chain changes side of the claim number. The width of the feasible
  range is drawn the same way for all three answers. Totals stay clear of the claim number.
- **Making listed features constant blinds the audit that lists them.** 292 of the audit's 304 features are now
  identical inside every triad. What is left lives in plain statistics of the numbers. R&D measured 13 of them
  outside the audit: the largest lift was +0.194 in the first prototype, +0.027 with claim numbers of 200 to 500
  and narrow ranges, and +0.010 on the final pool. The studio has decided to add those 13 to the audit's list.
- **A working rule for the leftovers.** A statistic that leaves out a part of the bound whose spread is M sees the
  answer with a lift of about shift / (1.5 × M). Nothing makes it exactly zero.
- **Variety had to be rebuilt.** One skeleton family passes the gate but is thin. The final prototype has twenty
  shapes, including a "fork" in which the two claim events sit on two branches from one root, so the bounds are a
  difference of two chains. Without forks, two older variety rules (claims with zero or backward distance in the
  stage order) could not be met.
- **Local judges fail at finding the chain, not at adding.** In a small pilot (180 items of the first, one-family
  version; thinking off) the strongest local judge was right on 48 and 54 of 90, where chance is 30. Its bounds
  were sums of the wrong chain on 53 and 45 items and sums of no chain at all on 15 and 6. For a smaller judge,
  three-digit numbers did make arithmetic worse (23 to 36 of 90).
- **Right for the wrong reason.** 23 and 17 of the strongest judge's correct answers rested on a wrong deciding
  bound. The studio has decided to add a second score, "grounded": the label is right and the deciding bound is
  exact. On the pilot that is 25 and 37 of 90.

## What changed because of it

- The construction was adopted for the next d5c build, and the rule changes were written into the
  pre-registration before any real pool is drawn: one claim per triad, the fork family, 5 to 8 events per item
  (amended after seeing the data, and recorded as such), decoy facts tagged and verified redundant, the 13 number
  statistics in the audit's list, and the grounded score as a secondary score with its own arm.
- The build that follows must reproduce the zero in the real generator and pass what the prototype never ran: the
  learned probe, both corruption probes, the planted-cue controls and a pool ten times larger.

## Caveats

- **Prototype only.** Public seeds, calibration-size parts, one range of claim numbers and widths. Only the
  audit's listed gate was run.
- **The list of 13 statistics is R&D's own.** A cue nobody listed is what the learned probe is for, and it has not
  been run on this construction.
- **The pilot is small:** 180 items of the one-family version, two usable judges, one prompt wording, thinking
  off, no fork items. It gives a direction, not a measured property of the benchmark.
- **The first draft of the library entry overclaimed.** An independent review by a model from another family
  failed it; the corrected text passed on the third round.
- The generator and audit code are not yet public. They are released with the benchmark.

## Receipts

`mcp-tool-shop-org/rnd`:
- `entries/2026/2026-11-19-one-claim-three-number-assignments-a-purpose-built-generator.md`, with every claim marked
  verified or unverified and every source tier-tagged.
- The study it follows: `entries/2026/2026-11-19-when-the-class-can-be-read-off-which-pair-is-asked-about-a-r.md`.

## Shelf status

Not promoted. It becomes a knowledge-base candidate when the real build has passed its full audit.
