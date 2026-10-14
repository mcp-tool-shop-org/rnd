# Argon consult, round 4: the answer and the disposition | 2026-10-14

Argon's verdict on the pilot brief at 1.1.8.2.16: **green light** for the Director and Seat C, with two fold-ins and no fifth pass.

## Findings and what was done

| # | Finding | Disposition |
|---|---|---|
| 1 | The three fixes from the first check are cleanly in the text; nothing still assumes five classes, 16 critic texts, or a B negative. | Confirmed; nothing to do. |
| 2 | "One missed negative passes the bar but fires the deferred trigger" is the wrong rule: at ten negatives, one miss is 10% with a 95% interval of roughly 0.25% to 44.5%, too thin to launch the deferred two-leg critic and its 64-item calibration set while the batch runs. Treat a single miss like a check defect: inspect it in the read; a critic prompt fix re-verified on the frozen 26 texts lets the batch proceed; if the single-leg critic still misses deceptive prose that carries the right tokens, the two-leg critic is triggered before the batch. | **Applied,** as Argon's sentence, in "What the read decides". The bar stays 9/10; the rule is now one path, no overlap with brief section 5's trigger. |
| 3 | Slot table audit against `sources.json` and the ordered decision table: slots 1, 2, 4–16 clean. **Slot 3 is an implementation trap:** the record carries "the local option failing a check" and its key is `proceed`, because the failed check belongs to the rejected local baseline and justifies the pod. A literal "any failed check → hold" solver fires row 1. The ledger must tag that check as the baseline's justification, not a failed check on the proposed run. | **Applied.** Slot 3's shape reads "the local baseline failing a check (justifying the pod, not failing the pod's own check)", and the slot's test line tells Seat C to tag it in the ledger. Seat C's decision-table test for slot 3 is the test of this. |

## What Argon reads first when the 26 texts come back

- Slots 3 and 1: did the solver and checks handle the baseline failure, and did the shortest record fit all five sections inside the length cap without clipping the alternative clause.
- The ten negative pairs: does each read as a natural brief that omitted the check or tripwire or used the altered figure, with no "told to hide" artefact.
- The retry log by family: the exact sentences that tripped trace, order or length, and whether one family needed many more attempts.

These three go into the hand-back's "what the surfaces revealed" so Seat C prints them without being asked.
