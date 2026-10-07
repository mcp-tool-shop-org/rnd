---
id: 2026-10-07-cuda-python-ecosystem
title: CUDA Python ecosystem (cuda.core, cuda.compute, nvmath, CuPy, Numba, cuTile)
date: 2026-10-07
kind: concept
relevance: watch
fields: [gpu-computing, python]
tags: [cuda-python, cupy, numba, cutile, nvmath, cccl]
---

## Summary

NVIDIA's set of packages for driving the GPU from Python without writing C++ wrappers. They range from drop-in array libraries, through just-in-time kernel compilers, to thin bindings over the CUDA driver and runtime.

## Key points

- `cuda.bindings` / `cuda.core`: low-level and Pythonic access to CUDA (memory, streams, devices, multi-GPU).
- `cuda.compute`: CCCL's parallel primitives (sort, reduce, scan, transform) from Python; version 1.1 can compile ahead of time on machines with no GPU.
- `nvmath-python`: GPU (and CPU) math libraries such as GEMM and FFT.
- Kernel DSLs: `cuda.tile` (cuTile) for tile-based kernels ([[2026-10-07-cuda-tile-programming]]).
- Three levels of effort: CuPy (NumPy on the GPU, no kernel code), Numba (`@cuda.jit` custom kernels), and the raw bindings (full control).

## Studio relevance

The practical lever for the studio is CuPy: pipeline steps that are NumPy-heavy (texture projection, mask math, batch image metrics in the turnaround and sprite stages) can often move to the GPU with little more than an import change. Do it only after profiling shows a CPU-bound step. Watch the interpreter: the default `python` on this rig has CPU-only torch ([[2026-10-07-robot-rig-cuda-stack]]).

## Claims

- [unverified] CUDA Python reached 1.0 with stable APIs (inferred from the NVIDIA blog post's title).
- [unverified] The pasted summary names a `cuda.lang` DSL; no primary source for that name was found, so it may be a summary error.
- [unverified] Numba's CUDA target is now maintained as the separate numba-cuda package (from memory; check before relying on it).

## Sources

- [primary] https://developer.nvidia.com/cuda/python — CUDA Python platform page
- [primary] https://developer.nvidia.com/blog/cuda-python-1-0-stable-apis-one-foundation-full-platform-access/ — NVIDIA Technical Blog
- [primary] https://docs.nvidia.com/cuda/cuda-programming-guide/02-basics/intro-to-cuda-python.html — CUDA Programming Guide
- [primary] https://pypi.org/project/cuda-python/ — PyPI
- [primary] https://cupy.dev/ — CuPy
- [secondary] https://thenewstack.io/nvidia-finally-adds-native-python-support-to-cuda/ — The New Stack
- [secondary] https://learning.rc.virginia.edu/courses/parallel-computing-introduction/acc_python_cuda/ — UVA Research Computing course
- [user] AI search summary pasted by the Director 2026-10-07
