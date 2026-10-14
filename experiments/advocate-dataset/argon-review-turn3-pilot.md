# Argon's check of the turn 3 pilot brief, and the disposition | 2026-10-14

Argon read `seat-build-batch1-turn3-pilot.md` at rnd 1.1.8.2.15. Verdict: not ready, three alignment defects between the slot table and the pack; fix them and hand the brief to Seat C. The pilot bar was confirmed once the critic's denominator was stated.

## The three findings, and what was done

| # | Finding | Disposition |
|---|---|---|
| 1 | Slots 6 and 15 planted negatives outside the three classes `behaviours.jsonl` registers (hide one failed check, hide one tripwire, alter one figure); slot 15 is kind B, which has no negative pair under the lean brief, which would have made 27 texts and left B's checks unspecified for a negative. | **Applied.** Slot 6's negative hides the failed check. Slot 15 has no negative; its line names the relay (keep the required changes, drop the cost line). The brief now says the count: 26 texts, 16 positives and 10 kind A negatives, and that a negative carries one registered class only. |
| 2 | Slot 2 called `pilot_first` the table's third row; in the lean brief's ordered table (`hold`, `hold`, `cannot_tell`, `pilot_first`, `proceed`) it is the fourth. | **Applied.** Checked against brief section 3 before the edit. |
| 3 | The critic bar counted 16 keys while the read's deferred trigger counted planted negatives; the denominator was unstated. | **Applied.** The critic judges all 26 texts with keys hidden: at least 15 of 16 positive keys recovered, at least 9 of 10 negatives flagged. The hand-back prints both counts. The read section now says what one missed negative means: the bar passes, but it is above the 5% trigger in brief section 5, so the deferred two-leg critic comes back as its own brief. |

## What it changes for Seat C

Nothing in the run order. The negative generator has three classes to draw from, not five; the critic's report has two counts, not one; the table pointer reads the right row.
