# Stage 1, part 2: a critic that can tell writers apart (design draft)

**Status: v2, passed by Argon's short-form review (2026-10-19, two rounds). Phases 0–3 done (`PHASE-0-1.md`, `PHASE-2-3.md`): no protocol adopted under §5 (Holm 0.0625). The confirmation test in §9 ran (`PHASE-4.md`): P2 catches 22 : 0 more errors than P0 (p ≈ 5 × 10⁻⁷) but refuses 12 of 32 good rows, so under §5 it is not adopted, and the options go to the Director.** Template: the rnd
[model comparisons](../../../site/src/content/docs/handbook/model-comparisons.md) design, sections 0–8, with a
phase 0 added in front. It comes before the T10 lesson's writer run, which waits on its outcome.

## Why this study exists

The writer screen (rnd newsletter issue 11, windows 12b–12h) and its two follow-on windows (W-A, W-B) chose writers
by what a critic accepted. The critic barely refused anything:
- Muse accepted 35 of 36 first drafts in the screen.
- The rescore (window 13t) gave a second critic from another family, Lightning, a blind sample: it accepted all 7,
  including the one draft Muse had refused.

Two readings fit those numbers, and the screen can't tell them apart: the drafts are good, or the critics can't see
what's wrong with them. A full run gated by a critic that accepts everything would measure nothing. So this study
asks first whether the critic can detect bad drafts, then makes it able to, and only then compares writers.

## 0. Licences first

Every model and source here is in `licences/registry.json` for the use made of it:
- **Writers whose drafts are re-checked:** Qwen3.8-27B, Gemma 4 31B, Granite 4.2 30B and Muse-Glimmer-30B
  (`apache-2.0`, `muse-glimmer-30b-card`; evaluation allowed); Nemotron-3.5 Bolt and Lightning (`openmdw-1.1`,
  `nemotron-model-cards`; evaluation allowed).
- **Critics under test:** Muse-Glimmer-30B and Nemotron-3.5-Lightning, as above.
- **The gold check (phase 1):** R&D, a Claude session, keying blind. Anthropic's terms allow Claude output for this
  non-competing specialized tool (`anthropic-help-12326764`). The gold labels are evaluation data only and never a
  training target.
- **Perturbations (phase 2)** are made by a deterministic script from accepted drafts. No model writes them.
- **Anything else a reviewer proposes** (a larger rented critic, a public dataset) gets its registry entry before
  it enters the design.

## 1. The check in three sentences

1. **The decision:** which critic protocol gates the T10 writer run, or whether no prompted protocol on our critics
   is good enough and the critic itself must change (a bigger model, or a trained critic).
2. **The candidates:** the current protocol (P0, below) as incumbent, against a small set of stricter protocols on
   the same two critics, each run on the same items.
3. **Why the measure answers the decision:** a critic is useful only if it refuses drafts that are wrong and keeps
   drafts that are right. So the measure is the false-accept rate on known-bad items together with the
   false-reject rate on known-good items, both against labels the critic never saw.

## 2. What the critic does today, measured from the receipts

Read from the code at role-set main (`Runner._critic_pass`, `critique_step`) and the call records in windows 12f,
12h, 13b and 13l (`drafts.jsonl` inside each `pilot-out.tar`):

- **The verdict check is already solve-first.** The critic gets the material and the statement with the key
  hidden, gives its own verdict and deciding lines, and a comparison rule checks them against the key. On those
  windows it agreed on 28 of 30 verdict checks.
- **The flaw check never refuses.** For a kind-C item, the critic names the reasoning flaw planted in a checker's
  trace. `flaw_gate` defaults to off and no window turns it on, so a disagreement is logged as advisory and the item
  is accepted anyway. The critic disagreed on 4 of the 12 flaw checks in those windows, and none of the 4 was
  refused for it.
- **The trait check does refuse.** The critic votes three times on which lesson trait an item teaches. It
  disagreed on 15 of 39 trait checks, 10 of them on twin items, and those drafts went back for rewrites or were
  dropped.
- **There is no check on anything else:** not the material's quality, not whether the statement is ambiguous,
  not whether "cannot_tell" was the honest verdict.

Argon's consult, checked by R&D against `critic.py` and `runner.py`, found three more gaps:
- **The critic never reads the writer's reply.** `verdict_messages` passes only the material and the statement, so
  a reply that contradicts its own key, or a wrong ESCALATE line, is never seen by the critic. Kind A items get no
  accuracy check from the critic at all.
- **A cannot_tell key accepts any quote.** When the key says cannot_tell and the critic agrees, `compare_verdict`
  returns AGREE without checking that the critic's deciding lines are empty.
- **A quote that is too long still passes.** For supported and unsupported, the scorer's `critic_mismatch` accepts
  a critic quote that covers the key's line inside a larger block, even if the critic relied on another clause.
- (Already in place, and so not a new protocol: a quote that isn't verbatim in the material goes VOID, gets one
  retry, and then refuses.)

So the leniency is at least partly structural: a check computed and then ignored, and comparisons that accept too
much. Whether the critic's own reading is also too easy is what phases 1 and 2 measure.

## 3. What the research says (the design implications)

Three research agents read the literature on 2026-10-19 (full reports filed with this design).
- **LLM judges lean towards accepting.** Most of the judges tested called mismatched short answers correct
  (0.87–0.99 of the time for most open models; Thakur et al. 2024, arXiv:2406.12624), and high percent agreement
  hid gaps of over 10 points from human scores. *For us:* 36 of 40 on the known-answer set is percent agreement,
  and doesn't rule out leniency on real drafts. Report a chance-corrected statistic and per-class accept rates.
- **Corrupting real outputs exposes blind spots.** Evaluator models missed the quality drop in over half of 2,400
  deliberately corrupted answers; given a reference, factual misses fell to 11% (Doddapaneni et al. 2024,
  arXiv:2406.13439). *For us:* phase 2 corrupts our own accepted drafts by script, with known effects, and our
  critic already has the material as its reference.
- **A model asked to find a reasoning error mostly says there is none.** Direct prompting found the mistake in
  40% of flawed traces for the strongest model tested (Tyen et al. 2023, arXiv:2311.08516). *For us:* the advisory
  flaw check is exactly this task; turning it into a gate needs its own measured catch rate first.
- **A reference is the strongest single lever, and self-critique without one is unreliable.** With a reference
  answer, a judge's false accepts on maths fell from 14 of 20 to 3 of 20 (Zheng et al. 2023, arXiv:2306.05685;
  a small test). Critique without tools gained nothing on QA (Gou et al. 2023, arXiv:2305.11738).
  *For us:* deterministic checks first, then require the critic to quote the material lines it relies on and
  check the quotes by string match.
- **Stricter critics trade false accepts for false rejects.** Verifiers in planning tasks showed false-positive
  rates of 0.5–18.6% but false-negative rates up to 97% (Stechly et al. 2024, arXiv:2402.08115). *For us:* every
  protocol is scored on both, and on known-good items as well as known-bad ones.
- **Seeded defects understate the natural miss rate** (error seeding, Mills 1972, technical report; cited from
  memory, unverified). *For us:* phase 2's catch rate is a floor and a way to compare protocols, never the headline
  false-accept rate. Phase 1 gives that.

Transfer risk: none of these studies tests current ~30B open models on grounded supported/unsupported/cannot_tell
rows. The direction (lenient judges, references help) recurs; the magnitudes may not.

## 4. The phases

**Phase 0, from existing receipts, free.**
- The per-check agreement table above, completed for every screen window (including the 12g and 12h extracts),
  per arm and per check.
- The verdict mix of accepted drafts (supported, unsupported, cannot_tell) against the release mix rule in
  aspire-si's `check_batch`.
- Output: a table in this folder, computed by a script from the receipts.

**Phase 1, the gold check of accepted drafts.**
- Take every accepted row from the screen, W-A and W-B: about 50 (the exact count goes in phase 0's table). With
  so few, the whole pool is checked rather than a sample.
- R&D keys each row blind: material and statement only, giving a verdict and deciding lines, without seeing the
  writer, the critic's answer or the row's key. For a kind-C row, R&D also names the planted flaw from the trace,
  blind to the row's label.
- Then a second pass compares with the row's key, and audits the writer's reply: does it agree with the key, and is
  its ESCALATE line right? Each disagreement gets a one-line reason.
- A disagreement is adjudicated by reading the material line by line.
- **An unclear row counts as a failure.** An item whose verdict can't be settled from its material is defective
  training data. Unclear rows are reported apart, counted with wrong rows for the decision rule, and kept out of
  phase 2's pool.
- **When R&D yields to the row's key,** a second seat reviews that row before it counts as correct.
- **Sizing:** with no wrong rows in 59, the one-sided 95% upper bound on the false-accept rate is 5%; in 50, about
  6%; in 29, 10% (exact binomial; Hanley & Lippman-Hand 1983, rule of three; Clopper & Pearson 1934). One or two
  wrong rows widen the bound; the pool can then be extended from T10's first batch.
- Cost: R&D's time only.

**Phase 2, perturbed drafts, by script.** From accepted drafts that phase 1 confirmed correct (unclear rows
excluded), make copies with one known change each. The critic never sees the key, so only changes to what it reads
need GPU calls.

Changes to what the critic reads (run on the GPU):
- (b) **material flip:** the material's deciding line negated or its number changed, so the true verdict changes
  while the key doesn't;
- (e) **cannot_tell trap:** the deciding fact replaced by a tangential or conditional clause, so the true verdict
  becomes cannot_tell while the key still says supported or unsupported. This tests over-inference;
- (f) **clean trace:** for C items, the checker's trace replaced by a sound one while the planted-flaw label stays.
  This tests whether the critic says "none" or rubber-stamps a flaw;
- (d) **controls:** the unchanged confirmed-good rows, to measure false rejects.

Changes to the key only (scored offline from the controls' replies, no GPU):
- (a) **verdict flip;** (c) **flaw relabel;** (g) **decoy deciding:** the key's deciding line swapped for a
  plausible non-deciding line of the material. Each is scored by running the comparison rule on the control
  replies against the changed key.

**How the script writes (e) and (f), so the wording doesn't give them away** (Argon, round 2):
- (e) deletes the deciding clause or value, or swaps its subject for another entity already in the passage. It
  never adds a templated qualifier such as "if approved" or "allegedly".
- (f) builds the sound trace from the item's own key: the key's deciding quote and the true verdict, with the
  checker's verdict set to match, so the trace uses the passage's own words.

About 30 confirmed-good rows give about 30 controls, 30 (b), 30 (e) and the C items' (f): about 100 GPU items.
Score: the accept rate on each perturbed type (a floor on false accepts) and the refuse rate on controls (false
rejects).

**Phase 3, the protocols**, all on the same items as phase 2, paired. Only the verdict and flaw checks run: the
trait check is the same under every protocol, is most of the calls, and would swamp the control refusals. It's
reported separately from phase 0.
- **P0, incumbent:** today's verdict and flaw checks, flaw advisory.
- **P2, the comparisons tightened:** from the same critic replies as P0, with no extra calls: the flaw gate on; a
  cannot_tell agreement requires the critic's deciding lines to be empty; a supported or unsupported agreement
  refuses a quote longer than the key's deciding lines plus one.
- **P3, two readings:** P2 on a second critic run at another seed, refusing if either reading refuses.

(v1's P1, the flaw gate alone, is folded into P2: with about 8 C items it could never reach significance.)

**The comparison:** for each critic, P2 and P3 against P0 by exact McNemar on the paired outcomes (right or wrong
against the label), with Holm across the two pairs and the critics run. No other pair is tested.
- **What the primary test counts** (Argon, round 2): the independent GPU-perturbed items, (b), (e) and (f) (about
  70), plus the offline (g). Types (a) and (c) re-score the same control replies deterministically, so they aren't
  independent trials and are never pooled with (d). Each type's catch rate is reported on its own.

**Power, stated plainly.** With about 100 GPU items plus the offline types, a drop in false accepts from about 30% to
10% is detectable; a drop from 10% to 3% needs about 160 paired items (Connor 1987, cited from memory, unverified). A
small improvement reads as "not shown", not "equal".

## 5. The decision rule

Written before anything runs:
1. **Adopt** the cheapest protocol that, against P0 on the same critic: lowers the perturbed-copy accept rate
   significantly (Holm-adjusted p < 0.05); keeps the control refuse rate at or under 10% on the verdict and flaw
   checks; and costs at most 3× P0's critic time per item. P2 costs the same as P0; P3 costs twice.
2. **If several qualify,** the cheapest wins. Ties in cost go to the lower perturbed-copy accept rate.
3. **If none qualifies on either critic,** no prompted protocol on these critics is good enough. The T10 run doesn't
   start, and R&D brings the Director the options: a larger critic on RunPod, or the trained-critic recipe line from
   rnd entry `2026-10-08-dataset-recipes-for-critic-jury-roles-designing-roles-by-dat`.
4. **Phase 1 stands on its own:** if R&D finds 3 or more rows wrong or unclear in the pool, the screen's choice
   of writers is reopened, whatever phase 3 shows.

## 6. Hardware, pins and cost

- **Machine line:** one A100 40 GB on Colab, as in the screen, with role-set at a pinned commit, the critics'
  Q8_0 GGUFs byte-matched to their pins, Lightning converted in-window, and Muse from the private GGUF repo.
- **Projection, measured rates only** (rnd handbook "Rented GPU windows"): Muse critiqued at 296 s per draft
  (12f) and Lightning at 247 s per item (13t). Most of that is the critic's thinking.
  - **P2 costs nothing extra:** it is P0's replies under tightened comparisons. **P3 adds one more run.**
  - **Without the trait votes,** an item is one or two verdict calls plus one flaw call on C items, against about
    five calls with traits. A verdict-and-flaw item hasn't been timed, so it takes the +30% rule: estimate 296 s ×
    2/5 ≈ 120 s per item for Muse.
  - **Step 1, Muse, seed 0 (P0 and P2):** about 100 items at 120 s is 3.3 hours, about 18 units, about 23 with +30%
    (all figures here are per seed; at the 156 s ceiling a seed is about 4.3 hours, so each seed is its own window,
    and a cut window resumes from its call journal).
  - **Step 2, Muse, seed 1 (P3):** the same again, about 23 units, run only if step 1 shows P2 short of the bar.
  - **Lightning** repeats steps 1 and 2 only if Muse's results leave the decision open: about 46 units more.
  - The whole study at its largest is about 92 units, inside the 134.15 left of 300. Each step is projected again
    from the one before it.
- **Budget:** 165.85 of 300 units spent. A3 applies to every window.

**Tooling this needs** (a role-set change, reviewed and laddered before any window):
- a scoring mode that runs the verdict and flaw checks on every item of a sealed set (no trait votes), and records
  each check's code and raw reply (today's `rescore` draws only 2+2 per arm);
- an offline scorer that applies P0's and P2's comparison rules to recorded replies, against any key, for the
  key-only types and for P2;
- the perturbation script (types a–g), with its seed recorded and its output sealed;
- (the download heartbeat needs no change: probe window 13u measured a Xet download growing steadily inside the
  download directory, with no preallocation and nothing held in the Xet cache.)

## 7. Receipts

Every window carries the handbook's receipts (launch file, job log, pin-result, gate rows, outcome.json with date
and commit). Every critic call keeps its raw reply and its check code. Phase 1's blind keys and the adjudication
notes are filed in this folder, before phase 2's items are made. The perturbation script and its seed are
committed before any perturbed item is scored.

## 8. Before the first counted run

- Phase 0's table is computed and read.
- Phase 1 is done, and its result recorded under the decision rule.
- The perturbation script is reviewed, and its output spot-read (every type, five items each).
- One free CPU stub run passes with the scoring mode, the offline scorer and two seeds wired.
- The Xet download probe has run (window 13u: no heartbeat change needed).
- An outside review of this design has passed.

## 9. The confirmation test (frozen 2026-10-19, Argon PASS round 3b)

The Director decided this after phase 3. P2 beat P0 13 : 0 across the two critics, but missed §5's Holm bar
(0.0625). The pool held only 6–7 clean-trace items per critic, because the pilot had no more gold kind C rows. This
section is written and committed **before any of its rows exist**.

**The one comparison.** P2 against P0 on Muse, by exact McNemar on the paired outcomes (two-sided, α = 0.05). It is
the only test, so there's no multiplicity adjustment. P3 isn't tested: at phase 3 it never differed from P2. Lightning
isn't run.

**Fresh items** (revised after Argon's round 3, F1–F4):
- **New rows are needed.** The pilot has no unused C rows: each arm carries the same 2 C rows through every wave, and
  Phase 1 used them all.
- **The slots: 38 kind C slots.**
  - **All 27 unused (f)-eligible C slots.** These are odd-numbered slots, which plant a flaw, with a supported or
    unsupported key. role-set's `slot_flaw` plants "none" on every even C slot, and perturb.py makes (f) only from a
    planted flaw with a decided key.
    - The slots: T02-C-03, -05, -07; T03-C-01, -05, -07; T06-C-05, -07; T07-C-01, -03; T08-C-01, -07; T09-C-01, -03,
      -05, -07; T10-C-01, -03, -07; T11-C-03, -05, -07; T15-C-03, -05; T18-C-01, -03, -05.
    - Their planted flaws: guess 12, loop 7, nitpick 7, rubber_stamp 1.
    - The draft's list of 38 slots held only 12 eligible; the Publisher confirmed this with role-set's own
      `slot_flaw`.
  - **11 even-numbered decided C slots as natural controls**, planted "none". They are the first 11 in lesson order
    (T02, T03, T06, T07, T08, T09, T10, T11, T15, T18) and then id order, with T02-C-01 and -08 left out.
    - The slots: T02-C-06, T03-C-02, T03-C-04, T03-C-08, T06-C-02, T06-C-06, T06-C-08, T07-C-02, T07-C-04, T07-C-08,
      T08-C-04.
    - 5 are supported and 6 unsupported. The Publisher computed them at role-set `47a5882`.
  - Each lesson is planned on its own, because `plan --lessons` refuses three or more lessons in one batch. The
    plans are merged before the slots are filtered. That's the `PIN_PILOT_LESSONS` change, which gets a CPU stub
    rung before any paid window.
- **Gemma 4 31B writes; the writing step has no critic** (Argon F2, replacing the draft's Qwen3.8).
  - With PIN_PILOT_WAVES=1 the window runs the write wave only, so the drafts end `awaiting_critique`.
  - Two reasons:
    - a critic would select rows on Gemma–critic agreement, at 5 calls a draft;
    - R&D's census gold check is the validity filter anyway.
  - Muse first meets these rows in critic-eval, and Gemma's family differs from Muse's, so there are no family skips.
  - **The population differs from phases 1–3:** these are drafts that passed role-set's write-time gates and R&D's
    gold check, with no critic selection. Phases 1–3 used critic-accepted rows, mostly accepted by Muse. The
    results are read with that difference stated.
- **The gold set:** R&D keys every new draft blind, under phase 1's protocol: the verdict, the deciding lines and the
  planted flaw.
  - Wrong rows and unclear rows are excluded.
  - **Trace-leaks-label rows are excluded too** (Argon F4). That's a trace that names or paraphrases its own planted
    flaw, read against role-set's FLAWS (rubber_stamp, guess, loop, nitpick, fix, obeyed_material, caved,
    reject_by_default).
    - A mechanical pre-screen flags the flaw words and their stems (guess, rubber stamp, loop, nitpick, fix,
      obey, cave, reject).
    - The final call is R&D's reading for meaning. P1-035, which said "that assumption is not in the material",
      leaked by meaning, not by stem.
  - The gold set is fixed, and its file sealed, before perturb.py runs.
  - **The gold record (Argon 3b, note 2).** A write-only draft has `row: null`, and its candidate text doesn't carry
    the planted flaw. So each gold record carries a `key` block on the draft record, as perturb.py's input contract
    asks:
    - `verdict` and `deciding`, from R&D's blind keying (where it agrees with the draft);
    - `planted_flaw`, from role-set's `slot_flaw` for the slot.
- **The items:** perturb.py at role-set `47a5882`, seed 0, as in phase 2: d, b, e and f on the GPU, g offline.
  - perturb.py isn't changed between phase 2 and this test.
  - R&D hand-checks every b, e and g item before the critic window. **The exclusion list and `items.jsonl.sha256`
    are committed to this repo before Muse runs** (Argon F3). Excluded items stay in the sealed file and are dropped
    at analysis.

**The primary pool and the outcome.** b, e, f and g pooled, as in §4. The outcome per item is right or wrong against
the label: a perturbed item should be refused.

**Size and the stopping rule.**
- Target: about 18 or more (f) items, from the 27 eligible slots after write-time drops and gold-check exclusions,
  plus about 10 natural controls.
- If the gold set gives fewer than 12 (f) items, more f-eligible slots are written and gold-checked before the
  critic runs. That's blinded calibration, not peeking, because no critic call has been made.
- Argon's figures: 12 : 0 gives p = 0.0005, and power is over 98% at an 80% catch rate.
- The critic window runs once, on the final sealed items. Nothing is scored before that, and nothing is re-run on
  the result.

**Decision.**
- **Adopt P2** (the flaw gate on, plus P2's two comparison rules) if both hold:
  - p < 0.05 with the discordance favouring P2;
  - P2's control refusal is at most 10%.
- **Otherwise,** R&D brings the Director the options §5 names.
- Each P2 rule's contribution is reported descriptively. At phase 3, every difference came from the flaw gate.
- **Reported beside the test** (Argon Q2 and Q4):
  - Muse's "none" agreement on the even-slot controls: the natural-prose benchmark for the fixed (f) frame. Phase 3
    measured Muse at 9 of 10.
  - The Gemma-only control refusal rate, next to phase 3's 1 of 44.
  - Phase 3 is never pooled with this test.

**Cost** (the Publisher's projection from measured rates; A3 applies to each window):
- **Writing:** write-only, 38 slots, one A100 window.
  - It's projected from Gemma's measured write wave: 118 s a slot in 12f and 234 s a slot in 13l, plus lesson warmups
    and setup.
  - That's 7.78–14.27 units, with a cap of 18.55 and a wall of 12,600 s.
- **critic-eval:** about 3–4 units, cap 15.2.
- **Ledger:** 176.96 of 300.

## What carries into the T10 writer run

Fixed here for the T10 design that follows:
- the projection rule: each measured rate with its receipt, +15% where measured, +30% for a wave kind with fewer
  than four measured slots; savings and overruns shown apart. Twin slots at each writer's measured twin rate (about
  2× its T02 rate; Bolt 1.15×), 2.5× for a writer with none measured, and twin critique at 410 s per draft (W-A:
  2,850 s for 7);
- the slot list, built to pass aspire-si's full batch-mix rule (cannot_tell at least 25% and supported at least
  25% of verdict-bearing items; per lesson, at least a quarter of the supported and unsupported items with 2–4
  DECIDING lines; at least one ESCALATE yes; at least one cannot_tell with ESCALATE no; at least two multi-turn D
  items, one changed and one stood), with one buffer slot per quota so a dropped draft can't sink the batch, and
  checked with the gate on a mock batch first;
- the pins: role-set and rnd commits, each process's `huggingface_hub` version (1.33.0 in Colab's kernel, 0.36.2
  in the converter's environment), and new conversions in their own environment with torch, numpy, gguf and
  safetensors pinned exactly;
- if P3 wins, the T10 critic projection doubles;
- the download heartbeat as it stands, which probe 13u showed reads Xet downloads correctly;
- the critic protocol this study adopts.
