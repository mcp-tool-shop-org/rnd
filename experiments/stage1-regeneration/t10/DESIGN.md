# Stage 1: the T10 writer run (design draft v2)

**Status: v2, 2026-10-21. Argon's consult on v1 (at 9d7f675) was a CONDITIONAL PASS: F1–F4 blocking, F5–F6 before the
window. §11 rules on each one and overrides the sections it names. Nothing has been built or run.**
- **Order:** this design → Argon's consult → one builder brief for role-set (and aspire-si where the gates live) →
  Argon's code round on each builder PR → the free rungs (§7) → the paid windows.
- **Template:** the rnd [rented GPU windows](../../../site/src/content/docs/handbook/rented-gpu-windows.md) path, with
  the carry-overs fixed in [`critic-signal/DESIGN.md`](../critic-signal/DESIGN.md) ("What carries into the T10 writer
  run") and [`critic-signal/PLAN-ROUND4.md`](../critic-signal/PLAN-ROUND4.md) §2.
- **The Director's go (2026-10-21):** T10 first, on P0. Track A runs separately and doesn't gate T10.

## Standards compliance

| Standard | Score | Evidence |
|---|---|---|
| PIN_PER_STEP | 2 | §6 pins every step: the role-set and rnd commits, each writer and critic by revision and GGUF sha256, the llama.cpp commit, `huggingface_hub` per process. Rises to 3 when the window receipts carry them. |
| ANDON_AUTHORITY | 2 | §7's rungs each stop the run on failure. §8's stops end a window early. The gates refuse a batch that misses a floor. |
| NAMED_COMPENSATORS | n/a | No irreversible call here. The windows spend units, booked in the ledger. Nothing is published until the dataset release, which has its own design (DATASET-RELEASE.md). |
| DECOMPOSE_BY_SECRETS | 2 | The writer run (role-set), the gates (aspire-si-gates) and the gold check (R&D) stay separate. Each fix in §4 lives where its rule lives. |
| UNCERTAINTY_GATED_HUMANS | 2 | R&D's blind gold check covers exactly the rows the critic can't check (§5). The Director is asked only for spend beyond §8's projection. |
| EXTERNAL_VERIFIER | 2 | Argon (Gemini) reviews this design and every builder PR. |

## 0. Licences first

Every model and source is in `licences/registry.json` for the use made of it:
- **The writer, Gemma 4 31B:** `apache-2.0`, with `gemma-prohibited-use-policy` read on 2026-10-17. Whether the
  policy binds Gemma 4 is unclear, and either way it doesn't restrict this use (training data for the studio's own
  model).
- **The critic, Muse-Glimmer-30B:** `apache-2.0` and `muse-glimmer-30b-card`. The card's intended uses include
  synthetic training data.
- **The gold check:** R&D, a Claude session, keying blind (`anthropic-help-12326764`). Its labels are evaluation data
  only, never a training target.
- **The kind B puzzles:** built and proved by role-set's T10 generator, which is code. The cell table's provenance is
  recorded in PROVENANCE.md (Grok's #53 and #54 tables are replaced, and the generator logic stays).

## 1. The check in three sentences

1. **The question:** can role-set write one full lesson, T10 (strict size words: "exactly", "at least", "at most"),
   that passes the release gates **and** R&D's blind gold check, with the two blind spots PLAN-ROUND4 §2 names closed?
2. **What's new against the screen and phase 4:** slots with real difficulty, a gate that refuses a trace naming its
   own flaw, and a bounded, gold-checked share for the kinds the critic can't check.
3. **What it decides:** whether role-set's pipeline, as fixed here, is ready to write the remaining lessons the same
   way.

## 2. What the run makes

- **The base plan:** role-set's `plan_lesson`, 40 slots, 8 each of kinds A–E (`src/role_set/plan.py:16`).
  - Kind E is 6 written and 2 verdict.
  - Verdict-bearing: 8 C + 8 D + 2 verdict E = 18.
- **The apply slots:** 5 C and 5 D (`plan.py:249`). The T10 apply item carries its `r10_twin` field
  (`assemble.py:302–306`).
- **Buffers (§4a):**
  - one per batch-mix quota;
  - plus 2 extra kind C slots for the gold check, 1 odd (planted flaw) and 1 even (planted none) (PLAN-ROUND4 §2,
    Argon F7).
- **The kind B puzzles** come from the T10 generator (`role_set.generate`): code builds and proves each puzzle, and
  the writer only words it.
- **60 slots in all:** 40 + 10 + 10 buffers, enumerated in §11 F1. That replaces v1's "about 58".

## 3. Roles

- **The writer:** Gemma 4 31B alone.
  - **Why Gemma:** it wrote 38 of 38 slots with 0 dropped in phase 4's write window (14a, 190 s a slot), the fastest
    measured rate.
  - **Why one writer:** twin counts of 2 per writer can't rank writers (13l), and the screen's slots were too easy to
    separate them (PHASE-0-1). Writer choice for the remaining lessons is a later question.
- **The critic:** Muse-Glimmer-30B under **P0**, today's rules. Its flaw check stays advisory.
- **The gold check:** R&D, blind, after the window (§5).

## 4. The fixes (the builder items)

**(a) Real difficulty in the slot list.** The batch-mix rule already lives in aspire-si-gates (`check_floors`,
`check_batch`) and is mirrored in `plan.py` (`FLOOR_SHARE = 0.25`, `check_plan`). It requires:
- cannot_tell and supported, each at least 25% of verdict-bearing items;
- at least a quarter of supported and unsupported items with 2–4 DECIDING lines;
- at least one ESCALATE yes, and at least one cannot_tell with ESCALATE no;
- at least two multi-turn D items, one that changes and one that stands;
- the contrast pairs and real-source items it already counts.

The screen's slots met none of the difficulty (PHASE-0-1: no cannot_tell among 30 rows). The fix:
- **T10's slot list is generated to the rule and committed before any window,** with one buffer slot per quota.
- **cannot_tell items include ones with no deciding line.**
- **A mock batch built from the slot list passes `check_batch`** before anything is written (rung 0).

**(b) A gate for a trace that leaks its label (defect class `trace-leaks-label`).**
- **What it checks:** a kind C checker trace must not name or paraphrase its own planted flaw. The mechanical check
  flags the flaw words and their stems from role-set's FLAWS: guess, rubber stamp, loop, nitpick, fix, obey, cave,
  reject.
- **Where:** a write-time gate in role-set, so a refused draft is rewritten within the window, before critique.
- **Its test cases:** P1-017 ("That is a guess, not the source") and P1-035 ("That assumption is not in the
  material").
  - P1-017 must be refused.
  - P1-035 leaked by meaning, not by stem, so the gate may pass it. It's in the tests as a known pass that R&D's gold
    check must catch.
- **The stem list errs toward refusing.** A false refusal costs a rewrite. A false pass reaches the gold check.

**(c) The kinds the critic can't check: A and written E.** The critic's accuracy path covers C, D and verdict E only
(`runner.py:697`); A, B and written E take the other path (`:650`). B is covered by the gates' deterministic
`puzzle_check`. For A and written E, this design takes the **bounded share** option:
- **The bound:** their share stays at the plan's 14 of 40 (8 A + 6 written E, 35%), with no top-up beyond one buffer
  each.
- **Every one is gold-checked by R&D** (§5), and only rows passing it count.
- **An automated accuracy check for A and written E** is deferred (§9). Building one well is its own study.

**(d) Gold-check buffers.** The 2 extra kind C slots in §2. At phase 4's 16% exclusion rate (6 of 38), they keep the
C quota whole after the gold check, which runs after the window, when role-set can no longer rewrite a refused slot.

## 5. The gold check

R&D keys blind, under phase 1's protocol, every accepted row of kinds A, C, D and E: the verdict, the deciding lines
and, for C, the planted flaw.
- **Excluded:** wrong rows, unclear rows, and `trace-leaks-label` rows read for meaning.
- **A row counts only if it passes the gates, P0 and the gold check.**
- **The cost is R&D's time, not units.**
- **The record:** a sealed gold file, then the exclusions committed, before anything is frozen.
- **Track B's trigger is read here** (PLAN-ROUND4 §4): label-boundary rows above 10% of C rows.

## 6. Pins

- role-set at the merge commit of §4's builder PRs, and rnd at this design's commit.
- **Gemma 4 31B** (rev 842da379, GGUF sha256 e357a450…) and **Muse-Glimmer-30B** (rev a4e59da5, sha256 c321320a…),
  from `writers.json`, which `pin_window.py`'s `MODELS` must equal.
- **llama.cpp** at commit 620d2225… (`writers.json` `llama_server`).
- **`huggingface_hub`** per process: 1.33.0 in Colab's kernel. No new conversion is planned.
- **The pre-step** (window 14f, role-set #98): tokenizer and fit checks on the served model before any call, with any
  allowed tokenizer mismatch recorded.
- **The computed HF floor** (role-set #99).

## 7. Free rungs before any paid window

0. **The slot list,** generated to the batch-mix rule with its buffers and committed. A mock batch passes
   `check_batch`. Counts per kind and per quota are recorded.
1. **The leak gate's tests:** P1-017 refused, a clean trace passed, each stem in the list refused once. P1-035 is
   recorded as a pass for the gold check.
2. **A CPU stub rung** of the full T10 path, write and critique, on a small model through the same scripts. It
   covers a deadline cut, a resume and a zero-call replay, with the leak gate firing on a planted leak.
3. **A non-mock probe** of a few slots through the real gate before the window's slot sha is recorded.

## 8. Windows, cost and stops

**Two A100 windows, write then critique,** the shape phase 4 used (14a, then 14b).

| Window | Basis | Projection |
|---|---|---|
| Write, about 58 slots | Gemma write-only, 190 s a slot (14a, 38 slots). +15% on C, D and verdict E (measured), +30% on A, B words and written E (fewer than 4 measured on this path) | about 3.7 h, **about 19.8 units** |
| Critique, P0 on every written slot | Muse, 296 s a draft (12f), +15% on verdict-bearing slots, +30% on the rest | about 5.8 h, **about 30.8 units** |
| Setup | prefetch (684 s in 13l), gate and pre-step, per window | about **1.6 units** |
| **Total** | | **about 52 units; high, with +15% overall, about 60** |

- **The budget (the Director, 2026-10-21):** the study ledger is reset to a new budget of **150 units**, starting at 0
  for this phase. The earlier 196.93 stays as the record of phases 0–4. T10 at its high (60) plus Track A at its high
  (36) is about 96 of 150.
- **Critique-window scope is a question for Argon on its merits** (§10, question 4): critiquing only the
  verdict-bearing slots would cut about 14.7 units, but the answer should rest on what the trait vote is worth.

**Hard caps and the cut order** (added after v1 went to Argon, at the Publisher's request):
- **Caps:** the write window is capped at 23 units, the critique window at 36 units (verdict-bearing and apply slots
  only: 19). Each cap is set in the window's launch file, and the deadline cut enforces it.
- **The budget rule:** a window that would take the ledger past the budget doesn't launch until the Director has been told
  the figure and says yes. He has said he'll raise the budget when it's needed, so the budget line isn't a reason to
  shrink the study: the design is sized for what T10 needs, and the cut order below is only the fallback.
- **The cut order, if the ledger comes within about 10 units of the budget:**
  1. the critique window drops to verdict-bearing and apply slots only (saves about 14.7);
  2. then the critique window's buffer slots are critiqued only if the gold check needs them;
  3. the write window is never cut, because T10's quotas depend on it.
- **The margin:** about 54 of the 150 units remain at both highs.

**Stops:**
- any rung failure;
- the gates refusing the batch;
- a window projected over its cap mid-run (the deadline cut);
- the ledger projection over the budget.

## 9. Deferred, with triggers

| Deferred | Trigger |
|---|---|
| An automated accuracy check for A and written E | The gold check excludes more than 2 of the 14 A and written E rows |
| A second T10 writer | The gold check excludes more than 16% of Gemma's C and D rows |
| Track B label rewrite | The gold check finds label-boundary rows above 10% of C rows |
| Pc as T10's critic protocol | Track A passes its pre-registered decision |

## 10. Questions for Argon

1. **The leak gate (4b).** Is a stem screen at write time the right place, or should it sit in aspire-si-gates so
   every lesson's freeze runs it? And is erring toward refusal right, given that a false refusal costs a rewrite in
   the window?
2. **The bounded share (4c).** Is 14 of 40, with every row gold-checked, an acceptable bound until an accuracy check
   exists? Or should A and written E be cut below the plan's counts for T10?
3. **One writer.** Is Gemma alone sound for a lesson that will train, given the fingerprint controls in BUILD-SPEC
   §6? Or does T10 need a second writer for variety, at its cost?
4. **Critique scope (§8).** P0 critiques every slot, but its trait vote on A, B and written E adds about 14.7 units and
   checks no accuracy. Keep it for comparability with the screen, or critique only the verdict-bearing slots and the
   apply slots?
5. **The projection.** Are the +15% and +30% margins, and the two-window shape, right for a run this size?

Severity levels for the consult: `blocking` (must change before the builder brief), `before the window`, and
`not blocking`.

## 11. Changes after Argon's consult (v2)

Argon's consult on v1 (rnd 9d7f675) was a CONDITIONAL PASS. R&D checked each finding against role-set main 89b5f2e
before ruling. This section overrides §2, §4, §5 and §8 where it says so.

**The budget, since v1:**
- **The Director reset the study budget to 150 units for this phase** (T10 and Track A), starting at 0. Phases 0–4
  are closed at 196.93 in the ledger.
- A window that would cross 150 waits until he's told the figure and says yes. He has said he'll raise it when
  needed, so the budget isn't a reason to shrink the study.
- Argon's F6 arithmetic against 300 is superseded by this. The rest of F6 stands.

### F1 (blocking): the exact buffers, and the trim after the gold check. Adopted.

**The 10 buffer slots, replacing §2's "about 6 + 2":**

| Buffer | Slots | Properties |
|---|---|---|
| Kind B | 0 | Only 8 puzzle structures, and none may repeat within a lesson (`plan.py`) |
| A | 1 | |
| Written E | 1 | |
| Contrast pair `t10-pair-3` | 2 | One cannot_tell with ESCALATE no, one unsupported with `multi_line` true and `real_source` false |
| Gold-check C | 2 | 1 odd (planted flaw) and 1 even (planted none); at least one supported, `multi_line` and `real_source` |
| D | 2 | Covering `two_turn` "stands" and "changes", one with ESCALATE yes |
| Apply | 2 | 1 C and 1 D, one with ESCALATE yes and `multi_line` |

**The selection and trim step.** It's new, deterministic and in role-set. After the gold check:
1. surviving buffers replace excluded base slots, in plan order, by matching quota;
2. a contrast-pair partner left alone loses its `pair` field or is dropped;
3. the frozen batch is trimmed back to the canonical 40 training rows (8 per kind) plus 10 apply rows;
4. then `check_batch` runs.

The trim keeps A plus written E at 14 of 40.

**Rung 0 adds:**
- `check_batch` on the trimmed 40 + 10 mock batch;
- `check_batch` on each single-exclusion substitution.

### F2 (blocking): critique in a window with no writer. Adopted in part. One premise corrected.

- **The correction.** Argon's premise was that P0's trait vote refuses about 38.5% of drafts. It doesn't: role-set's
  trait check is advisory by default (`runner.py:487`, `trait_gate=False`, logged through `_gated_or_advisory`).
- **What stands.** A verdict refusal in a critique-only window can't be rewritten.
  - **The measured rate is low:** P0 refused 0 of 32 good rows in phase 4 (`critic-signal/data/confirm-outcomes.csv`,
    P0 on kind d).
- **The ruling:**
  - **Critique covers the verdict-bearing training slots and the apply slots only** (this also answers question 4).
  - The trait vote stays advisory.
  - **No rewrite tail in window 2.** A verdict-refused slot is replaced by its quota's buffer, under F1's step.
  - If the buffers run out, a top-up write window follows, with its own cap.

### F3 (blocking): planner and runner defects. Adopted for 1 and 2. Item 3 corrected.

1. **`two_turn` collides with contrast pairs.** `plan.py`'s D selection for `two_turn` must skip paired slots:
   `[s for s in slots if s.kind == "D" and s.pair is None]`.
2. **`real_source` collides with pairs.** Select real-source slots with `s.pair is None and not s.two_turn`.
   - **In `runner.py`:** a `real_source` slot with no excerpt raises `AssemblyError` instead of drafting invented
     material.
   - Excerpts are indexed by slot id, not popped across retries.
3. **The kind B and fingerprint fields are not left empty.** Argon read only `plan_lesson`. The `role-set plan`
   command fills them after it:
   - `domains.assign` sets `domain` and `frame`;
   - `solvefirst.assign` and `lock_skeletons` set `pack`, `b_seed`, `b_path` and `b_skeleton` (`cli.py:98–111`).

   **Rung 0 checks the committed slot list carries them all.**

**The excerpt pool** is made by `role-set harvest` from pinned, licence-checked repos. The pool file and its
licence entries are pinned in the window receipts (§6 pins), and rung 0 records the pool's sha.

### F4 (blocking): the leak gate. Adopted.

- **Where it lives:** `check_trace_leaks_label` goes in aspire-si-gates and is wired into `check_batch`. role-set calls
  it at write time through its gates, so a leaking C draft is rewritten in the window.
- **The pattern:** anchored word stems, case-insensitive, covering all 8 FLAWS, with space and hyphen forms:
  `\b(?:guess(?:ed|es|ing)?|rubber[- ]?stamp(?:ed|s|ing)?|loop(?:ed|s|ing)?|nit[- ]?pick(?:ed|s|ing|y)?|fix(?:ed|es|ing)?|obey(?:ed|s|ing)?|cav(?:e|ed|es|ing)|reject(?:ed|s|ing|ion)?[- ]?(?:by[- ]?default)?)\b`.
  "caveat", "prefix", "fixture" and "loophole" don't match.
- **The carve-out:** a stem that also appears in the slot's material or statement is ignored, so a trace quoting a
  changelog's "Fix retry loop" isn't refused.
- **Tests:**
  - P1-017 is refused;
  - P1-035 passes (left to the gold check);
  - a changelog material "Fixed loop when rejecting requests", quoted by its trace, passes;
  - a trace with "caveat" and "prefix" passes;
  - each stem is refused once.

### A free rung added at the Publisher's review: the leak gate on real traces

**Rung 1b, R&D's, after the aspire-si-gates merge:**
- run `check_trace_leaks_label` over phase 4's stored kind C traces, which are private and on R&D's side;
- report the refusal rate on the planted-none (even) rows, where a refusal is false by construction;
- **the bar:** at most 1 of the 10 planted-none rows. If the rate is higher, the pattern or the carve-out is tuned and
  re-reviewed before any write window, so rewrites don't eat paid time.

### F5 (before the window): the gold-check rubric. Adopted.

- **For A and written E,** R&D checks blind:
  - (a) the accuracy of every strict-size-word claim ("exactly", "at least", "at most");
  - (b) fidelity to the slot's assigned T10 side;
  - (c) for written E, that the question is unambiguous and the keyed answer matches it.
- **For every apply row,** R&D also keys `r10_twin`'s verdict, and checks that the twin tests the literal size-word
  reading on the same material.
- **The critic doesn't check the twin today:** `runner.py` has no reference to `r10_twin`. So:
  - **role-set's critique pass gains a verdict check on the twin statement** (a builder item);
  - **the gold check covers the twin** either way.

### F6 (before the window): the projection. Adopted, against the new budget.

- **Pricing:**
  - the 12 apply slots (10 plus 2 buffers) are priced at Gemma's twin rate, 380 s, for writing, and 410 s a draft
    for critique;
  - setup is counted for both windows;
  - central is the measured rate; high adds +15% (measured) and +30% (under 4 measured slots), with no second
    overall multiplier.
- **Critique** is limited per F2.

| Window | Central | High | Cap |
|---|---|---|---|
| Write, 60 slots | 20.1 | 23.8 | **26** |
| Critique, 36 verdict-bearing and apply slots, plus 12 twin verdict calls | 17.9 | 20.8 | **23** |
| Setup, 1.6 a window | 3.2 | 3.2 | (in each cap: 23.8 + 1.6 = 25.4 → 26; 20.8 + 1.6 = 22.4 → 23) |
| **T10 total** | **41.2** | **47.8** | |

- **R&D recounted Argon's slot split.** The verdict-bearing and apply slots number 36, not 34:
  - 18 base, 10 apply;
  - buffers: the pair 2, gold C 2, D 2, apply 2.

  The non-verdict slots number 24, not 26: A 9, written E 7, B 8. The figures above use R&D's count, with the 12
  apply slots at the twin rates.
- **The twin calls:** 12 verdict calls at Muse's critic-eval rate, about 19 s a call (13w: 1,695 s for 89 calls), +30%
  because they're unmeasured on this path. That's about 0.4 units. With each window's setup inside its cap (Argon round 2, F4), the caps are 26 and 23.
- **Together with Track A** (31.5 central, 36 high), that's about 73 to 84 of the 150. §8's caps and cut order are
  replaced by this table and F2's ruling.
- **If buffers run out,** the top-up write window is priced and told to the Publisher before it launches.

### Argon's consult round 2 (on v2 at c575551): CONDITIONAL PASS. All four findings adopted.

- **F1:** the builder brief now skips A, B and written E in the critique pass, behind a run option. The twin check
  compares the verdict only, with the two-ask VOID retry.
- **F2:** buffer properties and the trim are respecified.
  - Base pairs are drawn from C only when buffers are on, preferring non-real-source kinds. `t10-pair-3` is C.
  - The gold C buffers and the apply C buffer carry ESCALATE yes where a base or apply C slot does. The stands-D buffer
    carries `multi_line`.
  - A broken base pair is replaced whole.
  - Side and verdict are preferences, not filters.
  - The single-exclusion pass test covers the 40 buffered slots. The 10 unbuffered (8 B, 2 verdict E) must refuse.
  - **One departure from Argon's text:** the stands-D buffer doesn't carry `real_source`, because two-turn items never
    do (round 1, F3). The 4 real-source items stay on non-paired C slots instead.
- **F3:** the own-flaw stem is never excused outside a verbatim quote of the material or statement.
- **F4:** the caps include each window's setup: 26 (write) and 23 (critique, which also carries the twin calls).

## 12. Free rungs: results and one change (2026-10-21, role-set c2955e9)

- **Rung 0:**
  - `role-set plan --lessons T10 --buffers --seed 0` gives 60 slots and passes the slot-field check. Seed 0 is the
    planner's default, recorded here; this design didn't fix one.
  - The pool (`51afb3cd`) covers the 6 real-source slots.
  - The frozen training set is uploaded as `training-inputs.tar`, sha256
    `12f2bffa3b46301f0410aa494f19f58e8cb395d9496820c442d76a32fbe40d5d`: the 21 FROZEN.md training files and their 21
    `.models.jsonl` sidecars, 810 rows, each data file's LF sha equal to FROZEN.md's. The window's own
    `training_inputs` accepts it.
- **Rung 1:** the leak gate's unit tests (aspire-si #167) pass.
- **Rung 1b:** `check_trace_leaks_label` over phase 4's 38 real kind C traces.
  - Planted-none rows: 0 of 11 refused (bar: at most 1 of 10).
  - Planted-flaw rows: 1 of 27 refused. T18-C-05 plants loop and its trace says "guess"; that's a correct catch.
- **Rung 2's wording changes:** the CPU stub can't fire the leak gate on a planted leak, because the stub's MockWriter
  writes no flaw stems. The refuse-and-rewrite path is covered by role-set #101's runner unit test instead (a leaking
  kind C draft is refused `GATE` and rewritten). The Publisher agreed, with no knob PR. The stub rung covers the write
  stub, a critique resume with scope `verdict` cut at the deadline, a resume and a zero-call replay.
- **Rung 2 results (Colab CPU stubs at role-set c2955e9):**
  - **15h, the write stub:** 60 of 60 drafts awaiting critique, the 48 training slots ahead of the 12 apply slots, the
    pool and the 21 training files pinned.
  - **15i:** the critique wave with scope `verdict` was cut at the deadline, with 35 calls journaled and none on A, B
    or written E.
  - **15j:** the resume reused 35 calls and called 141; w1 completed and was sealed, with trait calls 108
    (36 × 3) and `twin_verdict` 12.
  - **15k:** the replay reused 176 and called 0, with w1's review, refusals and accepted files byte-identical to 15j's.

  Rung 2 passes. Rung 3, the non-mock probe, runs at the merge commit of the verbatim-repair PR (#104), which T10's
  write window will run.
- **Rung 3, the non-mock probe** (role-set `30c6c37`, #104's merge): `role-set write` on the T10 plan (seed 0, buffers, 60
  slots, LF sha `a7432da695eda2f08145b9da2a30ab5c80ea011ccea35176aac2a92e26b98649`), with:
  - the real gates (aspire-si-gates 1.7.6), `writers.json`, the Muse and Gemma card values, the synced pack and the
    committed pool;
  - the 21 frozen training files plus their sidecars, loaded through `gates.load_models`;
  - the window's partition, an A100 machine line, and the GGUF and llama-server pins.

  Pointed at a dead endpoint, it passed every pre-call check and stopped only on the connection, at its first writer
  call. Rung 3 passes.
- **Verbatim quotes:** the Argon consult chose a strict check plus an unambiguous repair (role-set #104, merged
  `30c6c37`). T10's write window runs at that commit.
- **The noise floor** (Argon's consult, 2026-10-22): T10 keeps single-sample verdicts at the Muse card as designed. Its
  readout states Track A's measured noise floor: 7/102 verdict flips and 8/219 P0 outcome flips between two sessions
  on identical prompts.

## 13. The write window, and the kind B gap (2026-10-22)

- **Window 15l, the write window** (A100, role-set `30c6c37`, cap 26). It booked 16.38 units, with an exec wall of
  10,949 s.
  - **58 of 60 drafts awaiting critique.** 2 were dropped, both kind B after 3 attempts: T10-B-05 and T10-B-07.
  - By kind: C 18, D 16, A 9, E 9, B 6. model_errors 0, and the andon didn't trip (drop share 0.034).
  - The plan sha matched the freeze (`a7432da6`). Pool `51afb3cd` and training tar `12f2bffa` were as pinned.
  - Refusals along the way: GATE 7, PUZZLE 7, ASSEMBLY 5, FRAME 5, TRUTH_QUOTE 3, SPENT 2.
  - **The verbatim repair fired on no slot.** Both slots the repair was built for survived: T10-C-01 at attempt 3,
    after a trace/verdict disagreement and the heading-line gate, and T10-C-11 at attempt 1.
- **The kind B gap.** Kind B has no buffers, so the trim refuses to exclude a B slot, and `check_plan` refuses at B 6 of
  8. R&D confirmed both offline.
  - **Stub 15m** (CPU, 0.01 units) proved the two-slot path: the plan was screened to exactly T10-B-05 and T10-B-07
    at `a7432da6`.
  - **Window 15n** (A100, 2.29 units) re-wrote the two slots at the same plan, code and pins, with a fresh budget of
    3 attempts each. **Both dropped again,** each time on a different puzzle-check rule.
- **The pattern:** T10's 8 B slots split by path.
  - The 5 `solve_first` slots (generated, locked models) all passed.
  - Of the 3 `freehand` slots (the writer writes the whole puzzle and model): stopping_problem (B-05) and
    falsifier_first (B-07) failed 6 of 6 attempts, and when_to_stop (B-08) passed at attempt 2.
  - The Director's standing direction is that kind B comes from a proving generator, not freehand writing. So another
    re-write, or help for the freehand path, isn't an option.
- **Next:** an Argon consult chooses among three options:
  - generators for the freehand structures;
  - moving the two slots to existing generators, which also needs a change to the one-structure-per-lesson rule;
  - a trim rule allowing fewer B rows.
  
  It also answers whether B-08 must be replaced, and whether a critique of the 58 drafts still holds if the plan sha
  changes. T10's critique window is built and held until then.
- **Units:** 15l, 15m and 15n booked 18.68 in all.
