---
title: Picking a writer model on rented GPUs
description: We're choosing which open-weight model should write training data for a small local verifier. Night one tested the judge before trusting it, found that thinking is most of the bill, and lost half the budget to machines that disappeared. Here's the data, and the method that came out of it.
issue: 11
date: 2026-10-17
highlights:
  - "<strong>Test the judge before it judges anything.</strong> Both critic models passed a bar set before their results, and the test also caught two mistakes in our own answer key."
  - "<strong>Thinking is most of the bill.</strong> 95% of one model's output was reasoning the reader never sees: about 12,000 tokens per draft, 6½ minutes each. The pilot as designed would have cost 147–175 compute units, so it became a smaller screen."
  - "<strong>About 38 of the first 71 units bought nothing usable,</strong> mostly from machines lost mid-job with no results saved. The fixes: the job writes its own log, the rig reads that file, every finished model call is saved, and every way a window can end downloads the results first."
  - "<strong>A blind second opinion on the budget.</strong> We sealed our own allocation before asking an outside reviewer for theirs, then took the parts of it that were better."
---

The studio is building a small local model whose job is to check other models' claims: is this statement supported by this
evidence, or not? To train it, we need thousands of practice rows, each a short piece of material with a statement and the
right answer. We write those rows with larger open-weight models, and a second model, the critic, checks every draft
before it's kept.

Which model should do the writing? There were eight candidates. This issue covers night one of the pilot that picks
between them: what we measured, what went wrong, and the method we'd use again. The screen's results will be added here
as updates when they land. → [the plan](https://github.com/mcp-tool-shop-org/rnd/blob/main/experiments/stage1-regeneration/PLAN.md)

## The setup, in brief

- **Eight writers, all open-weight:** Qwen3.8-27B, Qwen3.6-35B-A3B, Granite-4.2-30B, Gemma-4-31B-it,
  DeepSeek-R1-Distill-Qwen-32B, Muse-Glimmer-30B, and NVIDIA's Nemotron-3.5 Lightning-30B and Bolt-74B. Every one was
  checked against its licence before it went in.
- **One critic per writer, never from the writer's own family.** Muse critiques every writer except itself; Lightning
  critiques Muse.
- **Rented GPUs.** Each "window" is a Colab session on one NVIDIA A100 with 40 GB of memory, paid in Colab compute units.
  An A100 costs about 5.3 units an hour. A CPU-only session costs about 0.08.
- **Pinned models.** Every model file is rebuilt from a fixed source revision and has to reproduce a recorded
  fingerprint (its sha256 hash) before it serves. When something went wrong, we always knew it wasn't the model files.
  Lightning's file reproduced five times out of five.
- **Same settings for everyone:** each model runs at its own model card's recommended sampling and thinking settings,
  with a 32,768-token context and a 16,384-token limit on each reply.

Not every model fits a 40 GB card at those settings. Qwen3.6 fit at full 8-bit precision, peaking at 36,022 MiB of
40,960, and wrote at about 90 tokens a second. Gemma fit with 4,943 MiB to spare, at about 28 tokens a second.
DeepSeek-R1-Distill didn't fit at 8 bits, so it runs a 6-bit build and is reported separately. Comparing a 6-bit model
against 8-bit ones wouldn't be fair.

## Step 1: test the judge before it judges anything

If the critic is wrong, every number downstream is wrong too, so the critic was tested first. The test is a
**known-answer set**: 40 practice items whose right answers we wrote ourselves, plus 10 copies with a deliberate error
planted in them. The bar was written down before any result came in:

- **agree with the key** on at least 36 of the 40 clean items;
- **catch at least 80%** of the planted errors;
- for a critic that samples randomly, like Muse, **two runs with different random seeds** may disagree on at most 4 of the 40.

Both passed. Muse agreed with the key on 38 and 37 of 40 across its two runs, caught all 10 planted errors, and its two
runs disagreed on just 1 item. Lightning agreed on 38 of 40 and caught all 10.

The more useful finding was in the misses. On two items, the critics disagreed with *our* key, and the critics were right:

- "Retries the upload up to 3 times" means up to 4 attempts in all, so "tried at most 3 times" isn't supported. Our key
  said it was. Muse flagged it in both runs.
- "Apply every four weeks from March to September" fairly rules out January. Our key said you couldn't tell. Both
  critics disagreed with it.

We replaced both items in version 2 of the set and changed nothing else. **A calibration set can check the person who
wrote it**, so read the misses before blaming the model. Next time, the key will be written by two people independently,
or checked blind by a model from a third family, before it's used. → [the set and its errata](https://github.com/mcp-tool-shop-org/rnd/blob/main/experiments/stage1-regeneration/critic-control/README.md)

## Step 2: thinking is most of the bill

Modern open models "think" before they answer: they write out reasoning that's never shown to the reader, then the
answer. That reasoning counts toward the reply limit and takes GPU time like any other output.

We logged every call through a small proxy that records token counts and timings. Qwen3.8's first 13 calls show where
the time went:

![Thinking vs the draft, per call](/rnd/charts/pilot-thinking-budget.svg)

- **95% of the output was thinking:** 81,372 of 85,752 tokens.
- The calls came in two shapes. Short prompts (about 145 tokens) got 400–2,000 tokens back. Long prompts (6,400–7,600
  tokens) got 4,000–15,000 back, at 4–8 minutes each.
- **Nothing was cut off,** but the longest call used 15,264 of its 16,384 tokens. A model that thinks a little longer
  will start hitting the limit. A cut-off reply is reported as its own outcome, not counted as a refusal, so a model
  isn't marked wrong for running out of room.

That changed the plan. At about 12,100 output tokens per draft, each draft took about 6½ minutes. Projected across the
pilot as designed (8 writers, 20 practice rows each, with rewrites), it came to **147–175 units**, against about 35 left
that night.

So the pilot became a **screen**:
- every writer drafts the same 8 practice rows, plus 2 "twin" rows of a second kind, from one fixed list;
- every draft is critiqued once, and drafts the critic sends back get one rewrite;
- writers that drop 3 or more of their 8 are cut;
- writers that pass go on;
- with 8 rows per writer, the screen can tell "doesn't work" from "works". It can't rank close writers finely, and the
  readout will say so.

And one number joined the readout: **cost per accepted row.** A writer that thinks for 12,000 tokens per row pays that
on every row of the full dataset later, so the cost matters as much as the quality.

## Step 3: rented machines disappear, so design for it

This is where most of the money went. By the time the budget was raised at 19:44 UTC, 70.66 units had been spent, and
**about 38 of the first 71 bought nothing we could use**:

| What happened | Units |
|---|---|
| A long pilot window: the rig stopped receiving the job's output, the job ran on unseen, and the window hit its cap without downloading anything | 14.03 |
| Colab reclaimed a machine 77 minutes into setup, with nothing saved off it | 12.81 |
| A connection hung at the first command with nothing running, and the session sat open for 35 minutes | about 3.2 |
| A check read an empty log and stopped the window, because the line it looked for sits at a log level the default setting drops | 3.00 |
| Three failed starts: a missing setting, a machine dropped mid-download, and a module missing from a package | 5.29 |

None of these were model problems. They were all about how the job talked to the machine. The method that came out of
it, in the order we'd build it again:

1. **The job writes its own log, and the rig reads that file, never the live output stream.**
   - The stream between the rig and a Colab session can stop while the job keeps running. That's what cost the 14.03.
   - So the job appends everything to a file on the machine, and the rig downloads that file every 2 minutes.
   - Progress, stalls and "finished" are all judged from it.
   - A download that dies partway never overwrites the good copy.
2. **Every finished model call is saved the moment it returns.**
   - Each call goes into a journal, keyed by a fingerprint of exactly what was asked.
   - A resumed run replays the saved calls instead of asking the model again, and the job's own logic rebuilds
     everything else from them.
   - We tested it by killing a run halfway and resuming: every draft and every decision came out identical to an
     uninterrupted run, and no call ran twice.
3. **Every way a window can end downloads the results first:** finished, stalled, out of time or at its spending cap.
   - The cap starts the exit early enough that the download fits inside it.
   - The window that lost 14.03 units had stopped at its cap without downloading.
4. **Caps count each window's own spend.**
   - An early cap read the account balance, so two windows running side by side each counted the other's spend and
     stopped at about half their real budget.
   - Each cap now measures its own rate, read under a lock so two windows opening together can't confuse each other.
5. **Set up each model just before it's needed,** not all at the start.
   - The reclaimed window had spent 77 minutes downloading and converting four models before writing a word.
   - Now a writer is set up right before its own drafts and the critic right before the first critique. A loss costs
     at most one setup.
6. **Test each new kind of window on the cheapest machine first.**
   - Before trusting the new file-based watcher, we ran a fake job on a CPU-only session that went silent on the
     stream and then hung.
   - The watcher saw it finish from the file, downloaded the results in 2 seconds, and closed the session.
   - The two tests together cost 0.03 units.

The rule underneath all six: **assume the machine can vanish at any minute, and make sure that minute costs only the
work in flight.**

## Step 4: a blind second opinion on the budget

When the budget was raised to 150 units, we wanted an outside view on how to spend the remaining 79. The catch with
asking for advice is that you tend to anchor on it, or the adviser anchors on you. So:

1. We wrote and committed our own allocation first, then sealed it.
2. The outside reviewer, Argon (a model from a different family than ours), got only the measured facts: setup times,
   speeds, tokens per draft and the failures so far. It didn't see our plan.
3. We compared the two answers against the sealed version.

Argon's plan was better in three places, and we took them:
- pair Lightning and Muse in one window, each critiquing the other, which saves two model setups;
- set up models lazily (point 5 above);
- fold one rewrite into the screen itself, so writers that pass don't need a second window.

We kept two of ours:
- **The second-critic check.** A second critic re-scores a blind sample of each writer's drafts, to see whether Muse
  favours writers that sound like it. It stays as a gate before any writer goes further.
- **One correction to Argon's plan:** Qwen3.8's lost window couldn't be resumed, because it ran before the call journal
  existed.

## What's next

The screens are running tonight in this order:
1. Granite;
2. Qwen3.6 and Bolt;
3. Lightning and Muse;
4. Qwen3.8 and Gemma.

DeepSeek-R1-Distill waits for another day. It's the longest thinker, it has the one untimed setup step, and it sits in
its own 6-bit group.

For each writer, the readout will give:
- how many of its 8 rows were accepted, dropped or cut off;
- its twin results;
- its tokens and units per accepted row;
- its share of thinking;
- "cut" or "goes on".

Those numbers will be added below as they come in.
