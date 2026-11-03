---
id: 2026-11-03-measured-2026-11-03-five-judges-timed-on-an-a100-and-the-s2-
title: Measured 2026-11-03: five judges timed on an A100, and the S2 memory fix
date: 2026-11-03
kind: finding
relevance: reference
fields: [training]
tags: [judge-bakeoff, aspire-si, gpu-memory]
---

## Summary

Two measurement sets from 3 November 2026, published as counts only so the newsletter can cite them.

First, the five local judge models of the reasoning-dataset-lab judge comparison were **timed** on one rented card type (A100 40 GB, Google Colab), 20 calls each, across two windows. Timing only: no judge has been scored, and these are burned pilot items, not counted items.

Second, the aspire-si GRPO smoke test S2 (path a) now passes at its registered shape on the local RTX 5090, after a memory fault was traced and fixed. Per-phase allocator figures from that passing run are below.

## Key points

**Judges, A100 40 GB, batch 1, greedy, 20 calls each, every reply parsed:**

| Judge | Mean s per call | Median s | Model load s (child) | Load + process overhead s (parent) | VRAM peak MiB |
|---|---|---|---|---|---|
| flow-judge-v0.1 | 5.934 | 5.539 | 30.6 | 40.0 | 8,362 |
| granite-guardian-4.1-8b | 0.282 | 0.254 | 60.3 | 64.9 | 16,850 |
| d3-mini | 0.128 | 0.099 | 32.85 | 41.05 | 9,314 |
| mu-judge | 0.102 | 0.074 | 31.2 | 35.8 | 8,438 |
| nemotron-3-nano-4b | 0.098 | 0.074 | 31.1 | 35.6 | 8,438 |

- **The two load columns measure different things.** "Model load (child)" is the judge process's own load time, from process start to model loaded. "Load + overhead (parent)" is the window's wall time for that judge minus its call time, so it also counts process start, imports and result handling. A chart of load time should use the first column; window planning uses the second.
- flow-judge writes feedback text before its score: median 92 words, at most 200. It is about 46× slower per call than the next judge, so it dominates the cost of the counted run.
- d3-mini first failed to load on the A100: its runtime needs a numbered device (`cuda:0`), and the launcher passed `cuda`. That was fixed in reasoning-dataset-lab #62, and a d3-only window then timed it.

**S2 path (a), the registered 20 steps** (G 8, 32 prompts, completion cap 2,048), with a dated set of memory flags:
- **Verdict S2-OK:** 20 of 20 steps.
- nvidia-smi sampler peak **22,484 MiB** against the 31,200 MiB line.
- rollout 66.8 tok/s; step median 89.2 s.

| Phase ending at | Max allocated GiB (torch) | Max reserved GiB (torch) |
|---|---|---|
| rollout | 8.67 | 19.62 |
| reference forward | 11.69 | 13.63 |
| training forward | **17.82** | 19.31 |
| training backward | 17.82 | 19.31 |

- **Torch GiB and nvidia-smi MiB are different measures.** The card total includes the desktop and the CUDA context; don't put them on one axis.
- The two stress steps before the registered steps (the longest prompt, forced to 2,048 tokens) peaked a little higher (training forward 18.07 / 19.57 GiB) and are reported apart.
- **The earlier fault:** an fp32 KV cache (the 4-bit load path had upcast the embeddings, output layer and norms, so activations and the cache ran in fp32), times the allocator's growth as the cache is extended token by token.
  - **A short probe** (256 generated tokens on the longest prompt): restoring bf16 on those weights cut the card peak from 18,189 to 12,858 MiB, and static weights from 8.05 to 5.73 GiB.
- **10 of 40 prompt groups had zero reward variance** (95% interval about 13–41%), so they gave no learning signal. A fix is decided for the training plan; it is not yet built.

**The judge comparison's counted run, window plan: PLANNED, NOT RUN** (R&D's estimate from the times above, at the live Colab A100-40 rate of 6.73 units/h, read 2026-11-03)
- **The counted run:** 2,580 calls per judge (430 triads × 3 claims × 2 orders), on one card type, A100 40 GB.
- **Six windows,** each downloading only its own judges:

| Window | Judges | Calls | Expected s (central / cautious) | Ceiling (units) |
|---|---|---|---|---|
| flow 1–5 (one per shard) | flow-judge-v0.1, 1/5 of its calls each | 516 each | 3,295 / 4,004 each | 8.97 each |
| fast | granite, mu, nemotron, d3-mini | 2,580 each | 2,294 / 2,880 | 6.73 |

- **Two waves of three A100 sessions** (at most three open at once): about **2 h** of wall clock, against about **5.2 h** in sequence.
- **Units:** **35.1 expected, 42.8 cautious** (call time × 1.2, setup × 1.5). The ceilings sum to **51.6**. The worst case with three windows open at their ceilings is 26.9.
- **Setup per window**, measured on the d3-only window: 115 s fixed plus 10.2 s per GB of weights.
- **Prerequisites before any counted window:**
  - the launcher's child-timeout forwarding and a real cost cap at the live rate;
  - splitting a judge into disjoint shards, with a merge check (the union equals the schedule, no overlap, pins equal);
  - resume within a shard;
  - a CPU stub of two parallel shards plus the merge.
  
  None of these is merged yet.

## Studio relevance

Reference numbers for the newsletter and for planning:
- The judge comparison's counted run is costed from these per-call times.
- The S2 figures set the memory envelope for the verifier training plan on one 32 GB card.

## Claims

- [verified] flow-judge-v0.1 averaged 5.934 s per call on an A100 40 GB, over 20 calls; the other four judges averaged under 0.3 s. (via: R&D, judge done-files timeone-02 and timeone-d3, 2026-11-03)
- [verified] S2 path (a) completed 20 of 20 steps at G 8 and cap 2,048, with an nvidia-smi peak of 22,484 MiB. (via: R&D, run readout and run.meta, 2026-11-03; also aspire-si #180's run record)
- [verified] The peak allocation phase is the training forward, at 17.82 GiB allocated in the registered steps. (via: R&D, phase log of the run, 2026-11-03)
- [unverified] The counted run is planned at about 35.1 units expected (42.8 cautious) in six windows; it has not run. (an estimate, not a measurement)
- [verified] Restoring bf16 on the non-quantised weights cut the probe's card peak from 18,189 to 12,858 MiB at 256 tokens. (via: R&D, probe A/B JSON, 2026-11-03)

## Sources

- [primary] https://github.com/mcp-tool-shop-org/aspire-si — aspire-si; the S2 pre-registration's "2026-11-03 run record: path (a) v3" (PR #180)
- [primary] https://github.com/mcp-tool-shop-org/reasoning-dataset-lab — reasoning-dataset-lab; the device fix is PR #62
- [rig] R&D run receipts (kept local): judge done-files timeone-02 (flow ba3fc5c8…, granite 6c504707…, mu f9a386f8…, nemotron 62ab9b48…) and timeone-d3 (d3-mini e46d6ef0…); S2 phase log b61d8520…, readout a30045dc…, probe A a55152fc…, probe B ee42555e…
