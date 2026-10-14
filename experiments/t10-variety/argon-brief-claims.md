# Consult brief for Argon: can a T10 claim item test "at least" and "at most"?

R&D, 2026-10-14. Follows the T10 variety fix (role-set #53), which passed its variety floors. Reviewing it turned up a defect and an open design question. We want your analysis before a fix is briefed to a seat.

## Background (self-contained)

**T10, "takes statements literally."** It's a review lesson in a synthetic training set. Each item is a small logic puzzle whose one load-bearing clue is a count: "exactly / at least / at most k of them are v". The lesson is to read the size word literally.

**A puzzle has:**
- n entities (3–5);
- one attribute with 2 values (lit/dark, open/shut) or 3 values (hot/warm/cold), values not distinct across entities;
- clues of the forms `is`, `is_not`, `count(op, k, v)` and `if` (at most 2 `if` clues).

**Two question types:**
- **claim:** "Is X v?" The answer is one of `supported`, `unsupported` or `cannot_tell`, computed by exhaustive solving over all assignments.
- **set:** "Which of them could be v?" The answer is the set of possible groups, and must have 2 to 4 groups.

**The build** (deterministic per seed):
1. Pick a cell: n, the trait clue's operator and k, and a target number of `if` clues.
2. Draw a hidden solution uniformly from the assignments where the trait count clue is true.
3. Add true clues (`if` first, then units; the pool can include further count clues) until the answer is decided. A clue joins only while the clues *without the trait* still leave the answer open.
4. Reduce: delete every clue the answer doesn't need, in tiers (`is`, `is_not`, `if`; the trait last). Refuse the build if the trait drops out, or if the `if` count misses the target.
5. Check: uniqueness, minimality, and the **shortcut check**: at least one registered misreading must give an answer different from the key.

**The four registered misreadings,** each a rewrite of every count clue with the matching operator:
- `=` read as `>=` ("exactly k" taken as "at least k")
- `=` read as `<=`
- `>=` read as `=` ("at least k" taken as "exactly k")
- `<=` read as `=`

## What we measured (locked seeds 21–40, 3 packs)

1. **On every three-value claim puzzle whose trait clue is "at least" or "at most" (9 of 9), the trait's own misreading gives the key's answer.**
   - The misreading that differs belongs to a *second*, "exactly" count clue the pool added.
   - So these items test "exactly" again, and the cell's operator label is cosmetic. On set puzzles this happens in 1 of 60.
2. **In those 9, the hidden count always equals k.** R&D's argument:
   - When an at-least clue directly forces the named entity to v, the other clues must cap the rest at k−1, so the true count is exactly k. At-most mirrors this.
   - Reading "at least k" as "exactly k" then forces the same verdict.
   - We haven't proved that no indirect path (through `if` clues or a second count clue) escapes this.
3. **Two-value packs build no claim with an at-least or at-most trait at all.** Every two-value claim is "exactly", both before and after #53. The cell probe found no buildable cell within 40 tries per cell.
4. **The defect:** the shortcut check accepts *any* differing misreading. It should require the trait clue's own misreading to differ. Class `trait_not_tested`.

## Questions

1. **Possibility.** For a claim item under these rules (the trait on the deciding path, minimal, the answer one of the three verdicts), can "at least k" or "at most k" be the trait with its own misreading changing the verdict?
   - Give a proof, or a concrete counterexample: entities, values, clues and the verdicts under both readings.
   - Consider `cannot_tell` keys, `if` chains, and three-value attributes where the count's value differs from the claim's value.
2. **If it's impossible:** what's the smallest change to the *claim* question that lets a claim item test "at least" or "at most" literally? Rank the candidates on soundness, readability, and whether they keep one load-bearing trait clue. Candidates we can see:
   - asking a claim about the count itself ("Are exactly two lit?");
   - a claim about two entities;
   - leaving the lesson to set items and declaring claims "exactly"-only.
3. **Two-value packs:** is the absence of at-least and at-most claim cells there structural (same proof) or a budget effect? If structural, say why two values are stricter than three.
4. **The `trait_not_tested` gate:**
   - If the shortcut check requires the trait's own misreading to differ, what breaks?
   - Should T10 also forbid a second count clue in the pool, so the lesson rests on one clue by construction?
   - What does each choice cost the variety floors? Distinct skeletons ≥ 75%, top repeat ≤ 3, and no repeat within one pack's file of 20.

## How to answer

- **Answer the questions in order.** Mark each claim as proven, shown by example, or your own inference.
- **For question 1, give the construction or the proof in full,** small enough to check by hand.
- **End with a recommendation** for the seat brief: the gate, the clue-pool rule, and the claim-question change if any, ranked.
