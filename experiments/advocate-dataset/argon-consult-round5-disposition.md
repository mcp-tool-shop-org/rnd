# Argon consult, round 5: the answer and the disposition | 2026-10-14

Argon read Seat C's phase 1 code at role-set `3141e2d`, with the spec and the tests inline. **Verdict: hold the grant. Phase 1 needs a fix-up turn before any model loads.** His earlier approve, given on the summary without the code, is superseded.

## Findings and what was done

| # | Finding | Disposition |
|---|---|---|
| R1–R6 | All six of R&D's findings confirmed at the lines cited: shapes are labels only; the record is padded; the order check matches by substring; the critic can't see the record; kind B has no directions and one escalation text; the variety hash isn't closed. | **Taken.** Fix-up steps 1, 2, 4, 5. |
| A1 | The brief-only probe never reads the prose. It draws `random.choice` over the labels, and its test checks that Python's RNG is uniform. | **Taken.** Step 5 builds a prose-only probe (positive or negative from length and a leave-one-out bag of words). R&D's own spec error is recorded: the lean brief said the probe would be "reused", and role-set has no such probe. |
| A2 | Trace needs `"coverage 0.71"` as one contiguous string, so "coverage is 0.71" fails. A threshold isn't on the ledger, so writing `0.75` counts as an invented number. | **Taken.** Step 1 puts thresholds and caps on the record as figures. Step 4 checks the number-and-unit token verbatim and the metric name in the same line or sentence. |
| A3 | The writer's prompt never names the five exact headings, the four verdict tokens or the section 5 form, and the checks require all three. Every test passed on a deterministic template (`render_brief`), never on a prompt a model would follow. | **Taken.** Step 4. The hand-back must show the rendered prompts, Argon's first read. |
| A4 | The number regex takes digits out of SHAs, grant ids and `B004`. `plant_exact` compares numbers as ordered lists, so a figure repeated in two sections fails. | **Taken.** Step 4: digits inside alphanumeric tokens aren't numbers, and numbers compare as sets. |
| C1 | Allow verdict-changing plants. Split the ten negatives five and five, so the critic can't flag on the verdict alone. | **Taken.** Slots 1 and 6 change the verdict, slots 4 and 10 keep it, and the planner assigns the rest with each plant class at least twice. A figure plant across a threshold counts as verdict-changing. |
| Q1 | One display phrase per tripwire, from section 0a, checked in section 4 ignoring case. | **Taken.** Step 1. |
| Q2 | Keep `qwen3:8b` (thinking off) and `llama3.1:8b` as writers, once A2 and A3 are fixed. | **Taken.** The grant request stands. |
| Q3 | Length at most 130 words, and at most `max(65, record words − 1)`. The copy ban stays. | **Taken.** Step 4, and the turn 3 amendment. |
| Q4 | The pilot runs on the approved pack hash. One pack revision after the read. | **Taken.** Step 7. |
| Q5 | A fixed sixteen-slot pilot planner and a `pilot --mock` runner, tested in CI before the grant. | **Taken.** Step 6. |

## What R&D takes from it

Two of the defects, A1 and A3, were in tests that passed for the wrong reason. Both tested the machinery against R&D's spec, never against what a model given the prompt would face. The fix-up's hand-back puts the rendered prompts and the mock run in front of the reviewers, and both reviewers read those first.
