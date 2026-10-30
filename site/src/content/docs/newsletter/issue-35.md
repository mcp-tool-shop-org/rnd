---
title: '30 October: a leak check that cried wolf, a perfect score on long tool lists, and Cosmos 3 on one card'
description: "Our check for shortcuts in the judge bake-off's test sets was failing sets that had none; a calibrated rule now false-fails at most 0.5% of them, says plainly how small a leak it can see, and passes the repaired pilot set. Gemma 4 31B made no mistakes on tool lists from 5 to 100, which also means this test can't find its limit. All four Cosmos 3 versions for the next comparison ran on one rented B200. Then notes in brief and the daily watch."
issue: 35
date: 2026-10-30
highlights:
  - "<strong>A leak check that cried wolf.</strong> The old 5-point rule failed 80% to 98.5% of test sets with no shortcut at all. The calibrated rule fails at most 0.5%, still catches all twelve planted leaks, and at 38 triads screens out only leaks above about 23 points."
  - "<strong>Gemma 4 31B: 170 of 170, 30 of 30.</strong> No mistakes on tool lists from 5 to 100, in all 12 conditions. Granite 4.2 8B is still the only model whose \"no\" slipped."
  - "<strong>Cosmos 3, four versions on one card.</strong> 144 clips on one rented B200, 36 per version, for a comparison by people that is still being designed. An operations note, not a quality result."
  - "<strong>A small model on one TPU chip.</strong> int8 weights moved the loss by 0.0005, but changed the generated text on three of four prompts."
---

Results from 29 and 30 October: the check that guards our judge bake-off against shortcuts, recalibrated, and the
last model in the long tool-list test. Then notes in brief, including all four Cosmos 3 versions on one card and a
small language model on a Google TPU chip, and the daily watch.

**In this issue:**

1. [Gemma 4 31B and the long tool list](#gemma-4-31b-and-the-long-tool-list-a-perfect-score-and-what-it-cant-tell-us)
2. [A leak check that cried wolf, recalibrated](#a-leak-check-that-cried-wolf-recalibrated)
3. [In brief](#in-brief)
4. [The daily watch](#the-daily-watch)

## Gemma 4 31B and the long tool list: a perfect score, and what it can't tell us

[Issue 34](/rnd/newsletter/issue-34/#how-many-tools-can-a-local-model-take-the-list-held-the-no-slipped) tested how
local models cope as their list of tools grows from 5 to 100. Two models had finished, and the third, Gemma 4 31B, was
still running. It has now finished, and it made no mistakes.

- **Picking the right tool:** 170 of 170 in all 12 conditions, from 5 tools to 100, with the narrowed "compass" lists,
  and with the padded 10-tool prompt that matches the length of the longest list.
- **Saying no when no tool fits:** 30 of 30 in every condition. Against the 10-tool baseline, no condition lost or
  gained a single "no".
- The run was 2,400 calls in two halves on an A100 at Q8_0.

**The comparison is unchanged.** Granite 4.2 8B is still the only one of the three models whose "no" slipped. Two
drops hold up after correcting for the number of comparisons: 19 of 30 at 40 tools, and 18 on the padded prompt. Its
22 of 30 at 70 tools doesn't. Qwen3.8-27B's lowest was 27 of 30 at 70 tools, which isn't a significant drop.

**What a perfect score can't tell us.** With every condition at 30 of 30, Gemma is at the ceiling of this test. The
result shows no cliff up to 100 tools for Gemma on these items. It can't show that Gemma is better than a model that
would also score perfectly, or where Gemma's own limit is. Finding that takes a harder set of items.

**How the run went.** One half lost its Colab machine 1,083 calls in. The copy-back step we added this week had saved
1,064 of them, so a 28-minute resume made only the 124 missing calls. The reused lines are byte-identical to the saved
copy. The three windows cost 34.56 Colab compute units: 17.00 and 15.12 for the two halves (the second is the one that
lost its machine), and 2.44 for the resume.

![Tool lists from 5 to 100 across all three model families. Picking the right tool on 170 calls per cell held flat at 0.965 to 1.00: Granite 4.2 8B 164 to 170 of 170, Qwen3.8-27B 169 to 170, and Gemma 4 31B 170 of 170 in all 12 cells. Declining on 30 no-tool requests per cell, plotted against Granite's prompt length in tokens with Wilson 95% intervals and no trend line: at 5 tools (1,004 tokens) Granite 28/30 (.79-.98), Qwen 30/30 (.89-1.0), Gemma 30/30 (.89-1.0); at 10 tools (1,737 tokens) Granite 29/30 (.83-.99), Qwen 30/30 (.89-1.0), Gemma 30/30 (.89-1.0); at 20 tools (3,184 tokens) Granite 26/30 (.70-.95), Qwen 30/30 (.89-1.0), Gemma 30/30 (.89-1.0); at 40 tools (6,108 tokens) Granite 19/30 (.46-.78), Qwen 29/30 (.83-.99), Gemma 30/30 (.89-1.0); at 70 tools (10,457 tokens) Granite 22/30 (.56-.86), Qwen 27/30 (.74-.97), Gemma 30/30 (.89-1.0); on the 10-tool prompt padded to 100-tool length (13,270 tokens) Granite 18/30 (.42-.75), Qwen 29/30 (.83-.99), Gemma 30/30 (.89-1.0); at 100 tools (14,804 tokens) Granite 27/30 (.74-.97), Qwen 28/30 (.79-.98), Gemma 30/30 (.89-1.0); and with the retriever's top-5 (~1,040 tokens) Granite 27 to 30/30 (.74-1.0), Qwen 29 to 30/30 (.83-1.0), Gemma 30/30 (.89-1.0). Paired against 10 tools, Granite drops at 40 tools (p=0.002, Holm 0.02), padded 10 (p=0.001, Holm 0.011), and 70 tools before correction (p=0.039, Holm 0.35, not significant); Qwen stays at or above 27/30 (p>=0.25); and Gemma is at the 30/30 design ceiling in all 12 cells (0 lost or gained, all p=1.0), where the test cannot go higher or separate a stronger model.](/rnd/charts/issue-35-tool-count-abstention-v2.svg)


## A leak check that cried wolf, recalibrated

We're building a bake-off for small "judge" models. Each item gives a judge a short table of facts and a claim, and the
judge says whether the table supports the claim, contradicts it, or doesn't say. Items come in sets of three built from
one table, one claim of each kind, and code, not a model, decides each answer. Before any judge sees a set, a check runs
on it: can a simple classifier guess the answer from surface features alone, such as the claim's length or how many of
its words appear in the table? If it can, a judge could score well by spotting the shortcut instead of reading the
table.

**The check kept failing sets that had no shortcut.** It used to fail any feature that beat chance by more than 5
points. At the size of our pilot sets (34 to 40 triads), 5 points is less than one standard error, so chance alone
crosses it most of the time. When we shuffled the answers within each triad, so that no feature could carry a real
signal, the old rule still failed between 80% and 98.5% of those sets, depending on the setup.

**The new rule** counts each triad as one sample, since its three items share a table. It asks whether chance lies
inside a Wilson interval (Wilson, 1927) widened for the number of features tested at once with the Holm correction
(Holm, 1979). The rule was chosen on the shuffled sets and on twelve planted leaks (one of them a copy of the leak from our
first pilot set) before it ran on the rebuilt pilot set, and it isn't tuned on that set:
- on the shuffled sets it failed at most 0.5% of the time, and an independent re-run with two more random seeds failed 0 of
  200 and 0 of 200;
- all twelve planted leaks still fail it, including a copy of the leak we found in our first pilot set.

**What a pass is worth.** A wider interval lets a smaller leak slip through. At 38 triads, the smallest leak in a
single feature that the check can detect is about 23 points. Catching a 14-point leak needs about 105 triads, and a
7-point leak about 419. Every report now prints these figures, and a pass at pilot size is reported as a coarse
screen, not a clean bill.

**The leak it has to catch.** In our first pilot set, the claims that weren't supported tended to use values that
never appeared in the table, so word overlap alone beat chance by 13.7 points on "supported or not" and by 7.8 points
on the three-way answer. That set stays failed on the record. The repair gives every claim a value that does appear in
the table, so an unsupported or undecidable claim points at a real value from the wrong place. On the rebuilt pilot
set of 38 triads, the claimed value appears in the table for all three kinds of claim, the overlap feature beats
chance by 1.8 points on the three-way answer and 0.0 on "supported or not", the three kinds stay at exactly a third
each, and the set passes. That clears it for a small judge pilot, which hasn't run yet. It isn't a finding about any
judge.

The rule, its calibration tables and the tests are public in
[reasoning-dataset-lab](https://github.com/mcp-tool-shop-org/reasoning-dataset-lab/blob/main/docs/shortcut-probe-gate.md).

## In brief

**Cosmos 3: all four versions on one card.** The comparison of shrunk Cosmos 3 versions in
[issue 34](/rnd/newsletter/issue-34/#super-shrunk-to-fit-one-card) was corrected on 30 October: three of its eight
prompts ask for more than a 2.5-second clip can show. For the next comparison, all four versions under test made
their clips on one rented NVIDIA B200, the same physical card for every clip, at 480p, 61 frames and 35 steps. Each
version made 36 of 36 clips, 144 in all, and every file's checksum verified:

| Version | Mean time a clip | Peak GPU memory |
|---|---|---|
| Super, full precision (BF16) | 39.0 s | 129,207 MiB |
| Super, FP8 | 58.0 s | 69,974 MiB |
| Super, Intel's int4 | 42.9 s | 39,600 MiB |
| Nano, full precision | 12.3 s | 36,027 MiB |

The pod was billed $16.95 from launch to shutdown, setup and teardown included, and an earlier timing probe on another B200 cost $1.64, $18.59 in all. This is an operations note. The clips for a blind comparison by people now all come from one card and one
run, so differences between versions can't come from the hardware. It says nothing about which version looks better;
that comparison is still being designed.

**A golden path for Colab, on any plan.** The handbook has a new page:
[Colab golden path, for any plan](/rnd/handbook/colab-golden-path/). It is the way we run paid GPU jobs on Google
Colab without surprises:
- a "window" is one session, one job, a spending cap and a time limit;
- eight steps, with a CPU test run on the exact path before any paid card opens;
- the guards, each tied to the run that proved it;
- a worked example that cost under two hundredths of a unit.

It has one version of the path for each Colab plan, from Free to the top tier. Google's own statements are kept apart
from what we measured. It also has a guard we learned this week: a session that fails to open on your side may still
be billing on Google's.

**interlock's model manager, on a real engine for the first time.** interlock is our tool for loading local models
and measuring them. Version 1.0.11 manages a model's load, reloads and unload itself, and it has now run against a
real Ollama engine: Qwen3 8B on a 16 GB Colab T4, over 21 cells of prompt length (up to 32k tokens) and concurrent
requests (1, 4 and 8). All four acceptance checks held: the model really sat on the GPU, every loaded row recorded
how it was loaded, each reload for a bigger context fell outside the timed part of a cell, and the model was unloaded
at the end. 16 of the 21 cells ran clean, and 4 ran out of GPU memory at 4 or 8 concurrent requests. The largest, 32k
tokens at 8 at once, was refused before loading because interlock projected it would need 29,599 MiB of host
memory against a limit of 12,954 MiB. Refusing before trying is the behaviour we were testing. This was a functional test on
one card and one model, not a speed benchmark. The 37-minute window cost 0.66 Colab compute units.

**A small language model on one Google TPU chip, and an int8 result a loss check would miss.** We ran
[cataluna84/nanogpt-jax-181m](https://huggingface.co/cataluna84/nanogpt-jax-181m) (Apache-2.0), a 181M-parameter nanoGPT model written in JAX, on a single Colab TPU v5e chip in two short windows (17 and 10 minutes).
The published checkpoint restored and scored a validation loss of 3.1259 against its card's 3.1271, and the second
window reproduced it to the last digit. Training ran at 38,981 tokens a second, 1.10 times the card's own per-chip
figure. Generating 256 tokens after a 1,792-token prompt ran at:

| | 1 at a time | 8 at once |
|---|---|---|
| bf16 | 1,148 tokens/s | 5,015 tokens/s |
| int8 weights | 1,383 tokens/s | 5,686 tokens/s |

Storing the weights as int8 moved the loss by only +0.0005, measured on a fixed 100 of the 800 validation batches. The
generated text is another matter: with greedy decoding, int8 matched bf16 on 67% of tokens, and only 1 of 4 prompts
came out identical; the other three changed after 25 to 45 tokens. A loss check alone would call int8 lossless here.
Four prompts are far too few to give a rate, so this is a reason to check generated text, not a measure of how often
int8 changes it. The two windows cost 1.28 Colab compute units.

## The daily watch

3 new since [issue 34](/rnd/newsletter/issue-34/).

- **Holoscan SDK 5.0.0** (2026-10-21): NVIDIA's SDK for streaming sensor pipelines is rewritten from the runtime up, with typed operators and ports, timing contracts checked when the graph compiles, and HoloMQ, a zero-copy transport for GPU data between processes; Vision, Visualization and Inference now install as separate pip packages. Breaking: it requires CUDA 13, drops IGX Orin and JetPack 6, and removes or renames several APIs with no compatibility shim. Worth reading before any robotics pipeline work. It came out before issue 34, but our watch missed it because the project wasn't on our list ([release notes](https://github.com/nvidia-holoscan/holoscan-sdk/releases/tag/v5.0.0)).
- **Claude Code 2.1.314** (2026-10-30): `claude -p` now prints the error and exits with code 1 when startup fails, where it used to exit 0 with no output, so scripts that call it can see the failure. A new `permissions.blockWritesOutsideWorkingDirectories` setting makes the write and edit tools refuse paths outside the working directories in every permission mode ([release notes](https://github.com/anthropics/claude-code/releases/tag/v2.1.314)).
- **NVIDIA gds-diag** (2026-10-30): an open-source command-line tool that checks whether a machine is set up for GPUDirect Storage, which moves data between storage and GPU memory without a copy through the CPU. It comes with an agent skill ([NVIDIA blog post](https://developer.nvidia.com/blog/how-to-check-and-configure-nvidia-gpudirect-storage-for-your-platform/)).
