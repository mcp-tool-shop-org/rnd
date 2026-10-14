# Brief: T10 skeleton variety (D007), for the Grok seat

**Status:** written 2026-10-13. Not dispatched: it goes to a seat on the Director's go, through the Publisher.
**Repository:** mcp-tool-shop-org/role-set, from main at `21236aa`.
**Template:** [diagnose-then-fix](../../site/src/content/docs/handbook/diagnose-then-fix.md) (prototype). The diagnosis is done. This brief is the fix and its check.
**Design input:** two rounds with Argon (Gemini, by hand, 2026-10-13), checked against the code by R&D. Where they differ, this brief follows R&D's reading and says why.

## 1. The check, in three sentences

- **Diagnosis (done):** T10 puzzles built on seeds 1–20 in all 8 packs repeat their skeletons far past the floor (table below). The cause is in the generator, not in any one pack.
- **The fix:** the generator assigns each seed a structural cell and deletes clues in a fixed order of complexity. No pack, solver check or shortcut reading changes.
- **Why the re-measurement answers it:** the same measurement, run on locked seeds the fix was never tuned on, shows whether variety comes from the construction or from fitting seeds 1–20.

## 2. The diagnosis

Measured by R&D on role-set#49 (head `8e482e4`), 8 packs × seeds 1–20 = 160 puzzles per question:

| Question | Distinct skeletons (floor ≥ 75%) | Top repeat of one skeleton (floor ≤ 3) | Repeats within one pack's file (floor 0) |
|---|---|---|---|
| set | 114 / 160 (71%) | 7 | 7 |
| claim | 93 / 160 (58%) | 8 | 8 |

Main measures the same on its 3 packs, so #49 didn't cause it.

**Causes, as read in the code at `21236aa`:**
- **Every T10 puzzle has the same shape:** `build_t10` defaults to `n=4`, the value sets are unordered, and the only clue forms are `is`, `is_not`, `count` and `if` (`recipes.py`).
- **The hidden solution is uniform over raw assignments** (`rng.randrange(len(sols))`). With unordered values this over-weights balanced splits; for n=4 and two values, the 2–2 and 3–1 splits take 14 of 16 draws.
- **Reduction deletes clues in a random order** (`reduce`, `build.py:155`; the loop in `_open_set`). When a unit clue and an `if` clue overlap, either can go. Unit facts are the commonest survivors, so many builds collapse to the same few count-plus-units skeletons.
- **Claim questions lose more,** because reduction drops every entity off the deciding path for the one named entity.
- **Seeds share no state** (`random.Random(f"T10:{pack}:{question}:{seed}")`). "No repeat within a file" can't come from history; it has to come from a fixed map of seed to cell.

## 3. Symptom-to-fix table (fixed in advance)

| Symptom | Fix permitted | Not permitted |
|---|---|---|
| One shape for every seed | A fixed table mapping (pack, question, seed) to a cell: (n, count operator, k, `if` count) | Changing packs, adding names, adding attributes |
| Unit clues outlive `if` clues in reduction | Delete in tiers: `is`, then `is_not`, then `if`, seeded order within a tier, the count clue last. In both `reduce` and `_open_set` | Removing a minimality, uniqueness or shortcut check |
| Repeats within a pack's file | Pigeonhole: at least 20 usable cells per pack, so a pack's 20 seeds land in 20 different cells | A filter that builds a puzzle, sees a repeat and throws it away |

A fix outside this table needs a dated amendment here before the locked seeds run (section 6).

## 4. Phase 1: the work

1. **List the usable cells.**
   - For each pack and question, try every cell: n in {3, 4, 5}; operator in {exactly, at_least, at_most}; k in 1..n−1; `if` count in {0, 1, 2}.
   - Record which cells build within `MAX_TRIES`.
   - Commit the list as data, with the script that made it. Argon estimated 14–18 usable cells for two-value packs without the `if` axis. That's an estimate; the list replaces it.
2. **Map seeds to cells.**
   - Use a fixed table, indexed so that seeds 1–20 in one pack and question never share a cell.
   - Offset each pack (for example, a stride coprime to the table length) so packs spread over different cells.
   - If a pack has fewer than 20 usable cells, stop and report. Don't widen the recipe to make it fit.
3. **Draw the hidden solution so the count clue is true, and only that.**
   - Don't pin the hidden solution to exactly k (Argon's "boundary sampling"). If every "at least k" and "at most k" puzzle had exactly k true, reading those size words as "exactly k" would always be right.
   - That is the size-word misreading T10 exists to train out, and the same kind of shortcut the selector had to block on #50 (class `filter_induced_shortcut`).
   - The count clue already has to sit on the deciding path and fail when loosened. Boundary sampling isn't needed for that.
4. **Delete clues in order of complexity.**
   - Sort the deletion candidates by (tier, seeded random): `is` (0), `is_not` (1), `if` (2). The count clue stays last, as now. Do this in both `reduce` and `_open_set`.
   - `_open_set` needs it as much as `reduce`: set questions stop at 2–`SET_MAX` groups, where unit and `if` clues often prune the same thing.
5. **Hold the cell's `if` count.**
   - A target count of `if` clues isn't a guarantee, because reduction can still delete one.
   - A build whose reduced puzzle doesn't keep its cell's `if` count is refused, and the seed tries again within `MAX_TRIES`.
   - That's a retry inside one seed's construction, not discarding finished builds.
6. **Keep every existing check.** Uniqueness, minimal reduction, the count clue on the deciding path, at least one shortcut reading that differs, `MAX_IF = 2` and `SET_MAX = 4` are all unchanged.

## 5. The measurement, shipped in role-set

Add `tests/test_t10_variety.py`, or a script plus a test, that builds T10 for every pack, both questions and a given seed range, and reports:
- distinct canonical skeletons, the top repeat, and repeats within each pack's file. A canonical skeleton renames entities and values by first appearance; it keeps attribute shapes and the clue list.
- each count operator's share;
- for at_least and at_most, how often the hidden count equals k. This catches a boundary shortcut entering by another route;
- the reduced puzzle's `if` count against the cell's target;
- refusals per cell.

The test asserts the three floors on the verification seeds. It also asserts zero weakened checks: every built puzzle passes `check_model` and `prove`, unchanged.

## 6. Split: tuning seeds and locked seeds

- **Tuning, D:** seeds 1–20, used freely to build and debug the cell table and the deletion order.
- **Verification, V:** seeds 21–40. Not run until the Phase 1 code is frozen in a commit. Its result is the verdict; re-scoring seeds 1–20 measures tuning, not the fix.
- The PR reports both, with V's commit hash.

## 7. Attribution

The fix counts as working only if the targeted symptoms fell, as well as the floors passing:
- the share of reduced puzzles keeping at least one `if` rose against the baseline (main at `21236aa` on the same seeds);
- n and the count operator actually vary in the built puzzles, as the cell table says they should.

If the floors pass but these didn't move, report it. Don't claim the fix.

## 8. Verdicts by stratum

Report the floors separately for set and claim, and for two-value and three-value packs. A pass in one stratum doesn't carry another.

## 9. Phase 2 (only if claim still misses a floor on V)

- Add `in` and `not_in` to T10's clue forms for three-value packs, deleted after `is_not` and before `if` (tier 1.5).
- Each needs template wording in every three-value pack.
- Then re-run the measurement on fresh locked seeds 41–60.
- Not in scope at any phase: a second attribute (it exceeds the solver cap at n=6 and reads like a logic drill), and n=6 (packs have 5 names).

## 10. What the PR reports

- The verdict per stratum and phase, on V.
- The baseline against the fix, on the same seeds.
- Refusals per cell, and any pack with fewer than 20 usable cells.
- Lines of code added, and any change in build time.
- No pack or check changes. If one was needed, stop and ask.

## R&D's reading of Argon's input

**Adopted:**
- the cell map per seed, including Argon's round-2 point that the `if` count must be one of its axes;
- deleting clues in order of complexity, in both reduction paths;
- Phase 2 as a contingency;
- dropping the second attribute.

**Changed or dropped:**
- **Boundary sampling:** dropped, for the shortcut it plants (section 4, step 3).
- **n up to 6:** packs hold 5 names.
- **"Set questions pin every entity":** not so; `_open_set` stops at 2–4 groups.
- **The 0.35 feature-distance floor:** no basis.
- **Argon's per-reading 15% floor:** the selector merged in #51 already floors shortcut readings per file.
- **Its variety projections:** untested estimates, replaced by the V measurement.
