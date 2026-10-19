# Phase 4: the confirmation test (DESIGN.md §9), result (2026-10-19)

The test was pre-registered in §9 (Argon PASS round 3b). Its inputs were frozen in `data/confirmation-prereg.json`
(rnd #162, v1.1.15.2.7) before any critic call. Item text stays local. This file and `data/confirm-*.csv` hold ids,
codes and counts only.

## The run

- **The rows:** window 14a wrote 38 new kind C rows (Gemma 4 31B, write-only, no critic, 11.78 units).
  - R&D keyed them blind and kept 32: 22 clean-trace eligible and 10 "none" controls.
  - The 6 exclusions are in the prereg record.
- **The items:** perturb.py (role-set `47a5882`, seed 0) made 80 GPU items: d 32, b 5, e 21, f 22.
  - Hand-check drops, recorded before the run: C9-030:e, C9-030:g and C9-035:g.
- **The critic run:** window 14b, Muse-Glimmer-30B, seed 0, A100, 6.40 units.
  - 80 of 80 scored, 0 family skips.
  - 160 calls: no VOID retries, no empty replies, all finished normally.
  - A median of 19.4 s a call.

## The pre-registered decision

The comparison is P2 against P0 on Muse, by exact McNemar on the primary pool (b, e, f, g after the drops: 5, 20, 22
and 19, so n = 66). P2 is adopted only if p < 0.05 in its favour **and** its control refusal is at most 10%.

| | P0 wrongly accepts | P2 wrongly accepts |
|---|---|---|
| b, material flip (5) | 0 | 0 |
| e, can't-tell trap (20) | 0 | 0 |
| f, clean trace (22) | 22 | 1 (C9-031:f) |
| g, decoy deciding line (19) | 1 (C9-003:g) | 0 |
| **all (66)** | **23** | **1** |

- **Discordant pairs:** 22 in P2's favour, 0 against. Exact McNemar p ≈ 5 × 10⁻⁷. **The first condition is met.**
- **Controls:**
  - P0 refused 0 of 32 good rows.
  - **P2 refused 12 of 32 (37.5%).** 11 are flaw mismatches and 1 is the quote-length rule (C9-030:d).
  - **The second condition (at most 10%) fails, so P2 is not adopted.**
- Under §5, R&D brings the Director the options.

## What the critic's flaw answers show

Muse's flaw answers on the 32 good rows, against the planted label:

| Planted | Muse agreed | Muse said instead |
|---|---|---|
| guess (8) | 7 | nitpick 1 |
| nitpick (6) | 5 | guess 1 |
| loop (7) | 2 | guess 4, nitpick 1 |
| rubber_stamp (1) | 0 | guess 1 |
| none (10) | 6 | guess 3, reject_by_default 1 |

- **The natural-prose benchmark** (Argon Q2) is the even "none" slots: Muse said "none" on 6 of 10.
  - On the template clean traces (f), it said "none" on 19 of 22. Its other 3 answers were "guess", which also
    refuses under P2.
  - Phase 3 measured Muse at 9 of 10 on its own critic-accepted rows, a different population (§9 states the
    difference).
- **The confusions follow the label boundaries.** Most are "loop" read as "guess". Three of the six gold-check
  exclusions were also guess/nitpick boundary cases. The flaw labels overlap, and the critic disagrees most where
  the labels themselves are fuzzy.
- **The verdict check held on every type.**
  - It agreed on all 32 controls and all 22 clean traces.
  - It refused all 5 material flips.
  - It refused all 21 can't-tell traps: 19 by verdict and 2 by evidence.

## Post hoc, not a result

**A coarser gate (an idea for a future pre-registered test).** This one refuses only when Muse's flaw-or-none
answer disagrees with the label's flaw-or-none. On these replies it would catch 19 of 22 clean traces, and falsely
refuse 4 of 32 controls (12.5%). That's still above the 10% bar, and it was found after seeing the data.

## Cost

- 18.18 units for the confirmation: 11.78 for writing and 6.40 for the critic.
- The ledger stands at 195.17 of 300.
