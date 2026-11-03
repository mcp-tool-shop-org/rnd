---
title: "3 November: taking the judge test to a rented GPU, and the daily watch"
description: "The launcher that carries our judge bake-off to a rented Colab GPU ran the whole path on a CPU machine, and its first GPU run stopped twice at the start, cheaply: once on a connection timeout, then, in 14 seconds, by the launcher's own check when the machine's tools didn't match the pin. No judge has been scored. Then the daily watch: five new items, including Ollama's sampler defaults and the Gemini 2.5 deprecations."
issue: 37
date: 2026-11-03
highlights:
  - "<strong>The whole path, on a CPU machine.</strong> Four calls on two practice items, all four replies parsed, 806 seconds, 0.018 Colab units. The model loads lazily: about 1 GB at the load step, about 7 GB during the first call."
  - "<strong>A drifted machine, stopped by name.</strong> The first GPU machine shipped an older uv that can't install the pinned Python, and the launcher refused in 14 seconds before building anything."
  - "<strong>The daily watch.</strong> Ollama 0.40.14 stops overriding a model's own sampler defaults, and Gemini 2.5 Pro and Flash route to newer models from 1 December."
---

A plumbing day: the launcher that will run our judge bake-off on a rented GPU, tested end to end on a CPU machine and
stopped twice at the start on its first GPU machine: once on a connection timeout, once by its own check. Then the daily watch.

**In this issue:**

1. [Taking the judge test to a rented GPU](#taking-the-judge-test-to-a-rented-gpu-the-path-works-and-the-gate-stops-a-drifted-machine)
2. [The daily watch](#the-daily-watch)

## Taking the judge test to a rented GPU: the path works, and the gate stops a drifted machine

Our judge bake-off compares small models that check whether a claim is supported by a passage. Its timing and counted
runs need a datacentre GPU, so we've built a launcher that carries the test to a rented Colab machine, checks the
machine before anything runs, and brings the records back. This is about that launcher only: no judge has been
scored, nothing here ranks one, and none of it touches the test's pre-registered rules.

**On a CPU machine, the whole path works.** The launcher ran one small judge model on a 2-CPU Colab machine through
the same path a real run takes: download, checks, its own locked environment, then four calls on two practice items.
All four calls finished and all four replies parsed. The run took 806 seconds and cost 0.018 Colab units. Each call
took 116 to 127 seconds for prompts of 169 to 178 tokens; on two CPUs that time is almost all prompt processing, so
it measures the path, not how fast a judge is.

One thing we learned from it: the model loads lazily. Memory stood at about 1 GB when the load step reported done, and
reached about 7 GB during the first call. A load timer on its own would understate the load, so the timing run counts
it as the load step plus the first call's extra time over the median call.

**On the first GPU machine, the run stopped twice at the start, both times cheaply: the first on a connection
timeout, the second by the launcher's own check, as designed.** Both stops together cost 0.41 units.
1. The command-line tool lost its connection to the machine on its first command, before anything ran there. Its
   default wait for that connection is 10 seconds. Our earlier launchers already set a longer one, and this one now
   does too.
2. With that fixed, the launcher's check ran and refused in 14 seconds, naming the cause. The GPU machine came with an
   older version of the uv package manager (0.13.4) than every CPU machine so far (0.13.5), and only the newer one
   can install the exact Python build the test is pinned to (CPython 3.15.1, first offered in uv 0.13.5). The launcher stopped before building anything, rather than
   run on a different Python whose results wouldn't compare with the CPU runs. The fix, which brings its own pinned
   copy of uv and checks its size and checksum before unpacking it, is still being built (PR #61, open).

No GPU timing exists yet; that comes from the next window.

## The daily watch

5 new since [issue 36](/rnd/newsletter/issue-36/).

- **Ollama v0.40.14** (2026-11-03): the OpenAI-compatible endpoints no longer override a model's packaged sampler defaults, so a request that sends no `temperature` or `top_p` now gets the model's own values instead of 1.0, as `/api/chat` already did. Scripts that relied on the old 1.0 will see different output ([release notes](https://github.com/ollama/ollama/releases/tag/v0.40.14)).
- **Claude Code 2.1.317** (2026-11-03): Agent SDK hook callbacks can set `onFailure: "block"`, so a callback that fails blocks the action instead of letting it run; a new check asks before a web or shell tool call sends the account email address to the network; and `CLAUDE_CODE_DISABLE_NESTED_SESSION_ID=1` restores the earlier session behaviour for `claude -p` runs inside a session ([release notes](https://github.com/anthropics/claude-code/releases/tag/v2.1.317)).
- **cosmos-xenna v0.5.13** (2026-11-02): NVIDIA's pipeline library stops removing logging sinks the host application added, writes to the current stderr, and no longer forces colours in CI or Jupyter ([release notes](https://github.com/nvidia-cosmos/cosmos-xenna/releases/tag/v0.5.13)).
- **Build world models for interactive simulation with NVIDIA Cosmos** (NVIDIA, 2026-11-02): recipes for synchronized camera and LiDAR simulation data with Cosmos 3 Nano, deploying Cosmos as a NIM microservice, and a table of GPU memory needs for Cosmos 3 Nano and Super. Its summary and its table disagree on one memory figure, so read the table ([the post](https://developer.nvidia.com/blog/build-world-models-for-interactive-simulation-with-nvidia-cosmos/)).
- **Gemini API: 2.5 Pro and 2.5 Flash deprecated** (2026-11-02): from 1 December, requests to `gemini-2.5-pro` route to `gemini-3.8-flash` and requests to `gemini-2.5-flash` route to `gemini-3.5-flash-lite`, each billed at the new model's rates. Breaking: `thinking_level` replaces `thinking_budget`, sampling parameters are removed, prefilled model turns are no longer supported, and `thought_signature` validation changes ([changelog](https://aistudio.google.com/docs/changelog)).
