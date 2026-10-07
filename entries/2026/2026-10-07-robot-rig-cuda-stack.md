---
id: 2026-10-07-robot-rig-cuda-stack
title: Robot rig CUDA stack, measured 2026-10-07
date: 2026-10-07
kind: rig-fact
relevance: act
fields: [studio-rig, gpu-computing]
tags: [rtx-5090, driver, nvcc, pytorch, comfyui]
---

## Summary

What the Robot rig (Omen 45L, RTX 5090) actually runs, measured on the machine.

## Key points

- GPU: NVIDIA GeForce RTX 5090, compute capability 12.0 (consumer Blackwell, sm_120), driver 617.14.
- CUDA compiler: nvcc 13.4, V13.4.59.
- ComfyUI embedded Python: torch 2.12.0+cu130, arch list includes sm_120, so the GPU is fully supported.
- Default `python` on PATH (3.10.11): torch 2.14.0+cpu, with **no CUDA**.

## Studio relevance

Action: decide interpreter policy. Any GPU script run with plain `python` silently falls back to the CPU. Either install a CUDA build of torch in that interpreter, or rule that GPU scripts always name their interpreter (ComfyUI's embedded Python or a project venv). Re-measure after driver or toolkit upgrades.

## Claims

- [verified] The default python's torch is a CPU-only build (2.14.0+cpu). (via: python -c "import torch" on the rig, 2026-10-07)
- [verified] ComfyUI's torch 2.12.0+cu130 includes sm_120 in its arch list. (via: ComfyUI embedded python on the rig, 2026-10-07)

## Sources

- [rig] nvidia-smi --query-gpu=name,driver_version,compute_cap
- [rig] nvcc --version
- [rig] E:/AI-Models/ComfyUI_windows_portable/python_embeded/python.exe -c "import torch"
- [rig] python -c "import torch" (default Python 3.10 on PATH)
