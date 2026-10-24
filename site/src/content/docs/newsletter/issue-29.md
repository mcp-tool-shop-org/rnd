---
title: "A win that didn't replicate, and a test that couldn't see"
description: "We tested a fix for our critic's false refusals against a rule written in advance. The first run passed by one call. The replication failed. Then we found that every refusal in both runs landed on six items, most of them picked because the old prompt had failed on them before. Here's what the bench measured, what it couldn't, and why we've stopped deciding from it."
issue: 29
date: 2026-10-24
highlights:
  - "<strong>Passed, then failed.</strong> Giving the critic the label definitions cut false refusals from 9 to 4 of 69 calls, clearing our pre-set bar by one call. On three new seeds the cut was 9 to 7, and the bar wasn't met."
  - "<strong>A trade, not a fix.</strong> The definitions ended the old prompt's refusals on cannot_tell items, 12 to 0, and started new ones on unsupported items, 1 to 6."
  - "<strong>Six items carried everything.</strong> On 17 of the 23 sound items, neither prompt refused once in 102 calls. Every refusal was on six items tied to the old prompt's past failures."
  - "<strong>No decision from this test.</strong> We've stopped making critic decisions from this panel until we have a test whose answers are known for certain."
---

The studio builds training data with local language models. A **writer** drafts each item and a **critic** checks
it: it reads the material and a statement, and gives one of three verdicts, **supported**, **unsupported** or
**cannot_tell**. When its verdict differs from the item's label, the item is refused. A **false refusal** throws away
a good item.

[Issue 28](/rnd/newsletter/issue-28/) found that the writer is told what each label means and the critic isn't. It
ended with a plan: test the critic's prompt as it is (**A**) against the same prompt plus the writer's definitions
(**B**), on 30 blind-graded items, with the decision rule fixed before any run. This issue reports that test.

## The rule, written first

Of the 30 items, 23 were graded **sound**: both blind graders and the item's label agreed, and nobody flagged it
unclear. The other 7 were ambiguous and counted apart. Each prompt ran on every item with three seeds, so 69 calls on
sound items per prompt.

B would be recommended only if both held:
- **(a)** B's false refusals on sound items are at most half of A's;
- **(b)** B accepts at most one more of the items whose label the graders contradict.

## Passed by one call

The first run, on seeds 0–2, gave A 9 false refusals and B 4. Half of 9 is 4.5, so (a) held, by one call. (b) held at
its limit. The rule said B.

One call is a thin margin, so we ran it again on seeds 3, 4 and 5, with nothing else changed.

## Failed on the rerun

On the new seeds A refused 9 again, and B refused 7. That's well over half, so (a) failed. Pooled over all six
seeds, A refused 18 of 138 calls and B 11. Half of 18 is 9, and 11 is more, so the pooled result fails too. **The rule
says keep A.**

![Bar chart of false refusals on the 23 sound items against the half-of-A bar. First run, seeds 0 to 2, 69 calls per prompt: A refused 9, B refused 4, under the bar of 4.5, so it passes. Rerun, seeds 3 to 5: A 9, B 7, over 4.5, so it fails. Pooled over all 6 seeds, 138 calls per prompt: A 18, B 11, over the bar of 9, so it fails](/rnd/charts/issue-29-rule-runs.svg)

The first run wasn't wrong. It was a favourable draw: two items, P20 and P26, happened to go B's way more often on
those three seeds than on the next three.

## A trade, not a fix

Splitting the refusals by the item's true label shows what the definitions actually do:

| Sound items, by label | Calls per prompt | A refused | B refused |
|---|---|---|---|
| cannot_tell (10 items) | 60 | 12 | 0 |
| supported (7 items) | 42 | 5 | 5 |
| unsupported (6 items) | 36 | 1 | 6 |

![Pooled false refusals over 6 seeds on the 23 sound items, by true label. cannot_tell, 10 items, 60 calls per prompt: A 12, B 0. supported, 7 items, 42 calls: A 5, B 5. unsupported, 6 items, 36 calls: A 1, B 6](/rnd/charts/issue-29-trade-by-label.svg)

A's main error is calling a silent item **unsupported**. The definitions fix that completely. But B then calls
some unsupported items **cannot_tell**, an error A almost never makes. B moves the line between the two labels; it
doesn't make the critic better at both.

## Six items carried everything

Then we looked at where the refusals were. **On 17 of the 23 sound items, neither prompt refused once: 0 of 102 calls
each.** Every refusal, in both prompts and all six seeds, was on the other six.

![Refusals per item over 6 seeds. On the 6 items tied to past failures, 36 calls per prompt, A refused 18 and B 11: T10-C-09, cannot_tell, A 6 and B 0; P15, cannot_tell, A 4 and B 0; P29, cannot_tell, A 2 and B 0; P26, supported, A 5 and B 5; P20, unsupported, A 1 and B 5; P06, unsupported, A 0 and B 1. On the 17 other sound items, 7 cannot_tell, 6 supported and 4 unsupported, 102 calls per prompt, neither prompt refused once](/rnd/charts/issue-29-refusal-concentration.svg)

Those six weren't a random draw. Five came from an earlier study, Track A, and were picked for this panel because the
old prompt had already failed on them there: three it refused, two it flipped on between runs. The sixth, T10-C-09,
came in under a rule that took every item of its kind from a later run, but its refusal in that run was one of the
failures that started this study.

So the test was built, deliberately, around the old prompt's known failures, and the new prompt was designed to fix
those failures. That's a fair way to find out whether a fix works on the cases it was made for. It can't tell you
whether the fix helps or hurts anywhere else, and the 17 other items gave no signal either way.

More seeds won't change that. Antigravity, the outside model we work with, worked through the numbers before the
rerun came back: almost all the spread in this result comes from differences between items, not from run-to-run
noise, so rerunning the same 23 items barely narrows it. Its estimate was that doubling the seeds would shrink the
uncertainty by only about 6%.

## What we're doing about it

**We're not deciding anything about the critic from this panel.** The old prompt stays, and no run that the critic
scores is being started. That hold lasts until we have a test whose answers are known for certain, rather than graded
after the fact.

The lesson we're taking is simple: **a test built from your failures can only tell you about those failures.**

The raw results, the scoring scripts and the graded panel are in the studio's research library, and every figure
here was recounted from the critic's own output files.
