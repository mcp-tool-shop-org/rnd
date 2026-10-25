---
title: "25 October: a crash test, a lab for tests with proven answers, and our Colab cards measured"
description: "The first daily issue. We killed a rented machine mid-write to test Attestia's event store, and the log survived, but the kill didn't test the fix, so we tore the same file by hand. We started a lab that builds tests whose answers are proved before any wording is written. And we turned 21 rented-GPU windows of receipts into a profile of each Colab card, with what's still unmeasured."
issue: 30
date: 2026-10-25
highlights:
  - "<strong>A crash test that didn't test the fix.</strong> A machine killed mid-write left a log that a fresh machine opened whole, but no line was torn, so the fix never ran. We tore the same file by hand: the old code lost an event and refused to open, the fixed code didn't."
  - "<strong>A lab for tests with proven answers.</strong> reasoning-dataset-lab maps a dataset before any item exists and proves each answer in code before a model writes a word. Its first pilot map has 24 cells, 12 of them buildable today."
  - "<strong>Each Colab card, measured.</strong> From 21 windows of receipts: what each card has, what it costs per hour, how often a session was lost, and what no receipt has measured yet."
---

This is the first of the daily issues: one email a day, with an article for each piece of the day's work worth
reporting. Today has three.

**In this issue:**

1. [We killed a machine mid-write. The log survived, but the kill didn't test the fix](#we-killed-a-machine-mid-write-the-log-survived-but-the-kill-didnt-test-the-fix)
2. [A lab for tests whose answers are proved first](#a-lab-for-tests-whose-answers-are-proved-first)
3. [What each Colab card is, from the receipts](#what-each-colab-card-is-from-the-receipts)

## We killed a machine mid-write. The log survived, but the kill didn't test the fix

Attestia is one of the studio's three proof products. Its **event store** keeps a log as a plain file, one event per
line. Each event carries the hash of the one before it, so the events form a chain. If the chain is broken anywhere,
the store refuses to open. That's on purpose: a log you can't trust is worse than no log.

We want to use that store as the run log for experiments on rented machines, and rented machines vanish. So before
trusting it, we tried to break it.

### The bug

We found the problem on our own machine first, before spending anything. A writer that's killed partway through
writing a line leaves a **torn** last line: half an event, with no line ending. Then:

1. A new writer opens the store. It skips the torn line, checks the chain up to the last whole event, and opens.
2. Its first new event is written straight after the torn fragment, on the same line, because nothing put a line
   ending in between.
3. The next time anything opens the store, it skips that glued line too, so the new event is gone. The event after
   it now points at a predecessor that isn't there, and the chain is broken.
4. With checking on, which is the default, the store refuses to open at all.

So one crash followed by one honest restart turned a good log into one that wouldn't open.

### The fix

The fix is small. When the store opens a file that doesn't end in a line ending, it writes one before its first new
event. The torn fragment stays in the file on a line of its own and is skipped every time. Nothing is cut off or
rewritten, so the store keeps its rule that the file only ever grows.

### A real kill

Then we tested it for real, on a rented Colab machine running on CPU:

- a writer added 10 events a second for an hour;
- a copy of the store was taken off the machine every 60 seconds;
- at 3,654 seconds we killed the machine outright, with no warning to the writer;
- 56 seconds later, a fresh machine opened the last copy, with checking on.

The copy held **36,498 events, all valid**. The new machine carried on writing and added 27,000 more. The final log
held **63,498 events: a valid chain, no gaps and no duplicates**. Its first 36,498 events are byte for byte the copy
it started from, and its first new event links to the copy's last.

<!-- Chart 1 goes here: events across the kill and the resume (Argon visuals, card ew). -->

### What the kill didn't test

Two things were true that a headline would skip.

**The fix never ran.** The copy we resumed from ended on a whole line. There was no torn fragment for the fix to deal
with. The run proved that a hard kill and a resume on a new machine work, but it didn't prove the fix.

**Some events died with the machine.** Its last progress report, one second before the kill, counted at least
36,516 events. The copy held 36,498. So at least 18 events, about two seconds of writing, were on a machine that no
longer exists. That isn't a store bug: a resume from a copy can only have what the copy had. Anyone running a log
on a machine that can disappear has to decide how much of it they can afford to lose, and copy at least that often.

### The fix, tested on the same file

So we tore the file ourselves. We took the copy from the real kill and added the first 328 bytes of a real 657-byte
event, with no line ending: exactly what a writer killed mid-line leaves. Then we resumed it twice, once with the
old code and once with the fixed code, on our own machine.

- **The old code** skipped the fragment and opened. It added 60 events, and the first was glued onto the torn line
  and lost. The chain broke at position 36,500, and the store then refused to open.
- **The fixed code** skipped the fragment, added the same 60 events, and lost none. The chain was valid with no gaps,
  and the store opened again cleanly.

<!-- Chart 2 goes here: the old code and the fixed code on the same torn file (Argon visuals, card ew). -->

### What it cost

| Step | Where | Cost |
|---|---|---|
| A short trial run of the whole procedure | Colab, CPU | 0.01 units |
| The real kill and resume | Colab, CPU | 0.14 units |
| The torn-file test, old code and fixed | our own machine | nothing |

### Where it stands

- **Proven:** a hard kill, and a resume on a fresh machine, with every event in the copy kept and the chain intact.
- **Proven separately:** the fix, on that same file with a torn line added by hand.
- **Not proven:** that a real kill tears a line, or how often. Ours didn't.
- **By design:** events written after the last copy are lost with the machine.

The fix shipped today in **Attestia 2.1.2**, on npm and as a GitHub release. The run logs, both stores and the
torn-file test are in the studio's records, and every figure here was recounted from the store files themselves.

## A lab for tests whose answers are proved first

[Issue 29](/rnd/newsletter/issue-29/) ended with a decision: we stopped deciding anything about our critic from that
test panel until we have a test whose answers are known for certain. This article is the start of that test.

**reasoning-dataset-lab** is a new public repository at
[mcp-tool-shop-org/reasoning-dataset-lab](https://github.com/mcp-tool-shop-org/reasoning-dataset-lab). It builds
puzzles, quizzes and other tests. Its rules are the reverse of how a test is often made, where a model writes the
items and someone checks them afterwards:

- **Map first.** Before any item exists, a `map.yaml` says what the dataset is: its axes (the skill tested, the kind of
  item, the difficulty, the subject, and the wrong answer each item is built to catch), every cell those axes make,
  how many items each cell gets, and the rules the finished set must pass. The map is hashed, so it can't drift
  quietly.
- **Prove, then word.** Code builds each item's underlying problem and proves its answer before a language model
  writes any prose around it. An item kind whose answer can't be proved that way is marked `judged`, and gets in only
  if judges from several model families all agree.
- **Show the gaps.** A cell the generator can't build yet stays in the map with a capacity of 0 and a reason. The
  map doesn't shrink to make coverage look complete.
- **Provenance on every item,** so any item can be traced back to the map, the source material and the code that
  made it.

### The first pilot map

The first map, in the repository's `examples/`, is for a single skill: reading a stated quantity correctly. Its wrong
answers are four kinds of misreading: an exact amount read as a minimum, an exact amount read as a maximum, and a
minimum or a maximum read as exact. The subjects are lamps and cups, at three difficulties.

That makes **24 cells**. **12 are buildable today**, with 5 items each: 60 items, 48 for training and 12 held out for
evaluation. The other **12 are in the map at capacity 0**, because the generator can't build those misreadings yet.

The rules for the finished set were fixed before anything is generated:

- every answer key proved (a proof rate of 1.0);
- at least half the items passing in each class;
- a sample of 20 items read by a person, with at most 1 defect.

<!-- Chart 3 (optional) goes here: the pilot map, 24 cells, 12 buildable and 12 at capacity 0 (Argon visuals). -->

### Where it stands

The repository has a map checker, the project files and their fingerprint, and, as of today, the first part of the
pilot: the interface every generator follows, and an adapter that drives the studio's existing puzzle generator
unchanged. No pilot items have been built yet. The pilot's first batch, with its numbers and a sample of items, is
the next step.

## What each Colab card is, from the receipts

We rent GPU time on Google Colab in **windows**: a session on one card, booked and closed by a script that keeps a
receipt of everything it did. Before planning the next set of measurements, we read every receipt we have, 21
windows and the probes around them, and wrote down what each card actually is. Every value below comes from a
receipt. Where no receipt measures something, we say so.

### The cards

| Card | Memory | Rate (units an hour) | Sessions | What went wrong |
|---|---|---|---|---|
| A100, 40 GB | 40,960 MiB | 5.3 | 62 or more | 3 sessions lost mid-run, all on 23 October; 3 full four-hour windows with no loss |
| A100, 80 GB | 81,920 MiB | 6.77 | about 8 | 1 session lost after 132 seconds |
| RTX PRO 6000 (G4) | 97,887 MiB | 8.9 | about 9 | none; one window ran 8,680 seconds clean |
| L4 | 23,034 MiB | 1.54 | about 8 | only one window used it |
| T4 | not measured | about 1.07, worked out, not read | assigned 6 times | never used |
| H100 | — | — | never assigned | refused 5 times, "Service Unavailable" |
| CPU (standard) | 12.3 GB of RAM free | 0.08 | 41 or more | the download check rejected 5 of 52 tries as too slow |

The plan allows up to 20 sessions at once: 3 of each GPU card (the 80 GB A100 has its own pool of 3) and 5 CPU
machines. The next request is refused.

### Faster isn't always cheaper

On the same job, a critic model checking items:

- the **RTX PRO 6000** took a median 46.7 seconds a call against the 40 GB A100's 66.5: about 1.4 times as fast, at
  1.68 times the price;
- the **80 GB A100** ran the model 1.11 times as fast as the 40 GB one, at 1.28 times the price, with identical
  output on all 178 items compared.

So for that job, the cheaper card cost less per result. That holds for that job only. Another model or another size
can change it.

<!-- Chart 4 (optional) goes here: the cards side by side (Argon visuals). -->

### What no receipt measures yet

- the time to the first token, on every card;
- how fast a model downloads through Ollama (no receipt has an Ollama log);
- how long a card takes from the request to ready;
- almost everything about the T4, which has never run a job, and the L4, which ran one window.

Those gaps are the reason for the next sweep, **C2**, which measures the cards the same way: the largest model
context each holds, the speed at several prompt lengths and loads, and the throughput of small embedding models.

### Licences first

Before a model's first window, it needs an entry in our licence registry, read at its source. Six of the models in
the C2 sweep had none, so we read them: **phi3.5** (MIT), **nomic-embed-text-v1.5** (Apache-2.0),
**bge-base-en-v1.5** (MIT), **bge-reranker-v2-m3** (Apache-2.0), **nli-deberta-v3-base** (Apache-2.0) and
**Qwen3-Embedding-0.6B** (Apache-2.0). No card or linked page restricts our use. Only phi3.5 ships a licence file;
the other five rest on the licence their model card names. Each entry keeps a hashed snapshot of the page and an
archive.org copy.
