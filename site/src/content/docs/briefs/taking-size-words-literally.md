---
title: Can a puzzle test whether a model reads "at least" as "at least"?
description: role-set's T10 puzzles hinge on one size word, and the generator kept building the same handful of shapes. Three briefs later the shapes are varied, the floors are enforced in CI, and we proved which size words a claim can test at all.
date: 2026-10-14
status: measured
shelf: stays in rnd (studio tooling)
---

## The question

[role-set](https://github.com/mcp-tool-shop-org/role-set) builds logic puzzles to train and test small models. Its
T10 family turns on one clue with a size word: "at least two of the lamps are on", "exactly one clinic opens in the
morning". A model that quietly reads "at least" as "exactly", or the other way round, gets a different answer.

The generator proves every puzzle: it checks that the stated answer follows, and that a solver taking a shortcut
(reading the size word loosely) would be caught. The trouble was variety. Under the proofs, the generator kept
building the same few skeletons: the same number of entities, the same clue shape, the same place for the trap.
A test set that repeats one shape teaches the shape, not the reading.

## What we set out to do

Three briefs, each fixed in advance with its symptom-to-fix table and its measurement, each reviewed by a model
from a different family before a seat built it:
- **Brief 1** named the floors: in each stratum (two-value or three-value packs, "set" or "claim" questions), at
  least 75% of skeletons distinct, no skeleton more than 3 times, and no skeleton twice in one pack's file of 20.
  Tuning on seeds 41–60, the verdict on locked seeds 61–80 that nobody tunes against.
- **Brief 2** asked what a *claim* puzzle can test at all.
- **Brief 3** made the packs of one kind share their skeleton space, with an allocator that spreads builds across
  cells (entity count, size word, count, number of conditional clues) under a cap on the barest cells.

## What we found

**A claim can only test "exactly".** A claim puzzle states something and asks whether it holds. If the claim says
"at least two" and exactly two is the truth, the claim is true, and a solver that read "at least" as "exactly"
agrees. Every world where "exactly k" holds is a world where "at least k" holds, so no claim with "at least" or
"at most" can separate the careful reader from the careless one. Only "exactly" can. The generator now refuses to
build what can't be tested (`trait_not_tested`), and claims carry "exactly" alone. Two-value claims are therefore
narrower by construction; that's a property of the puzzle, not a defect.

**The allocator clears every floor on the locked seeds.** Measured on seeds 61–80, 40 or 120 builds per stratum:

| Stratum | Distinct | Top repeat | Before |
|---|---|---|---|
| set, two values | 40/40 | 1 | 40/40 |
| set, three values | 120/120 | 1 | 110/119, one seed refused |
| claim, two values | 40/40 | 1 | 38/40, top 2 |
| claim, three values | 108/120 | 3 | 106/120, top 4 |

Three-value claims sit exactly on the top-repeat floor. With "exactly" the only size word, those cells are the
scarcest, and a cap of 3 visits on the barest ones is what fits six packs. A seventh three-value pack needs the
next design step, a shape axis for the conditional clues, and the capacity check fails loudly if one is added
first.

**The floors are enforced in CI, from a committed record.** The full measurement is 640 proven builds and takes
too long for a 15-minute job under coverage. So the measurement is committed, with a hash over every file that
decides a build. The normal job recomputes the hash, fails on a mismatch by naming the regenerate command, and
computes the floors from the stored skeletons in about four minutes. The exhaustive rebuild runs on demand and
must reproduce the record exactly. A cap on build attempts was refused twice: it changes which puzzles get built.

## Caveats

- **Variety is measured on skeletons, not on text.** Two puzzles with the same skeleton read differently; two
  with different skeletons might still share a trap. The floors are a lower bound on structural variety.
- **One generator, nine packs, two questions.** The figures are for role-set's T10 family as built in October
  2026. They say nothing about other puzzle families.
- **Measured, not independently checked beyond the studio:** R&D reproduced the table in clean worktrees, and the
  CI record was rebuilt on ubuntu and on the rig. No outside party has.

## Receipts

- role-set `787ccf8` (#49): the allocator, the record `src/role_set/generate/t10_record.json`, and the CI gate.
- rnd `experiments/t10-variety/`: the three briefs, the outside reviewer's input, and the outcome.
- The proof that claims can test only "exactly": brief 2, section 3.
