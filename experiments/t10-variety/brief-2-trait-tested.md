# Brief 2: T10 tests the trait clue's own size word (`trait_not_tested`), for a seat

**Status:** written 2026-10-14 on the Director's go. Goes to the Publisher for review and seat assignment. **Landed** in role-set (#53, then folded into #49, merged 2026-10-14 at `787ccf8`): claims carry only `=`; `trait_not_tested` refuses the rest.
**Repository:** mcp-tool-shop-org/role-set. Start from main after #53 merges; this brief builds on its cell table.
**Template:** [diagnose-then-fix](../../site/src/content/docs/handbook/diagnose-then-fix.md) (prototype). It follows [brief 1](brief.md).
**Design input:** Argon (Gemini, by hand, 2026-10-14), checked by R&D against #53's builds. The consult is [argon-brief-claims.md](argon-brief-claims.md).

## 1. The check, in three sentences

- **Diagnosis (done):** on #53's locked seeds, all 9 three-value claim items with an "at least" or "at most" trait got through the shortcut check on a *second*, "exactly" count clue. The trait's own misreading gave the key's answer, so those items test "exactly" again.
- **The fix:**
  - the shortcut check credits only the trait clue's own misreading;
  - T10 puzzles carry one count clue;
  - claim cells use "exactly" only, while set cells keep all three size words.
- **Why the re-measurement answers it:** on fresh locked seeds, every item's differing misreading must be its trait's, and the variety floors must still hold in every stratum.

## 2. The diagnosis

Measured by R&D on #53 at `7306adf`, seeds 21–40, 3 packs:

| Question | Trait's own misreading differs | Only another count clue's misreading differs |
|---|---|---|
| claim | 51 (all "exactly" traits) | 9 (7 "at least", 2 "at most", all three-value) |
| set | 59 | 1 ("at least", with 2 count clues) |

**Cause:** `_finish` accepts a build when *any* registered reading differs (`any(p["differs"] ...)`), and the T10 clue pool includes further `count` clues. Class `trait_not_tested` (new class). It has been there since #48.

## 3. Why claims can't test "at least" or "at most"

Proven by Argon, and R&D agrees.

- **The subset argument:** every assignment that fits "exactly k" also fits "at least k", so the misread clue lets through a subset of the assignments the real clue does.
  - A claim key of `supported` or `unsupported` is true of every assignment that fits, so it stays true of the subset. The misreading can't change it.
  - If the subset is empty, the answer is "no assignment fits", which `differs()` already doesn't count.
- **A `cannot_tell` key can't carry the trait:** adding a clue only removes assignments. If the answer is `cannot_tell` with the trait, it was `cannot_tell` without it, so the trait isn't needed and reduction drops it.
- **Any claim about one assignment is covered the same way,** including "both X and Y" and "exactly m are v".
- **Set questions differ:** their answer is the set of possible groups, and the misreading drops groups of other sizes. So set items test all three size words.
- **"Exactly" claims work:** the misreadings "at least k" and "at most k" let more assignments through, and that can change the verdict.
- **Two-value packs can't escape this with a second count clue:** in a two-value pack an "exactly" clue fixes both counts, so it makes an "at least" or "at most" trait redundant. That's why two-value packs never built an inequality claim.

**Decision:** claims test "exactly", and set questions test "at least" and "at most". The four registered readings stay as R&D ruled them on 2026-10-11. Argon's alternative, off-by-one readings ("at least k" taken as "at least k−1"), is rejected: it would change the lesson to fit the generator.

## 4. Symptom-to-fix table (fixed in advance)

| Symptom | Fix permitted | Not permitted |
|---|---|---|
| An item passes on a non-trait clue's misreading | `_finish` (T10) requires a registered reading that applies to the **trait clue's operator** to differ, with that rewrite applied to the trait clue only | Changing the four readings, or `differs()` |
| A second count clue in a T10 puzzle | Leave `count` out of T10's auxiliary pool. The trait is the only count clue by construction | Building, then discarding puzzles with two count clues |
| Inequality claim cells that can't be tested | Claim cells use "exactly" only. Rebuild the claim cell table from the probe | Changing the claim question's wording |

A fix outside this table needs a dated amendment here before the locked seeds run.

## 5. Phase 1: the work

1. **The gate.**
   - In the T10 path, prove the trait clue's own reading: apply the registered rewrite whose `from` matches the trait's operator, to the trait clue alone, and require `differs` to be true.
   - Keep the existing `prove` output for receipts. The new requirement sits on top of it.
   - The selector (#51) should rest each item on the trait's reading. Confirm that `rests_on` picks it, or make it pick it.
2. **One count clue.** Leave `count` out of the candidates T10 adds after the trait.
3. **The claim cells.**
   - Re-run `scripts/t10_usable_cells.py` with the gate and the pool rule in place.
   - Claim cells are "exactly" only. Set cells keep all three operators.
   - Every pack and question still needs at least 20 usable cells. If one doesn't have them, stop and report.
4. **Record the proof.** Add section 3 of this brief to `docs/generator-design.md` in your own words: what each question type tests, and why.
5. **Keep every existing check:** uniqueness, minimal reduction, the trait on the deciding path, `MAX_IF = 2`, `SET_MAX = 4`, and the `if` target with its retry. No pack text changes.

## 6. The measurement

Extend `tests/test_t10_variety.py` (or add to it) so that, on the locked seeds, it asserts:
- the three variety floors (distinct skeletons ≥ 75%, top repeat ≤ 3, no repeat within one pack's file), per stratum: set and claim, two-value and three-value;
- **every** built item's trait reading differs. That's a hard assertion, not a share;
- every item has exactly one count clue;
- the count operator shares on set items, and how often the hidden count equals k on set inequalities (report only).

## 7. Split: tuning seeds and locked seeds

- **Tuning:** seeds 1–40, which #53 has already seen. Use them freely.
- **Locked:** seeds 41–60. Not run until the Phase 1 code is frozen in a commit. Their result is the verdict, and the PR names the freeze commit.

## 8. Attribution

- The `trait_not_tested` count must go to 0 on the locked seeds. Report the before (#53's code on 41–60, run after the freeze) and the after.
- Claims are "exactly" only, and set items still use all three size words.
- If the floors hold but `trait_not_tested` isn't 0, the fix hasn't worked. Report it, and don't claim it.

## 9. Phase 2 (only if a claim stratum misses a floor on the locked seeds)

- Add `in` and `not_in` to the three-value claim pool, deleted after `is_not` and before `if`, with wording in the three-value packs.
- Re-run on fresh locked seeds 61–80.
- Not in scope at any phase: changing the readings, the claim wording, a second attribute, or n = 6.

## 10. What the PR reports

- The verdict per stratum, on the locked seeds.
- `trait_not_tested`, before and after.
- Usable cells per pack and question, and refusals per stratum.
- Lines of code added, and the change in build time and suite time.
- No pack or check changes. If one was needed, stop and ask.

## Note for #49

#49's variety re-check should run on top of this fix, not on #53 alone. Otherwise it would count claim items as "at least" or "at most" when they test "exactly".
