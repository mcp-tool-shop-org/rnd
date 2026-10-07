---
id: 2026-10-07-decision-si-jam-sessions-cuda-13-4
title: "Decision: si-jam-sessions keeps CUDA 13.4"
date: 2026-10-07
kind: decision
relevance: act
fields: [gpu-computing]
tags: [cuda, si-jam-sessions, decision]
---

## Summary

The Director ruled on 2026-10-07 that si-jam-sessions (the Rust → WebAssembly
music-law repo, mcp-tool-shop-org/si-jam-sessions) keeps CUDA 13.4.

This ruling does not apply to ai-jam-sessions. An earlier version of this entry
named ai-jam-sessions by mistake: the R&D session misread the repo name. Its pods
stay on 12.8 / cu128 per [[2026-10-07-cuda-13-on-rented-pods]].

## Key points

- Generic 13.4 requirements, for any machine si-jam-sessions builds or runs on:
  - an R615-branch driver for 13.4 features (R580+ under minor-version
    compatibility for builds that use no 13.4-only feature);
  - Turing or later GPUs.
- The local Robot rig already meets both (driver 617.14, nvcc 13.4;
  [[2026-10-07-robot-rig-cuda-stack]]).

## Studio relevance

Recorded so the toolkit pin is not "corrected" downward later. How si-jam-sessions
uses CUDA is not described here; see that repo.

## Sources

- [user] The Director's ruling in the R&D session, 2026-10-07, with the repo name corrected by the Director
- [primary] https://docs.nvidia.com/cuda/archive/13.4.1/cuda-toolkit-release-notes/index.html — CUDA 13.4.1 release notes
