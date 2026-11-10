---
title: "10 November: deciding how to judge before the result"
description: "A warning check in aspire-si's new training series went over its line once, and we wrote down how a stop would be reviewed before the next reading came in. Also: whether to add vLLM beside Ollama, where a research report was wrong on two counts we checked, why batching an evaluation pass by eight makes it about twice as fast and not eight times, and the daily watch."
issue: 42
date: 2026-11-10
draft: true
highlights:
  - "<strong>Deciding how to judge before the result.</strong> One of the five warning checks in aspire-si's S2 v1.1 run went over its line at one reading. Two in a row would stop the run for review, and the study record didn't say how that review works. We wrote the rules down before the next reading. It came in clean."
  - "<strong>A second engine, checked first.</strong> vLLM could run our bulk jobs many requests at a time. A Deep Research report on it got two things wrong that we checked at source. One small trial is planned, and its output will never be mixed with Ollama's."
  - "<strong>Eight at a time isn't eight times faster.</strong> Batching the next study's evaluation pass by eight would make it about 2.15 times faster. Up to a third of the time can go to a dozen answers that may never stop."
---

A night of procedure. A warning light in a training run flickered once, and the rule for what happens next had to be
written before we knew whether it would flicker again. A faster inference engine looked tempting, so we read the research
first and checked it. And a plan to speed up our exams turned out to promise far less than the obvious arithmetic.

**In this issue:**

1. [Deciding how to judge before the result](#deciding-how-to-judge-before-the-result)
2. [A second engine, checked first](#a-second-engine-checked-first)
3. [Eight at a time isn't eight times faster](#eight-at-a-time-isnt-eight-times-faster)
4. [The daily watch](#the-daily-watch)

## Deciding how to judge before the result

[Issue 41](/rnd/newsletter/issue-41/) ended with a new, pre-registered training series for
[aspire-si](https://github.com/mcp-tool-shop-org/aspire-si): S2 v1.1, seeds 45, 46 and 47. Each seed is 197 updates of
training on our RTX 5090, run in five chunks of about three and a half hours each, with the first chunk also carrying a
long check of the untrained model.

**Where seed 45 stands.** Chunks 1 to 4 have run, 160 of its 197 updates, and the run's own checker passed every one.
None of them needed a confirmation pass, the extra check a guard must pass before it can stop the run. Chunk 5, the last
37 updates, started at 03:40 ET this morning.
<!-- PUBLISHER: replace with the chunk 5 and seed-level result if it lands before release. -->

**The warning checks.** Besides the guards, the run has five **canaries**: cheaper checks that look for early signs that
the model is learning a bad habit. One of them looks at the quotes the model gives as evidence. It counts how often a
quote runs across a paragraph break or the edge of a table, which a real quote from one place in the text shouldn't do.
Its line is 1% of the quotes checked. Its rule, written before the series started: over the line in **two readings in a
row** (each reading covers 10 updates), and the run stops for the Publisher to review. A single reading over the line
only counts.

**What happened.** At the reading after update 150, 4 of 360 checked quotes crossed a boundary: 1.1%, just over the line.
The count went to 1. The next reading was due about 50 minutes later.

**The gap we found.** The study record says a second crossing means "stop and report", and that a review decides what
happens. It doesn't say what the review looks at, what it may decide, or who may decide it. The code only asks for a
written reason before it will resume. That leaves the reviewer free to choose the rules after seeing the stop, which is
exactly what pre-registration exists to prevent.

So, before the next reading, we added a clarification to the study record:
- **What the review reads:** the counts for every canary and guard in the two readings, the checker's verdict, and the
  flagged quotes themselves, sorted by kind.
- **When the run may resume:** only if no guard tripped, no other canary was over its line, and the flagged quotes are
  formatting slips rather than one new kind of mistake repeating.
- **Who else decides:** in every other case, and on any second stop in the same seed, the studio's director decides.
  Ending a seed, and how an ended seed is scored, are the director's decisions too.

**The next reading:** 0 of 375 quotes crossed a boundary. The count went back to 0 and the run carried on. The rules
weren't needed this time. They'll be in place if the canary crosses its line again.

![TODO V3 diagram](/rnd/charts/issue-42-review-first.png)

One more thing we learned on the way: the run stores the counts for each reading, not the flagged quotes themselves. A
review would have to recount them from the saved answers with the run's own, unchanged checking code, and the recount
would have to match the stored count before anyone read a single quote.

## A second engine, checked first

We run local models through [Ollama](https://github.com/ollama/ollama), one request at a time. Several of our bulk jobs,
like a few hundred questions to a judge model or eight sampled answers per question for 500 questions, would go much
faster on an engine built to serve many requests at once. [vLLM](https://github.com/vllm-project/vllm) is the best-known
one. We don't want to replace Ollama; we want vLLM as a second option.

**What we already knew, and what we can't compare.** In June we had vLLM 0.22 running on this card under WSL2 (Linux
inside Windows), serving a 4-bit 7B model, and swept it at 1, 16 and 64 requests at once. The script's raw output
wasn't kept, but our engine notes recorded the results the same day: about **65** tokens per second with one request,
**1,912** with 16, and **4,138** with 64, counting all the requests together. At 64 requests the card drew up to 579 W,
past the 480 W limit we now run it at.

We meant to set that beside Ollama. When we checked, the Ollama figure in the same notes was for a different, much
larger model, so it isn't a comparison, and we're not drawing one. The trial below runs both engines on the same
model, each in its own 4-bit format, and keeps the output. A later attempt to start vLLM with a different model failed with an error saying a memory
feature ("UVA") wasn't available, and nothing had been tried since.

**What the research said.** We asked Gemini's Deep Research what it takes to run vLLM well on this machine today. Its
report was long and mostly useful, and we checked its load-bearing claims against the vLLM and WSL sources:
- **Held:** the current version is 0.33.0 (2 November), and the setting that works around the UVA error under WSL2
  exists in vLLM's code.
- **Wrong:** the report said vLLM 0.30 and later fall back to a working mode by themselves when UVA is missing. The
  change that would do that ([vLLM #47579](https://github.com/vllm-project/vllm/pull/47579)) is still open, not merged.
  So we set the workaround ourselves.
- **Wrong:** it said the card's fast 8-bit (FP8) arithmetic now works under WSL2. The open WSL issue it relied on
  ([microsoft/WSL #40333](https://github.com/microsoft/WSL/issues/40333)) says the opposite, which matches what we found
  in June.
- **Misread:** it cited [vLLM #37242](https://github.com/vllm-project/vllm/issues/37242) as a start-up crash. It's a
  report that the feature works on a 5090 under WSL2, with a configuration we can use.

**What it changes about the answers.** At temperature 0 a model should give the same answer every time, but on vLLM the
answer can depend on which other requests happen to share its batch, and on whether the start of the prompt was cached
from an earlier one. For a fixed list of questions there's a way round that: run the whole list in one go, in a fixed
order, with prompt caching off, so the batches come out the same each time. That repeats run to run. It still doesn't
match asking each question alone. That's the same lesson as issue 41's prompt cache, from another direction.

**What we'll do.** One small trial, after seed 45 finishes. First, June's 1 / 16 / 64 sweep again on both engines, with
the same 7B model (each engine's own 4-bit format, so the tables say "engine and format"), this time saved. Then an
8-billion-parameter model at full precision on about 100 public questions with 8 answers each, under an hour of card
time. It passes only if three things hold:
1. memory stays under the card's safety limit and is fully freed afterwards;
2. the same 50 questions at temperature 0, run twice, give the same answers;
3. long answers (up to 2,048 tokens) end cleanly.

If it passes, vLLM becomes an option for new jobs, chosen at the start of a study and fixed for all of it. Its output is
never mixed with Ollama's in one result, because two engines are two models as far as our measurements go. The larger
30–35B models are a separate decision for later: vLLM can't load our Ollama copies of them, so it would mean new 4-bit
versions, which count as new models.

## Eight at a time isn't eight times faster

The training run above stops now and then to take an exam: 184 fixed questions, answered with the randomness switched
off, one question at a time. Each exam takes about 83 minutes, and a run can need several. For the next study we
wanted it faster. The obvious move is to answer eight questions at once, since a step that decodes eight answers takes
about the same time as one that decodes a single answer.

We asked Argon (Gemini 4 Argon, in Antigravity) to design it, and checked its arithmetic with our own script:

![TODO V2 chart](/rnd/charts/issue-42-exam-time.png)

**Why only about twice as fast.** Most answers stop by themselves after a few hundred words. Up to a dozen of the 184
may not: in the untrained model's exam, 12 were flagged as cut off or malformed, and each one that runs to the
2,048-token cap costs about 145 seconds. Together that is up to a third of the whole exam. In a batch, the whole batch
waits for its slowest answer. So batches of eight, with those long answers spread across them, come to about 38.6
minutes: **2.15 times faster**, not eight. The design's suggestion for more: put the long answers in a batch of their
own, and choose the cap from the answer lengths we actually measure.

**What batching changes.** The same question can get a slightly different answer when it shares a batch with other
questions, because the card's arithmetic isn't exactly the same at every batch size. The
[Thinking Machines Lab](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/) measured this: 1,000
identical requests under varying load gave 80 different completions, and 1 with kernels made to ignore the batch. Our
exam compares answers before and after training, so the batches must be frozen: the same questions in the same batches in
the same order every time. And before trusting it, we'll measure how often an answer flips between one-at-a-time,
batches of four, and batches of four shuffled.

**What we checked and didn't accept.** The design cited 15 outside sources, all marked by the designer as not opened. We
opened the five that mattered most. Three of its figures weren't in them, including a memory size the NVIDIA page puts at
about 24 MiB, not 32, and two speed costs no source gives. None of those figures will go into the next study's plan until
we've measured them here.

Nothing here changes seeds 45 to 47. Their exams stay exactly as they were registered.

## The daily watch

<!-- PUBLISHER: daily watch goes here (R&D's rnd watch block + the Deep Research watch seed planted just before release). -->

**How the watch works.** A script lists every new item from our sources; a research agent and Gemini's Deep Research
look through it; we read the primary source for anything we report, and hold anything we couldn't check.
