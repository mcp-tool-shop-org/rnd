---
title: "6 November: the memory guard that counted the cache"
description: "Our first Colab run on Google's newest GPU card got through every check and a 57.7 GB download, then our own memory guard stopped it before the first training step. The guard was counting cached model files as memory the job was using. The fix is in review. Also: Colab locks that no longer break when a library ships, aspire-si's training run at 120 updates, and the daily watch."
issue: 40
date: 2026-11-06
highlights:
  - "<strong>A guard that counted the cache.</strong> Our G4 run stopped on a memory projection of 183,924 MiB against a 181,130 MiB machine. The job itself was using 52,493 MiB; the rest was cached model files."
  - "<strong>Locks bounded in time.</strong> A library release on PyPI broke a Colab lock check on every pull request. Each lock now records the moment it was resolved against."
  - "<strong>aspire-si at 120 updates.</strong> Three training chunks on the local RTX 5090 passed their checks. 54 of 3,840 answers (1.41%) ran into the length limit, against a stop line of 20%."
---

A day of guards. One of ours stopped a run it should have let through, and one stopped breaking every time a
library shipped. Then aspire-si's training run, and the daily watch.

**In this issue:**

1. [The memory guard that counted the cache](#the-memory-guard-that-counted-the-cache)
2. [Locks bounded in time](#locks-bounded-in-time)
3. [aspire-si at 120 updates](#aspire-si-at-120-updates)
4. [The daily watch](#the-daily-watch)

## The memory guard that counted the cache

[style-dataset-lab](https://github.com/mcp-tool-shop-org/style-dataset-lab) trains image models on Google Colab when a
job is too big for our local card. On 6 November we ran its third lane, a fine-tune of the Qwen-Image model, for the
first time on a **G4**: Colab's RTX PRO 6000 Blackwell card with 96 GB of memory. Three earlier tries on Colab's 80 GB
A100 had found no card free; the G4 opened at once.

Everything before training passed:

| Check | Reading |
|---|---|
| Card | RTX PRO 6000 Blackwell, 97,887 MiB |
| Host memory | 176.9 GiB total, 173.1 GiB available |
| Disk free | 229 GiB |
| Matrix-multiply smoke test | 192 TFLOPS |
| Model download | 57.7 GB in 168 s (343 MB/s) |
| Live rate | 10.05 compute units an hour |

Then, while training was caching its latents (8 of 12 done), our own guard stopped the run, before the first training step. The run
cost 0.86 units.

**What the guard does.** Before and during a run, the kit reads the machine's memory every 15 seconds and projects
whether the job is about to run out of host memory: what it is using now, plus an allowance for growth, plus 5%. If the
projection passes the machine's total, the kit stops the run cleanly instead of letting Linux kill it mid-step.

**What went wrong.** The guard read the job's memory from the wrong counter. It first took `AnonPages`, the memory the
program itself holds, then overwrote it with the container's `memory.current`, which also counts the **page cache**:
files the system keeps in memory because they were read recently. After a 57.7 GB download that the job then mapped
into memory, most of `memory.current` was the model files sitting in cache, which the system can drop whenever it needs
the room.

![Diagram titled "The guard counted the cache": one bar for the Colab G4 machine's 181,130 MiB of memory. A teal segment of 29% is the job's own memory (AnonPages), 52,493 MiB; an amber segment up to 95.6% is cached model files (page cache), about 120,600 MiB, which the system can drop when it needs room. A long bracket over both segments reads "What the guard counted: memory.current, 173,118 MiB, projected 183,924 MiB, stop". A short bracket over the teal segment reads "What it should count: 52,493 MiB, projected 57,268 MiB, fine". Footnote: projection = (memory counted + 2,048 MiB allowance) × 1.05.](/rnd/charts/issue-40-guard-diagram.jpg)

![Line chart over 17 memory readings about 15 seconds apart on the Colab G4 machine. The container's memory.current, which includes page cache, climbs from 1.5 GiB to 169.1 GiB at reading 17, where the old guard's projection of 183,924 MiB (179.6 GiB) passes the 181,130 MiB (176.9 GiB) machine total and stops the run. The job's private memory (AnonPages) stays between 0.6 and 27 GiB until a jump to 51.3 GiB at reading 17, as the model loads. Available memory never falls below 122.8 GiB. The shaded gap between the two lines is page cache from the 57.7 GB download. On private memory the projection is 57,268 MiB.](/rnd/charts/issue-40-guard-counted-cache.svg)

On the last reading, `memory.current` was 173,118 MiB and `AnonPages` 52,493 MiB, with 125,791 MiB still available.
The projection was (173,118 + 2,048) × 1.05 = **183,924 MiB**, just over the machine's 181,130 MiB, so it stopped. On
the job's own memory the same projection is 57,268 MiB, about a third of the machine.

**The fix** ([style-dataset-lab #64](https://github.com/mcp-tool-shop-org/style-dataset-lab/pull/64), in review):
- the guard counts private memory only (the container's `anon` plus `shmem`, which counts because Colab machines have
  no swap), never the cache;
- a second check trips if available memory would fall below 2 GiB;
- it reads only complete samples, so a reading cut off halfway can't stop a healthy run or wave a real overrun through;
- every way a run can be stopped now records a named reason in the run record. This one, and several others, had
  recorded none.

A test replays this run's 17 real readings: it stops the run on the old code and lets it through on the fix.

**One thing the fix doesn't cover.** While the model loaded, the job's own memory jumped about 50 GB between two
readings 15 seconds apart. The guard's 2 GB growth allowance can't foresee a jump that size. That run was nowhere near
the limit, but a bigger job could be. It is tracked as
[style-dataset-lab #65](https://github.com/mcp-tool-shop-org/style-dataset-lab/issues/65): a growth allowance sized per
job, or more frequent readings while a model loads.

## Locks bounded in time

Each Colab lane installs from a **lock file** that pins every package version, so a run on Thursday installs exactly
what was tested on Monday. A check on every pull request re-resolves the lane's requirements and fails if the result
differs from the lock.

On 6 November, transformers 5.22.2 reached PyPI at 15:42 UTC. The lock pinned 5.22.1, so the check found a newer
version, reported drift and failed on every pull request, though nothing in the repository had changed.

![Diagram titled "A lock bounded in time": a timeline for 6 November 2026 (UTC) with a teal marker at 15:00, the lock's bound, and an amber marker at 15:42, when transformers 5.22.2 was published. Everything after the 15:00 bound is shaded as ignored by the check. Before the fix, the check read the package index as it is now, found transformers 5.22.2 while the lock says 5.22.1, and reported drift: a red check on every pull request. After the fix, the check reads the index as it was at the bound, finds 5.22.1, the same as the lock, and passes. Footnote: uv pip compile --exclude-newer 2026-11-06T15:00:00Z; moving the bound is a deliberate pull request.](/rnd/charts/issue-40-locks-diagram.jpg)

[style-dataset-lab #63](https://github.com/mcp-tool-shop-org/style-dataset-lab/pull/63) (merged) gives each lock a
committed time bound beside it. The check resolves with `uv pip compile --exclude-newer` at that instant, so it sees
the package index as it was when the lock was made, and a new upstream release no longer reads as drift. Moving to
newer packages is now a deliberate pull request that moves the bound and re-locks together. A missing or malformed
bound, or one set in the future, stops the check with a named reason.

## aspire-si at 120 updates

aspire-si's S2 run trains a model by reinforcement learning on our local RTX 5090: for each prompt the model writes 8
answers, each answer is scored, and the model is nudged toward the answers that scored better than their group.
[Issue 38](/rnd/newsletter/issue-38/) covered the memory test that cleared it to run. The run goes in chunks of 40
updates, each checked before the next is allowed to start.

Seed 42's first three chunks, 120 updates, all passed their checks. Chunks 2 and 3 took 3.37 and 3.23 hours with the
card capped at 480 W. Card memory peaked at about 23.2 GB, and there were no hardware errors.

| Chunk | Updates | Answers cut off at the length limit | Groups with no reward spread |
|---|---|---|---|
| 1 | 0–39 | 24 of 1,280 | 12 of 160 |
| 2 | 40–79 | 14 of 1,280 | 20 of 160 |
| 3 | 80–119 | 16 of 1,280 | 19 of 160 |
| **All** | **120** | **54 of 3,840 (1.41%)** | **51 of 480** |

![Bar chart of answers cut off at the length limit in aspire-si S2 seed 42, per chunk of 40 updates (1,280 answers each), on a track from 0% to the 20% stop line with the 4.2% flag line marked: chunk 1 (updates 0 to 39) 24 of 1,280 (1.88%), chunk 2 (updates 40 to 79) 14 of 1,280 (1.09%), chunk 3 (updates 80 to 119) 16 of 1,280 (1.25%), and the run total 54 of 3,840 (1.41%). A note gives the 10-update rolling peak of 5.0% at updates 39 to 47.](/rnd/charts/issue-40-s2-seed42-truncation.svg)

**Why we count cut-off answers.** An answer that runs into the length limit is scored on a part of what the model
meant to write, so a rising share would mean the model is learning to ramble. The run watches it over a rolling window
of 10 updates: above 4.2% an update is flagged for a look, and at 20% the run stops. The highest so far is 5.0%, at
the end of chunk 1, where 9 of the 32 answers at update 39 were cut off; it fell back below 1% within ten updates.

**Groups with no reward spread** are prompts where all 8 answers scored the same, so they give the model nothing to
learn from. Here that was 51 of 480 groups (10.6%).

These are numbers about the run's health, not results: nothing has been evaluated yet. The run is paused after chunk 3
and resumes at update 120.

## The daily watch

3 new since [issue 39](/rnd/newsletter/issue-39/).

- **Claude Code v2.1.319** (2026-11-06): MCP tasks in the terminal, where a tool call an MCP server runs as a task moves to the background and reports back when it finishes (`CLAUDE_CODE_DISABLE_MCP_TASK_BACKGROUND` waits instead), and a `permissions.denyInsteadOfPrompting` setting that denies a call instead of waiting on a permission prompt. A behaviour change: with telemetry or feature flags off, including behind LLM gateways, auto mode now asks about or denies calls the server can't check, instead of falling back to the built-in classifier; `CLAUDE_CODE_AUTO_MODE_SERVER=0` keeps the old behaviour ([release notes](https://github.com/anthropics/claude-code/releases/tag/v2.1.319)).
- **Ollama v0.40.15** (2026-11-03, stable): Xiaomi's MiMo V2.6 (9B, for code and agents) and the AutoTrust decision-model family; recurrent and vision GGUF models can now serve more than one request at a time; `ollama launch` supports Kimi Code CLI ([release notes](https://github.com/ollama/ollama/releases/tag/v0.40.15)).
- **NVIDIA/skills** (2026-11-05 to 2026-11-06, 9 commits): validation signatures attached to skills, the NeMo MBridge skills synced, skill-finder made the default install, and the catalogue metadata regenerated ([latest commit](https://github.com/NVIDIA/skills/commit/c663e5799366d945a70a40b1ab18cedfc817495c)).
