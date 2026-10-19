# Critic-signal, round 4: the plan after phase 4 (draft for Argon's audit, 2026-10-19)

**Status: draft.**
- Nothing here has run, and nothing runs until Argon passes it and the Director gives the go.
- It extends `DESIGN.md` in the same template: the rnd model-comparisons design, sections 0–8.
- It builds on `SYNTHESIS.md` and corrects that file's last recommendation (§1 below).

## 1. Where it stands, and one correction

- **No protocol is adopted.**
  - P2, the exact-label flaw gate, catches what P0 misses: 22 : 0 in phase 4, p ≈ 5 × 10⁻⁷.
  - But it refuses 12 of 32 good rows, against a 10% limit.
- **The two gates fail for different reasons.** Measured from `data/confirm-outcomes.csv` (P0 rows; for the good
  rows, an f item exists exactly for the planted-flaw rows):

| Good rows (d) | n | Muse answered a flaw | Muse answered none |
|---|---|---|---|
| planted a flaw | 22 | 22 | 0 |
| planted none (a sound trace) | 10 | 4 | 6 |

  - **P2's 12 false refusals** are 8 wrong-label answers on planted-flaw rows, mostly loop read as guess, plus the
    4 sound traces read as flawed. (One of the 12 was decided by the quote-length rule; see `PHASE-4.md`.)
  - **The coarse gate's 4** (refuse only when the critic's flaw-or-none answer disagrees with the label's) are
    **all** sound traces read as flawed. It refused none of the 22 planted-flaw rows.
- **The correction to `SYNTHESIS.md`.** It recommended testing the coarse gate "against the better labels".
  - Tightening the loop/guess boundary only reduces P2's errors.
  - The coarse gate's errors sit at the **none boundary**: a sound trace read as flawed.
  - That's a different lever, so this plan separates the two.
- **The none boundary as role-set states it** (`src/role_set/critic.py`, `FLAW_DEFINITIONS`, role-set main
  `89b5f2e`):
  - "none" is defined only as "the check was right". It is the one label with no description of what it looks like.
  - "guess" includes "or a misreading", which lets it absorb any trace the critic doubts.
  - Of Muse's 4 flaw answers on sound traces, 3 were "guess" and 1 was "reject_by_default".

## 2. T10 runs on P0 now, with the deterministic fixes

The T10 writer run doesn't wait on this plan.
- **Critic protocol:** P0, today's rules. The flaw check stays advisory.
- **Phase 1's fixes,** as builder items for role-set and aspire-si:
  - slots with real difficulty, under the batch-mix rule already carried in `DESIGN.md`;
  - a gate that refuses a trace naming its own flaw (defect class `trace-leaks-label`, with P1-017 and P1-035 as its
    test cases);
  - for kinds A and non-verdict E: an accuracy check, or a share of the batch bounded until one exists.
- **The known risk, stated in T10's design:** a C row whose trace is sound but whose label names a flaw passes P0.
  - **Its rate in real writer output isn't known:** f items are built by a script.
  - **The safety net:** R&D's blind gold check on every accepted T10 C row, as in phases 1 and 4.
    - At the phase-4 gold check it excluded 6 of 38 rows, 3 of them at label boundaries. It reads each trace
      against its label, which is the check this class needs.
    - The cost is R&D's time, not units.

## 3. Track A: the none boundary (the test this plan proposes)

**The hypothesis:** the coarse gate fails only where the critic reads a sound trace as flawed, and a fuller
definition of "none" reduces that without losing the catch.

**The change, one prompt edit in role-set's flaw prompt:**
- "none" gets a definition of what a sound check looks like: it quotes the deciding lines, reasons only from them,
  and reaches the material's verdict.
- "guess" loses "or a misreading", which becomes part of "none"'s contrast: a check that quotes the right lines and
  reaches the right verdict is not a guess.
- The other labels are unchanged.

The exact wording is drafted in the role-set PR and reviewed there. Argon is asked about the direction here (Q3).

**The rule sets, all scored from the same replies:**
- **P0:** as now.
- **Pc:** the coarse gate. It refuses when the critic's flaw-or-none answer disagrees with the label's flaw-or-none.
  Otherwise it is P0.
- **Arms:** Pc is scored on two critic runs over the same items:
  - **Pc-old:** today's prompt;
  - **Pc-new:** the Track A prompt.

**The rows.** About 40 fresh kind C rows: Gemma 4 31B, write-only, no critic, built as in §9.
- **Half planted none, half planted a flaw.** Phase 4's 10 none controls were too few to measure a 10% rate.
- **Whether fresh rows can use the same slots** isn't settled yet. Phase 4 used every unused f-eligible slot.
  - Before the slot list is frozen, the Publisher probes whether re-writing a slot gives new material.
  - If it doesn't, new slots are planned from other lessons.
  - T10's own slots are not used.
- **R&D keys them blind,** and the exclusions are committed before any critic call (as §9, F3).

**The items:** perturb.py at seed 0, same tool pin. The primary pool is f (the hole) plus b, e and g (so Pc keeps
P0's catches).

**The decision rule (pre-registered):**
- **Primary comparison:** Pc-new against P0, by exact McNemar on the primary pool.
- **Secondary comparison:** Pc-old against P0, which replicates the phase-4 post hoc on fresh rows.
- **Holm across the two.**
- **Adopt Pc-new only if both hold:**
  - it wins at Holm-adjusted p < 0.05;
  - its false-refusal rate on good rows is at most 10%.
- **The false-refusal rate is weighted to T10's mix:** the mean of the planted-none and planted-flaw rates, since
  even slots plant none and odd slots plant a flaw. This is Q2 to Argon.
- **If Pc-old passes and Pc-new doesn't,** Pc-old is adopted on the same rule. The prompt change is then dropped.

**Rungs, all free and before any paid window:**
1. **critic-rescore-offline with Pc, on phase 4's stored replies.** It must reproduce the post hoc exactly:
   - 19 of 22 clean traces caught;
   - 4 of 32 controls refused, all 4 on planted-none rows.

   That checks the new rule set's code against a known answer.
2. **A `--mock` CPU check** of the prompt edit through critic-eval.
3. **A CPU stub rung** on a small model through the same path: a deadline cut, a resume, a zero-call replay.
4. **A non-mock probe of the frozen items** before their sha is recorded.

**Cost (Colab, from phase 4's measured rates):**
- Writing about 40 rows: about 12.4 units (phase 4: 11.78 for 38).
- Two Muse runs of about 90 items each: about 7.2 units each (phase 4: 6.40 for 80), so about 14.4.
- **Total about 27 units.** The study ledger would go from 195.17 to about 222 of 300.
- Applying the design's +15% where measured, the high is about 31.

## 4. Track B: exact labels (deferred)

Tightening the flaw labels themselves, mostly loop against guess, would reduce P2's wrong-label refusals. It matters
only if an exact-label gate is still wanted after Track A.
- The labels also shape the training rows, so a change there touches the lessons, the slots and the gold keys.
- **It is deferred.**

| Deferred | Its trigger |
|---|---|
| Track B label rewrite | Track A fails, or T10's gold check finds label-boundary rows above 10% of C rows |
| P3 (two seeds) | Never on these items: it matched P2 on every type in phase 3 |
| §10 at a still larger critic (step 2) | §10's step 1 fails, and only on the Director's go |

## 5. §10, the larger critic, unchanged

Step 1 stays parked until RunPod spending resumes. A free availability check for an H200 on a CUDA 13.0 host runs
first. The plan adds one thing at no cost: when its replies exist, Pc is scored offline beside P0 and P2 on the
frozen phase-4 items.

## 6. Order and stops

1. **T10 proceeds on P0** with §2's fixes, independently.
2. **Track A's rungs 1–3,** free. Any failure stops Track A, with no paid window.
3. **Track A's rows:** the write window, the gold check, the exclusions committed, perturb, rung 4, the freeze.
4. **The two Muse runs** (14c and 14d, or the next free names), then the pre-registered decision.
5. **§10 when RunPod resumes,** with Pc added to its report.

**Stops:**
- any rung failure;
- a family or VOID loss above §9's limits;
- the ledger projection over 300 units.

## 7. Questions for Argon

1. **The correction in §1.** Is it right to read the coarse gate's errors as a none-boundary problem, separate from
   P2's label confusions, from these 32 rows? Or is 4 of 10 too few to locate them?
2. **The control bar.** Is the T10-weighted false-refusal rate (the mean of the planted-none and planted-flaw rates)
   the right quantity for the 10% bar? Or should planted-none rows carry their own bar, since that's the only
   stratum where Pc can fail?
3. **The prompt edit.** Does moving "or a misreading" out of "guess" and defining "none" risk making real guesses
   read as none, which would cost catches on f? Should the primary pool report f by the flaw it hides?
4. **Template clean traces.**
   - The f items are built by a script, and Muse read them as "none" more often than natural sound traces: 19 of 22
     against 6 of 10.
   - Does that bias the catch side of the test upward?
   - Should a natural sound-trace stratum, the planted-none rows, carry the power instead?
5. **Size.** Is about 20 planted-none and 20 planted-flaw rows enough, or should the bar's stratum be larger, for
   the decision to mean something?
6. **T10 on P0.** Is running T10 on P0, with a blind gold check as the safety net, defensible while Track A runs? Or
   should T10 wait?

**Severity levels:** `blocking`, `before the write window`, `not blocking`.

## Licences

- **Models:** Muse-Glimmer-30B (critic) and Gemma 4 31B (writer), as in `DESIGN.md` §0. No new model or source.
- **§10's critic:** Nemotron-3.5-Super-VL-120B, OpenMDW-1.1, already in `licences/registry.json`.
