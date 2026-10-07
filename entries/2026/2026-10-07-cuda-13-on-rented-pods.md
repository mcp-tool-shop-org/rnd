---
id: 2026-10-07-cuda-13-on-rented-pods
title: Moving rented GPU pods from CUDA 12.8 to CUDA 13.x
date: 2026-10-07
kind: finding
relevance: act
fields: [gpu-computing, ai-infrastructure]
tags: [cuda, driver, pytorch, runpod, offrig, a40, ai-jam-sessions]
---

## Summary

Asked by the ai-jam-sessions session: would CUDA 13.4 help its rented pods
(A40, torch 2.11 cu128, SoulX-Singer fp16)? It would not. CUDA 13.x needs
a newer host driver, PyTorch ships CUDA 13.0 builds at most, and nothing in 13.4
speeds up fp16 PyTorch on Ampere. Moving to 13.x is a compatibility change, not
a performance one.

## Key points

- Driver floors: CUDA 13.0 needs the R580 branch (Linux 580.65.06); 13.1 R590,
  13.2 R595, 13.3 R610, 13.4 R615. Same branches on Windows.
- Minor-version compatibility holds inside 13.x: a 13.x app runs on any R580+
  driver, but 13.4's new features need R615+. A 12.x-era driver (R570 or older)
  runs no 13.x app at all.
- CUDA 13.0 dropped Maxwell, Pascal and Volta. Turing and later remain; Ampere
  (A40, sm_86) is supported through 13.4.
- PyTorch: cu130 wheels from 2.9; from 2.11 the default PyPI build is CUDA 13.0.
  No cu132/cu134 wheels were found.
- 13.4's cuBLAS work (FP64 emulation, grouped GEMM) targets Blackwell and Rubin.
- An unconfirmed secondary report says CUDA 13.2 produced garbled GGUF output in
  one toolchain; worth knowing before rebuilding llama.cpp on 13.2.

## Studio relevance

Recommendation for the jam pods: stay on CUDA 12.8 / cu128 until a dependency
demands 13.x. If moving, require a host driver of R580 or later per provider,
use torch with cu130, and rebuild CUDA extensions. The real speed levers for
SoulX are elsewhere: batching or running several takes in parallel on one GPU
(the model uses about 4 GB of a 48 GB A40), and a smaller, cheaper GPU class.
(The Director's CUDA 13.4 ruling of 2026-10-07 is for si-jam-sessions, not this
pipeline: [[2026-10-07-decision-si-jam-sessions-cuda-13-4]].) The Robot rig's
driver (617.14) already clears 13.4's R615 floor
([[2026-10-07-robot-rig-cuda-stack]]).

## Claims

- [verified] CUDA 13.4 requires an R615-branch driver; CUDA 13.0 requires R580. (via: CUDA 13.4.1 and 13.0.0 release notes, read by a research agent 2026-10-07)
- [verified] CUDA 13.0 removed support for Maxwell, Pascal and Volta. (via: CUDA 13.0.0 release notes, read by a research agent 2026-10-07)
- [unverified] PyTorch 2.11 makes CUDA 13.0 the default PyPI build.
- [unverified] CUDA 13.2 produced garbled GGUF output in one toolchain (search snippet of Unsloth docs, not read directly).

## Sources

- [primary] https://docs.nvidia.com/cuda/archive/13.4.1/cuda-toolkit-release-notes/index.html — CUDA 13.4.1 release notes
- [primary] https://docs.nvidia.com/cuda/archive/13.0.0/cuda-toolkit-release-notes/index.html — CUDA 13.0.0 release notes
- [primary] https://dev-discuss.pytorch.org/t/transitioning-pypi-cuda-wheels-to-cuda-13-0-as-the-stable-release-2-11/3325 — PyTorch dev-discuss
- [user] Question from the ai-jam-sessions session, 2026-10-07; research agent (claude-sonnet-5-5) web search
