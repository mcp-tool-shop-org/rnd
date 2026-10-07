---
id: 2026-10-07-decision-ai-jam-sessions-cuda-13-4
title: "Decision: ai-jam-sessions keeps CUDA 13.4"
date: 2026-10-07
kind: decision
relevance: act
fields: [gpu-computing, ai-infrastructure]
tags: [cuda, ai-jam-sessions, offrig, runpod, decision]
---

## Summary

The Director ruled on 2026-10-07 that ai-jam-sessions stays on CUDA 13.4. This
supersedes the research recommendation in [[2026-10-07-cuda-13-on-rented-pods]]
to hold pod images at 12.8 / cu128.

## Key points

- Hosts: 13.4 needs an R615-branch driver for its new features. Under 13.x
  minor-version compatibility, a 13.4 build that uses no 13.4-only feature still
  runs on R580+. A host on a 12.x-era driver (R570 or older) runs none of it, so
  filter pods by host driver.
- PyTorch: no cu134 wheels exist. Use the cu130 wheels (torch 2.9+; the PyPI default
  from 2.11). A wheel bundles its own CUDA runtime, so it runs on a 13.4 driver.
- GPUs: Turing and later. The A40 (Ampere, sm_86) is supported; pre-Turing cards
  (Maxwell, Pascal, Volta) are not.
- llama.cpp and any CUDA extensions are rebuilt against 13.4 (sm_86 for the A40,
  sm_120 for the local 5090).
- An unconfirmed report says CUDA 13.2 produced garbled GGUF output in one
  toolchain: smoke-test GGUF output after rebuilding.
- The local Robot rig (driver 617.14, nvcc 13.4) already meets every requirement
  ([[2026-10-07-robot-rig-cuda-stack]]).

## Studio relevance

Applies to ai-jam-sessions pod images and the offrig jam profile. Update the
image's CUDA pin, select hosts with an R615+ driver, and run a GGUF smoke test
after the first rebuild.

## Sources

- [user] The Director's ruling in the R&D session, 2026-10-07
- [primary] https://docs.nvidia.com/cuda/archive/13.4.1/cuda-toolkit-release-notes/index.html — CUDA 13.4.1 release notes
