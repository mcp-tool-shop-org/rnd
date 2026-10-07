---
id: 2026-10-07-cuda-graphs
title: CUDA Graphs
date: 2026-10-07
kind: concept
relevance: reference
fields: [gpu-computing, systems-performance]
tags: [cuda-graphs, pytorch, vllm, llama.cpp, launch-overhead]
---

## Summary

CUDA Graphs record a sequence of GPU work (kernel launches, copies) once, with its dependencies, then replay the whole sequence with one call. Setup and validation are paid once, and the per-launch CPU overhead that dominates small, repetitive workloads disappears.

## Key points

- Lifecycle: capture (stream capture via `cudaStreamBeginCapture`, or the explicit graph API) → instantiate (validate, allocate, build an executable graph) → replay (`cudaGraphLaunch`).
- PyTorch: `torch.cuda.graph` / `torch.cuda.CUDAGraph`; inputs must keep static shapes and be updated in place (`copy_()`) before each replay; `torch.compile(mode="reduce-overhead")` uses graphs automatically.
- vLLM uses graph modes to speed up repetitive decode steps.

## Studio relevance

Mostly already working for us under the hood: LLM engines use graphs for single-token decoding, where launch overhead is large relative to the work. Diffusion steps are big kernels, so graphs buy little in ComfyUI. If the studio ever runs a custom torch inference loop, `reduce-overhead` is the cheap thing to try.

## Claims

- [unverified] llama.cpp enables CUDA graphs by default for single-sequence decoding (from memory; check the current build).

## Sources

- [primary] https://developer.nvidia.com/blog/cuda-graphs/ — NVIDIA Technical Blog (link shared by the Director)
- [primary] https://docs.nvidia.com/cuda/cuda-programming-guide/04-special-topics/cuda-graphs.html — CUDA Programming Guide
- [primary] https://docs.nvidia.com/dl-cuda-graph/ — NVIDIA CUDA Graph guide for deep learning
- [primary] https://pytorch.org/blog/accelerating-pytorch-with-cuda-graphs/ — PyTorch blog
- [primary] https://docs.vllm.ai/en/stable/design/cuda_graphs/ — vLLM design docs
- [secondary] https://leimao.github.io/blog/PyTorch-CUDA-Graph-Capture/ — Lei Mao
- [secondary] https://arxiv.org/html/2501.09398v1 — arXiv 2501.09398
- [user] AI search summary pasted by the Director 2026-10-07
