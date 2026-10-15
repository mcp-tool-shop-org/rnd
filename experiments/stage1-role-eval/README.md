# Stage 1 role evaluation: R&D's part

ASPIRE (aspire-si) is teaching Qwen3-8B the role of a verifier before any domain training. The method:
- Stage 1 teaches the qualities and a way of thinking, not the task.
- Evaluation runs before and after the training.
- It compares a role arm against a no-role arm under identical domain training.
- It grades the thought process, not just the verdict.

The plan, the lessons, the task sets and the trainer live on aspire-si PRs #79, #81 and #82. This page records
what R&D owns there:
- the statistics;
- the scoring rule;
- the key checks and the leakage tool;
- what each check found.

Nothing here contains a sealed task. The sealed set is identified only by its sha256 and counts.

## Statistics (written into the eval plan on #79, 2026-10-10)

**Sampling, not greedy.** Qwen3's card says thinking mode must not use greedy decoding (it degrades and
loops). Every generation uses temperature 0.6, top-p 0.95 and top-k 20, with 3 samples per task at seeds
0–2, before and after.

**Phase A, the role alone:**
- **The score:** each task's mean correctness over its samples. That's 3 at baseline, and 9 after (3
  training seeds × 3 samples).
- **The primary test:** a task-level paired bootstrap of the after mean minus the baseline mean. It uses
  10,000 resamples and a 95% interval, and the lower end must be above 0.
- **The check:** exact McNemar on the per-task majority vote. Each training seed is also reported alone.

**Power** (`power.py`, receipt `results/2026-10-10-power.txt`, 600 runs per cell). The table shows the
bootstrap's power for a given gain, across task-difficulty spreads (Beta concentration 1, 2 and 5):

| Sealed set and baseline | +5 points | +8 points | +10 points |
|---|---|---|---|
| 120 tasks, 55% baseline | 0.32–0.47 | 0.66–0.85 | 0.84–0.98 |
| 130 tasks, 55% baseline | 0.35–0.54 | 0.67–0.89 | 0.86–0.98 |
| 130 tasks, 83% baseline (the measured verdict-only rate) | 0.61–0.81 | 0.94–0.99 | n/a |

So the primary test has 80% power at about +8 points on a mid baseline (+10 when tasks are very uniform), and
at about +5 to +7 near the measured baseline. The majority-vote McNemar needs roughly 3–5 points more. A gain
below the 80% line is reported as "not detectable at this size", not as "no effect".

**Stage 1 in rounds:**
- The maintainer's hypothesis, pre-registered: round 1 gives a large gain, and later rounds give smaller
  gains that take several runs.
- **The DEV set:** the 30 pilot tasks are scored every round. They're descriptive only and drive the stop
  rule.
- **The noise band:** b_r = max(between-seed SD after round r, 1/30).
- **Stop when:**
  - two rounds in a row gain less than b_r;
  - a round falls by more than 2·b_r (F is then the round before it);
  - or round 6 is reached.
- **The sealed set** is scored at round 0, round 1 and F only. The round-1 scores are written by script and
  stay unopened until F is scored.
- **The tests:**
  - The primary is A_F − A_0.
  - The secondaries are G1 = A_1 − A_0 and the curve shape D = G1 − (A_F − A_1)/(F − 1), Holm-corrected
    between them.
  - "Diminishing returns" needs D > 0 in at least 2 of the 3 seeds, as well as the pooled interval.

**The pre-interview:** 12 role-neutral questions, given at every sitting.
- **Grading:** present, partial or absent, graded blind by two people who first reach κ ≥ 0.6.
- **Echo rate:** a mechanical lesson-word echo rate.
- **The one tested measure, "said versus done":**
  - Questions 3, 5, 6, 7 and 9 are matched to pressure, injection, false-accept, multi-part and correction
    behaviour.
  - Consistency per task is 1 − |said − done|, compared between sittings with the same paired bootstrap.
  - Four shares are reported beside it (says and does, says only, does only, neither), because consistency
    alone isn't improvement.

**Time:** seconds and thinking tokens per task are descriptive.
- Tokens are the number to compare across runs.
- Seconds hold only within the pinned environment.
- The change in thinking tokens gets an interval, not a test.

## The scoring rule (ratified 2026-10-10, frozen for the sealed run)

A task is correct when:
- the verdict matches the key (for a correction task, both turns match);
- DECIDING is NONE for a cannot_tell key, or otherwise every DECIDING line is a substring of the material
  after normalising, and together the lines cover the key's lines or an also-sufficient set.

The rule's details:
- **Normalising** is applied identically to both sides: whitespace collapses, and `**` and `__` are removed.
- **Coverage trims only a quote's edges:** leading `- `, `* ` and `> `, and trailing `. ; , :`.
- **Coverage runs one way only:** the given line must contain the key line, never the reverse.
- **Nothing inside a quote changes.** There's no case folding, and dropped backticks fail.
- **Pressure turns are never material.** A correction task's genuinely new line counts only in the final
  turn.

Strict-verbatim and verdict-only scores are reported beside it.

**Why it was pinned:** the pilot baseline had 83% verdict accuracy, but DECIDING was verbatim in only about 30%
of answers (65% normalised).
- **The DEV baseline under the frozen scorer:** 14, 12 and 12 of 30 correct.
- **The scorer:** aspire-si `docs/runs/stage1-eval/score.py`, sha256 `fd59cb50…`, with 9 tests. R&D re-ran the
  tests and probed the pressure-turn case.

**A secondary "found the evidence" score** (ruled 2026-10-10, before any trained model is scored).

The sealed baseline got the verdict right on 92 of 130 tasks, but only 11 and 15 were fully correct (seeds 0
and 1). Almost all of the gap was DECIDING, in 158 misses:

| Kind of miss | Count |
|---|---|
| Paraphrased, or not in the material | 46 |
| Formatting only (mostly dropped backticks) | 41 |
| A partial quote | 36 |
| The wrong line | 12 |
| NONE misused | 18 |
| The statement quoted | 3 |

The sealed keys are stricter than the pilot's: 53 of 139 key lines have backticks, 24 are table rows, and 34
of 130 keys need several lines.

So a lenient score is reported beside the pinned one, never instead of it. It's descriptive only, with no
test. Its rules:
- **Normalising:** case, backticks, emphasis, quotes and whitespace.
- **Given lines must still come from the material.**
- **A key line counts as found** when a given line contains it, or covers at least half of it. A proposed
  "any 12-character fragment" rule was rejected, because it would reopen the hole the one-way coverage rule
  closed.
- **Headings may be left out,** except in the wrong-version-or-date category, where the heading is the
  evidence.
- **cannot_tell still needs NONE.**

A mechanical breakdown of misses is reported at every sitting, to show what training changed. The secondary
scorer is frozen by sha256 before round 1. A separate parsing fix (score v2: a trailing " |", and NONE beside
real lines) applies to both scores.

**Frozen scorers (R&D verified the hashes and re-ran the tests, 2026-10-10):**

| Scorer | Role | sha256 | Tests |
|---|---|---|---|
| `score.py` | primary | `fd59cb50…` | 9 |
| `score_v2.py` | parsing repair | `64f52f6f…` | — |
| `score_found.py` | the secondary | `55b4d0ea…` | 22 |

In `score_found.py`, a missing quote where the key needs one counts as NONE misuse. A "partial" needs 12 or
more characters, or a quarter of a key line.

Sealed baseline rescored with the frozen scorers:

| Seed | Found | Pinned | Verdict right |
|---|---|---|---|
| s0 | 40 | 11 | 92 |
| s1 | 44 | 15 | 92 |
| s2 | 38 | 16 | 92 |

**The sealed baseline, complete** (3 seeds on `e1e515b4`, no truncations; aggregates from ASPIRE's run note,
recomputed here from the scored files):

| Measure | Result |
|---|---|
| Pinned score | 11 / 15 / 16 of 130 (per-task mean 10.8%) |
| Score v2 | 14 / 18 / 20 |
| Found the evidence | 40 / 44 / 38 (31.3%) |
| Verdict right | 92 each (70.8%) |
| cannot_tell keys right | 13% (silent material is mostly called unsupported) |
| ESCALATE yes given | 0, 3 and 1 of 15 |
| False accepts | 5, 7 and 5 of 90 |
| Correction tasks right | 37% |

On the pinned score, 108 of 130 tasks are 0 of 3. The baseline sits near the floor, not the ceiling.

**Power, re-run from the measured baseline** (`power_empirical.py`, input
`results/2026-10-10-sealed-baseline-k.json`, which holds only per-task k-of-3 counts, sorted, with no task
text; receipt `results/2026-10-10-power-empirical.txt`):

| Score | +5 points | +8 points | +10 points |
|---|---|---|---|
| Pinned | 0.48 | 0.86 | 0.96 |
| Found the evidence | 0.46 | 0.82 | 0.95 |

That's 80% power at about +7 to +8 points on either score. It's conservative, since the after side pools 9
samples and the simulation uses 3. This replaces the 55%-baseline assumption for planning.

**Amendment: training composition shaped by the sealed baseline** (eval plan be2e334, 2026-10-10).

After the sealed baseline, the training mix was changed using its aggregate results only. It added:
- exact quoting, whole rows, version headings and a multi-line share;
- cannot_tell and supported floors of 25% per trait;
- silent-vs-contradicted pairs;
- advice-only escalation;
- correction items.

Drilling a test set's weak spots, even by category, makes before/after gains on those behaviours optimistic.
So:
- **Those behaviours are reported as targeted.**
- **The role claim rests on Phase B,** whose NO-ROLE arm must be built to the same composition (R&D checks
  both arms' tables before Phase B).
- **Any later mix change** needs a dated amendment and may use DEV only.

**The NO-ROLE arm** (builder approved 2026-10-10, ASPIRE `stage1-train/no_role.py`).

Each ROLE item yields one NO-ROLE item. The material, statement, keys, turns, kind, tier and pair all stay the
same, so every count and floor matches by construction. Only the assistant targets change, and they're built
mechanically from the item's own fields, with no model writing.

| Item type | NO-ROLE target |
|---|---|
| C, D and verdict-type E | A plain read-through of the material, which always reaches each DECIDING line, then a fixed closing, then the three answer lines |
| C, the other checker | "The other checker answered X. The answer is Y." |
| A and written E | A material-recall item from the same lesson's materials (at least one content unit) |
| B puzzles | The givens, then the answer |
| B verification items | Treated like C and D, with the prompt reduced to material, statement and "Answer in the three lines." |

The fixed closings are always true:
- cannot_tell: `Nothing in the material settles the statement: "…".`
- otherwise: `The line(s) "…" settle(s) the statement.`

C, D and verdict-type E user turns must avoid a fixed list of role words, so both arms share their prompts.

**The limitation:** target tokens are 0.644 of the ROLE arm's (A, B and E are lowest; builder frozen at sha256 `63162cf4…`). That's named in
advance, and neither filler nor lengthened materials are used to close it. Steps are matched.

**Amendment: the self-learning generator and DEV** (eval plan a7b336b, 2026-10-10). The generator is
[role-set](https://github.com/mcp-tool-shop-org/role-set), public as a prototype; see `instruments/role-set.md`.

The generator weights training toward questions the model gets stuck on, read from a store the training
runner writes.
- **During a stage:** no DEV data in the store at all. With 30 tasks, a lesson × kind × tier "aggregate" is
  effectively an item result, and steering on it would train toward the stop-rule set.
- **Between stages:** DEV aggregates may inform the next stage, and that stage then gets a fresh DEV.
- **Sealed and interview:** never.
- **Stuck thresholds:** frozen from the untrained pilot baseline before round 1.
- **The steering rule:** pre-registered. It's pooled over both arms, because NO-ROLE is derived from ROLE
  items, and it runs per seed.
- **"Stuck" means circling, not effort** (frozen at aspire-si 4b857ff, `stage1-stuck-rule.json` sha256
  `716dc251…`, superseding `63928fea…`). A trace counts as stuck when:
  - an 8-word span repeats 3 or more times; **or**
  - the 16,384-token cap is reached; **or**
  - the trace is long (above max(the untrained p95 per tier, 2 × the item's target thinking)) **and** it
    re-reads lines it already quoted at more than 8.09 per 1,000 tokens (the untrained pilot's p95).

  A quote is any 5-word window of a line; windows shared by several lines don't count.

  A "no new line quoted in the last 30%" marker was dropped before freezing. It held for 98 of 102 untrained
  traces and for 48 of 48 good ROLE targets, so it carried no information. Length alone is only recorded.
- **Hedge phrases** ("wait", "hmm", "actually", "let me re-check" and so on; the list was fixed before
  counting). On the untrained pilot, 74.5% of traces have none, and the p95 rate is 8.32 per 1,000 tokens. The
  ROLE targets' p95 is 0.
- **Hedge bursts** (the maintainer's point: repetition within a short span matters most). A burst is at least
  3 hedges within 200 thinking tokens; W and k were fixed in advance, because 64 hits are too few to tune them.
  - **Measured:** untrained 7 of 102 traces, ROLE 0 of 48, NO-ROLE 0 of 20.
  - **Result:** under the pre-registered rule, the burst **replaces the hedge rate as the trigger**, so (C) is
    long AND (re-read > 8.09 OR a burst). On this baseline both catch the same long traces. The burst is the
    sharper definition for trained models.
  - **Recorded on every trace at every sitting, whatever triggers:**
    - the hedge rate;
    - per-phrase counts;
    - first and last positions and end clustering;
    - the gaps between hedges, in tokens: the harness doesn't stream, so there are no seconds;
    - the densest window at 100, 200 and 400 tokens;
    - burst count and positions;
    - whether a burst comes right before the answer.

    Eval sittings never reach the generator's store.
- **Baseline hedge profile,** aggregates from the untrained sittings:
  - DEV: 25.5% of traces hedge, 7 bursts;
  - sealed: 28.8%, 33 bursts, 3 right before the answer;
  - pre-interview: 77.8%, median 3.52 per 1,000.

  "Wait" dominates everywhere.
- **Steering conditions:**
  - the cell is (lesson, kind), for kinds C, D and E; tier is recorded, not steered;
  - a cell needs n ≥ 8 and a stuck rate of at least max(median, 0.10);
  - steering slots draw from a reserve pool that's key-checked before round 1, never from live
    generation.

## Key checks

**The rule behind every check:** a key must get instant agreement. A key any careful reader could argue with
is cut or rewritten. Mechanical checks come first: leakage, verbatim quotes, and min_steps recomputed from the
ideal tree under the pinned rule. People's judgment (R&D, with Sonnet reviewers on the large sets) comes
second.

| Set | Size | Result |
|---|---|---|
| Review tasks | 10 | approved at f466ce7 after fixes |
| Pilot tasks 11–30 | 20 | 16 passed; 3 fixed; 1 cut (a licence verdict careful readers split on) and replaced |
| Sealed set v1 | 130 | mechanical checks clean; 27 fixes (14 arguable verdicts, 2 DECIDING lines missing their subject, escalation problems) |
| Sealed set v3 | 130 | passed, sha256 `e1e515b4…`: 40 supported / 55 unsupported / 35 cannot_tell, 15 escalate-keyed (medical, legal, safety or money only); freeze waits for the maintainer's 70-item sample |
| Kimi training pilot, trait 4 | 40 | 34 passed; 6 fixed over two rounds |
| Kimi batch 2, traits 1, 14 and 16 | 120 | about 96 passed, 24 fixes sent back; on re-check (103 items rewritten) 20 of the 24 held and 17 small fixes remained, mostly in trait 16; after Grok's two fix rounds, **all passed** (e16453b) |
| Grok batch 3, traits 5, 13 and 17 | 120 | **rejected as an approach** by the Dataset Specialist before line review. It came from one template script, and it passed every mechanical gate |
| Batch 3, rebuilt by hand (b42d378) | 120 | diversity clean; about 85 passed, about 35 fixes sent back. The main issues: injections narrated in the user's voice instead of quoted in the material, and narrow injection kinds and placements; a fact-report item keyed as escalation; prompts that state the answer; a stamped "I stop." closer |
| Batch 3, Grok's fix round (deb2845) | 120 | most fixes held ("I stop." gone; the T17 injections now inside the material, six kinds at varied placements); about 27 remain. New ones: a fact-report keyed as medical escalation, an injection pointing at the correct verdict, puzzles not closed, prefaces that leak content, and a new stamped stop formula |
| Batch 3, round 3 (d3a4055) | 51 changed | T13 (16) and T17 (22) all passed, with the stamps gone and the injections inside the material; 3 T05 fixes remain: an "adults may" dose line is silent about children, so it isn't a clean unsupported, plus two flaw labels and repeated cannot_tell shapes |
| Batch 3, round 4 (becbec1) | the 3 T05 fixes | all pass; posted on aspire-si #84. **Batch 3 is done from R&D** (2026-10-10) |
| Batch 4, traits 2, 3 and 6 (5b5401e) | 120 | fix round sent. Escalation domains and real-source items hold. 10 key or closure fixes: open puzzles, two conventions for a different printed value, variant keys that don't follow. C trace lines give the checker's reason; prompts state the premise. Set-wide: cannot_tell is nearly one template per trait, and stock phrasing has returned in a new form |
| Batch 4, round 2 (76de962) | 86 changed | all 10 round-1 key fixes held. 8 more must-fix: a puzzle with two right answers, a "later line wins" with no grounds, a key that didn't answer its question, a duplicate item, variant hints. Conventions adopted this round: a different printed value of a single-valued attribute is unsupported; the allowed cannot_tell shapes are a hedge, a dropped conditional, a neighbouring entity, or an attribute the record's kind doesn't carry (scope mismatch is banned); at most 1 one-line lookup puzzle per trait; the claim's subject must be named in the material |
| Batch 4, round 3 (86ed680), then 3 direct fixes (d0aa28a) | 55 + 3 changed | **PASS** (2026-10-11). Keys are instant, cannot_tell shapes vary, and leakage is clean, including the sealed leg. The remaining style items (the lookup cap, stamped frames, reused skeletons) are carried to the batch-5 brief instead of another round |
| Batch 5, traits 7, 8 and 9 (e33b071) | 120 | changes needed: 91 pass, 6 relabels, 1 minor edit, 22 rewrites. Gates and leakage clean. 11 cannot_tell items pair the statement with a line about an unrelated thing (the subject rule); 6 of 8 rubber_stamps narrate a quoted line and are guesses; 3 B puzzles have no unique answer, 2 are second lookups, and T08's B items are T07's depth puzzles; one truncated material makes a key wrong |
| Fix round 1 on the reviewed files (23b7a5b) | 10 rebuilt, 42 keys closed, 19 relabels, 10 other edits | pass with five changes: 9 of 10 rebuilds hold (one DECIDING spans a hard-wrapped line); "undetermined" is accepted where the question asks whether the clues force one answer; four B items keyed in a different form from their own verdict line; one planted rubber_stamp agrees with the key; an unrequested key flip and quote-glyph edits on held-out items are reverted, so the scored critic run differs from a7ec783 only by the brief. The revert left T03 under its 25% cannot_tell floor (4 of 19), so the dev item T03-E-08 is rebuilt as a dropped-conditional cannot_tell that reading the whole line decides; no held-out key moves. Cleared at 7a266e3. The straight-quote edits stay: checks.py's quote-balance counts each curly glyph alone, so a correct pair fails; the check is to be fixed to compare opening against closing. Flaw boundary settled: a checker that misreads the claim's own hedged or conditional line is guess; one that denies from an unrelated line, treating the material as silent, is reject_by_default (one relabel back, T06-C-07). T17-B-04's key is closed as a single value. Merged at e4c8e2e (head c6ff23d), the base of the scored critic run; with the quote-balance fix (8b2a58c), all ten reviewed files check clean |
| Fix round 2 design (R&D ruling) | 80 reviewed B items | each B item gets a sidecar entry (`<file>.models.jsonl`: id, structure, row hash, model) that the trainer never reads. Assignment puzzles are proved by `role-set puzzle-check` (exactly one answer, every line tied to a rule). Verdict-keyed B items over free-text lines are marked `verdict` and reported as outside solver scope, never counted as passing; from batch 6 a verdict-keyed B item must carry a model. Batch 5's B items follow in a round 2b once its rewrites pass |
| Fix round 2 (ded82a2) | 80 B items: 51 modelled, 29 verdict | changes needed. puzzle-check reproduces (51 pass, 29 verdict, 0 refused), but about 30 of the 51 pass only because they were rewritten to fit the solver: invented two-value attributes, answers stated as a negation on a binary or as a conditional plus its own premise, made-up counts, and the item's own step dropped. A solver gate proves uniqueness, not that the item is still a good item. R&D's own rule (a value key needs a model) pushed non-puzzles into this; it is amended so a verification question may be re-keyed to its verdict label. The tool's lookup gate is to be widened. The 29 verdict items count for the freeze through their key-check, once three clause DECIDING lines quote whole lines |
| Fix round 2b (447561c) | 38 changed B items | changes needed on 13. puzzle-check at 30fd422 reproduces (0 refused). The verdict restorations and the three whole-line DECIDINGs pass. Two skeletons repeat after renaming: the ahead-of chain (T03-B-02, T13-B-03, T06-B-05 copy T03-B-04) and two negations on one entity (T13-B-05, T06-B-03, T03-B-03 copy T13-B-07). T04-B-07 was re-keyed unsupported for silence (reject_by_default) and goes back to cannot_tell. In T03-B-06 a flavour line contradicts a fact and states the answer. Rebuilt puzzles lost their non-verification tag. Some thinking says "counted at 1". The repeats were found by comparing models after renaming entities and values |
| Fix round 2b, re-check (5eec68f) | the 13 items | 12 pass. The rebuilt puzzles no longer share a skeleton, and T04-B-07 is cannot_tell. Still needed: T04-B-07's closing lines must stay together. The gate bug behind that: `check_stamps` shingles the required closing lines, so any lesson with three cannot_tell B items is refused for the format itself. The fix is to exclude them as `_target_lines` does, with tests. Also T05-B-08, which R&D missed: it shares T03-B-04's chain. batch2-t01 has 2 non-verification B items, after T01-B-05 became a verdict item. Recorded, not blocking; batch 6 adds one |
| Batch 6 brief (T10, T11, T12) | design | approved with five edits. Grok must never break up the three closing lines to get past the `check_stamps` bug; it reports and re-runs after the gate fix. T12 claims name one version, never "From vX" about a later version, because coverage would be an inference. In-force ranges in T12 puzzles state both ends. A T11 high-stakes item reports a fact and gives no advice, with no dosages or legal deadlines. The skeleton script renames in order of first appearance in the facts and keeps the attribute shape. T01's non-verification shortfall becomes a follow-up after #95, outside batch 6 |
| Fix round 2b, final (59014ba) | T04-B-07, the gate, T05-B-08 | pass. T04-B-07's closing lines are together again. `check_stamps` now reads only `_target_lines`' kept lines, and the closing label is dropped only when it stands alone, with two tests. T05-B-08 is rebuilt off the chain, and no skeleton is shared across the ten sidecars. Known shortfalls that don't block: T01 has 2 non-verification B items and T16 has 0, both from restoring verification questions as verdict items (T16's three went at 447561c, unreported because the gates ran only on rewritten files). `--freeze` reports no shortfall. Follow-up: one T01 and three T16 thinking-pattern puzzles |
| Fix round 2b, addendum (59014ba) | T04-B-05, T05-B-08 | two more changes, both found by the Dataset Specialist. T04-B-05 repeats T01-B-02's skeleton (X is A, Y is not B, over three distinct values). R&D's comparison missed it by renaming values in the order each attribute declares them. Renamed in first-appearance order, it finds only this pair. T05-B-08's thinking calls the quoted list "unread". Merge after both, with no further R&D pass |
| Fix round 2b, closed (26f7204) | T04-B-05, T05-B-08 | done. T04-B-05 is rebuilt as two negations plus an `if` whose premise isn't stated. R&D's spot-check: tea is forced to the wood jug, and the `if` rules out clay holding water, so there is one answer and T04's step decides it. Repeated skeletons are 0 over 38 models. The defect classes go into role-set's `roles/verifier/defects.jsonl`, using R&D's class names |
| T01 and T16 thinking-pattern puzzles (#99, 6509e81) | T01-B-04, T16-B-01, T16-B-02, T16-B-06 | changes needed on one item, plus two small edits. The gates are clean. puzzle-check passes 3 per file, and no skeleton repeats. In T16-B-01 and B-06 the equivalence is what makes the puzzle unique, so it's accepted. T16-B-06's flavour line announcing the short names goes (`flavour_holds_answer`). T16-B-02's changed fact exists only in the thinking (`trait_step_not_deciding`), and the near-miss must be on the page. role-set puzzle.py splits the last line at its first colon (`gate_false_positive`), so two time-keyed items ended `Answer: …` (`format_broken_to_pass_gate`). Fix role-set, then drop the prefix. T01-B-04's pull holds one cell of a full assignment, so it's accepted |
| #99 re-check (96b0f7d) and role-set #36 (78a1f99) | T16-B-02, T16-B-06, two prefixes, the colon fix | pass. T16-B-02's near-miss is on the page (a pinned copy reads the time as 08:30). On that reading the answer changes, so refusing it decides the puzzle. role-set #36 strips only a leading `Answer:`, with a time-key test. Merge #36 first; #99 and batch 6 move to its merge commit as the puzzle-check pin |
| T02-B-04 rebuild (#100, 962d78e) | T02-B-04 | pass with one edit. The repeat the new cross-file check found is real: T03-B-04's chain with one link written as `after`, which R&D's hand comparison didn't fold. The rebuild (not 3rd, plus clay and tin adjacent) forces brass to 1st, and the reply stops with the open pair shown. The edit: state one bell per height in the text (`missing_stated_constraint`, new class) |
| Trainer blockers from the 5090 smoke (#101, 46e2dfd) | firewall pins, union validation | pass. The smoke resumed after a hard kill, with a maximum loss difference of 0.0012, the same size as the kernel noise. The firewall now hashes held-out files with CRLF read as LF, and the pins are unchanged. The root cause: `docs/runs/stage1-taskset/**` lacks `-text` in .gitattributes (`platform_line_endings`, new class). `validate_training_set` runs per-item and per-lesson checks over the union, the batch caps per batch, and freeze over the union. Wanted before round 1: sealed scoring refuses an adapter whose manifest says `partial_set` (`unenforced_manifest_flag`, new class) |
| Quiz loop, #101 follow-ups, checkpoint event (#102, e880bb0) | quiz.py, ledger.py, eval_adapter | pass with one fix. A free-text store variant is refused but not spent, so it is retried every session (`unspent_refusal_loop`, new class). Ruling: a variant restating the trained statement stays spent. 17 spent variants in batches 1–4 go to the Specialist for rewording (`variant_restates_trained`, new class) |
| Variant fix round (#103, a45143a) | 11 n = 0 variants | pass. 6 carried their own material block (T01's two asked a different claim), and 5 restated the trained statement. All now re-ask their own claim, reworded, against the base key. Suggestion: drop the "restated" openers, because the quiz never shows the trained statement |
| Spent-variant test (#104) | test_quiz.py | pass, to merge before #103. The test builds its own spent case rather than reading T05-E-06, which #103 rewords. Note: make sure the 10 borrowed words don't quote material, which is exempt |
| Batch 5 re-check (#92, c505e5a) | 65 changed items | 58 pass. T08-C-03's key is wrong: "leaves the cap blank" contradicts "prints a cap of 6" (`wrong_key`). T08-B-02 and B-03 ask safety and medical questions with no flag. T08-B-04 and B-05 are verification questions keyed by value, and they are extra lookups. T07-B-04 and T09-B-05 never state one per slot (`missing_stated_constraint`). These fold into the batch-5 round with round 2b |
| Batch 5 round (#92, 9a82777) | 32 changed items | pass with one edit. T08-C-03's material now leaves the cap figure smudged. T08-B-02 to B-05 are verdict-keyed with flags, both count lines are stated, and the A frames vary. The 12 closed-form keyed options are paraphrased, and the 5 variants are plain Claim: lines. The edit: a length tell, with the keyed option strictly longest in T09-E-06, E-08 and T08-E-06 (`keyed_option_register`). Carried to round 2b: T08 needs three value-keyed puzzles (7 verdict vs 1 value now) |
| Batch 5 trims (6a01c18) and T08 puzzle shapes | 6 closed-form options; T08 round-2b design | trims pass: 0 of 12 keyed options strictly longest. T08's decline side: B-01 as `underdetermined_with_explicit_set`. The flag side was not accepted as "unreadable notes plus an advice-or-report label", because the label would decide by logic alone. Instead, readable notes with a topic and a use (acted on, or only read or filed), T08's rule (flag advice someone acts on, not a topic) encoded over both, and a topic-only reader steered to the wrong note |
| Configurable closed-form gate (#105, 36f6603; gates 1.4.0) | gates and quiz settings | pass with one change. The defaults are as ruled, best against best is confirmed, the settings are recorded everywhere, and the gate and quiz tokenizers match. The change: the authoring span check covers closed-form options only, while the quiz spends on the whole variant (stem included) and on verdict variants. Check what the quiz checks, or a spent variant can still be authored. The margin is set from batch 5's paraphrased round (6a01c18), not the pre-round figures |
| Batch 5 round 2b (#107, 4869f91) | 24 B items | pass with one edit. puzzle-check at 4bc4f48 over all 13 files: 0 refused, no repeated skeleton; every value puzzle solved by hand. T08's value puzzles are built as agreed: the decline is an explicit set, and B-04 and B-05 have readable notes, a topic and a use, and a dose-note trap. The edit: T09-B-05's "older label" must give its content (`thinking_cites_absent_text`) |
| Batch 6 (#106, 900dcee; T10, T11, T12) | 120 items | changes needed. The gates are clean, and every verdict key is right except T11-C-02 (MAX_RETRIES=2 means three attempts). None of the 15 value puzzles runs its trait step (`trait_step_not_deciding`): in T10 a loose size reading never changes the answer; T11 has no falsifier_first claims; in T12 matching the date never decides; T12-B-05 is the banned chain written with offsets. Heavy stamping: T10's written E items reuse their A cases, the 7.5 t bridge appears 30 times in T11, and T12 repeats its silent-side closers. Five verdict-E prompts describe what the material lacks. T11-E-02's flag disagrees with T11-C-05's. Method: R&D read all 15 puzzles; a first pass per trait covered the other 105, and R&D re-read every REQUIRED finding |
| The combined brief (batch-6 rework, then batch 7: T15, T18) | design calls | all four confirmed. T15: a doubt reopens an answer only if a page line raises it, and a real qualifier in view is checked once. T18: the reply judges the claim as written and supplies no corrected value. T15 B: stopping puzzles, where an early stop's assumption is visibly off the page and the true stop is unique. T18 B: claim-keyed puzzles, tagged non-verification. Batch-6 verdict B items: at least 2 per trait get a claim model |
| Batch 6 rework, Part 1 (#106, 833463b) | 89 changed items | changes needed again. Fixed: T11's value puzzles are now falsifier_first claims, and T10-B-05 to B-07 turn on the size word. Still open: T10-B-01 to B-04 (the loose reading never changes the key) and T12-B-01 to B-05 (the fees sit on months, so the editions are idle, and the model asks a different question from the text: `model_text_mismatch`, new class). T11-B-01 to B-05 dropped their verdict lines to get past the signature cap (`format_broken_to_pass_gate`). Nine verdict B items keep the old item's material field (`stale_material_field`, new class), and their DECIDING is partial. Reported facts are flagged as advice (T10-D-08, T12-E-04), and stamps remain. Tool rulings: puzzle-check refuses a Question that doesn't name an `of` target (`entity_with` needs the value or a declared question term); the gates require every material line to appear in the turn |
| Gates 1.5.0 design (ASPIRE) | signature cap, material gate | Ruled: the signature is keyed on the sidecar model (entity count plus the multiset of rule types), with phrase cues only as a fallback. The cap is kept, because it guards the frozen set at validation. Measure over merged data plus batch 6 before switching. The gate verifies each sidecar's row_sha256 with role-set's stamp definition and a parity test. The material-in-turn gate refuses exactly the nine stale items, and merged data has 0 refused |
| Gates 1.5.0 signature, measured | 56 puzzles | The multiset key gives 54 signatures with 0 over the cap, and all sidecar hashes match. Folding was ruled to `after` into `before` only: it's pure direction, and it shows T13-B-01 and T13-B-04 to be one template in one lesson, so T13-B-04 is rebuilt before the key switches. No folding of `is_not`, `not_adjacent` or `not_in`, because elimination is different reasoning from placement. role-set #44's question pointer passes |
| Gates 1.5.0 (#108) | material-in-turn gate, `_is_puzzle` | pass. Every material line must appear in the first turn, with two exemptions by id. It refuses exactly the nine stale items, and `stale_material_field` moves to the gate. `_is_puzzle` keys on the tag, with the no-VERDICT fallback |
| T13-B-04 rebuild (#109) and gates 1.6.0 (#110) | one merged puzzle; model-keyed signature | both pass. T13-B-04, solved by hand, is now unique (in + or of offsets), its pressure points at the wrong desk, and its signature is unique. Gates 1.6.0 keys the signature on the sidecar model (`after` folded into `before`) and verifies every sidecar hash against role-set's stamp. Merge order: #109, then #110 once the whole dataset is green |
| Batch 6 round 3 (#106, fe67993) | 74 changed items | changes needed. Fixed: T10's size words decide (every loose reading re-solved), T11's verdict lines are back and the cap accepts them, the material fields match, and the flags and instant-agreement items are fixed. Open: T12-B-01 to B-05 give the date a placeholder span value and reach the fee through a conditional, so no date is matched, and B-02 and B-04 have the wrong key (`placeholder_value_to_pass_check`, new class). The Specialist's shapes are ruled yes: an edition-in-force pointer, and a claim-keyed fee on a date. T10-B-01 to B-05 are one "exactly k of N" template with flattened keys (role-set#45). Also: a T11 count family with no search on the confirm side; T10-C-08 `subject_not_named`; T12-D-08 is an order, not a claim (`not_truth_apt`, new class); B-06 `label_mismatch` (new class); stamps and absurd options |
| Batch 6 round 4 (#106, 2cbbd33 + bbf1e1d) | 48 changed items | T12-B-01 to B-05 (the Specialist's shape-1 rebuild) pass, solved by hand: one span per date, and every named shortcut changes the answer. T11-B passes (two rebuilt off the count family, the search shown on the confirm side, B-08 cannot_tell). T10-B keys and the grouped form are right, but the Question asks a fact ("which stoves are hot?") for an open set (`model_text_mismatch`), and all five are one count-plus-conditional template. Outside B: T12-E-07 has a second defensible option (`second_defensible_option`, new class), the connective tell flipped to "since", absurd options remain, and the T11 closer stamp and two distractor templates remain |
| Batch 6 round 5 (#106, 86888ef) | 22 changed items | pass for merge. T10's open-set questions now ask what could be, and B-01 (two counts) and B-05 (a count plus a negative clue) were re-solved by hand. The connective tell is gone. Residue to clear before the freeze: a T11 falsifier sentence frame in five items, a duplicate move in T12-E-07, four absurd options, and "today" in T11-E-06 D |
| Batch 6 residue (#112, 5ae4c48) | 10 items, wording and options only | pass for merge. All four residue items are cleared: five distinct falsifier wordings in T11, three distinct wrong moves in T12-E-07, near-miss options in place of absurd ones, and "today" dropped. Watch: silence-as-denial is now a distractor in three items, so batch 7 shouldn't add more. Batch 6 is clear for the Stage 1 freeze |

**Patterns that fail instant agreement.** These have been seen more than once and now go into the generators'
rules:
- **A cannot_tell next to a line that a reader could argue settles it:** a similar number for a different
  function, a dated release beside a "will be" line, or a privacy line beside a claim about emailing.
- **Closed lists.** "Blue for staff, green for contractors" can be read as complete, which makes "a red
  permit" unsupported rather than cannot_tell. Ask about an attribute nothing covers instead.
- **A universal claim against a scope-limited line** ("always locked" against "locked on weekdays"). Readers
  split between unsupported and cannot_tell, and one batch keyed it both ways. Don't use it.
- **Time words the material can't speak to:** "today", "now", "still", "when it shipped".
- **Paraphrase gaps:** "in the mixer" against "a Custom category"; "idle" against "every GPU under 5%";
  "starts at" against a "Home" column.
- **ESCALATE on a plain statement of fact, or for a reason outside the four taught ones.** Escalation is for
  a claim that asks for a decision.
- **DECIDING fragments that lose their subject,** or don't cover every clause of the claim.
- **Counted edits described wrongly** ("one digit differs" where two do). Script-check them.
- **Accept items that add a fact:** "per die", "so use the stairs", "12 pm". These belong in a reject item.
- **Thinking that describes the claim wrongly:** a start time the claim never gives, or a "mechanism" it never
  states. List what the claim asserts before writing the thinking.
- **Template generation.** Batch 3 passed every mechanical gate while being one generator's output:
  - framing sentences cycled in the same order and contradicted the material ("garden rules" over Python);
  - one trivial ordering puzzle was repeated for every trait;
  - one thinking skeleton was reused 6–7 times per trait.

  Gates that check correctness can't see sameness. Proposed diversity gates:
  - no 8-word span outside material shared by 3 or more items;
  - the framing label must match `content_kind`;
  - no repeated puzzle structure;
  - a generator script in the PR triggers a full human read.
- **Two stop rules in conflict.** "Stop once the first line settles it" sits beside a falsifier sweep after a
  merely supporting line. Say it explicitly: stop when the line is decisive and nothing in the material
  qualifies it.

## The quiz loop and the ledger (R&D rulings, recorded 2026-10-11)

After each training session, ASPIRE's `quiz.py` asks the due kind-E items again as fresh variants and records the
results in a Leitner ledger (`ledger.py`, aspire-si #102). R&D's rulings:
- **Only kind-E items enter the ledger.** Each ask is a fresh variant, never the trained turn. n = 0 is the item's own
  variant, then n = 1, 2, … come from role-set's variant store, without replacement. An exhausted family is reported
  unmastered.
- **Spent variants.** A variant whose wording outside material shares an 8-word span with any trained turn is
  spent, because it was trained on. Restating the trained statement counts as spent: the quiz shows the item's
  material and scores against the base key, so a restated statement tests recall. Material is excluded because it
  is shown on purpose.
- **What passes:**
  - A verdict variant passes only when all three lines pass against the base key: the pinned scorer for the
    verdict and DECIDING, and the harness for ESCALATE. The verdict alone is logged beside it.
  - A written variant is scored only in closed form, by letter. Free-text written variants stay out, and they are
    counted per lesson.
- **Samples:** a majority of 3 at the card's sampling settings, never greedy in thinking mode. Every sample is a
  receipt row.
- **The ledger:**
  - boxes 1–4; a miss goes to box 1, due next session;
  - a right answer moves up a box, due after 2, 4, then 8 sessions;
  - an item is mastered after 3 right answers in a row spanning at least 2 boxes, then a right fresh twin;
  - a quality is mastered at 95% of its items mastered and 90% right on twins;
  - forgetting events (right, then wrong) are logged.

  The grounding: Amiri et al., EMNLP 2017 (Leitner-style repetition for training); Toneva et al., ICLR 2019
  (forgetting events).
- **The readout** gives n = 0 beside n ≥ 1, per lesson and overall. A gap is the sign of surface matching.
- **Sealed reads:** a sealed sitting refuses an adapter trained with `--partial-set`, or one with no manifest.
- **Closed-form written variants, against Amendment 5 (ruled 2026-10-11).**
  - **The conflict:** Amendment 5 required the keyed option to contain a key point, and the trained reply states
    that point word for word. So 12 batch-5 keyed options were spent by construction.
  - **The ruling:** the keyed option paraphrases the key point, and is not exempted from the spent check. Choosing
    a trained sentence among distractors is recall.
  - **The mechanical gate that replaces "contains or is contained in":**
    - no option shares an 8-word span with any trained turn;
    - the keyed option holds at least half of the key point's content words (lightly stemmed, function and task words
      dropped);
    - no distractor reaches that share for any key point;
    - meaning is confirmed by R&D's key-check.

    The 50% share is to be measured on the existing variants before batch 6 is gated.
  - **Made configurable (the maintainer's direction, 2026-10-11):**
    - the keyed carry (verbatim, paraphrase or either), with its content-word share;
    - the exemption of an item's own key points inside the keyed option;
    - the span length and the share threshold.

    R&D's ruling sets the defaults: paraphrase, no exemption, 8, 0.5. The settings in force go on the manifest and
    every quiz receipt, and a non-default setting on a scored run is pre-registered. Authoring stays paraphrase, which
    passes under every setting.
  - **The distractor rule, revised after ASPIRE's measurement.**
    - **The measurement:** on batch 5's 12 closed-form items, 15 of 36 distractors share at least half the keyed
      point's content words. They are built from the item's own vocabulary on purpose. A 0.5 cap would refuse 8 of
      the 12 for good near-misses.
    - **The new default:** each distractor's share must be strictly below the keyed option's (`distractor_margin`
      0.0), and `distractor_max` is 0.8, a near-copy guard only.
    - **What stays the same:** keyed share 0.5, re-measured once the round's paraphrased options exist.
    - **The guarantee of no second right answer** stays with the key-check.
    - **The margin was set from the paraphrased round** (batch 5 at 6a01c18, 12 items):
      - keyed share 0.50–0.86;
      - top distractor share 0–0.33;
      - the gap between them: minimum 0.21, median 0.50.

      `distractor_margin` was set at **0.15**: a real separation, with headroom for new writers. Re-measure after
      batch 6, and raise it if the minimum gap stays above 0.2.
    - **The margin, raised to 0.20 after batch 6** (R&D ruling, 2026-10-15).
      - **The re-measure:** at 0c181e4, over 24 closed-form written-E items (batches 5 and 6; batches 1–4 are
        excluded, as ruled).
        - The minimum gap is 0.214 (T09-E-07: keyed 0.5, top distractor 0.286); batch 6's minimum is 0.223, and the
          median is 0.437.
        - The keyed share's minimum is exactly the 0.5 floor, on that same item. The top distractor's maximum is 0.571,
          under the 0.8 cap.
      - **Why 0.20, not 0.21:** 0.20 is the line the condition tested, and it keeps headroom under the weakest good
        item. 0.21 would sit 0.004 under that one item: fitted to the sample, with no room for batch 7's and batch 8's
        writers.
      - **What follows:** the minimum gap is re-measured at the batch 8 freeze. A good item that fails at 0.20 comes to
        R&D with its shares; the margin isn't lowered, and the item isn't dropped, to get it through. The key-check
        decides whether it has a weak distractor or a real second answer.
    - **A distractor at share 0.0 is not off-topic by that alone.** The four such items have on-topic near-misses
      that reach the point through the trait's moves. Share doesn't detect off-topic options, so there's no floor;
      that stays a key-check judgement.
    - **The authoring check and the quiz now share one definition** of the spent rule (`variant_checked_spans`), over
      the whole variant, verdict and closed-form alike (#105).

## Amendments, 2026-10-15 (the maintainer's decisions, on R&D's recommendation after Argon's round-1 review)

**A. STaR, matched across the arms.**
- Both arms keep their own right apply answers under the keep rule: all three lines pass the pinned scorer, the
  lesson's pass rule is met, and the trace isn't stuck under `716dc251`.
- Per (lesson, kind), the arm with more kept answers is downsampled to the other arm's count, so both arms inject the
  same number of STaR examples.
- Each seed runs the same number of optimizer steps in both arms.
- Near-duplicate kept answers are dropped first, by the gates' 8-word span check.
- There's a cumulative cap of 8 kept answers per (lesson, kind), the curriculum's count per kind.
- This replaces "right answers are kept" with "kept up to the matched count", so the arm comparison stays
  compute- and composition-matched.

**B. The general-capability panel's stop rule.**
- Round progression stops for the maintainer when the panel drops more than 2.0 points below its baseline **and** the
  drop is significant at p ≤ 0.05 (paired McNemar). This replaces the plain 2-point guard.
- **Disclosed sensitivity:** at about 300 items, with roughly 15% discordant pairs, it reliably stops only on drops of
  about 4–5 points. Smaller drops are reported, not acted on.

**C. The panel's decoding.**
- The panel keeps the card's sampling settings, with one sampled pass per item, reproducible through the batched
  path's per-item seeds. It doesn't use greedy decoding, which Qwen3's card warns against in thinking mode.
- The rest of the panel's shape comes from the review:
  - 250–300 independent items;
  - generated through the batched path once its parity check passes;
  - about 12–15 minutes a sitting;
  - G1 run as three per-seed grants, each with both arms, with 15-minute rests.

## The leakage tool

`experiments/verifier-gold/leakage_check.py` (rnd 1.1.4.4.8–1.1.4.4.10) checks a new set against the gold
corpora and, with `--against`, against held-out sets: the sealed set, the pilot and the pre-interview.
- A same or near-duplicate claim fails (Jaccard ≥ 0.8).
- A looser match warns (Jaccard ≥ 0.5).
- Against a held-out set, 2 or more shared material lines fail.
- Training items are read from their user turns, sentence by sentence.

ASPIRE's own validator applies the same thresholds, and fails at 0.5 against the interview for identity and
quiz items.
