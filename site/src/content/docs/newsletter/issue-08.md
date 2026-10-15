---
title: Room for the seventh pack
description: A puzzle generator kept building the same shapes. Three briefs, one proof, an allocator, a committed record in CI, a stop, and a new axis later, it has room for twice the packs it was built for. How the variety floors were set, missed, met, and then given headroom.
issue: 8
date: 2026-10-14
highlights:
  - "<strong>A claim puzzle can only test \"exactly\":</strong> a short proof settled which size words a claim can catch a careless reader on, and the generator now refuses what can't be tested."
  - "<strong>The floors are enforced in CI from a committed record:</strong> every build's skeleton, keyed by a hash over every file that decides a build, checked in seconds inside the normal CI job; the exhaustive rebuild runs on demand and must reproduce it."
  - "<strong>The build stopped itself on a pre-existing defect</strong> and the fix was the one the rules allowed: split the capacity weights by stratum, not cap the tries or drop the cell."
  - "<strong>Three-value claims went from 27 usable cells to 61,</strong> from a top repeat of 4 (a fail) to 2 on fresh locked seeds, and the allocation test places twelve packs where six fit before."
---

Every claim below links to the record it came from.

## The problem

[role-set](https://github.com/mcp-tool-shop-org/role-set) builds logic puzzles to train and test small models. Its T10 family turns on one size word: "at least two of the lamps are on", "exactly one clinic opens in the morning". Every puzzle is proven before it's kept: a solver checks the model, and a set of registered readings checks that a solver taking a shortcut (reading the size word loosely) would be caught.

Under those proofs the generator had collapsed onto a few shapes. A test set that repeats one shape teaches the shape, not the reading. So the work was to make the shapes vary, measurably, without loosening a single proof.

## The floors, set before any fix

The first brief fixed the measure and the bar before anyone touched the code. A puzzle's **canonical skeleton** is its structure with the wording removed: how many entities, which clue forms, where the trap sits. In each stratum (two-value or three-value packs; "set" or "claim" questions): at least 75% of skeletons distinct, no skeleton more than 3 times, none twice in one pack's file of 20 seeds. Tuning on seeds 41–60; the verdict on locked seeds 61–80 that nobody tunes against. → [Brief 1](https://github.com/mcp-tool-shop-org/rnd/blob/main/experiments/t10-variety/brief.md)

## The proof that narrowed the claim strata

Brief 2 asked what a claim puzzle can test at all, and the answer was a proof, not a measurement. A claim states something and asks whether it holds. If the claim says "at least two" and exactly two is the truth, the claim is true, and a reader who read "at least" as "exactly" agrees. Every world where "exactly k" holds is one where "at least k" holds. So no claim built on "at least" or "at most" can separate the careful reader from the careless one; only "exactly" can. The generator now refuses to build what can't be tested (`trait_not_tested`), and claims carry "exactly" alone. That is correct, and it left the claim strata with very few structural cells. → [Brief 2](https://github.com/mcp-tool-shop-org/rnd/blob/main/experiments/t10-variety/brief-2-trait-tested.md)

## The allocator, and the first stop

Brief 3 made the packs of one kind share their skeleton space, with an allocator (a min-cost flow) that spreads a pack's twenty seeds across cells (entity count, size word, count, number of conditional clues), with a cap on the barest cells. It stopped on arithmetic: six three-value packs needed 26 visits to the nine cells with no conditional clue, against a supply of 18 at a cap of 2. The stopgap ruled was a cap of 3 for that one stratum, which passed exactly on the floor: 108 of 120 distinct, top repeat 3. → [Brief 3, amendments 1 and 2](https://github.com/mcp-tool-shop-org/rnd/blob/main/experiments/t10-variety/brief-3-multipack.md)

## The floors in CI, from a committed record

Proving 640 puzzles under coverage took 46 minutes against a 15-minute job. The ruling, after a cross-family consult: the measurement is committed. A record holds every build's cell, try count and skeleton, keyed by a hash over every file that decides a build, closed under the package's imports. The normal job recomputes the hash, fails a mismatch by naming the regenerate command, and computes the floors from the stored skeletons in seconds, inside a CI job that finishes in about seven minutes. The exhaustive rebuild runs on demand and must reproduce the record exactly. A cap on build attempts was refused twice: it changes which puzzles get built. → [role-set #49](https://github.com/mcp-tool-shop-org/role-set/pull/49)

## The new axis, and the second stop

To get the claim strata off the floor, the conditional clues gained a shape coordinate: for one `if`, the consequent's polarity; for two, chain, shared consequent, shared antecedent or disjoint. (A finer coordinate, whether the `if` touches the claimed entity, was dropped because the skeleton can't see it, so it would have inflated cell counts without adding measured variety.) The zero-`if` cap went back to 2. On fresh locked seeds 81–100 the claim strata cleared every floor.

Then set three came in at 118 of 119: one build needed 435 tries against a limit of 400, and the baseline failed the same build. The cause was a pooled weight: the capacity script had measured one weight per set cell across two- and three-value packs, so a cell that builds easily for two-value packs looked rich and sent a three-value pack there in every file. Brief 3 had always said capacity is per stratum. The ruling was to split the weights, re-freeze, and take the verdict on fresh locked seeds 101–120. The alternative, a stricter probe, drops cells, which is the same forbidden move as a try cap. → [Brief 3, amendment 4](https://github.com/mcp-tool-shop-org/rnd/blob/main/experiments/t10-variety/brief-3-multipack.md)

## The verdict

On locked seeds 101–120, with the baseline code run on the same seeds beside it:

| Stratum | Before | After |
|---|---|---|
| set, two values | 40/40, top 1 | 40/40, top 1 |
| set, three values | 118/120, top 2 | 118/120, top 2 |
| claim, two values | 40/40, top 1 | 40/40, top 1 |
| claim, three values | 112/120, top 4 (fail), 26 zero-`if` visits | 118/120, top 2, 0 zero-`if` visits |

All 1,280 builds across four seed files build inside the try limit; the one that caused the stop now takes 8 tries. Three-value claims have 61 usable cells against 27. An allocation test places twelve three-value packs at a cap of 2 with no zero-`if` visit. R&D reproduced the baseline and the record figures independently before passing it. → [role-set #55](https://github.com/mcp-tool-shop-org/role-set/pull/55)

## What we'd do the same

- **Set the floors and the locked seeds before the first fix,** and take every verdict on seeds nobody tuned against. Fresh locked seeds after every change to the allocation.
- **Freeze, then measure.** The verdict run starts only from a named commit, and the record names it.
- **The baseline beside the verdict,** on the same seeds, every time.
- **Refuse the easy fixes that change what gets built.** A try cap and a dropped cell both passed the floors by changing the population; both were refused, twice.
- **Keep the hash closed.** The record's hash list missed two files at first; an import-closure test written by the builder caught them, and it's the better instrument.

## Released

All of it shipped as role-set [v0.2.0](https://github.com/mcp-tool-shop-org/role-set/releases/tag/v0.2.0) on 2026-10-14, after a full treatment: a README rewritten for the generator, two new handbook pages ([the T10 generator](https://mcp-tool-shop-org.github.io/role-set/handbook/generator/) end to end, and [the role packs](https://mcp-tool-shop-org.github.io/role-set/handbook/roles/)), the README in seven more languages, and a ship-gate scorecard of 37 of 50, up from 31, with the audit passing every gate. It stays 0.x: role-set is a prototype, and nothing it writes is training data until a person checks it.

→ [The T10 brief](/rnd/briefs/taking-size-words-literally/), updated with these figures.
