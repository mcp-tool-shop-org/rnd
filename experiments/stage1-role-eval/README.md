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

## The leakage tool

`experiments/verifier-gold/leakage_check.py` (rnd 1.1.4.4.8–1.1.4.4.10) checks a new set against the gold
corpora and, with `--against`, against held-out sets: the sealed set, the pilot and the pre-interview.
- A same or near-duplicate claim fails (Jaccard ≥ 0.8).
- A looser match warns (Jaccard ≥ 0.5).
- Against a held-out set, 2 or more shared material lines fail.
- Training items are read from their user turns, sentence by sentence.

ASPIRE's own validator applies the same thresholds, and fails at 0.5 against the interview for identity and
quiz items.
