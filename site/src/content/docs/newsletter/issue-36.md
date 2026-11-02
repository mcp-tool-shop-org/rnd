---
title: "2 November: a coverage figure left to chance, three CI races fixed, and the week's watch"
description: "Our dataset lab's tests now run in parallel, and a coverage figure that moved from run to run is pinned down. role-set's tests stop failing now and then, Escape the Valley fixes two bugs, and XRPL Lab names one verify command. Then the weekly watch: 13 items from the week, grouped."
issue: 36
date: 2026-11-02
highlights:
  - "<strong>A coverage figure left to chance.</strong> Running reasoning-dataset-lab's tests in parallel exposed a 0.04-point wobble; one test drew fresh random keys each run. Fixed-input tests now pin it, and every CI leg runs well inside its limit."
  - "<strong>Three CI races, fixed at the cause.</strong> role-set's two new tests failed 20 of 20 runs before the fix and pass 20 of 20 after."
  - "<strong>The weekly watch.</strong> 13 items from the week, grouped: PyTorch 2.15.0, a known CUDA 13.4 cuBLAS bug on Blackwell, with a fix awaited before we move more work to 13.4, NeMo Relay 0.11.0 and more."
---

Results and fixes from 30 October to 2 November, then the weekly watch: everything new on the sources we follow this
week, grouped in one place.

**In this issue:**

1. [In brief](#in-brief)
2. [The weekly watch](#the-weekly-watch)

## In brief

**The judge bake-off's first shakedown.** Following on from issue 35's leak check: three of four small judges scored
at or near ceiling on a first shakedown set whose supported claims were same-line lookups; the test needs harder items
before it can rank them.

**A green run by luck, closed for good.** On Friday, reasoning-dataset-lab's tests were running close to their
15-minute CI limit, so a leg could be cut off after its tests had passed; we raised the limit to 25 minutes. Over the
weekend we fixed the cause. The test legs now run in parallel, and the slowest single test, a 200-round permutation
check, runs as four parts that must add up to exactly the same result. Before the change the coverage leg took 23
minutes 40 seconds against the 25-minute limit. On 2 November's three runs on main, the slowest leg took 13 minutes 5
seconds. Running in parallel also exposed a wobble: the coverage figure moved by about 0.04 points from run to run. The
cause was one end-to-end test that draws fresh random keys on each run, so whether it reached a few lines of the
scorer was down to chance. A new set of tests with fixed inputs now reaches those lines on every run. Coverage reads
96.68%, against a floor of 90.

**role-set's CI stops failing now and then.** Three timing races made the test suite of role-set, our harness for
local-model runs, fail from time to time. Each was traced to its cause and fixed there, with no added sleeps or
retries and no loosened checks:
1. The test server for model calls counted a request as finished only after sending its reply, so a client's next
   request could arrive first and a one-at-a-time run looked like two at once. It now marks the request done before
   replying.
2. The tool-count runner wrote its call log before the matching log of generated text, so a reader could catch the
   call log one line ahead. It now writes the generated-text line first.
3. The live copy-back from a Colab session tried to process a file that didn't exist yet on the first round; it now
   waits for the next round. Its test also never produced the half-written last line it was meant to check, and now
   does.

Two new tests force the bad orderings. Both failed 20 of 20 runs before the fix and pass 20 of 20 after, and no
existing check was changed.

**Escape the Valley: two bugs fixed, and the 2.0 rewrite moves on.** In our survival game, reloading a save made on
arrival at a fork used to skip the camp stop. And when a hunting injury, a failed desperate repair or hard rationing
took a party member to zero outside the travel check, that death went unreported. Both are fixed on main: the reload
now plays out like an unbroken run, except that a save made while choosing a route reloads at the camp at that fork,
so you press Travel once more to see the routes again, at no cost in game time. Every death now names its cause in
the log. Python 1.3 is now the legacy line and gets bug fixes only; these fixes are on main, not in a release. On the
Rust 2.0 branch, the game's content is now kept as its own content set, hashed in every save and checked by a
validator; a save made under different content is refused with both hashes named.

**XRPL Lab: one way to verify.** The four older verify commands still work and still print their deprecation note,
but `xrpl-lab --help` no longer lists them; the README and handbook name `verify-artifact` only. Separately, the
suite failed before collecting a single test on the newest pytest-asyncio, which raises two new deprecation warnings
that the repo treats as errors. It's fixed, and all tests pass again.

## The weekly watch

13 items from the week of 26 October to 1 November, including those issues 33 to 35 already carried, checked
against each item's own source. Two are dated earlier but reached our watch this week.

**GPU stack**
- **PyTorch 2.15.0** (2026-10-28): CUDA 13.2 is the default wheel (13.4 alongside), `torch.compile` works on Python 3.15, and 4-bit NVFP4 decoding is faster on Blackwell GPUs. Breaking: `import torch` now runs once per process, and its distributed checkpoints won't load in 2.14 ([release notes](https://github.com/pytorch/pytorch/releases/tag/v2.15.0)).
- **CUDA 13.4, a known cuBLAS bug**: listed as a known issue in NVIDIA's CUDA 13.4 and 13.4 Update 1 notes (cuBLAS, bug 6798616), with no fix listed: grouped matrix multiplies in cuBLASLt can give incorrect results on Blackwell and Rubin GPUs. *What we're doing:* we are watching for a fix before moving any more work to 13.4 ([release notes](https://docs.nvidia.com/cuda/cuda-toolkit-release-notes/index.html)).
- **Holoscan SDK 5.0.0** (2026-10-21): NVIDIA's SDK for streaming sensor pipelines, in a ground-up rewrite of its runtime and API, with typed ports, timing contracts checked when the graph compiles, and HoloMQ for zero-copy GPU data between processes. Breaking: it requires CUDA 13, drops IGX Orin and JetPack 6, and removes or renames several APIs with no shim. We added it to our watch this week, after missing it ([release notes](https://github.com/nvidia-holoscan/holoscan-sdk/releases/tag/v5.0.0)).
- **NVIDIA gds-diag** (2026-10-30): an open-source tool that checks whether a machine is set up for GPUDirect Storage, with an agent skill ([NVIDIA blog post](https://developer.nvidia.com/blog/how-to-check-and-configure-nvidia-gpudirect-storage-for-your-platform/)).

**Runtimes**
- **llama.cpp v0.8.0** (2026-10-28): a tagged release (marked Latest) with Liquid AI's LFM3 models, `/v1/realtime` and `/tts` server endpoints, a selectable reasoning effort and Nemotron 3.5 Embed. Scripts beware: the CLI now requires `--model` or `-hf` ([release notes](https://github.com/ggml-org/llama.cpp/releases/tag/v0.8.0)).
- **Ollama v0.40.12 and v0.40.13** (2026-10-27 and 10-28): LFM3, including the speech models `lfm3-audio` and `lfm3-omni`, arrived on Apple silicon and then on Linux and Windows. Check the model's licence before building on it ([0.40.13 notes](https://github.com/ollama/ollama/releases/tag/v0.40.13)).
- **ComfyUI v0.43.0** (2026-10-27): fixes the top-p threshold and Gemma 4 31B's global attention, starts dynamic VRAM KV caches, and sets a minimum Pillow version ([release notes](https://github.com/Comfy-Org/ComfyUI/releases/tag/v0.43.0)).

**Agent tools**
- **Claude Code 2.1.311 to 2.1.316** (2026-10-26 to 10-31): in 2.1.314, `claude -p` now prints the error and exits 1 when startup fails, where it used to exit 0 with no output, and a new setting makes the write and edit tools refuse paths outside the working directories in every permission mode. Also: 2.1.311 stops `claude -p` transcripts saving messages out of order, and in 2.1.316 PowerShell hooks block on exit code 2 in more cases and fast mode for Opus 4.8 is deprecated, going on 30 November ([2.1.314 notes](https://github.com/anthropics/claude-code/releases/tag/v2.1.314)).
- **NeMo Relay 0.11.0** (2026-10-28): the agent-tracing tool's coding-agent hooks now verify TLS, fail closed by default, and return exit code 2 when they can't deliver, which can stop an agent mid-task. Breaking: it needs Node.js 24.13.1 or later ([release notes](https://github.com/NVIDIA/NeMo-Relay/releases/tag/0.11.0)).
- **NVIDIA skills catalogue** (2026-10-26 to 10-29): new skill sets for DGX Spark, NeMo Fabric, a Nemotron voice agent and TileGym, 53 skills for DOCA 3.5, six for the PVA SDK, Omniverse Content Services 0.1.0, and more Run:ai and BioNeMo skills ([commit history](https://github.com/NVIDIA/skills/commits/main)).

**Models and research**
- **NVIDIA Cosmos tools** (2026-10-21): Cosmos Data Factory, the Cosmos Framework as agent skills, Cosmos 3 Nano checkpoints for policy testing in simulation, and updated NIM microservices. The post states no licence terms; read each model card ([the post](https://blogs.nvidia.com/blog/cosmos-open-train-evaluate-deploy-world-models/)).
- **Serving world models, latency against throughput** (Nebius, 2026-10-26): Cosmos 3 Super on eight-GPU B200 and H200 nodes split four ways. By the authors' figures, eight one-GPU replicas gave 42.5% more validated video per node-hour than one eight-GPU replica on B200, at 5.5 times the mean latency ([the post](https://nebius.com/blog/posts/serving-world-models-latency-node-throughput)).
- **DeepSeek-V4.1-Flash, NVFP4** (NVIDIA, 2026-10-30): NVIDIA's 4-bit quantization of DeepSeek's multimodal mixture-of-experts model, with a 552-billion-parameter backbone and a context of up to a million tokens, under the MIT licence. Its files come to about 429 GB, far beyond a single 32 GB card ([model card](https://huggingface.co/nvidia/DeepSeek-V4.1-Flash-1017-NVFP4)).

Also seen: 5 items, not linked here: the livestream of the Nebius talk (2026-10-28); NVIDIA's Metatron-v1, a humanoid-robot control policy outside our fields; and three NVIDIA blog posts we haven't read yet, on neural rendering and AI characters in games, memory-enforced GPU sharing in Kubernetes, and building agents with NemoClaw. Skipped: llama.cpp's 15 numbered builds, which are pre-releases.
