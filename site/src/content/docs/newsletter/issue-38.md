---
title: "4 November: the dataset labs this week, aspire-si's memory test passes, and two releases"
description: "The judge bake-off reached a datacentre GPU: all five judges timed on an A100, from 0.10 s to 5.93 s a call, and the counted run planned at about 35 units, though no judge has been scored. aspire-si's memory smoke test passed at full size after a fix that cut a probe's peak from 18,189 to 12,858 MiB. Two releases, rnd 1.1.23.1.55 and rnd-data 0.1.0. A watchdog lesson. Then the daily watch."
issue: 38
date: 2026-11-04
highlights:
  - "<strong>Every judge timed on an A100.</strong> 20 calls each, every reply parsed: flow-judge-v0.1 5.93 s a call, the other four 0.10 to 0.28 s. The counted run is planned at about 35 units in six windows. No judge has been scored."
  - "<strong>aspire-si's memory test passes.</strong> The registered shape peaked at 22,484 MiB against the 31,200 MiB line, after a fix for a KV cache kept in 32-bit floats."
  - "<strong>Two releases.</strong> rnd 1.1.23.1.55, and rnd-data 0.1.0, a read-only reader for the store of raw data behind our research."
  - "<strong>A heartbeat should prove the work happened.</strong> Our GPU watchdog went blind for almost two days and still looked healthy."
---

The judge bake-off reaches a datacentre GPU, aspire-si's memory test passes at full size, and two releases. Then a
lesson from the rig's GPU watchdog, and the daily watch.

**In this issue:**

1. [The dataset labs, this week](#the-dataset-labs-this-week)
2. [aspire-si: the memory test passes at full size](#aspire-si-the-memory-test-passes-at-full-size)
3. [Releases](#releases)
4. [A heartbeat should prove the work happened](#a-heartbeat-should-prove-the-work-happened)
5. [The daily watch](#the-daily-watch)

## The dataset labs, this week

**[reasoning-dataset-lab](https://github.com/mcp-tool-shop-org/reasoning-dataset-lab): the judge test reaches a
datacentre GPU, and every judge is timed.** The lab makes puzzles, quizzes and verification items where code proves
the answer key before any model words the item. Its judge bake-off compares five small models that check whether a
claim is supported by a passage. Last issue its launcher had run end to end only on a CPU machine. On 3 November it
ran on a rented A100 40 GB:
- Four of the five judges loaded and answered all 20 timing calls each, and every reply parsed.
- The fifth, d3-mini, stopped as it loaded. Its own loader needs a numbered GPU device (`cuda:0`), and the launcher
  passed plain `cuda`. The fix (reasoning-dataset-lab #62) also added a check that catches this on a cheap CPU run,
  and a d3-only A100 run then timed it: 20 calls, all parsed.
- The two A100 windows cost 2.10 Colab units together.

![Horizontal log-scale bar chart of the five judges timed on an A100 40 GB across 20 calls each in two windows (batch 1, greedy; timing only, no judge scored): mean time per call is 5.934 s for flow-judge-v0.1, 0.282 s for granite-guardian-4.1-8b, 0.128 s for d3-mini, 0.102 s for mu-judge, and 0.098 s for nemotron-3-nano-4b; paired child-process model load times on a linear scale are 30.6 s for flow-judge-v0.1, 60.3 s for granite-guardian-4.1-8b, 32.85 s for d3-mini, 31.2 s for mu-judge, and 31.1 s for nemotron-3-nano-4b.](/rnd/charts/issue-38-judge-call-times.svg)

| Judge | Mean per call | Model load |
|---|---|---|
| flow-judge-v0.1 | 5.934 s | 30.6 s |
| granite-guardian-4.1-8b | 0.282 s | 60.3 s |
| d3-mini | 0.128 s | 32.85 s |
| mu-judge | 0.102 s | 31.2 s |
| nemotron-3-nano-4b | 0.098 s | 31.1 s |

flow-judge-v0.1 writes feedback before its score, which is why it is about 21 times slower per call than the next
slowest judge, granite-guardian-4.1-8b. Model load is the judge process's own time from start to model loaded.

From those times, R&D has planned the counted run: 2,580 calls per judge. **This plan is an estimate; it has not
run.**

| Window | Judges | Calls | Expected seconds (central / cautious) |
|---|---|---|---|
| flow 1 to 5, one per shard | flow-judge-v0.1, a fifth of its calls each | 516 each | 3,295 / 4,004 each |
| fast | granite, mu, nemotron, d3-mini | 2,580 each | 2,294 / 2,880 |

Run as two waves of three A100s, the six windows take about 2 hours instead of about 5.2 in sequence. They are
expected to cost about 35 units (about 43 in a cautious case), and flow-judge-v0.1's calls are most of that. Before
any counted window opens, the launcher must pass the judge time limit through and cap spending at the live rate, split
a judge into separate shards with a check when they merge, resume inside a shard, and pass a CPU rehearsal of two
shards run in parallel and merged; none of that is merged yet.
**These are timings and costs only: no judge has been scored.**

The figures above are in the [rnd entry for 3 November](https://github.com/mcp-tool-shop-org/rnd/blob/main/entries/2026/2026-11-03-measured-2026-11-03-five-judges-timed-on-an-a100-and-the-s2-.md).

**[understanding-dataset-lab](https://github.com/mcp-tool-shop-org/understanding-dataset-lab)** went public this week,
as a v0.1.0 prototype: multi-party scenes for cognitive empathy, with answer keys made by code. The full story follows
in a later issue.

**[style-dataset-lab](https://github.com/mcp-tool-shop-org/style-dataset-lab)** makes visual datasets bound to a
project's own visual rules: snapshots, splits, training packages, eval scorecards and re-ingest. Its latest release is
v3.4.0 (4 August, also on npm); since then main has had maintenance only, a dependency security update and a CI fix.

**[dataset-desk](https://github.com/mcp-tool-shop-org/dataset-desk)** makes and reviews visual datasets: duplicates,
outliers, search by words or picture, and a gate for image descriptions that uses no model. Latest release v0.2.2
(20 October); nothing new this week.

**[repo-dataset](https://github.com/mcp-tool-shop-org/repo-dataset)** turns code repos and curated visual repos into
training datasets checked for contamination, for local fine-tuning. Latest release v1.2.1 (17 April); nothing new this
week.

## aspire-si: the memory test passes at full size

Before aspire-si trains on the local 5090, a smoke test checks that its training loop fits the card at the size we
registered: 20 steps, 32 prompts, 8 answers per prompt, up to 2,048 tokens each. On 3 November it passed. Memory
peaked at 22,484 MiB against the 31,200 MiB line, and allocated memory peaked in the training pass.

| Phase ending at | Most allocated (GiB) | Most reserved (GiB) |
|---|---|---|
| generating answers | 8.67 | 19.62 |
| reference forward | 11.69 | 13.63 |
| training forward | 17.82 | 19.31 |
| training backward | 17.82 | 19.31 |

![Horizontal bar chart of S2 path a torch allocator memory by phase across the registered 20 steps on the RTX 5090 (G = 8, 32 prompts, completion cap 2,048, 20 of 20 steps completed with verdict S2-OK): rollout is 8.67 GiB max allocated and 19.62 GiB max reserved, reference forward is 11.69 GiB max allocated and 13.63 GiB max reserved, training forward holds the allocation peak at 17.82 GiB max allocated and 19.31 GiB max reserved, and training backward is 17.82 GiB max allocated and 19.31 GiB max reserved; a separate nvidia-smi card-total note records the 22,484 MiB sampler peak against the 31,200 MiB watchdog line, and a footnote records the 2 pre-run stress steps at 2,048 forced tokens peaking at 18.07 GiB allocated and 19.57 GiB reserved in training forward.](/rnd/charts/issue-38-s2-phase-memory.svg)

These are PyTorch's own figures for the registered steps. The 22,484 MiB peak is the card's total from `nvidia-smi`,
which also counts the desktop and the CUDA context, so the two don't share an axis.

Getting there took a fix. Earlier runs went over the line, and about 15 GB of the peak was unexplained. A probe traced
it to the model's KV cache being kept in 32-bit floats, twice its 16-bit size, multiplied by the memory allocator's
overhead as the cache grows one token at a time. In a short probe (256 generated tokens on the longest prompt),
restoring 16-bit (bf16) weights for the embeddings, output layer and norms, which keeps the working cache in 16-bit,
cut the card's peak from 18,189 MiB to 12,858 MiB ([aspire-si #180](https://github.com/mcp-tool-shop-org/aspire-si/pull/180)).

In 10 of the 40 prompt groups (25%, with a 95% interval of about 13 to 41%), all eight answers got the same reward,
so those groups give the model nothing to learn from. A fix has since been built
([aspire-si #181](https://github.com/mcp-tool-shop-org/aspire-si/pull/181)); its first results will follow.

![Bar share chart of S2 path a prompt groups across 20 steps on 32 tune prompts (2 groups per step, G = 8 completions each): 10 of 40 groups (25%) had zero reward variance where all 8 completions scored the same (8 of 10 steps with such a group had mean reward +0.89 to +1.04) and 30 of 40 groups (75%) had active reward variance, with a 95% confidence interval whisker at 14.2% to 40.2% by Wilson score (12.7% to 41.2% by Clopper-Pearson exact, or about 13% to 41%), plus a dashed box noting that leaving zero-variance groups out of the loss (KL included) and mean-centring advantages without dividing by standard deviation is built in aspire-si #181, with first results to follow.](/rnd/charts/issue-38-zero-variance-groups.svg)

The run also measured generation speed: 66.8 tokens a second. At that speed the full plan would take roughly 74 to 97
hours of card time, about one and a half to nearly three times the plan's first guess of 36 to 48 hours. That
projection is provisional, because the plan's step count isn't fixed yet.

## Releases

- **rnd 1.1.23.1.55** on GitHub and PyPI, the first tool release since 1.1.23.1.31:
  [release notes](https://github.com/mcp-tool-shop-org/rnd/releases/tag/v1.1.23.1.55).
- **rnd-data 0.1.0**, its first release on PyPI: a read-only reader and schema checker for the store of raw data
  behind our research (`pip install rnd-data`). [Release notes](https://github.com/mcp-tool-shop-org/rnd-data/releases/tag/v0.1.0).

## A heartbeat should prove the work happened

The rig's GPU watchdog went blind for almost two days after a driver changed one of the fields it reads, and it still looked
healthy, because its heartbeat was written on every loop whether or not it had read anything. It now writes the
heartbeat only after a reading parses, and marks itself blind after five bad readings in a row. We proved the fix by
setting its line far below normal use and watching it trip. Some of our study kits run their own separate guard, which
logged readings.

![Two-row concept diagram titled A heartbeat should prove the work happened: before, the watchdog loop polled the card and wrote the heartbeat whether or not it read the card; after, the heartbeat is written only after a reading parses, an unparsed reading writes no heartbeat update, and five bad readings in a row write a blind marker.](/rnd/charts/issue-38-heartbeat-lesson.svg)

Two lessons: write a heartbeat only after the work it stands for has happened, and test a safety check with a case it
must catch.

## The daily watch

2 new since [issue 37](/rnd/newsletter/issue-37/).

- **Claude Code v2.1.318** (2026-11-04): `claude -p` JSON results and `claude auth status` now carry the date a stored sign-in ends (`credential_expires_at`, `loginExpiresAt`); unattended runs stop rewriting `~/.claude.json` when nothing in it changed; and a mod's `turn.step` hook can no longer make a cut-off or stopped reply finish as a success in headless runs ([release notes](https://github.com/anthropics/claude-code/releases/tag/v2.1.318)).
- **ComfyUI v0.44.0** (2026-11-04): fixes `fp8_e4m3fn_fast` falling back to bf16 compute under dynamic VRAM and a VAE compute-dtype crash on the LTX 2.5 decoder; adds a node to set the VAE compute dtype, and ProRes video saving ([release notes](https://github.com/Comfy-Org/ComfyUI/releases/tag/v0.44.0)).
