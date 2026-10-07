---
id: 2026-10-07-nsight-copilot
title: Nsight Copilot in Nsight Compute
date: 2026-10-07
kind: tool
relevance: watch
fields: [gpu-computing, developer-tools, agent-tooling]
tags: [nsight, profiling, performance, ai-assistant, nvidia]
---

## Summary

An AI assistant built into the Nsight Compute profiler (Tools menu, F9). It reads a collected kernel profile and explains what is limiting performance, ranks the issues by estimated speedup, points at the source lines involved, and suggests fixes. It is free and signs in with an NVIDIA developer account.

## Key points

- Explains GPU architecture concepts, hardware metric definitions, and common bottlenecks.
- Interprets a collected profile, prioritises the most impactful issues and links them to source locations.
- The demo answer to "what's the biggest performance issue in this kernel?" ranked low utilisation, low occupancy (register and shared-memory pressure), shared-memory bank conflicts, uncoalesced shared accesses and long scoreboard stalls, then concluded the kernel was memory-latency bound.

## Studio relevance

Worth knowing the moment the studio writes or tunes its own GPU code (cuTile, Warp, custom ComfyUI nodes): it turns profiler output into a ranked to-do list. Before pointing it at proprietary code, check what profile data it sends to NVIDIA; the slide does not say. It needs the Director's NVIDIA developer account, so the Director signs in, not an agent.

## Claims

- [verified] Nsight Copilot is integrated into the Nsight Compute UI and is free with an NVIDIA developer account. (via: NVIDIA CUDA 13.4 livestream slide, screenshot shared by the Director 2026-10-07)
- [unverified] Profile data is processed by an NVIDIA-hosted model (not stated on the slide; check before use on proprietary kernels).

## Sources

- [user] NVIDIA CUDA 13.4 livestream slide, screenshot shared by the Director 2026-10-07 ("Nsight Copilot in Nsight Compute")
