---
id: 2026-10-13-nvidia-pair-a-lan-inference-router-and-how-it-compares-with-
title: "NVIDIA PAIR: a LAN inference router, and how it compares with interlock"
date: 2026-10-13
kind: tool
relevance: watch
fields: [local-inference]
tags: [pair, interlock, router]
---

## Summary

NVIDIA PAIR (Personal AI Router), v1.0.0 under Apache-2.0, released on 2026-10-13, joins the computers on one network into a cluster. Each machine runs a proxy that local applications talk to as Ollama, OpenAI-compatible or Anthropic Messages. Each independent request goes to one machine that advertises the requested model and has a running engine (Ollama, LM Studio or llama.cpp). It doesn't pool VRAM, shard a model or split a request.

Its scheduler is model-blind: pending jobs plus coarse GPU pressure (0–3 units at 40/70/85% utilisation of the busiest GPU). A capability gate keeps a request to the machines that hold the model. Its own documentation lists what that ranking can't see:
- capacity: VRAM, GPU model and latency;
- whether the model is already loaded;
- job size: every job counts as one;
- per-GPU detail: only the busiest GPU is seen.

## Key points

- **The ports:** the Ollama-compatible proxy takes port 11434 and moves Ollama to 11435 or above. The plaintext side answers only loopback. The same port serves mutual TLS to paired nodes, chosen by the connection's first byte (0x16).
- **Telemetry:** the probe's "telemetry" code hits are host and GPU telemetry exchanged between paired nodes, by the architecture's account. Nothing read shows it sent off the network, but the architecture document at v1.0.0 says the telemetry is plaintext, not authenticated, and readable by anything on the same subnet (architecture.mdx lines 172-185), and SECURITY.md (lines 87-89) says local-first doesn't prove no data leaves the machine or LAN.
- **The 1.0.0 release notes** (read 2026-10-13, flagged by the weekly watch) add:
  - llama.cpp management;
  - per-engine launch options, including context size;
  - Anthropic Messages API routing through Ollama and LM Studio, with model-aware failover, so Claude Code can use a PAIR cluster;
  - endpoints that follow each engine's CORS policy.

  PAIR can set a context size, but can't tell what fits. E5's card answers that for the 5090.
- **The roadmap** lists KV-cache-aware scheduling, request queuing, more scheduler variables, vLLM and ComfyUI.

## Studio relevance

- **Its stated limits map onto what interlock measured on one machine:**
  - warm versus cold, and the cost of a cold load (E1);
  - context capacity before a spill (E5);
  - whether co-scheduled devices interfere (E4b: free, within ±10%).
- **Not for the rig now.** It would take port 11434 from the 5090 Ollama server that interlock measures and restarts.
- **Revisit if the studio pairs a second machine.** Before any install, run `rnd probe` and read its SECURITY.md.
- **The brief:** [Where should this request run? NVIDIA PAIR and interlock](https://mcp-tool-shop-org.github.io/rnd/briefs/pair-and-interlock/).

## Claims

- [verified] PAIR is Apache-2.0, with v1.0.0 published 2026-10-13 (via: rnd probe of github.com/NVIDIA/Personal-AI-Router, 2026-10-13)
- [verified] PAIR's scheduler ranks nodes by pending work plus coarse GPU pressure, is model-blind, and doesn't consider VRAM, latency or whether the model is loaded (via: docs/architecture.mdx at v1.0.0, read 2026-10-13)
- [verified] PAIR's Ollama-compatible proxy uses port 11434 and moves Ollama to 11435 or above (via: docs/architecture.mdx port map at v1.0.0, read 2026-10-13)
- [verified] PAIR 1.0.0 adds per-engine launch options including context size, llama.cpp management, and Anthropic Messages API routing through Ollama and LM Studio (via: gh release view v1.0.0 --repo NVIDIA/Personal-AI-Router, 2026-10-13)
- [wrong] PAIR sends no telemetry beyond the paired nodes. (via: architecture.mdx lines 172-185 at v1.0.0: host and GPU telemetry is plaintext, unauthenticated and readable by anything on the subnet, re-read for the readouts promotion, R&D, 2026-10-20)
- [verified] PAIR's host and GPU telemetry is plaintext HTTP, not authenticated, and readable by anything on the same subnet; NVIDIA advises against running PAIR where that is unacceptable. (via: NVIDIA/Personal-AI-Router architecture.mdx lines 172-185 and SECURITY.md lines 87-89 at v1.0.0, re-read for the readouts promotion, R&D, 2026-10-20)

## Sources

- [primary] https://github.com/NVIDIA/Personal-AI-Router — the README and docs/architecture.mdx at v1.0.0
- [primary] https://developer.nvidia.com/blog/nvidia-pair-virtual-inference-router-expands-available-compute-on-your-local-network/ — the launch post
- [[2026-10-12-e4b-block-2]] — E4b
- [[2026-10-13-e5-fill-card]] — E5
