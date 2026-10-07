---
id: 2026-10-07-cuda-13-4-developer-experience
title: CUDA 13.4 developer-experience changes (compiler, runtime, packaging)
date: 2026-10-07
kind: release
relevance: watch
fields: [gpu-computing, developer-tools, compilers]
tags: [cuda, nvcc, wddm, windows, gpudirect-storage, cuda-checkpoint]
---

## Summary

A livestream slide listing the smaller 13.4 changes. On the compiler side: better nvcc diagnostics and fast-math flags, JSON source-line output from the disassembler, and PTX-version selection in libNVVM. On the runtime side: a multithreading stall removed, memory-pool IPC on Windows, GPUDirect Storage improvements, and the driver shipping separately from the toolkit.

## Key points

- nvcc: `-fmax-errors=N` now applies to device code; a new narrowing-conversion warning; `-fno-signed-zeros` and `-ffinite-math-only`; UTF-8 source files.
- nvdisasm can emit source-line information in its JSON output.
- libNVVM can be told which PTX version to emit.
- cuda-checkpoint can write checkpoints straight to storage.
- Multithreaded apps: creating an event no longer waits behind pageable asynchronous copies.
- IPC for stream-ordered memory pools now works on Windows under WDDM.
- GPUDirect Storage: vectored I/O plus RAID1/RAID10 support.
- The driver and its components (Fabric Manager, IMEX, nvidia-fs) are now posted separately from the CUDA Toolkit.

## Studio relevance

The WDDM item is the one that touches this rig: the 5090 runs under WDDM, and memory-pool IPC is what lets two processes share GPU buffers allocated from a stream-ordered pool, which used to be Linux-only. That could matter if two pipeline processes (say a render server and a scorer) ever need to hand tensors across without a host round trip. Separate driver packaging means toolkit and driver upgrades can be decided independently.

## Claims

- [verified] nvcc 13.4 applies -fmax-errors=N to device code and adds a narrowing-conversion warning. (via: NVIDIA CUDA 13.4 livestream slide, screenshot shared by the Director 2026-10-07)
- [verified] 13.4 supports IPC for stream-ordered memory pools on Windows WDDM. (via: NVIDIA CUDA 13.4 livestream slide, screenshot shared by the Director 2026-10-07)
- [verified] Driver components (Fabric Manager, IMEX, nvidia-fs) are posted separately from the CUDA Toolkit from 13.4. (via: NVIDIA CUDA 13.4 livestream slide, screenshot shared by the Director 2026-10-07)

## Sources

- [user] NVIDIA CUDA 13.4 livestream slide, screenshot shared by the Director 2026-10-07 ("Developer Experience Improvements")
- [primary] https://docs.nvidia.com/cuda/cuda-toolkit-release-notes/index.html — release notes, for the full detail
