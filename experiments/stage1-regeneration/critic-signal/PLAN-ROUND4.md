# Critic-signal, round 4: the plan after phase 4 (v2, after Argon's audit, 2026-10-19)

**Status: v2, passed by Argon's re-check (round 4b, 2026-10-19, at `85c81a1`): no open findings at any severity.**
- Nothing here has run. Track A's paid windows wait on the Director's go, and the plan is parked until then.
- **v1** (`4452274`) got a CONDITIONAL PASS from Argon on 2026-10-19: 3 blocking findings, 4 to settle before the
  write window, 2 not blocking. All nine are taken in. Where one changed on checking against the data, §8 says how.
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
  - Argon checked the split: 4 of 10 against 0 of 22 gives Fisher's exact p = 0.0058. Since Pc maps every flaw label
    to one class, a confusion between two flaw labels can't cause a Pc refusal.
- **The correction to `SYNTHESIS.md`.** It recommended testing the coarse gate "against the better labels".
  - Tightening the loop/guess boundary only reduces P2's errors.
  - The coarse gate's errors sit at the **none boundary**: a sound trace read as flawed.
  - That's a different lever, so this plan separates the two.
- **The none boundary as role-set states it** (`src/role_set/critic.py`, `FLAW_DEFINITIONS`, role-set main
  `89b5f2e`):
  - "none" is defined only as "the check was right". It is the one label with no description of what it looks like.
  - "guess" includes "or a misreading", which lets it absorb any trace the critic doubts.
  - Of Muse's 4 flaw answers on sound traces, 3 were "guess" and 1 was "reject_by_default".
- **Pc can fail on both sides of that boundary.** Today it fails on planted-none rows. A prompt that widens "none"
  could also make it answer "none" on a real flaw, which refuses a planted-flaw row. The bar in §3 guards both.

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
  - **The safety net:** R&D's blind gold check, after the window.
    - At the phase-4 gold check it excluded 6 of 38 rows, 3 of them at label boundaries. It reads each trace
      against its label, which is the check this class needs.
    - The cost is R&D's time, not units.
- **What the safety net needs (Argon F7):**
  - **Buffer slots for the gold check.** It runs after the window, when role-set can no longer rewrite a refused
    slot. At phase 4's 16% exclusion rate, T10 gets at least 2 extra kind C buffer slots beyond the batch-mix rule's
    one per quota: 1 odd (planted flaw) and 1 even (planted none).
  - **Coverage.** Every accepted kind C row, and every kind A and non-verdict E row admitted under a bounded share, is
    keyed in the blind gold check.
  - **Acceptance.** Only a row that passes both P0 and the gold check counts as accepted, for the release and for any
    comparison of writers' yields.

## 3. Track A: the none boundary (the test this plan proposes)

**The hypothesis:** the coarse gate fails mostly where the critic reads a sound trace as flawed, and a fuller
definition of "none" reduces that without losing the catch.

**The change, one prompt edit in role-set's flaw prompt** (Argon F3: the contrast is stated the same way in both):
- **"none":** "quoted the deciding lines, reasoned only from what they state (with no outside assumption and no
  misreading of their words), and reached the material's verdict."
- **"guess":** "gave a reason from outside the material (an assumption, what usually happens, general knowledge), or
  misstated what a quoted line says, instead of what the material says. A check that quotes the deciding lines, adds
  no outside assumption, reads them as written, and reaches the material's verdict is none, not a guess."
  - A misreading of a quoted line keeps a home in "guess", so no flawed trace is left without a label.
- **The other labels are unchanged.**
- The exact wording is fixed in the role-set PR, against this text, and reviewed there.

**The rule sets:**
- **P0:** as now.
- **Pc:** the coarse gate. It refuses when the critic's flaw-or-none answer disagrees with the label's flaw-or-none.
  Otherwise it is P0.
  - **A VOID flaw reply refuses** (one not in the label list after its retry), whatever the key (Argon F6). Pc checks
    the label list before it compares flaw-or-none, so a VOID can never read as "a flaw" and pass a planted-flaw row.
  - **P2's quote-length rule is not part of Pc,** so C9-030:d, refused by that rule under P2, is accepted under Pc.
- **The arms (Argon F8):** two Muse runs over the same items at seed 0, from one pinned role-set commit.
  - **Run 1 (old prompt):** P0 and Pc-old are scored from its replies.
  - **Run 2 (new prompt):** Pc-new is scored from its replies, paired against run 1's P0.
    - Both runs send byte-identical verdict prompts at the same seed.
    - The analysis checks the two runs' verdict replies agree, and reports any that don't.

**The slots (Argon F4 and F5):**
- **48 kind C slots:** 24 planted none (even) and 24 planted a flaw (odd), with no T10 slot.
- **The slot list is frozen and committed before the write window,** as a free rung (rung 0 below).
  - Every odd slot must have slot_flaw ≠ "none" and a decided key (supported or unsupported), so perturb.py can
    make its f item.
  - Every even slot must have slot_flaw = "none" and a decided key.
- **Where the odd slots come from:** the 9 non-T10 lessons phase 4 used hold only 24 odd f-eligible slots, and phase
  4 wrote them all.
  - **The first choice** is odd slots from lessons phase 4 didn't use, checked for eligibility as above. Argon
    notes that T04 and T14 key many slots cannot_tell, which perturb.py can't use for f; rung 0 counts what's there.
  - **The second choice** is re-writing phase 4's slots. A re-write counts only if it isn't a near-copy of phase 4's
    row, as checked by **the near-duplicate rung** below. That replaces v2's "the Publisher shows", which had no tool
    behind it (corrected 2026-10-21).
  - **Where it landed (2026-10-21, role-set #100 at 394b8e6, Argon's seed ruling):**
    - Track A is planned at **seed 1**;
    - the census gives 24 odd (5 from unused lessons, 10 unused phase-4 slots, 9 re-writes) and 24 even (5, 18, 1);
    - **10 re-writes in all,** each marked `needs_novelty_check` with fresh domains against phase 4's seed-0 draws.
  - **The near-duplicate rung** runs after the write window and the gold check, before perturb.py and any critic call.
    It's free, on CPU (float32, as calibrated), with no GPU grant.
    - **What it does:** for each of the 10 re-written rows, it embeds the material and the checker trace, and compares
      each with the same slot's phase-4 row.
    - **The thresholds, calibrated on prose rows** (the Director's ruling; Argon's consult design, 2026-10-21).
      Rung 2b's 0.98 was measured on run files, not prose, and isn't used.
      - **Pool:** the 32 phase-4 kind C drafts.
        - Positives: 64, deterministic: 32 surface near-copies (P-close) and 32 domain-noun swaps of the same layout
          and trace skeleton (P-template).
        - Negatives: all 496 off-diagonal pairs. The hard strata are 109 pairs for material (same lesson or content
          kind) and 146 for trace (same lesson or planted flaw).
      - **Measures, per field:**
        - bge-m3 cosine, through dataset-desk's text embedder on CPU (float32, revision 5617a9f6);
        - character 4-gram Jaccard;
        - a trace is scored after stripping verbatim quotes of its material or statement.
      - **Script and receipt:** `scripts/nearcopy_calibration.py` and `data/nearcopy-calibration-2026-10-21.json` (ids
        and statistics only; the rows stay private).

      | Field and measure | Hardest negative | Lowest P-close | Threshold (auto) | Recall close / template | FP hard / all |
      |---|---|---|---|---|---|
      | Material, char 4-gram | 0.293 | 0.303 | **0.298** | 32/32 / 32/32 | 0/109 / 0/496 |
      | Material, bge-m3 | 0.846 | 0.796 | **0.851** | 29/32 / 26/32 | 0/109 / 0/496 |
      | Trace, char 4-gram | 0.293 | 0.494 | **0.393** | 32/32 / 32/32 | 0/146 / 0/496 |
      | Trace, bge-m3 | 0.751 | 0.855 | **0.803** | 32/32 / 31/32 | 0/146 / 0/496 |

    - **The rule:** a re-write is excluded when **any** of the four scores is at or above its threshold, then topped
      up under the stopping rule.
      - On the pool, that rule catches 64 of 64 positives, with 0 of 496 false positives (0 of 199 hard).
      - **The 95% bounds:** recall at least 95.4%; FP at most 0.6% overall and 1.5% on the hard pairs.
      - **These bounds are in-sample.** The thresholds were set on this same pool, so they describe the pool, not new
        rows.
    - **A review band:** a score from the hard negatives' 95th percentile up to its threshold is read side by side by
      R&D, after the gold file is sealed.
    - **Its limits, stated:**
      - the material's char 4-gram margin is thin (0.293 against 0.303);
      - the positives are made by a script, so a real re-write that rewords more freely may score lower;
      - bge-m3 alone misses 3 P-close and 6 P-template materials, which is why the lexical measure is in the rule.
    - **What the rung's result records** (the Publisher's conditions, 2026-10-21):
      - **all four scores for each of the 10 re-writes,** with each one's margin to its threshold, not just pass or
        exclude;
      - **the context:** all 10 have `domain_changed` true, so near-copies should be rare. If the rung excludes
        several, read it as a signal about the thresholds, not about the writer, and say so in the result;
      - **a stop:** if more than 2 of the 10 land in the review band, stop and send the scores to the Publisher before
        any top-up.
    - **The scores and exclusions are committed** with the gold file.
  - The even slots can come from the decided even slots those 9 lessons hold that phase 4 never used (Argon counts
    about 16; rung 0 confirms the number).
- **Gemma 4 31B writes, write-only, with no critic,** as in §9.
- **R&D keys every row blind,** and the exclusions are committed before any critic call (as §9, F3).
- **The stopping rule (blinded calibration, as §9).** If the gold check leaves fewer than 20 kept rows in either
  stratum, more slots of that kind are written and gold-checked before perturb.py and before any critic call. No
  critic call has been made at that point, so it's calibration, not peeking.

**The items:** perturb.py at seed 0, same tool pin. The primary pool is b, e, f and g, as in phases 3 and 4.

**The decision rule (pre-registered):**
1. **Each arm against P0:** Pc-new against P0 and Pc-old against P0, by exact McNemar on the primary pool, with Holm
   across the two.
2. **The control bar, per stratum (Argon F2):** an arm qualifies only if it wins step 1 at Holm-adjusted p < 0.05
   **and** both:
   - its false-refusal rate on planted-none rows is at most 10%;
   - its false-refusal rate on planted-flaw rows is at most 10%.

   At 20 kept rows per stratum that's at most 2 refusals in each. This also keeps the T10-weighted mean at or under
   10%.
3. **If only one arm qualifies,** it is adopted.
4. **If both qualify (Argon F1),** Pc-new is adopted only if:
   - its worse stratum's false-refusal rate is strictly lower than Pc-old's;
   - or that rate ties, and it wrongly accepts strictly fewer items on the primary pool.

   Otherwise Pc-old is adopted, and the prompt edit is dropped.
5. **If neither qualifies,** nothing is adopted, and R&D brings the Director the options.

**Reported beside the decision:**
- **The natural clean-trace catch rate** (Argon Q4): 1 − the planted-none false-refusal rate. On a sound trace, Pc
  accepts the good row exactly when the critic says "none". A sound trace under a false flaw label is caught on that
  same answer. So the planted-none bar already demands at least 90% here. It is reported beside f's template catch
  rate, never pooled with it.
- **Planted-flaw rows by their planted flaw** (guess, loop, nitpick, rubber_stamp), for each arm. That shows whether
  the new prompt made real flaws read as "none".
- **Per-type catches split by the check that refused** (Argon F9): verdict or evidence, against flaw.
  - In phase 4, C9-003:g was refused only because the critic called that row's sound trace a guess.
  - Under the full protocol, a false flaw refusal on a row also "catches" its b, e and g copies.
  - The primary pool is unchanged, for continuity with phases 3 and 4. The split is reported beside it.

**Rungs, all free and before any paid window (Argon F6):**
0. **The slot list,** checked mechanically with role-set's `slot_flaw` and slot metadata as above, and committed.
1. **critic-rescore-offline with Pc, on phase 4's stored replies.** It must reproduce this table, computed by R&D
   from `data/confirm-outcomes.csv`:
   - f 19 of 22 caught, b 5 of 5, e 20 of 20, g 19 of 19;
   - discordance against P0: 20 : 0;
   - d: 4 of 32 refused, all 4 of them planted-none (4 of 10), 0 of 22 planted-flaw, and C9-030:d accepted.

   Plus a unit test: a VOID flaw reply refuses under Pc, for key "none" and for a key in the label list.
2. **A `--mock` CPU check through critic-eval:**
   - the old-prompt setting gives flaw messages byte-identical to role-set `89b5f2e`;
   - the new-prompt setting gives the Track A prompt;
   - the prompt setting is recorded in the receipt and the call journal.
3. **A CPU stub rung** on a small model through the same path:
   - a deadline cut, a resume, a zero-call replay;
   - a resume or replay that would mix old-prompt and new-prompt journals refuses.
4. **A non-mock probe of the frozen items** before their sha is recorded.

**Cost (Colab, from phase 4's measured rates):**
- Writing 48 rows: about 14.9 units (phase 4: 11.78 for 38).
- Two Muse runs of about 104 GPU items each: about 8.3 units each (phase 4: 6.40 for 80), so about 16.6.
- **Total about 31.5 units,** plus any top-up. The study ledger would go from 195.17 to about 227 of 300.
- Applying the design's +15% where measured, the high is about 36.

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
2. **Track A's rungs 0–3,** free. Any failure stops Track A, with no paid window.
3. **Track A's rows:** the write window, the gold check, any top-up, the exclusions committed, perturb, rung 4, the
   freeze.
4. **The two Muse runs** (14c and 14d, or the next free names), then the pre-registered decision.
5. **§10 when RunPod resumes,** with Pc added to its report.

**Stops:**
- any rung failure;
- a family or VOID loss above §9's limits;
- the ledger projection over 300 units.

## 7. Questions for Argon (v1, answered)

Argon answered all six on 2026-10-19. Each answer is folded into the section named.
1. **The correction in §1:** right, algebraically and by Fisher's exact test. Folded into §1.
2. **The control bar:** both strata at 10% or under. Folded into §3, step 2.
3. **The prompt edit:** state the contrast in both labels, and report planted-flaw rows by their flaw. Folded into
   §3.
4. **Template clean traces:** keep f in the pool. The planted-none bar already demands at least 90% on natural sound
   traces; report that rate beside f. Folded into §3.
5. **Size:** at least 20 kept per stratum, so write 24 and 24, with a top-up rule. Folded into §3.
6. **T10 on P0:** defensible, with buffer slots and full gold coverage. Folded into §2.

**Severity levels for the re-check:** `blocking`, `before the write window`, `not blocking`.

## 8. What changed from v1, and one correction to Argon's figures

| Argon | Taken in where |
|---|---|
| F1: no rule when both arms pass | §3, step 4 |
| F2: the weighted bar lets one stratum reach 20% | §3, step 2 |
| F3: the guess/none contrast left out "reasons only from them" | §3, the prompt edit |
| F4: 40 rows fall below 20 a stratum after the gold check | §3, 48 slots and the stopping rule |
| F5: slot selection as a pre-write gate | §3, the slots; rung 0 |
| F6: rungs miss the prompt switch, journal mixing and VOID | §3, the VOID rule; rungs 1–3 |
| F7: T10's buffer and gold coverage | §2 |
| F8: what P0 is paired with | §3, the arms |
| F9: false flaw refusals inflate b, e and g | §3, the split by check |

**One correction, to F6's rung-1 table.**
- Argon expected Pc to accept C9-003:g, giving g 18 of 19 and a discordance of 19 : 0. That depended on C9-003
  being a planted-flaw row.
- It is planted-none, and Muse called its sound trace a guess. So Pc refuses C9-003:g, the same way P2 did, and the
  table is g 19 of 19 and 20 : 0, computed from `data/confirm-outcomes.csv`.
- Under P2 the recorded refusal code on C9-003:g is QUOTE_TOO_LONG, which is checked first. The flaw mismatch would
  also have refused it.
- It is still the case F9 describes: that g catch comes only from the false flaw refusal on the row's own sound
  trace.

## Licences

- **Models:** Muse-Glimmer-30B (critic) and Gemma 4 31B (writer), as in `DESIGN.md` §0. No new model or source.
- **§10's critic:** Nemotron-3.5-Super-VL-120B, OpenMDW-1.1, already in `licences/registry.json`.

## Track A's free rungs: results (2026-10-21)

- **Rung 0 (the slot list):** the 48 slots are frozen on role-set `10c1ebf` (`data/track-a-slots-10c1ebf.json`), and
  the census is unchanged at `e7abbcd` (#102). With the committed excerpt pool (sha `51afb3cd…`), all 14 real-source
  slots assemble from distinct excerpts.
- **Rung 1 (Pc on phase 4's stored replies):** it reproduces the table above exactly once PHASE-4's hand-check drops
  are applied: f 19/22, b 5/5, e 20/20, g 19/19, 20 : 0, and d 4/32 refused, all planted-none. It ran on role-set
  `e3f9fd1d` with aspire-si-gates 1.7.5, the pair phase 4 was scored with. Later role-set needs gates 1.7.6, and the
  rescore refuses a gates mismatch. #101 didn't touch the Pc code.
- **Rung 2 (the flaw prompt):** under `old`, the messages are byte-identical to role-set `89b5f2e`'s code; under
  `new`, they carry this plan's wording, changing only the guess and none lines.
- **Rung 3 (CPU stubs on Colab, role-set `e7abbcd`, 0.06 units in all):**
  - **15a, the write stub:** the 48 ids, seed 1, the pool pinned. 47 of 48 reached awaiting_critique, and all 14
    real-source drafts carry pool sources. The one drop is a stub MockWriter defect, queued for role-set.
  - **15b:** flaw prompt `new`, cut at the deadline in seed 1.
  - **15c:** the resume replayed seed 0 with 0 calls and byte-identical scores, then finished seed 1 (109 reused, 51
    called).
  - **15d:** a resume under `old` refused before any call (the journals mixed settings).

## Track A's rows: results (2026-10-21)

- **The write window (15e, A100):** 47 of 48 drafts. T12-C-02 was refused by the gate: Gemma's quote dropped the
  excerpt's markdown backticks.
- **The gold check:** R&D keyed all 47 blind before opening the writer's keys.
  - Verdicts agree on 47 of 47, and planted flaws on 46 of 47.
  - 43 kept: odd 21, even 22. Both strata are above 20, so there's no top-up.
  - 4 excluded: 2 UNCLEAR (a qualifier the material never names), 1 flaw label, and 1 draft with no checker_verdict
    (a new defect class).
  - The flaw-stem leak pre-screen flags 0. Details: `data/track-a-gold-2026-10-21.json`.
- **The near-duplicate rung:** 0 of the 9 kept re-writes excluded. 2 fell in the review band and were read side by
  side; both were kept. 2 is under the Publisher's stop (more than 2). Details: `data/track-a-nearcopy-2026-10-21.json`.
- **perturb.py at seed 0:** 102 GPU items (d 43, b 7, e 31, f 21).
- **Rung 4 (a non-mock probe):** passes.
- **Frozen items:** sha256 `b00f45d09d226f5cc0ed0fae6393d298ef6e256d835f00729d802952d7f1d449`, recorded before any critic call.
- **One code version for Track A** (agreed with the Publisher, 2026-10-21): both Muse runs (15f old prompt, 15g new
  prompt) and the offline scoring of P0, Pc-old and Pc-new run at role-set `e7abbcd` with aspire-si-gates 1.7.6. A
  later role-set change, such as the verbatim-quote repair for T10 that also touches `compare_verdict`, doesn't reach
  Track A, so the two runs differ only in the flaw prompt.

## Track A's analysis: held (2026-10-22)

- **The premise failed.** The agreement check between the two Muse runs fails. Their verdict prompts are
  byte-identical (rung 2), and the prompt token counts match on all 102 items. But:
  - the raw verdict replies differ on 22 of 102;
  - `critic_verdict` differs on 7;
  - `critic_deciding` differs on 19;
  - P0's outcome differs on 8 of 219 scored items.

  Muse's card samples at temperature 1.0 (top_k 64, top_p 0.95), and seed 0 doesn't make GPU sampling reproducible
  across sessions.
- **The Publisher ruled** that the question goes to Argon before anything further is computed or reported.
- **A disclosure:** R&D's analysis script computed the full decision in the same pass, before the ruling arrived, so
  R&D has seen those figures. They're held, unreported, and have no bearing on the choice of analysis. That choice
  comes from Argon, who hasn't seen them.
- **Argon's ruling on the analysis** (consult of 2026-10-22, given without sight of any outcome figure). It's fixed
  here before anything further is computed.
  - **Primary:** (a), exactly as pre-registered above.
  - **Beside it, (b):**
    - Pc-new′, scored from run 1's verdict check and run 2's flaw check, paired against P0₁ and against Pc-old;
    - within-run Pc-new against P0₂.
  - **Thresholds unchanged:** α 0.05 with Holm, and at most 10% false refusals on each d-control stratum.
  - **The concordance rule:** an arm is adopted automatically, under steps 3–4, only if (a) and (b) agree on
    qualification and winner. If they diverge, the result counts as noise-bounded, and both tables go to the Director
    under step 5.
  - **The noise floor is reported beside the result:** run 1 against run 2 on identical prompts, by call (raw, deciding
    and verdict), by type, on the primary pool, and by d-control stratum.
- **Track A's result** (`data/track-a-result-2026-10-22.json`):
  - (a) and (b) are concordant: neither arm qualifies.
  - Both beat P0 on the primary pool, but both fail the planted-none control bar (9/22 and 10/22 against at most 10%).
    Muse names "guess" on sound traces.
  - So it's step 5. **The Director chose option 1, with Track B next, 2026-10-22.** P0 stays the gate (T10 carries on
    unchanged), and Track B (exact labels) is designed next: from the experiment template, reviewed by Argon before any
    slot, key or label changes, with no spend until the design is approved.
