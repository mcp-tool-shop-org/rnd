---
title: "9 November: the guard that cried wolf"
description: "aspire-si's training run stopped two of its three seeds on a guard that, measured afterwards, fires on a healthy run 81% of the time. The fix is a new, pre-registered series. Also: why our own inference server gave two different answers to the same question, a judge result re-checked with its cache switched off, a CI image that changed under us, and the week's watch."
issue: 41
date: 2026-11-09
highlights:
  - "<strong>A guard that cried wolf.</strong> aspire-si's S2 run stopped seeds 42 and 44 on its U2 guard. Measured on all three seeds, that guard would stop a healthy run 81% of the time. Running both seeds on with the guard set to monitor only showed nothing wrong."
  - "<strong>Same server, same question, two answers.</strong> Our inference server gave different log-probabilities on 45 of 50 prompts when asked twice. The cause was its prompt cache. With the cache off, 401 of 401 repeat readings matched to the last bit."
  - "<strong>A judge result re-checked.</strong> Our reference judge's 145 of 149 stands exactly with the cache off. A second, larger judge moves by up to 5 pairs, and its row now says so."
---

A Monday of second looks. A guard that stopped two training runs turned out to be stopping healthy ones. A server
we trusted to repeat itself didn't, until we found out why. A published result got re-checked with that in mind.
Then the week's watch.

**In this issue:**

1. [The guard that cried wolf](#the-guard-that-cried-wolf)
2. [Same server, same question, two answers](#same-server-same-question-two-answers)
3. [A judge result, re-checked](#a-judge-result-re-checked)
4. [A CI image that changed under us](#a-ci-image-that-changed-under-us)
5. [The weekly watch](#the-weekly-watch)

## The guard that cried wolf

[aspire-si](https://github.com/mcp-tool-shop-org/aspire-si)'s S2 run trains a small model by reinforcement learning on
our local RTX 5090 ([issue 40](/rnd/newsletter/issue-40/) left seed 42 at 120 of 197 updates). Before it started, we
**pre-registered** it: we wrote down, in advance, what would be measured, what counts as success, and which guards stop
the run, so the result can't be reshaped afterwards.

The registered result is now in, and it is reported exactly as registered:

| Seed | Outcome |
|---|---|
| 42 | stopped by the U2 guard at update 139 |
| 43 | completed all 197 updates |
| 44 | stopped by the U2 guard at update 69 |

**What U2 watches.** A training run can learn a shortcut: answers that score well while being wrong. U2 is one of the
guards for that. It counts warning events in each window of training and stops the run when they arrive too often.

**What we found when we measured the guard itself.** Across the three seeds, the warning event U2 counts happened 19
times in 41 windows, about 0.46 per window. At that rate, U2's rule would stop a perfectly healthy run within 20
windows **81% of the time**. The guard was mostly measuring its own noise.

**Checking that, rather than assuming it.** We ran seeds 42 and 44 on for 30 more updates each, with U2 set to
monitor only (still counting, but unable to stop the run). These runs are **exploratory**: they don't count toward the registered result. If
something had really been going wrong, these windows would have shown it. Neither did: U2's rule never triggered again
in either run. Both stops look like false alarms.

**What happens now.** The registered result stands as it is. Two halts are two halts. The fix is a new series, S2 v1.1,
pre-registered before it runs and never pooled with seeds 42–44:
- the warning guards now use a **CUSUM**, a running total that only rises when events come faster than the measured
  normal rate, with limits set from the 41 measured windows;
- a guard trip no longer stops the run on its own: it first gets a confirmation pass with the sampling randomness
  turned off, on a fixed set of 128 or 184 questions depending on the guard, and only a confirmed trip stops it;
- seeds 45, 46 and 47 run the new series.

The v1.1 trainer is merged ([aspire-si #196](https://github.com/mcp-tool-shop-org/aspire-si/pull/196)). The script that
runs it is in its final review. Reviews overnight caught two ways it would have stopped a healthy run: it
looked for old names of the warning measures, and it treated a correctly recorded "stop for review" as a broken chunk. No GPU time is booked until that is fixed.

## Same server, same question, two answers

We run local models through [Ollama](https://github.com/ollama/ollama), and many of our experiments read the model's
**log-probabilities**: how likely it thought each possible next word was. For those to mean anything, asking the same
question twice must give the same numbers.

We had built our own version of Ollama's GPU backend against CUDA 13.5, and needed to show it was equivalent to the
stock one before switching. The first step of that test was simply to ask stock Ollama the same 50 questions twice,
on the same server. **On 45 of the 50, the answers' log-probabilities differed**, by up to 0.61 in the units we
measure (nats). On a few, the most likely next word itself changed.

**Why.** We asked Gemini's Deep Research what changes a running server's arithmetic, then checked its answer in Ollama's
and llama.cpp's source. Two caches are on by default:
- the server reuses the start of the previous prompt when the next one begins the same way, and every one of ours begins
  with the same chat template;
- it also keeps recent prompts in an 8 GB memory cache.

So on the second pass, each question started from a different cached point. That meant the graphics card processed a
different number of words at once. Different batch sizes run different internal routines, which add numbers up in a
different order, and in floating point, (a + b) + c isn't always exactly a + (b + c).

**The test, rebuilt.** With both caches off, and the server cleared before every question, we read each of 401
fixed prompts twice: once in order, once shuffled. **All 401 matched to the last bit.** Only then did we compare the two
builds:

| Check | Result |
|---|---|
| Same build, asked twice (caches off) | 401 of 401 identical |
| Difference between stock and ours (KL divergence, average) | 0.0005 nats (limit 0.003) |
| Most likely next word changed | 1 of 401, where the top two were nearly tied |
| Speed, ours against stock, same settings | 0.987× |

Our build passed, and the studio's machine now runs it. One honest note: with matching settings it is about 1% slower,
not faster. The reason to switch is that it is built on the CUDA version the rest of our stack uses.

The lesson for anyone comparing model outputs on a long-running server: **turn the prompt cache off, or start a fresh
server for each pass**, and check that a run repeated twice matches before you trust any difference.

## A judge result, re-checked

That finding raised a question about our own published work. In October,
[aspire-si's judge confirmation](https://github.com/mcp-tool-shop-org/aspire-si/blob/main/docs/runs/2026-10-08-kev-confirmation.md)
scored 149 pairs of answers, each pair in both orders, on one running server. The second order of every pair shares a
long question with the first, so it could have reused the first one's cache. That could look like a preference for
whichever answer comes second.

We re-ran both judges with the cache on and off:
- **Kev-4B, the reference judge: unchanged.** All 298 readings were identical with the cache on or off, and identical to
  October's. Its result, 145 of 149, stands.
- **Qwen2.5-32B, a second judge we reported alongside it: sensitive.** With the cache on versus off, 6 pairs changed
  their verdict and single readings moved by up to 0.24. Across three runs its count ranges from 132 to 137 of 149.

The October report now carries a dated note saying so
([aspire-si #197](https://github.com/mcp-tool-shop-org/aspire-si/pull/197)). None of its conclusions change, and from
now on our judging runs switch the cache off and record that they did.

## A CI image that changed under us

GitHub's `ubuntu-latest` label, which most of our automated builds run on, now means **Ubuntu 26.04**. We noticed it in
a build log today, not in an announcement we follow.

That matters for anything we build there and ship as a program people run on Linux. A program compiled on a newer
system can ask for a newer version of the system's core library than an older machine has, and then refuse to start.
Eleven of our repositories ship such a Linux build.

One had already shipped since the change: escape-the-valley 1.3.3, built on 26.04. We unpacked it and checked every one of
its 44 bundled libraries. The newest core-library version any of them needs is 2.17, from 2012, so it runs on older
systems. It's fine, but only because of how its Python was packaged. A part compiled on the new image could
have needed up to 2.43, the version 26.04 ships, and nothing would have warned us.

Linux release builds will move into an Ubuntu 22.04 container, with a check that fails the build if any shipped file
needs more than 22.04 provides. The first change is queued, and we're making it repository by repository as we work in
each one.

## The weekly watch

Every Monday we check our fixed list of sources: NVIDIA, CUDA, Ollama, llama.cpp, OpenVINO, PyTorch, ComfyUI, NeMo
Relay, PAIR, Holoscan, Claude Code and Docker. The week of 2 to 8 November turned up 76 new items across those
sources. Release notes below were read at the source.

### What we acted on

- **Ollama 0.40.14 and 0.40.15** (3 November). We moved to 0.40.15 with the build tested above. One quiet change
  in 0.40.14: Ollama's OpenAI-compatible endpoints now use **a model's own default sampling settings** when a request
  doesn't set `temperature` or `top_p`, instead of 1.0. We checked our code: one client, in
  [offrig](https://github.com/mcp-tool-shop-org/offrig), sends neither. It talks to a pinned older Ollama today, and a change to set both
  explicitly is planned. ([0.40.14 release notes](https://github.com/ollama/ollama/releases/tag/v0.40.14))
- **The Ubuntu 26.04 build image**, covered above.

### Worth knowing

- **Claude Code 2.1.317 to 2.1.319.** More cases where a headless `claude -p` run now exits with an error, and a new
  `permissions.denyInsteadOfPrompting` setting. Our one harness that drives the CLI pins an earlier version and reads
  each run's outcome from its result rather than its exit code, so this is filed for the day that pin moves.
  ([Claude Code releases](https://github.com/anthropics/claude-code/releases))
- **llama.cpp** shipped builds through b12211 in the week. One change on 8 November removed `clip.h` and merged
  the multimodal code into `mtmd` ([#31865](https://github.com/ggml-org/llama.cpp/pull/31865)), which matters the next
  time we rebuild Ollama's backend against a newer llama.cpp.
- **llama.cpp, a determinism fix** (8 November, build b12208): on CUDA, the routine that picks the top few candidate
  tokens now settles ties the same way every time
  ([#31084](https://github.com/ggml-org/llama.cpp/pull/31084)). It's the same family of problem as the cache story
  above: results that should repeat, and didn't always.
- **ComfyUI 0.44.0** (4 November) adds a node to set the image decoder's compute precision, and new targets for the
  Flux video upscale node. ([release notes](https://github.com/Comfy-Org/ComfyUI/releases/tag/v0.44.0))
- **Docker Engine 29.9.3** (3 November) is a security release, including fixes for a possible CPU exhaustion on crafted
  RSA keys and a possible crash when decompressing zstd data.
  ([release notes](https://github.com/moby/moby/releases/tag/docker-v29.9.3))
- **CVE-2026-43632**, an older llama-server vulnerability (published in August), is still worth a line: it only bites
  when the server's idle-sleep option is switched on. We checked: none of our servers set it, and they listen only on
  the local machine.

Nothing new this week from PyTorch, OpenVINO, NeMo Relay, PAIR, Docker Desktop, Docker Sandboxes or Docker Model
Runner.

**Since Friday (7 to 9 November):** a quiet weekend. Of our watched projects, only llama.cpp shipped, with 29 routine
builds (b12182 to b12220), including the determinism fix above. There were no new releases of Ollama, ComfyUI,
Claude Code, PyTorch, transformers, TRL, OpenVINO, NeMo Relay, PAIR, Holoscan, Docker Engine or Docker Model Runner.

One thing to watch if you run ComfyUI 0.44 on Windows: users have opened several crash and slowdown reports since
that release, all still unconfirmed by the maintainers. Two point at its dynamic video-memory manager (comfy-aimdo
0.6.0) on RTX 50-series cards: a hard crash inside `aimdo.dll` during video generation
([#17606](https://github.com/Comfy-Org/ComfyUI/issues/17606), 8 November) and system-wide stutter that wasn't there
on 0.42 ([#17578](https://github.com/Comfy-Org/ComfyUI/issues/17578)). A third, on an RTX 4060 Ti, crashes on the
second prompt with dynamic memory on ([#17609](https://github.com/Comfy-Org/ComfyUI/issues/17609)). Our own image
machine runs an older ComfyUI (0.23, with comfy-aimdo 0.4.7), so we haven't hit these, but they're worth reading
before an upgrade.

**How the watch works.** A script lists every new item from our sources; a research agent and Gemini's Deep Research
each read the week; R&D and the Publisher check what matters against the release notes themselves. This week that
check mattered: one research report placed a known CUDA bug on the wrong version, and wrote a section about actions we
had "taken" that we hadn't. Neither appears here.
