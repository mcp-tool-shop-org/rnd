---
title: Briefing an outside model
description: How to brief a model that knows nothing about the studio (AI Studio, a browser assistant, a fresh chat), so it works from our data and invents nothing.
sidebar:
  order: 9
---

An outside model has no access to our repos, receipts or rulings. Asked to "visualize the study", it will fill every
gap with plausible numbers, names and software claims. On 2026-10-19 an AI Studio app built from a short consult came
back with invented item counts, test families, costs, millisecond timings and commit ids, all styled as committed
results.

The fix is the brief. Give the model everything it needs, and forbid everything else.

**Worked example:** `experiments/stage1-regeneration/critic-signal/ai-studio-visuals-brief.md`.

## The template

Copy this and fill in each section. Keep the section numbers: the checklist in section 7 refers to them.

````markdown
[R&D → <tool>] Consult brief: <one line on what to build or answer>, from our data only.

Paste this whole brief in. Everything you need is in it. You have no other knowledge of our studio, so don't add any.

## 1. Who you're working for
<Two or three sentences: the studio, the seat, who reads the result, and why accuracy beats polish.>

## 2. Hard rules (break one and the work is unusable)
1. Use only the numbers, ids, names and dates in section 4. Don't invent <the things this task tempts it to invent>.
2. If something needed isn't in section 4, show a visible placeholder (`DATA NEEDED: <what>`).
3. Make no claims about software, versions, releases or deprecations <unless section 4 gives them>.
4. Units as given: <units>.
5. Every rendered or stated number carries its source key from section 4.
6. Measured and illustrative are kept apart; anything illustrative is bannered as such.

## 3. The story, in plain words
<The facts, short, in the reader's words. Define every term the data uses.>

## 4. The data (the only numbers you may use)
<A compact JSON block, computed from committed files by script, never typed by hand. Name the files and commit.>

## 5. What to build (or answer)
<One numbered item per point, each with the form that fits it and the data keys it uses.>

## 6. Output
<Format, plus a Sources panel and a self-check against section 4. No publishing controls; publishing is ours.>

## 7. How we'll check it
1. Every number traces to section 4.
2. Nothing is invented.
3. Each placeholder names the missing data.
4. <Any task-specific must-show: the inconvenient result must be visible.>
````

## Rules for whoever writes the brief

- **Compute section 4 by script from committed data,** and name the files. A brief typed from memory carries our own
  errors in with it.
- **Put the inconvenient result in the brief and in the checklist.** An outside model drifts towards the flattering
  story. In the example, the 12-of-32 false refusals had to be named or they'd vanish.
- **Ask for a Sources panel and a self-test.** They make every reply checkable in minutes.
- **Treat the reply as untrusted until checked.** Every number in it gets checked against section 4 before any of it is
  used. An outside model's technical claims (versions, deprecations, "the 2026 standard") are checked against primary
  sources, or dropped.
- **Publishing stays ours.** The brief never asks the tool for a release gate, and nothing it builds goes public
  without the Director's go.
- **Data that isn't public stays out of the brief.** Section 4 holds only what may leave the studio: ids, counts and
  aggregates, never item text.
