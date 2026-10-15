---
title: The backend that changed under us
description: An Ollama update quietly swapped out the studio's CUDA 13.4 backend. Rebuilding it took two builds, a CPU incident that set the rules for every heavy job since, three rounds of outside review, and a weekly check so it can't happen silently again.
issue: 9
date: 2026-10-15
highlights:
  - "<strong>A one-line hash check caught it:</strong> the Ollama 0.40.4 install replaced the studio's CUDA 13.4 <code>ggml-cuda.dll</code> with the stock build, and the start script refused to call it the studio's."
  - "<strong>Copying the old build back was never an option:</strong> 0.40.4 pins a different llama.cpp (b11521, against b11232), so the backend had to be rebuilt from the new pin."
  - "<strong>An uncapped CPU job took the whole machine</strong>, and every heavy job since runs pinned to efficiency cores at below-normal priority, with its load stated before it starts."
  - "<strong>Nothing is activated until a sandbox test passes</strong>, and the first one didn't: the new build loaded and kept pace, but its outputs diverged from stock on 2 of 3 prompts, so the stock backend stays. A weekly Argon check now asks what the newest setup should be."
---

Every claim below links to the record it came from. The build records are in rnd, under [`experiments/ollama-cuda-backend/`](https://github.com/mcp-tool-shop-org/rnd/tree/main/experiments/ollama-cuda-backend).

## What happened

The studio runs its own CUDA backend for Ollama on the RTX 5090. It's a `ggml-cuda.dll` built from Ollama's own llama.cpp pin with CUDA 13.4, for compute capability 12.0 only, and dropped into Ollama's `lib\ollama\cuda_v13` folder. The script that starts the studio's Ollama checks that file's sha256 before it calls the server ready.

On the morning of 2026-10-15 that check failed. The 0.40.4 install of the night before had written the stock CUDA libraries over the studio's: same file name, different hash. Ollama ran normally, so only the check noticed. Every GPU grant was held until the studio build was back. → [the 0.35.1 build record](https://github.com/mcp-tool-shop-org/rnd/blob/main/experiments/ollama-cuda-backend/build-0.35.1-cuda-13.4.1.md)

## Why it had to be rebuilt

Ollama doesn't vendor ggml. It fetches llama.cpp at a pinned tag and builds the backend against it. 0.35.1 pinned b11232, and 0.40.4 pins b11521. The old DLL was built against the old ggml ABI, so copying it back next to the new `ggml-base.dll` would have been a guess. The rebuild used the same recipe as the first build (Ollama's `llama_cuda_v13_windows` preset, architecture 120 only, CUDA 13.4's nvcc, target `ggml-cuda`), from the new tag.

It built in 343.8 s (156 steps), and every dependency of the new DLL resolved. → [the 0.40.4 build record](https://github.com/mcp-tool-shop-org/rnd/blob/main/experiments/ollama-cuda-backend/build-0.40.4-cuda-13.4.1.md)

## The CPU incident, and the rules it set

Earlier the same day, a different job taught the lesson this build was run under. An index rebuild through offrig's new embedding server ran torch at its default thread count: all 24 logical cores. The CPU went to 100%, and it was stopped by hand. Nothing broke, but the job took a shared machine from everyone on it, without warning, from a team that already knew torch takes every core.

Since then, every heavy job is pinned before it starts:
- **Efficiency cores only, at below-normal priority.** On this CPU, `GetSystemCpuSetInformation` puts the 8 performance cores at logical 0, 1, 10–13, 22 and 23, and the 16 efficiency cores at 2–9 and 14–21. That isn't the "first eight" a guess would give. Jobs run under an affinity mask over efficiency cores only, set at launch (`start /AFFINITY … /BELOWNORMAL`), so every child process inherits it.
- **The load is stated before the start,** with a stop rule (total CPU held above a threshold for so many seconds) and CPU logged every 5 s.
- **The process that's watched is the one doing the work.** The first corrected rerun watched a Python launcher shim, which was idle at 6 MiB, and its gates "passed" on the wrong process. They were declared void, and the rerun was repeated against the real interpreter.
- **Every thread pool is capped, not just torch's.** An outside review of the embedding server found that capping torch's threads isn't enough: OpenMP, MKL and the tokenizer's Rayon pool each size themselves to the machine unless capped before torch loads. → [the review and its disposition](https://github.com/mcp-tool-shop-org/rnd/blob/main/experiments/embeddinggemma-2/argon-consult-embed-serve-resources-disposition.md)

The CUDA build ran under these rules: 8 efficiency cores (`0x3FC`), below-normal priority, `-j 8`. A per-core reading mid-build showed those 8 cores at about 97% and every other core at about 22%. Total CPU averaged 41.7%.

## Three rounds of review before the GPU

The plan to test the build was reviewed by Argon, the studio's outside reviewer, before any GPU use. It came back twice with changes, and they're why the test looks the way it does:
- **Isolation.** The sandbox Ollama runs from its own tree, with the stock install stripped from `PATH` and the CPU-only switches from the embedding work removed from its environment. A stray `CUDA_VISIBLE_DEVICES=-1` would have quietly tested the CPU.
- **One model at a time,** checked before every prompt, not once per block, with a warm-up generation after each load.
- **A breach kills, not just records.** If card memory passes the cap, the sandbox's process tree is killed and the stock server unloaded at once.
- **A pre-registered tolerance.**
  - The outputs must match token for token.
  - The one exception is a near-tie: at the first differing token, the stock run's top two candidates are within 0.001 in log-probability, and the sandbox chose the second.
  - The tolerance needs the top two candidates, so the source was read to check where they come from. Ollama 0.40.4 asks llama-server for `n_probs` and never sets `post_sampling_probs`. llama.cpp then reads the candidates from the full pre-sampling logits, so greedy `top_k: 1` can't hide the runner-up.
  - → [the v3 test](https://github.com/mcp-tool-shop-org/rnd/blob/main/experiments/ollama-cuda-backend/sandbox_test-v3.py) and [its diff from v2](https://github.com/mcp-tool-shop-org/rnd/blob/main/experiments/ollama-cuda-backend/sandbox_test-v2-to-v3.diff)

Argon also set the build to the studio's standard, not the minimum:
- explicit `sm_120a` SASS with no PTX;
- every FlashAttention quant compiled;
- fatbins compressed for speed;
- CUDA graphs and VMM on;
- cuBLAS from CUDA 13.4 Update 2, whose release notes list a fix for an NVFP4 heuristic on compute capability 12.x.

## A note on version numbers

CUDA 13.4's first release is 13.4.1 (nvcc V13.4.59). "13.4 Update 2" is `version.json` 13.4.3, with nvcc V13.4.92 and cuBLAS 6,14,11,1380. The review asked for "13.4.2", which is off by one. The build script now refuses any nvcc but the one installed and verified. → [the 13.4.3 build script](https://github.com/mcp-tool-shop-org/rnd/blob/main/experiments/ollama-cuda-backend/build-0.40.4-cuda-13.4.3.cmd)

## The build to the studio standard

It built in 374.0 s: 201 steps and 189 CUDA objects, each compiled as `arch=compute_120a,code=[sm_120a]`, which is machine code for this card only, with no PTX. The DLL is 217 MB, against 56 MB for the first rebuild; the extra FlashAttention kernels and the speed-first compression account for it. It ran under the same cap: 8 efficiency cores, total CPU averaging 37.5%, and one 5-second sample above 50%. Every dependency resolved. → [the 13.4.3 build record](https://github.com/mcp-tool-shop-org/rnd/blob/main/experiments/ollama-cuda-backend/build-0.40.4-cuda-13.4.3.md)

## Update, the same afternoon: the sandbox test failed

Argon gave round 3 a green light, and the test ran under a GPU grant: 46 seconds, peaking at 7.4 GB of card memory against a 9.2 GB cap, and cleaned up completely.
- **The new DLL loaded,** and the log names its path. It's at least as fast as stock.
- **It failed the output check on 2 of 3 prompts.** Stock matched itself token for token. The sandbox matched stock exactly on the coding prompt, but diverged at token 15 of one prompt and token 6 of another. At both points it ranked stock's top two candidates the other way round, by margins of about 0.7 and 0.8 in log-probability. That's not the near-tie the rule allows.

So by the rule set before the run, nothing is activated and the stock backend stays. The difference is larger than reordered sums usually give, and the cause isn't identified: build options or toolkit. Neither answer is wrong, but the bar was identity with stock, and identity isn't quality. Finding the cause is its own decision, with its own review. → [the result](https://github.com/mcp-tool-shop-org/rnd/blob/main/experiments/ollama-cuda-backend/sandbox-result-cu1343.md)

## So it can't happen silently again

A weekly check now runs every Monday. It reads the rig's live versions:
- Ollama's version;
- the installed backend's hash against the studio's builds;
- the start script's expected hash;
- nvcc and the driver;
- the newest Ollama and llama.cpp releases.

It writes them into a paste-ready brief that asks Argon for the newest recommended setup: the toolkit, the Ollama release and its pin, the build options, whether a rebuild is due, and any security advisories. If an update has replaced the studio's backend again, the brief opens with an alert.
