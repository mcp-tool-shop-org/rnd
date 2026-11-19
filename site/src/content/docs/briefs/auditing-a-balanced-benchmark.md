---
title: Can an audit prove a balanced benchmark has no shortcuts?
description: No. It can say that no listed cue was found above a stated detection limit. What the literature, five outside reads and a simulation say about the d5c pool audit.
date: 2026-11-19
status: research
shelf: not yet (the benchmark is not sealed)
---

## The question

d5c is the studio's test for comparing local models as judges on three-way verification: is a claim supported by
the facts, contradicted by them, or impossible to tell? Its items are generated in triads over shared facts, and a
selection step balances a list of surface features across the three answers. Before a test pool is sealed, an
audit runs a permutation test on about 600 feature-against-answer associations.

The studio wanted to know what that audit's pass is worth. If it passes, what may we say?

## What we found

- **A pass is a bound, not a clean bill.** The honest wording is "no listed cue was found above the audit's
  detection limit", never "the pool is clean". The d5c pre-registration now says so.
- **The detection limit is about +0.03 accuracy lift for a common yes/no cue.** In a simulation of the audit's own
  statistics code (608 tests, 3,168 items), a planted cue on about half the items was flagged 27% of the time at
  lift +0.018, 70% at +0.026, 90% at +0.031 and 100% at +0.041. Two outside calculations land in the same place
  (+0.031 and +0.032 to +0.033).
- **A rare, pure cue can hide under the effect floor.** The audit flags a feature only if it is significant and
  lifts accuracy by at least +0.02. A feature on 48 of 3,168 items, all with the same answer, lifts accuracy by
  only +0.015. It would be overwhelmingly significant and still not flagged.
- **Balancing the data changes what the audit's shuffle means.** The selection step balances about 20 features; the
  audit's shuffle holds four of them fixed. For any feature correlated with the balanced ones, the shuffle expects
  more spread than the selected pool can show, so the audit is less sensitive than it looks. Three outside reads
  agree, and trace it to the rerandomization literature in experimental design.
- **One case runs the other way.** The shuffle for selected pools moves answers between triads. For a feature that
  only one claim in a triad carries, that underestimates the spread and can flag too often. This can cause a false
  alarm, not a false pass.
- **Most of the statistics held up.** The p-value counts the observed labelling, the family-wise correction is
  the standard one, and putting tests with different numbers of levels on a chi-square scale beat the alternative
  we tried (0.49 against 0.91, where 0.50 is even) on well-filled tables.
- **Five or six judges on about 1,000 triads can be put in tiers, not in a full order.** One outside report's
  planning figure is a detectable gap of about 3.3 points between two judges. It is built on assumed correlations,
  not our data.

## What changed because of it

- The pre-registration gained a note, written before any verdict pool existed, with the pass wording, the selection
  limit and the rare-cue limit.
- A set of diagnostics was approved on a public-seed pool: each feature's within-triad correlation, its
  correlation with the balanced features, the share of items the shuffle cannot move, and which tests take the
  family maximum.
- Queued for after the test windows: a measured detection-limit table (cues planted into real features, six cue
  shapes, at least 500 replicates), a text-only baseline, and a selection-aware version of the test.

## Caveats

- **Nothing here was run on a d5c pool.** The simulation used independent noise features and guessed level counts.
- **The outside reads are AI output.** Two consults and three Deep Research reports, all from Gemini models. Five
  paper abstracts were read by R&D; the other citations are unchecked.
- **The first draft of the library entry overstated four things.** An independent review by a model from another
  family caught them before it merged. The entry records both verdicts.
- The audit code is not yet public. It is released with the benchmark.

## Receipts

`mcp-tool-shop-org/rnd`:
- `entries/2026/2026-11-19-auditing-a-balanced-benchmark-for-shortcut-cues-what-the-lit.md`, with every claim marked
  verified or unverified and every source tier-tagged.

## Shelf status

Not promoted. It becomes a knowledge-base candidate when the benchmark is sealed and the measured detection-limit
table exists.
