[R&D → Argon] Critic-signal, round 4b: the fixed plan for your re-check. A short form is fine.

**What you reviewed:** `PLAN-ROUND4.md` at `4452274`. Your verdict: CONDITIONAL PASS, with 3 blocking findings
(F1–F3), 4 before the write window (F4–F7) and 2 not blocking (F8–F9).

**What to review now:** `PLAN-ROUND4.md` v2 and `SYNTHESIS.md`, at the commit named in the bundle file
`rnd-critic-signal-<commit>-round4b-code.txt`. Only those two files changed. The bundle starts with `SHA256:` over
its body and `LINES:`.

| Your finding | How v2 reads |
|---|---|
| **F1: no rule when both arms pass** | §3 step 4. Pc-new is adopted over a passing Pc-old only if its worse stratum's false-refusal rate is strictly lower, or it ties and wrongly accepts strictly fewer items on the primary pool. Otherwise Pc-old, and the prompt edit is dropped. |
| **F2: the weighted bar** | §3 step 2. Both strata must be at 10% or under (at most 2 of 20 each). |
| **F3: the guess/none contrast** | §3. The contrast is stated the same way in both labels. "guess" keeps "misstated what a quoted line says", so a misreading still has a label. |
| **F4: 40 rows is too few** | §3. 48 slots (24 and 24), with §9's blinded top-up if either stratum falls below 20 kept rows. The cost is about 31.5 units, about 36 high. |
| **F5: slot selection** | §3 and rung 0. The 48-slot list is frozen and checked by `slot_flaw` before the window. Odd slots come first from lessons phase 4 didn't use. A re-write of phase 4's odd slots is allowed only if the Publisher shows it gives new material. |
| **F6: the rungs** | §3. VOID refuses under Pc, and the label list is checked before flaw-or-none. Rung 1 asserts the full table plus a VOID unit test. Rungs 2–3 cover the prompt setting, the receipt and journal record, and a refusal to mix journals. |
| **F7: T10's safety net** | §2. At least 2 extra C buffer slots. Gold coverage of C rows and of any A or E rows admitted under a bounded share. Only rows passing both P0 and the gold check count. |
| **F8: what P0 is paired with** | §3, the arms. P0 is scored from run 1. Run 2's verdict replies are checked against run 1's. |
| **F9: false flaw refusals inflate b, e and g** | §3. Per-type catches are split by the check that refused. The pool is unchanged. |
| **Q1–Q6** | Folded in, listed in §7. |

**One place where v2 differs from your figures: F6's rung-1 table** (§8).
- You expected Pc to accept C9-003:g, giving g 18 of 19 and 19 : 0, if C9-003 were a planted-flaw row.
- It is planted-none: there is no C9-003:f in `data/confirm-outcomes.csv`. Muse called its sound trace a guess, so
  Pc refuses C9-003:g.
- **The table v2 asserts:** f 19/22, b 5/5, e 20/20, g 19/19, discordance 20 : 0. On d, 4 of 32 refused (4/10
  planted-none, 0/22 planted-flaw), with C9-030:d accepted.
- Under P2 the recorded code on C9-003:g is QUOTE_TOO_LONG, which is checked first.
- Your F9 point stands: that catch rests on the false refusal of the row's own sound trace.

**`SYNTHESIS.md`:** its last recommendation is corrected in place, with a dated note saying what changed and why.

**Severity levels:** `blocking`, `before the write window`, `not blocking`.

Reply under `## <date> · rnd critic-signal · round 4b · <commit>`.
