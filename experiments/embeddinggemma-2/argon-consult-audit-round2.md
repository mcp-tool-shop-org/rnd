# CONSULT | Argon | EmbeddingGemma 2 text benchmark: audit round 2, adjudication | from R&D | 2026-10-15

**Status:** your Part A grades are in: 501 of 501 chunks. Three rows had unescaped quotes inside the reason. R&D repaired the escaping only, and the grade in each (all 2) was never in doubt. `grading.py agree` against the frozen Sonnet key gives:

| Measure | Result | Bar | |
|---|---|---|---|
| Quadratic weighted κ | 0.821 | ≥ 0.75 | pass |
| Binary κ | 0.747 | ≥ 0.80 | **miss** |
| Raw disagreement | 12.6% (63 of 501) | ≤ 10% | **miss** |
| Two-step (0 against 2) | 0% | ≤ 2% | pass |

As pre-registered, a miss stops the scoring, and the disagreements come to you query by query before anything is regraded. No score has been computed.

## What the disagreements look like

**Every one of the 63 has you one step higher than the Sonnet grader:** 41 are 0 against 1, and 22 are 1 against 2. None goes the other way. They spread over 14 of the 16 queries; the worst are w055 and w065 at 9 each. So this isn't noise; it's an offset. You read the 0/1 boundary, and to a lesser degree the 1/2 boundary, more generously than the brief led the Sonnet graders to. That offset is what fails binary κ.

**Your Part A grades and your proposed rules disagree in places.** On code-tagged queries, your Part B rules cap external prose docs, tool descriptions and tests at 1. Your Part A gave 2 to:
- 11132 and 11154, rnd instrument notes;
- 11086, a calibration README;
- 1046, a tool description;
- 939 and 359, tests.

On 11154, 11086, 939 and 359, the Sonnet grader gave 1, which is what your rule gives. So which stands, your Part A grade or your rule? It decides several of the 22 disagreements of 1 against 2.

**A correction to your Part B answer.** w079 is not one of the four queries with no relevant chunk: both you and the Sonnet grader gave it a 1. The four are l006, w059, w060 and w068. Two of them, l006 and w068, were in your sample, and you and the Sonnet grader agree all their chunks are 0.

## Asked of you

1. **Adjudicate the 63** in the attached private packet. Each entry gives the query, its intent and note, the chunk, the Sonnet grade with its reason, and yours. For each, give the final grade and the boundary rule that decides it, in JSON Lines: `{"query_id", "chunk_id", "final", "rule"}`. Apply one rule set, the one you want in the template's next version, and say where it overrides your own Part A grade.
2. **The revision the regrade runs under.** Amendment 2 settled this before any run: "a fail means revising and regrading the whole pool". So all 100 queries are regraded by fresh Sonnet graders under a revised brief, and a fresh set of 16 is audited against the same four bars. The frozen round 1 key and this audit stay as the record. **What R&D needs from you is the revision:** your boundary table, made consistent with your adjudication in item 1. R&D writes it into the brief and the template, and sends you the amended brief before any regrading starts.

**Ruled and recorded (your Question 1 answer):**
- Queries with no relevant chunk are dropped from every mean, paired difference, bootstrap and group floor.
- They are reported with their count, ids and why each is unanswerable.
- The excluded ids are locked only after the adjudication and any regrade, before the arms are unsealed.
- The stage 1 thresholds stand at whatever N remains.

R&D records this as design amendment 4.
