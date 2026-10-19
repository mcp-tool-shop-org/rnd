---
title: "Testing the tester: does our critic catch bad training rows?"
description: Our training data is checked by a second model, a critic, and in the writer screen it accepted 35 of 36 rows from one writer. Was the data that good, or was the critic too easy? We broke good rows on purpose and counted what two critics caught. One rule turned out to decide almost everything, and the pre-registered test still said "not shown". Here's why, and the confirmation test that comes next.
issue: 14
date: 2026-10-19
highlights:
  - "<strong>The critics catch most planted errors already.</strong> On the three kinds of broken copy the critic reads for the verdict (a changed number, a can't-tell trap, a decoy deciding line), the two critics refused 82 of 83."
  - "<strong>One gap, one rule.</strong> When we swapped a checker's flawed reasoning for sound reasoning but left the flaw label on, both critics said \"no flaw\" every time, 13 of 13. Today's rules ignore that answer. Counting it catches every one, at the cost of 1 wrongly refused good row in 44."
  - "<strong>A clear result that didn't pass its own test.</strong> The stricter rules won 13 to 0, but the multiple-test correction we committed to in advance put the result at 0.0625, short of 0.05. So nothing changes yet."
  - "<strong>Cheaper than planned.</strong> A critic call took a median of 12 to 21 seconds, against our projection of about 120 seconds an item. The three paid windows cost 11 units, against about 23 projected for one."
---

The studio builds training data with a pipeline of local models. One model, the **writer**, drafts each row. A
second model from a different family, the **critic**, checks it before it's kept. In last week's writer screen
([issue 11](../issue-11/)), the critic accepted almost everything: 35 of 36 rows from one writer. That's either
very good data or a critic that rarely says no.

This study tests the critic itself. Every figure here comes from files in the repo, and the last section says
which. The design was written and reviewed before any of it ran:
[`DESIGN.md`](https://github.com/mcp-tool-shop-org/rnd/blob/main/experiments/stage1-regeneration/critic-signal/DESIGN.md).

## What the critic checks

Many of the rows are reading exercises. A short document (the **material**) and a **statement** about it; the
answer is whether the material supports the statement, contradicts it, or can't tell, plus the line or lines that
decide it. Some rows add a twist: a **checker's reasoning** that contains a planted mistake, which the learner has
to name. Each kind of mistake has a label, such as "guess" (reasoning from outside the material).

The critic gets two checks:
- **the verdict check:** it solves the row blind, without seeing the answer, and its verdict and deciding lines are
  compared with the row's;
- **the flaw check:** on rows with a checker's reasoning, it names the mistake.

Today the flaw check is **advisory**. A disagreement is logged, but the row is kept. That was decided earlier,
when an older setup agreed with the flaw labels only 9 times in 24.

## Step one: were the accepted rows actually right?

Before testing the critic, R&D checked its accepted rows by hand, blind: 30 rows with a verdict, keyed without
seeing the writer, the critic's answer or the row's own answer.
- **29 agreed** with the row's answer. **1 was unclear**, and none were wrong.
- So the critic wasn't letting wrong rows through. But the rows were easy, and none of them had "can't tell" as
  the true answer, so they don't show what the critic would do with a hard one.
- **New finding:** two rows had reasoning that named its own planted mistake ("that is a guess"), which gives the
  answer away. That's now a defect class the pipeline checks for.

## Step two: break good rows on purpose

From 27 rows that passed the hand check, a script made copies with one known change each. The critic never
sees which copy is which.

| Copy | What changed | A good critic should |
|---|---|---|
| **controls** | nothing | accept it |
| **material flip** | a number on the deciding line changed so the true verdict flips | refuse it |
| **can't-tell trap** | the deciding line deleted, or its subject swapped for another one in the passage | refuse it |
| **clean trace** | the checker's flawed reasoning replaced with sound reasoning, but the flaw label kept | refuse it |
| **decoy deciding line** | the answer's deciding line swapped for a line that doesn't decide anything (scored offline) | refuse it |

R&D read every material-flip, can't-tell and decoy copy before any critic saw them. One flip turned out not to
flip, because the script missed a number with "px" stuck to it. That copy was set aside before the run, and the
decision is on record.

Two critics took the test: **Muse-Glimmer-30B** (two runs, at seeds 0 and 1) and **Nemotron-3.5-Lightning** (one
run). A critic never checks rows written by its own model family, so Muse skipped 14 copies and Lightning 11.

## What they caught

![What a critic catches, P0 against P2](/rnd/charts/critic-catch.svg)

Each row is scored under two rule sets, from the same critic replies:
- **P0** is today's rules (the flaw check is advisory).
- **P2** makes the flaw check count, and adds two rules about quoting.

**Most broken copies are caught already.** Across the material flips, can't-tell traps and decoy lines, both
critics refused nearly everything under either rule set. The one miss was Muse reading a time changed from
5:00 PM to 7:00 PM as still matching. Lightning caught it.

**The clean traces are the gap.** On every clean-trace copy, both critics answered "no flaw": 13 of 13. That's the
right answer, because the reasoning really is sound. But the label still says "guess", so the row is wrong, and
under today's rules the critic's correct answer is ignored. P2 counts it, and catches all 13.

**The cost:** P2 refused 1 of the 44 unchanged good rows, where Muse named a flaw the row didn't have. The two
quoting rules never decided a single item. Everything P2 changes comes from making the flaw check count.

Muse's second run (seed 1) refused nothing that its first run didn't.

## Then why didn't we adopt it?

Because the design said in advance how strong the evidence had to be, and it wasn't.

The test compares the two rule sets item by item and counts only the items they disagree on. All 13 disagreements
favoured P2: 6 for Muse and 7 for Lightning. Each comparison on its own gives p = 0.031 or 0.016.

But the design ran several comparisons: P2 and a two-run variant, for each critic. Testing more things gives
chance more opportunities, so the design applies a correction (Holm's) across all of them. With four comparisons,
the smallest result has to be under 0.0125, and 0.016 isn't. Corrected, the result is **0.0625, above the 0.05
bar.**

The reason is plain from the data: there were only 6 or 7 clean-trace copies per critic. Even a perfect 7-to-0
can't clear a four-way correction. We didn't run Lightning's second seed, because its outcome was fixed before it
started: P2 already catches everything P0 misses on Lightning's items, so a second run couldn't add a
disagreement. Skipping it saved about 4.5 units.

So under the rule we committed to, nothing changes yet. A "not shown" isn't a "no", though.

## Next: one clean confirmation test

The fix is more clean-trace items, judged by one comparison that was set in advance. The design is
[§9 of `DESIGN.md`](https://github.com/mcp-tool-shop-org/rnd/blob/main/experiments/stage1-regeneration/critic-signal/DESIGN.md):
- **New rows.** Gemma 4 31B writes 38 fresh reasoning rows, and R&D hand-checks each one blind.
- **No critic decides which rows are kept.** In the earlier rows, Muse helped pick what was kept, so it was partly
  being tested on its own choices.
- **One test.** P2 against P0 on Muse, at 0.05 with no correction, written down before any of the rows exist.

**How the outside review changed it.** An outside model, Argon, reviews every design before it runs. The first draft
picked 38 slots by lesson. Argon pointed out that the pipeline plants "no flaw" on every even-numbered slot, so
only 12 of the 38 could ever make a clean-trace copy. Too few. The fixed design takes all 27 eligible slots there
are, plus 11 even-numbered slots as natural controls. Argon passed the fix the same day.

![The confirmation test's 38 slots](/rnd/charts/critic-confirmation-slots.svg)

## What it cost

The study runs on Colab A100s, paid in compute units: about 5.3 units an hour.

| Window | What | Units | Projected |
|---|---|---|---|
| 13v (a, b, c) | the free test ladder on a CPU runtime: a forced cut, two resumes | 0.05 | – |
| 13w | Muse, seed 0 | 3.10, plus 0.24 for a launch mistake | 2.83–10.43 |
| 13x | Muse, seed 1 | 3.17 | about 2.69 |
| 13y | Lightning, seed 0, converted on the GPU | 4.52 | 3.82–8.83 |

The design had projected about 23 units for each critic run. That projection used Lightning's earlier timings,
which included three extra calls per item. Measured, a critic call is short:

![How long one critic call takes](/rnd/charts/critic-calls.svg)

The flaw check takes longer than the verdict check: its prompt is about twice as long, and the critic thinks more
before answering. Lightning thinks two to three times as much as Muse per call and still answers faster.
Lightning's one empty reply came after it spent its whole 16,384-token reply budget thinking. The retry was
counted, and the copy it was answering was scored as refused.

## Where the figures come from

- **The slot diagram** is `data/confirmation-slots.json`, the frozen list in §9.
- **The broken-copy results** are `experiments/stage1-regeneration/critic-signal/data/outcomes.csv`: one row per
  copy, critic and rule set, written by role-set's `critic-rescore-offline`.
- **The per-call timings and thinking counts** are `data/calls.csv`, from the logging proxy that sat between
  role-set and the model in every window.
- `scripts/extract_data.py` writes both files from the window receipts. The text of the rows stays off the public
  repo: these files hold ids, codes and counts only.
- **Hand checks, windows and decisions:** `PHASE-0-1.md` and `PHASE-2-3.md` in the same folder. Units come from
  the study's ledger, one row per window.
- **The tools:** [role-set](https://github.com/mcp-tool-shop-org/role-set) (`critic-eval`, `critic-rescore-offline`,
  `scripts/critic_signal/perturb.py`) at commit `47a5882`. The three pictures are built by
  `experiments/charts/make_charts.py`, and `manifest.json` pins each input's commit and sha256.
