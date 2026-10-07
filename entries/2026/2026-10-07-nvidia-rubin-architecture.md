---
id: 2026-10-07-nvidia-rubin-architecture
title: NVIDIA Rubin / Vera Rubin platform
date: 2026-10-07
kind: concept
relevance: reference
fields: [data-center-hardware, gpu-computing]
tags: [rubin, vera, hbm4, nvlink, nvfp4, nvl72]
---

## Summary

Rubin is NVIDIA's data-center GPU generation after Blackwell, built as a six-chip platform: the Rubin GPU, the Arm-based Vera CPU, the NVLink 6 switch, the ConnectX-9 SuperNIC, the BlueField-4 DPU and the Spectrum-6 Ethernet switch. It is aimed at agentic and multi-step reasoning workloads at rack scale. CUDA 13.4 carries an early compiler preview for it.

## Key points

- Rubin GPU: TSMC 3 nm, about 336 billion transistors, around 50 PF of NVFP4 inference, third-generation Transformer Engine.
- HBM4: up to 288 GB and about 22 TB/s per GPU.
- Vera CPU: custom Arm design with 88 Olympus cores.
- Vera Rubin NVL72: 72 Rubin GPUs and 36 Vera CPUs in one liquid-cooled rack; larger configurations are named NVL144.
- Production ramped in mid-2026; a Rubin Ultra variant follows.

## Studio relevance

Reaches the studio only through rented cloud capacity (offrig) and as a signal of direction: FP4-class inference and huge HBM pools are where serving is heading, which shapes which quantisations upstream engines optimise first.

## Claims

- [unverified] Rubin GPU has 336 billion transistors on TSMC 3 nm and delivers 50 PF NVFP4 inference.
- [unverified] Each Rubin GPU carries up to 288 GB of HBM4 at about 22 TB/s.
- [unverified] Vera has 88 custom Olympus Arm cores.
- [unverified] Rubin's compute capability is 10.7 (sm_107); the figure came from aggregator and social posts, not NVIDIA docs.

## Sources

- [primary] https://developer.nvidia.com/blog/inside-nvidia-rubin-gpu-architecture-powering-the-era-of-agentic-ai/ — NVIDIA Technical Blog
- [primary] https://www.nvidia.com/en-us/data-center/technologies/rubin/ — NVIDIA product page
- [primary] https://nvidianews.nvidia.com/news/rubin-platform-ai-supercomputer — NVIDIA newsroom
- [secondary] https://en.wikipedia.org/wiki/Rubin_(microarchitecture) — Wikipedia
- [aggregator] https://vrlatech.com/nvidia-vera-rubin-architecture-explained/ — VRLA Tech
- [aggregator] https://www.thundercompute.com/blog/nvidia-rubin-architecture — Thunder Compute
- [user] AI search summary pasted by the Director 2026-10-07
