# CONSULT | Argon | EmbeddingGemma 2 text benchmark: audit round 3, the revised brief and the fresh audit | from R&D | 2026-10-15

**Status:** your adjudication covers all 63 disagreements.

| Final grade agrees with | Rows |
|---|---|
| The Sonnet grader | 56 |
| Your Part A | 7 |

All 7 are a Sonnet 1 raised to 2: five under your split-implementation rule, and two research-finding chunks. Your note put this at 55 and 8, and said the packet held only 56 rows. It held all 63; your paste may have been cut. Your 7 extra rows weren't disagreements, but R&D counted them in the comparison below: five lower to 0 a 1 that both graders had given, under R1, R2 and R5.

Applying your rule set to the 501 audited chunks, the round 1 Sonnet key differs from it on 12: 7 too low and 5 too high. The corrections run both ways, so the whole pool is regraded under the revised brief, as amendment 2 requires. No score has been computed.

## Part A: approve or amend brief version 2

R&D wrote your boundary table into `harness/grader-brief-v2.md`. The text is below. **Every chunk id, query id and file name from your examples was taken out.** The brief is public, and the same queries are being regraded, so an example that pins a chunk to a grade would leak the answer into the regrade.

R&D also resolved four places where your table met version 1. Check each:
1. **R3 replaces version 1's "split code" rule.** Version 1 gave 1 to logic whose enclosing function the chunk didn't name. Version 2 gives 2 to each load-bearing half that the chunk's text or header ties to the implementation. The brief also warns that a chunk's header title can name the definition *before* the chunk's text, since offrig's chunker does that.
2. **R2 overrides version 1's "a doc that explains the control flow is 2"** on code queries. Prose queries keep that rule.
3. **R11 (two-part queries, one half earns 1 unless the note says otherwise) and R12 (grade a mismatched premise against the real mechanism)** come from your round 1 Part B answer, not your table. Confirm you want them.
4. **R5's heading** in your paste had a stray non-English word ("adjacent مراحل"). R&D read it as "other pipeline stages".

Reply **"approve as written"**, or give the exact changes. If you change anything, stop there: R&D revises the brief and sends it back before any grading.

[brief version 2, pasted in full below]

## Part B: only if you approve as written, grade the fresh audit blind

Four private packets are attached. They hold 16 queries drawn by round 1's criterion (the highest share of pooled chunks that two or fewer decision runs found, 8 code and 8 prose), from the 84 queries round 1 didn't audit. The draw was made before any regrading.

Grade every chunk 0, 1 or 2 under brief version 2. Reply in JSON Lines, one row per chunk, in packet order: `{"query_id", "chunk_id", "reason" (at most 15 words), "grade"}`. Use plain quotes inside a reason only if you escape them. Three round 1 rows broke on that.

The four bars are unchanged: quadratic κ ≥ 0.75, binary κ ≥ 0.80, raw disagreement ≤ 10%, two-step ≤ 2%. Once you approve, the Sonnet regrade runs under the same brief while you grade, and you see none of it.
