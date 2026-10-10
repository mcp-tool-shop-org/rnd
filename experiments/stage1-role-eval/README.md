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
| Kimi batch 2, traits 1, 14 and 16 | 120 | about 96 passed; 24 fixes sent back |

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

## The leakage tool

`experiments/verifier-gold/leakage_check.py` (rnd 1.1.4.4.8–1.1.4.4.10) checks a new set against the gold
corpora and, with `--against`, against held-out sets: the sealed set, the pilot and the pre-interview.
- A same or near-duplicate claim fails (Jaccard ≥ 0.8).
- A looser match warns (Jaccard ≥ 0.5).
- Against a held-out set, 2 or more shared material lines fail.
- Training items are read from their user turns, sentence by sentence.

ASPIRE's own validator applies the same thresholds, and fails at 0.5 against the interview for identity and
quiz items.
