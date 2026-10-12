---
id: 2026-10-12-e4-co-scheduling-inconclusive
title: "E4: 5090 and Intel co-scheduling is inconclusive on run 7"
date: 2026-10-12
kind: finding
relevance: act
fields: [local-inference]
tags: [switchyard, npu, igpu, e4]
---

## Summary

E4 asked whether the router may run the Intel NPU or iGPU beside qwen3:8b decode on the 5090 without either side
slowing the other by more than 10%. Run 7 (2026-10-12, 8 minutes, A-B-A with 5 repeats) is a valid run. All four
pairs are **inconclusive** under the pre-registered half-band noise rule: the alone sets were too noisy to call.
Nothing was slower when paired. The iGPU was about 15% faster beside the 5090, which the rules also count as "not
free". The noise has identified causes, so the next step is a redesigned, pre-registered E4b, not a repeat.

## Key points

- **Results** (band 0.10; a pair is callable only if its alone spread is at most 0.05):

  | pair | metric | difference | alone spread |
  |---|---|---|---|
  | 5090 beside NPU | decode tok/s | −3.8% | 0.356 |
  | 5090 beside iGPU | decode tok/s | −1.9% | 0.256 |
  | NPU beside 5090 | latency | −9.2% (faster) | 0.234 |
  | iGPU beside 5090 | latency | −15.2% (faster) | 0.113 |

- **A 4.1 s 5090 latency is a model reload.** Five slots each paid about 3.6 s of load. The likely cause is the
  companion "stop" request, a generate with no options, which Ollama treats as a load at its default context. The
  decision metric (server decode rate) excludes load, so it is unaffected.
- **The 5090's decode rate followed GPU clock ramp-up.** A 128-token decode (about 0.6 s) is too short for the clocks to
  settle. Decode was about 211 tok/s right after a reload and about 175 otherwise. The per-slot clock and power readings
  the spec asks for were null, so this is inferred, not measured.
- **The NPU paid a re-entry cost:** about 66 ms on the first call after a gap, and about 55 ms otherwise.
- **The iGPU ran faster when paired,** most likely through shared power management: CPU work feeding the 5090 raises
  the uncore clocks the iGPU uses. It is a platform effect, not contention.
- **E4b** would add a re-entry warm-up before every measured slot, no reloads (`load_duration` recorded, and a slot
  with a load refused), a longer 5090 decode, real per-slot clocks, and a paired-difference analysis over 10 repeats.
  The band and the noise rule stay as registered.

## Studio relevance

The router has no measured basis yet for running Intel work beside 5090 decode freely, and none against it either.
Until E4b, co-scheduling stays a judgement call. Two by-products matter beyond E4:
- a session-control request can silently reload the measured model;
- short calls on all three devices measure power state as much as compute.

## Claims

- [verified] All four E4 run-7 pairs fail the half-band noise check (alone spreads 0.356, 0.256, 0.234 and 0.113) (via: R&D readout of the switchyard receipts at efbcafe, 2026-10-12)
- [verified] Five 5090 alone-before slots took about 4.1 s against about 0.45 s for the other warm slots (via: R&D readout of the per-slot receipts, 2026-10-12)
- [unverified] The reloads come from `stop_session`'s option-less generate; `load_duration` per slot would confirm it.
- [unverified] The iGPU speed-up comes from shared CPU and uncore power management.

## Sources

- [primary] https://github.com/mcp-tool-shop-org/switchyard/pull/76 — the receipts and R&D's readout
- [primary] https://github.com/mcp-tool-shop-org/switchyard/blob/main/experiments/e4/spec.yaml — the pre-registered rules
