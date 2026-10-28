---
title: "28 October: the T4 sweep is done, and a ready-made critic fails its test"
description: "Yesterday the T4 part of the C2 sweep finished. Replayed over the earlier windows, interlock 1.0.11's new check would have refused every load that had been killed and none that had completed; on its live windows, nothing crashed. We also tested whether an off-the-shelf language-inference model could check our verifier's quotes. It couldn't: on real supporting quotes it agreed 21% and 7% of the time, against a bar of 85%."
issue: 33
date: 2026-10-28
highlights:
  - "<strong>The T4 sweep is done.</strong> Three repetitions on Colab's T4 card closed on 27 October. The sweep has spent 19.572 of the 800 units set aside for it."
  - "<strong>A check that held on a live run.</strong> interlock 1.0.11 refuses a cell whose memory would overflow the machine, before loading it. On its first live windows it refused the same five cells per model and quant, and nothing crashed."
  - "<strong>A ready-made critic, failed.</strong> An off-the-shelf language-inference model read real supporting quotes as support 21% and 7% of the time, against a pre-set bar of 85%. It won't be used."
---

Two results from 27 October: a sweep that finished, with a fix that held on its first live windows, and a test that failed, as its
pre-registration said it might.

**In this issue:**

1. [The T4 sweep is done, and the host-memory check held](#the-t4-sweep-is-done-and-the-host-memory-check-held)
2. [A ready-made critic fails its test](#a-ready-made-critic-fails-its-test)

## The T4 sweep is done, and the host-memory check held

**C2** measures how fast and how large the studio's models run on Colab's rented cards, with interlock.
[Issue 31](/rnd/newsletter/issue-31/) told how its first trial runs on a T4 card exposed problems in our
measurement, and [issue 32](/rnd/newsletter/issue-32/) noted one more: some cells filled the machine's memory, and
its limit killed the model server, three times taking our harness down with it.

### The fix, checked against the past first

**interlock 1.0.11**, released on 27 October, works out before each cell how much of the machine's memory the
cell's working cache would need, from the cell before it. If that, with a 5% margin added, is over the machine's
limit (12,954 MiB on a T4), the cell is recorded as out of memory and never loaded.

Before it ran live, it was replayed over the seven T4 windows already on record. Of 234 loads, 12 were the first of
their run and can't be projected. Of the other 222, it refused **all 34 loads that had been killed** and **none of
the 188 that had completed**.

### Then live

The first window on 1.0.11, s2c, ran phi3.5 at Q4_K_M: 21 cells, 13 measured and 8 out of memory. Five of those
eight were refused by the new check before loading. Two were the exact cells that had killed the harness in windows
s2a and s2a2; with the margin, the check projected them at **15,544 MiB** and **42,349 MiB**. The machine's memory log showed
**no model-server kills and no harness kills.**

The last window, s3a2, ran all four phi3.5 quants on 1.0.11 and refused the same five cells in each, again with no
kills.

### Its limits, stated with it

- The first cell of each run is never projected, because there's nothing earlier to scale from. No first cell on
  record was killed.
- It can refuse a cell that would have fitted. A cell projected at **12,337 to 12,954 MiB** is under the T4's
  limit, but the margin lifts it over, so it is refused; and the projection overstates a partly offloaded load. The
  closest completed load on record was projected at **12,021 MiB** (12,622 with the margin), 316 MiB short of
  that band.

### What the sweep cost

The T4 part of C2 ran three repetitions, finishing with window s3a2 on the evening of 27 October. Not every window
came back whole: one stopped at its spending cap, one was lost to the memory limit before the fix, one was stopped by the launcher after the same kill,
and one was lost twice when our own machine restarted, then re-run in full. With the trial runs before them, C2 has
spent **19.572 of the 800 units** set aside for it. The T4 bills **1.07 units an hour**.

## A ready-made critic fails its test

**aspire-si** trains models to judge the way a teacher does. Its current plan trains a **verifier**: a model that
checks a claim about code and quotes the line that settles it. A cheap way to check those quotes would be a ready-made **natural-language
inference** model, one trained to say whether one sentence supports another. Smoke test **S1** asked whether one
such model, `cross-encoder/nli-deberta-v3-base`, can tell a real supporting quote from one that fooled a verifier.

The pass line was fixed before the run. Real supporting quotes had to be read as support at least **85%** of the
time, and quotes that had fooled a verifier on an unsupported claim no more than **15%** of the time (the upper end
of a 95% interval).

### The result

| check type | real supporting quotes read as support | fooling quotes read as support (upper bound) | pass |
|---|---|---|---|
| grounded | **0.210** (of 267) | 0.073 (of 110; upper 0.137) | no |
| reasoning | **0.071** (of 210) | 0.029 (of 68; upper 0.101) | no |

The model rarely calls a fooling quote support, so that half holds. But most of what it reads, it calls
"neutral": on the NPU, 473 of 637 distinct labels came back neutral. It was trained on prose, and these are lines of code. The pre-registration named
that risk, and pairs with a prose comment in the code didn't rescue it: on grounded claims, 0.208 with a comment and
0.153 without.

It ran on both of the rig's Intel devices. They agreed on 636 of 637 labels, and the integrated GPU was about three
times faster than the NPU (0.089 s a pair against 0.271 s). That's moot for this model, which fails on both.

### What it means

The model won't be used. That was the pre-registered consequence of a fail, and nothing else changes: it was never
going to enter the training reward, and S1 says nothing about the verifier's answer keys, which are provisional. The
next smoke tests, S2 and S3, are separate pre-registrations and haven't run.
