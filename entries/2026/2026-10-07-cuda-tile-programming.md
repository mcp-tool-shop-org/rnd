---
id: 2026-10-07-cuda-tile-programming
title: CUDA Tile programming (cuTile Python, cuda::tiles, Tile IR)
date: 2026-10-07
kind: concept
relevance: watch
fields: [gpu-computing, compilers]
tags: [cutile, tile-ir, kernels, cuda]
---

## Summary

A block-level way to write GPU kernels: instead of computing one thread's index and work, a kernel loads a whole tile of an array, operates on the tile as a value, and stores it back. The compiler decides how many threads to use and how to map the work onto them. Python (`cuda.tile`) and C++ (`cuda::tiles`) share one compiler backend, CUDA Tile IR.

## Key points

- Tiles are fixed-size multidimensional arrays whose shapes and element types are known at compile time; every dimension is a power of two.
- One logical control-flow path per block, so per-thread branch divergence is not the programmer's concern.
- Partition views map an array into tile-sized regions with block-aligned indexing.
- The C++ API arrives in CUDA 13.3; 13.4 adds dependent-launch support for tile kernels.
- NVIDIA's TileGym skills cover writing, autotuning and converting cuTile kernels (to Triton or Julia); see [[2026-10-07-nvidia-agent-skills-catalog]].

## Studio relevance

This is the most approachable route to a custom GPU kernel if the studio ever needs one: it hides the coalescing and shared-memory tiling that SIMT kernels make you do by hand ([[2026-10-07-locality-aware-programming]]). Open question: whether it runs on the 5090 at all ([[2026-10-07-cutile-on-sm120]]).

## Claims

- [verified] The C++ tile API (cuda::tiles) is available from CUDA Toolkit 13.3. (via: CUDA Programming Guide 'Writing Tile Kernels', fetched 2026-10-07)
- [verified] Tile dimensions must be powers of two with shapes known at compile time. (via: CUDA Programming Guide 'Writing Tile Kernels', fetched 2026-10-07)
- [unverified] CUDA 13.4 adds programmatic dependent launch (PDL) for tile kernels.

## Sources

- [primary] https://docs.nvidia.com/cuda/cuda-programming-guide/02-basics/writing-tile-kernels.html — CUDA Programming Guide (link shared by the Director)
- [secondary] https://www.linkedin.com/posts/nvidia-ai_cuda-134-brings-changes-across-the-toolkit-activity-7513424705010315264-K0Ou — NVIDIA AI LinkedIn post
