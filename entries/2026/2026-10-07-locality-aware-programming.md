---
id: 2026-10-07-locality-aware-programming
title: Locality-aware programming
date: 2026-10-07
kind: concept
relevance: reference
fields: [systems-performance, software-design, gpu-computing]
tags: [cache, numa, data-locality, locality-of-behaviour]
---

## Summary

Arranging code and data so the work happens near the data it needs, because moving data costs far more than computing on it. The idea appears at three scales: CPU caches, distributed systems, and (as a design principle) human readability.

## Key points

- Cache locality: CPUs fetch 64-byte cache lines. Spatial locality means touching neighbouring memory (contiguous arrays, not pointer-chasing lists and hash maps). Temporal locality means reusing data while it is still cached (loop tiling/blocking).
- Row-major languages (C, C++, NumPy) want the inner loop over the last index; iterating column-first misses cache on almost every access.
- NUMA: on multi-socket machines, pin threads near the memory bank they use.
- Distributed: move code to the data (MapReduce, Spark, Hadoop). Locality-aware request distribution (LARD) routes requests by content so each backend serves from a warm cache.
- Locality of Behaviour: a unit's behaviour should be readable in place, without chasing it through many files (the htmx and Tailwind philosophy).

## Studio relevance

On the GPU the same rule becomes coalesced memory access and shared-memory tiling, which is exactly what tile programming ([[2026-10-07-cuda-tile-programming]]) and libraries like cuBLAS ([[2026-10-07-cublas]]) do for you. Locality of Behaviour is a useful lens for the studio's own codebases and skills.

## Claims

- [unverified] LARD comes from Pai et al., "Locality-Aware Request Distribution in Cluster-based Network Servers", ASPLOS 1998.

## Sources

- [primary] https://htmx.org/essays/locality-of-behaviour/ — Carson Gross, htmx essay
- [user] AI search summary pasted by the Director 2026-10-07 (no citations in the original)
