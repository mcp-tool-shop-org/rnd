---
id: 2026-10-07-cuda-compute-fabric-transport
title: CUDA Compute Fabric Transport (CFT)
date: 2026-10-07
kind: concept
relevance: reference
fields: [gpu-computing, networking, data-center-hardware]
tags: [cft, nvlink, nccl, nvshmem, multi-gpu]
---

## Summary

A low-level driver API in CUDA 13.4 for people who write communication libraries (the authors of NCCL or NVSHMEM), not for application teams. It moves data across NVLink-connected GPUs by addressing named logical endpoints instead of peer virtual addresses.

## Key points

- Unicast logical endpoints: point-to-point targets owned by one device and its bound memory.
- Multicast logical endpoints: group operations such as multicast and reductions.
- Asynchronous put, get and reduce across peers.
- CFT handles pair a logical-endpoint ID with a memory offset, replacing peer virtual addresses.
- Cliques: dynamic groups of GPUs that can reach each other at a given capability level.

## Studio relevance

No use on a single-GPU rig. Field knowledge for how multi-GPU communication is being re-plumbed underneath NCCL.

## Claims

- [unverified] CFT targets communication-library developers rather than application teams.

## Sources

- [primary] https://docs.nvidia.com/cuda/cuda-programming-guide/04-special-topics/compute-fabric-transport.html — CUDA Programming Guide
- [primary] https://developer.nvidia.com/nvshmem — NVSHMEM
- [aggregator] https://www.fullstack.com/labs/resources/blog/cuda-13-4-update-1-what-early-adopters-are-hitting — Fullstack Labs
- [aggregator] https://www.a90skid.com/nvidia-cuda-13-4-adds-windows-on-arm-and-rubin-preview-support/ — a90skid
- [aggregator] https://wccftech.com/nvidia-cuda-13-4-support-windows-on-arm-ahead-of-rtx-spark-launch/ — Wccftech
- [user] AI search summary pasted by the Director 2026-10-07
