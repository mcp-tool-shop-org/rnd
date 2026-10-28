---
title: "28 October: the T4 sweep is done, a ready-made critic fails its test, and Cognate learns to choose between plans"
description: "Yesterday the T4 part of the C2 sweep finished. Replayed over the earlier windows, interlock 1.0.11's new check would have refused every load that had been killed and none that had completed; on its live windows, nothing crashed. We also tested whether an off-the-shelf language-inference model could check our verifier's quotes. It couldn't: on real supporting quotes it agreed 21% and 7% of the time, against a bar of 85%. And Cognate took in a plan chooser, with three fixes on the way in. In reasoning-dataset-lab, two models agreeing certified 26 test sets, and a blind second key found only 3 of them sound. A first paid run on batching found that it rewrites most of a model's replies, though few of its verdicts. Overnight, a CPU-only test run turned out to be on the GPU, and CPU runs now hide every route to it. The issue ends with the first daily watch."
issue: 33
date: 2026-10-28
highlights:
  - "<strong>The T4 sweep is done.</strong> Three repetitions on Colab's T4 card closed on 27 October. The sweep has spent 19.572 of the 800 units set aside for it."
  - "<strong>A check that held on a live run.</strong> interlock 1.0.11 refuses a cell whose memory would overflow the machine, before loading it. On its first live windows, for phi3.5 it refused the same five cells in each of four quants, and nothing crashed."
  - "<strong>A ready-made critic, failed.</strong> An off-the-shelf language-inference model read real supporting quotes as support 21% and 7% of the time, against a pre-set bar of 85%. It won't be used."
  - "<strong>Cognate chooses between plans.</strong> civility-kernel joins Cognate: it drops plans that break a hard rule, scores the rest, and executes the best or asks a person. Its decisions can now be hashed and recorded."
  - "<strong>Two readers agreeing wasn't enough.</strong> Two models certified 26 of 50 test sets, but a blind second key found only 3 that hold a contradiction on every pair. The sets are being rewritten before any rerun."
  - "<strong>Batch 1 for verdicts that must repeat.</strong> Served one request at a time, a 30B model repeated all 60 replies. Batched eight at a time, only 1 of 60 matched. Verdicts moved far less, on 1 to 4 of 60."
  - "<strong>CPU runs now hide every GPU.</strong> A CPU-only test server that hid only CUDA put a 24B model on the RTX 5090 through Vulkan. CPU runs now hide every route, ask for no GPU layers, and stop if the server takes any of the card's memory."
---

Two results from 27 October: a sweep that finished, with a fix that held on its first live windows, and a test that
failed, as its pre-registration said it might. Then a change that landed overnight in Cognate, a certification that two
models agreed on and a second key didn't, a test of what batching does to a model's replies, a CPU run that turned
out to be on the GPU, and, from this issue on, a short daily watch at the end.

**In this issue:**

1. [The T4 sweep is done, and the host-memory check held](#the-t4-sweep-is-done-and-the-host-memory-check-held)
2. [A ready-made critic fails its test](#a-ready-made-critic-fails-its-test)
3. [Cognate learns to choose between plans](#cognate-learns-to-choose-between-plans)
4. [Two readers agreed, and it wasn't enough](#two-readers-agreed-and-it-wasnt-enough)
5. [Batching rewrites a model's replies](#batching-rewrites-a-models-replies)
6. [A CPU run that wasn't](#a-cpu-run-that-wasnt)
7. [The daily watch](#the-daily-watch)

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
"neutral": on the NPU, 498 of the 677 pairs it scored came back neutral. It was trained on prose, and these are lines of code. The pre-registration named
that risk, and pairs with a prose comment in the code didn't rescue it: on grounded claims, 0.208 with a comment and
0.153 without.

(The run's own note first gave these two counts as 473 of 637 and 636 of 637. Both had been counted with each quote
cut to 80 characters, which made the 677 pairs look like 637; the note was corrected on 28 October.)

It ran on both of the rig's Intel devices. They agreed on 676 of 677 labels (99.9%), and the integrated GPU was about three
times faster than the NPU (0.089 s a pair against 0.271 s). That's moot for this model, which fails on both.

### What it means

The model won't be used. That was the pre-registered consequence of a fail, and nothing else changes: it was never
going to enter the training reward, and S1 says nothing about the verifier's answer keys, which are provisional. The
next smoke tests, S2 and S3, are separate pre-registrations and haven't run.

## Cognate learns to choose between plans

[Cognate](https://github.com/mcp-tool-shop-org/cognate) records how AI is governed: which model version was used,
which policy applied, which agent acted, with each record provable afterwards. Its policy engine checks one event at a
time, such as a prompt, an output or a spend. Until now it had nothing for the step before: deciding which of several
plans an agent should carry out.

On 28 October Cognate took in **civility-kernel**, imported from its earlier standalone package, as a new package of
its own. Given an agent's candidate plans, it drops any that break a hard rule (an irreversible change, a spend over a
limit), scores the rest by the policy's weights, and then either carries out the best one or, when that plan is too
uncertain, asks a person. If no plan survives, it asks the person to relax a rule or offer another option.

### Three fixes on the way in

- **A cache keyed on too little.** From the policy, the kernel's compile cache read only the version, so two
  policies with the same version but different weights or constraints got the first one's rules. The cache is gone.
- **Decisions that can be reproduced.** A caller can now supply the decision's id and time; then the same inputs give
  a byte-identical record.
- **A number JSON can't hold.** A plan that broke a rule was scored minus infinity, which JSON writes as `null`, so a
  record read back from storage was no longer the record that was made. Such plans now score `null` from the start.

### What it adds

A decision can now be hashed in the form Cognate's run pre-registration uses, and recorded on its event log. The record
carries the outcome and which rules each rejected plan broke, and never the plans' steps; the chosen plan's digest
still covers them, so a step changed afterwards no longer matches.

The new package has **164 tests**: 143 carried over and 21 new. Its tests cover **91.89%** of its lines (578 of 629),
against a floor of 90%. It is on Cognate's main branch and not yet in a release.

## Two readers agreed, and it wasn't enough

[reasoning-dataset-lab](https://github.com/mcp-tool-shop-org/reasoning-dataset-lab) builds test sets with a known
answer. One kind is a set of five values for one attribute of a machine, chosen so that only one can be true of a
unit: a transformer's vector group, a vessel's berth status, a reactor's coolant. Any two of them then make a
contradiction, and a test item can be built from each pair. Before a set is used, it is **certified**: two language
models, each reading blind, must call every one of its 20 ordered pairs a contradiction.

On 28 October the lab ran certification on 50 sets with two readers, Mistral Small 3.2 (24B, thinking off) and
Nemotron 3.5 Lightning (30B). Both first passed a fixed test on 20 known-compatible pairs (19 and 20 of 20), so neither
was simply answering "contradiction" to everything.

### The run

- **26 of 50 sets certified**, and 24 went to a review queue. There were 2,000 calls and none failed.
- 121 pairs kept those 24 sets out. On 55, one reader called a contradiction and the other called the pair compatible. Both readers called
  27 compatible. Another 25 were Nemotron runs whose thinking hit the length limit, which count as failures, not
  verdicts. On the other 14, a reader answered "unsure".

### A second key

Agreement between readers is only worth something if the pairs really are contradictions, so we had every pair of the
26 certified sets keyed a second time, by a model blind to the readers' verdicts. It was allowed three answers:
contradiction, arguable, or compatible.

| Pairs | Contradiction | Arguable | Compatible |
|---|---|---|---|
| 520 pairs in the 26 certified sets | 272 | 216 | 32 |
| 27 pairs both readers called compatible | 2 | 19 | 6 |

Only **3 of the 26 certified sets** came back as contradictions on all 20 pairs. The faults are in the sets, and both
readers missed them the same way:

- Under the collision regulations a vessel that is drifting is still "underway", so *underway* and *adrift* can both
  hold.
- A large generator is often cooled by hydrogen and by water at once.
- A three-winding transformer carries two vector groups.

Our own read of a sample, made before the second key and without sight of it, had found the first two. The second key
agreed with every fault that read named, and found others, such as the three-winding transformer, in sets the read
had called clean.

### What it means

Two readers agreeing is a weak filter for this task: it rules out clear failures, but it doesn't prove a pair is a
contradiction. That's a finding about the test sets, not a measurement of the readers. "Arguable" is a judgement, and
some of the second key's calls are strict ones (most people would read "the transformer" as a two-winding unit). The
sets are being rewritten before any rerun, under four rules: one axis per attribute, no relative terms ("higher"), no
label that contains another value, and no values that can occur together on one unit.

## Batching rewrites a model's replies

A model served one request at a time gives the same reply to the same request, if the seed and settings are fixed.
Servers are faster when they batch several requests together, but batching changes the arithmetic. We wanted to know
how much it changes the answers.

On 28 October we ran Muse Glimmer 30B on a Colab A100 (40 GB) under llama.cpp's server, and sent it the same 60
critic requests, each asking for a verdict, at batch widths 1, 2, 4 and 8 (the server's slot count). Widths 1 and 4
were run twice. The seed, the settings and the server build were fixed. (The study's code is public, in
[role-set](https://github.com/mcp-tool-shop-org/role-set), under `scripts/batchdrift/`.)

| Compared with batch 1 | Identical replies | Verdict changed |
|---|---|---|
| Batch 1, run again | 60 of 60 | 0 |
| Batch 2 | 30 of 60 | 3 |
| Batch 4 | 12 of 60 | 1 |
| Batch 4, second run | 12 of 60 | 3 |
| Batch 8 | 1 of 60 | 1 |

- **Batch 1 is deterministic** on this card and build. It matched itself on all 60, and matched an earlier reference
  run on all 60.
- **Batching rewrites most replies**: half of them at width 2, all but one at width 8.
- **And a batched run doesn't repeat itself.** Batch 4 run twice gave the same reply on only 37 of 60.
- **Verdicts move much less than the text.** They changed on 1 to 4 of the 60 requests in each comparison. With 60
  requests that is still loose: the 95% intervals reach about 16%.

### What we take from it

Any verdict that has to be reproducible runs at batch 1. Batched runs are their own tier, and their replies can't be
compared one by one with batch 1's. Two limits: we recorded the server's slot count but not how many requests the
client kept in flight, so we can't yet say every slot was full. And this is one model on one card under one build;
other engines and cards may behave differently.

## A CPU run that wasn't

On 28 October we ran a dry run of a 24B model, the Mistral reader above, on the rig's processor only, to check a code
path before asking for time on the RTX 5090. The second Ollama server it started hid CUDA with `CUDA_VISIBLE_DEVICES=-1`, and that was all
it hid. Ollama 0.40.9 also ships a Vulkan backend, and through it the "CPU" server loaded the model onto the 5090
anyway: its process held 15,114 MiB of the card's memory for about 29 minutes before we found it and stopped it.
Nothing broke, but the card was meant to stay free, and the run wasn't measuring what it said.

### The guard

CPU-only runs now do three things:

- **Hide every GPU route**, not just one. The server starts with CUDA, Vulkan and HIP hidden.
- **Ask for no GPU layers on every request.** A small wrapper adds `num_gpu: 0` to each call, so a backend we didn't
  think of still gets no layers.
- **Check, and stop on a rise.** Every 10 seconds a guard reads the GPU memory held by the server's own processes and
  the card's total, and stops the job unless the server holds nothing and the total hasn't risen by more than 512 MiB.

We tested the stop path three ways, including a forced baseline and a live run that failed closed on a counter it
couldn't read. Then the guard passed on a 4B model and on the same 24B model: both runs reported `library=cpu`, the
24B server started with no GPU layers (`-ngl 0`), the server held 0 MiB of the card, and the card's total went down
slightly over each run rather than up.

### A two-second name

The same night turned up a smaller cost. An embedding job that talked to Ollama at `localhost` hit its 15-minute stop
(902.4 s) without finishing. Each call was taking about 2 seconds against hundredths of a second at `127.0.0.1`,
most likely because the rig tries IPv6 first and falls back. With `127.0.0.1` the whole job took 30.8 seconds.

### A study whose retrieval can't miss

That job was the retrieval arm of a study we're preparing: how a model's tool choice holds up as the list of tools
grows. (Its code is public, in [role-set](https://github.com/mcp-tool-shop-org/role-set), under `scripts/toolcount/`.)
With real embeddings, the arm found the right tool in its top five for all 170 answerable items, at every list size
from 10 to 100. That isn't a result: the study's paid run hasn't happened. It says something about the items, which
name their tool almost word for word. The study will report that alongside whatever it finds.

## The daily watch

*New since the [weekly watch](/rnd/watch/2026-10-26/) of 26 October, checked against each release's own notes.*

**NeMo Relay 0.11.0** (NVIDIA, released 2026-10-28;
[release notes](https://github.com/NVIDIA/NeMo-Relay/releases/tag/0.11.0)). This is the agent-tracing tool we tried in
a sandbox on 0.10.1. The new version changes how its coding-agent hooks behave: tool checks now fail closed by
default, and a hook that can't deliver returns exit code 2. It also adds opt-in diagnostics and continues traces
through Claude Code hooks. For us, a hook that fails closed can stop an agent mid-task, so the 0.10.1 trial doesn't
carry over. *What we'll do:* run the sandbox trial again on 0.11.0, hooks included, before we use it in our own
harnesses.

**ComfyUI v0.43.0** (Comfy-Org, released 2026-10-27;
[release notes](https://github.com/Comfy-Org/ComfyUI/releases/tag/v0.43.0)). Among many partner-node additions, it
fixes the top-p sampling threshold and Gemma 4 31B's global attention, starts dynamic VRAM KV caches, and sets a
minimum Pillow version. For us, our image pipeline pins one ComfyUI commit per run, so this is the candidate for the
next pin. *What we'll do:* check it on a CPU run before anything paid.

**Ollama v0.40.12** (released 2026-10-27; [release notes](https://github.com/ollama/ollama/releases/tag/v0.40.12)).
Its listed changes are on the Apple-silicon side (MLX, faster prompt processing), an updated llama.cpp, and Liquid AI's
new LFM3 models, which run on Apple hardware only for now. For us, the C2 sweep ran on 0.40.11. *What we'll do:*
nothing for now; C2 stays on 0.40.11, so its windows stay comparable.
