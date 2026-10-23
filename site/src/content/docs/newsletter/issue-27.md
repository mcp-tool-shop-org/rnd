---
title: "Same request, same seed, same bytes?"
description: "If you send a language model the same request with the same seed, do you get the same answer back on a different machine? We sent the same critic requests to five rented Colab GPUs. Every A100 gave back identical bytes, including one with twice the memory. A Blackwell card on its own build gave back different answers on 65 of them. Getting there first meant finding a bug of our own that had been dropping the seed."
issue: 27
date: 2026-10-23
highlights:
  - "<strong>The seed never arrived.</strong> A first re-run gave the same model scores on two A100s but different words. The cause was our own proxy, which dropped the seed before the request reached the model."
  - "<strong>Three A100s, one answer.</strong> With the seed passed through and the prompt cache off, three separate A100 VMs agreed byte for byte on all 176 critique calls they shared. An 80 GB A100 matched the 40 GB one on 178 of 178."
  - "<strong>A different card, different answers.</strong> An RTX PRO 6000 Blackwell, on its own build of the same server, matched on 113 of 178. Every one of the other 65 changed a verdict. It was 1.33× faster at 1.68× the price."
  - "<strong>Three VMs lost, the logs kept.</strong> Colab took back three of six long sessions. Each call's record goes into a log the rig copies every 2 minutes. What the log held was rebuilt; on one lost VM it stopped two calls short of the end."
---

The studio builds training data with local language models. One model writes, and a second model, the **critic**,
checks what it wrote. Everything is pinned so a study can be run again: the model files, the server build, the
settings, and a **seed** for the random choices the model makes while it writes. If the same request comes back with
different bytes, a re-run can't tell a real effect from noise.

So we asked a narrow question: **with the seed fixed, does the same request return the same bytes on a different
machine?** We rent GPUs on Google Colab by the hour ([issue 13](/rnd/newsletter/issue-13/) covers how), and every
session lands on a fresh virtual machine, so this matters to every rented run.

## First, a bug of our own

The first test re-ran three writer requests on a second A100. A model doesn't pick words directly. At each step it
scores every possible next token, and then a sampler picks one, using the seed for any randomness. The two VMs gave
**identical scores for the top five candidates**, but **picked different tokens**.

Identical scores mean the model's arithmetic matched. The difference was in the sampling, and the cause was ours. Our
model proxy, which sits between the study code and the model server, removed the per-request `seed` along with other
sampling settings it overrides. Each request reached the server with no seed. The fix (rnd 1.1.23.1.28) passes the
seed through.

This corrects something [issue 21](/rnd/newsletter/issue-21/) reported: the same critic prompts, sent twice at the
same seed, gave 7 different verdicts out of 102. Issue 21 put this down to the critic sampling at temperature 1. It
wasn't: those calls went through the same proxy, so the seed never reached the critic, and the prompt cache was on.
With the seed passed through, the same critic at the same settings gave identical flaw votes on 101 of 101 calls.

We also turned off a second possible cause: the server's **prompt cache**, which reuses work from earlier requests
that start the same way. Every request now asks for the cache off. A checker reads the server's own record of cached
tokens on every call, and fails the run if any call used the cache. To show the checker works, we ran it on the first
test, which had the cache on. It flagged 3 of the 4 calls, with 7,016, 350 and 350 cached tokens.

## The method

- **The same requests every time:** one pilot study's 178 critique calls, built from drafts written and sealed in an
  earlier session, so every machine critiques the same text.
- **The same software:** one build of the llama.cpp model server, the same model files (Muse-Glimmer-30B as critic,
  Gemma 4 31B as writer, both at 8-bit), with one request at a time.
- **One VM per arm.** Each arm ran in its own Colab session.
- **Matched by request.** Every request has a key, a hash of its role, messages and settings. A comparison script
  matches the calls by key and compares the replies byte for byte. When bytes differ, it also checks whether a verdict
  changed.

## The result

![Share of matched calls that came back byte-identical, by comparison](/rnd/charts/issue-27-match-share.svg)

| Compared with an A100 40 GB | Calls compared | Byte-identical | Verdict changed |
|---|---|---|---|
| A second A100 40 GB VM | 176 | 176 | 0 |
| A third A100 40 GB VM (stopped partway) | 72 | 72 | 0 |
| A100 80 GB, same server build | 178 | 178 | 0 |
| RTX PRO 6000 Blackwell, its own build | 178 | 113 | 65 |

178 calls cover 176 distinct requests; two were sent twice, identically.

The critic's second task, voting on flaws, agreed on 101 of 101 calls across two A100 VMs. The three writer requests
that diverged in the first test now match too, which shows the seed fix working where the bug appeared.

**On the A100, the answer is yes.** Three separate VMs gave the same bytes on every call they shared. So did an A100
with 80 GB of memory instead of 40, on the same server build.

**The Blackwell card is different.** The RTX PRO 6000 needs its own build of the server, compiled for its newer
architecture. On that build, 65 of the 178 replies changed, and every one of those 65 changed a verdict, not just
some wording. Because both the card and the build differ, this run can't say which one is responsible. The 80 GB A100
does rule out one explanation: the amount of memory doesn't matter. In practice we keep the two apart. Results from
the Blackwell card are never pooled with the A100's.

## Is a faster card worth it?

The two other cards cost more per hour. Here's what that bought, over the same 178 requests:

| | A100 40 GB | A100 80 GB | RTX PRO 6000 |
|---|---|---|---|
| Price per hour, vs the A100 40 GB | 1.00× | 1.28× | 1.68× |
| Speed reading the prompt | 1.00× | 1.01× | 3.06× |
| Speed writing the reply | 1.00× | 1.11× | 1.32× |
| Total model time | 11,118 s | 10,046 s | 8,350 s |
| **Cost per request, vs the A100 40 GB** | **1.00×** | **about 1.15×** | **about 1.26×** |

A critic reads a long prompt and writes a short reply, one request at a time, so most of its time goes to writing. The
Blackwell card reads prompts three times as fast, but writes only a third faster, so for this job it costs about a
quarter more per request. It would pay off on jobs that read far more than they write, on large batches, or on models
too big for 80 GB. The 80 GB A100 is worth its price only when a job needs the memory.

## The same pattern in a second study

The same day, a separate benchmark ran a 30-item judging task through Ollama, a different model server, with Gemma 4
31B. It had already been run twice on the studio's own RTX 5090. We ran it on two Colab A100 VMs:

| | 5090 vs 5090 | A100 vs A100 | A100 vs 5090 |
|---|---|---|---|
| Items with any difference | 0 of 30 | 0 of 30 | 16 of 30 |
| Final verdict differs | 0 | 0 | 1 |

Again, the same card gives the same answer, and a different card mostly changes the wording. Of the 16 items that
differed, 15 differed only in the model's reasoning. The one changed verdict was an item where the 5090 ran out of room
mid-answer and Colab finished it.

The earlier run of this benchmark found the one thing that broke reproducibility **on the same card**: running two
requests at once. Two requests decoding together go through batched arithmetic, which changed 1 verdict, 2 quoted
passages and 15 of 30 reasoning texts. Every pinned study now runs one request at a time.

That run also hit a quieter problem. The model's public tag, `gemma4:31b`, had been republished as a different build,
with different weights. The first paid attempt stopped at a guard that refuses any model whose digest doesn't match the
pinned one, before any call was made. The fix installs the pinned build from its manifest, file by file, and checks
every file's hash.

## Three VMs lost, and what the logs kept

Colab can take back a VM at any time. Three of the six long A100 sessions in this study were lost: one after 1 h 16 m,
one after 1 h 30 m, and one after 3 h 16 m. Each loss happened while 3–4 of our sessions were
running at once. Three losses are too few to name a cause, so we've recorded them and left them unexplained.

As each call finishes, the job writes its record into the job's log, and the rig downloads that log from the VM every
2 minutes while the job runs. When a VM is lost, the rig keeps its last copy, at most about 2 minutes behind. What the
log held was rebuilt; on one lost VM it stopped two calls short of the end. The log can't show whether those two calls
ran before the VM was lost. To check the rebuild, we ran it on a session
that closed normally, and it matched the official records on 178 of 178 rows. What a lost VM still costs is the timing
log and the session's own summary. Writing those into the log the same way is next on the list.

## What it cost

Colab bills in compute units. The A100 40 GB costs about 5.3 units an hour.

| | Units |
|---|---|
| Reproducibility study: 12 GPU sessions, including the three lost VMs, the first test and the bug's halted session | 112.93 |
| Its CPU test runs | 0.13 |
| Second benchmark: 5 GPU sessions, including two lost to a missing unpack tool and the guard's stop | 7.85 |

Every figure was reconciled against our units ledger.

## Where things stand

- **Pinned studies on Colab run on A100s,** one request at a time, with the seed passed through and the cache off.
  40 GB and 80 GB results can be pooled.
- **Other cards are their own baseline.** Results from the RTX PRO 6000 or the local 5090 are reported separately,
  never pooled with the A100's.
- **The cause on the Blackwell card is still open:** the card, its build, or both. Separating them would need a second
  build on the Blackwell card.
- **The full write-ups** are in rnd: [the reproducibility study](https://github.com/mcp-tool-shop-org/rnd/blob/main/experiments/stage1-regeneration/colab-drift/RESULTS.md)
  and [the benchmark](https://github.com/mcp-tool-shop-org/rnd/blob/main/experiments/offrig-jobs/results/RESULTS.md).
