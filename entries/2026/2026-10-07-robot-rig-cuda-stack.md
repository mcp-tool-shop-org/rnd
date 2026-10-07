---
id: 2026-10-07-robot-rig-cuda-stack
title: Robot rig CUDA stack, measured 2026-10-07
date: 2026-10-07
kind: rig-fact
relevance: reference
fields: [studio-rig, gpu-computing]
tags: [rtx-5090, driver, nvcc, pytorch, comfyui]
---

## Summary

What the Robot rig (Omen 45L, RTX 5090) actually runs, measured on the machine.

## Key points

- GPU: NVIDIA GeForce RTX 5090, compute capability 12.0 (consumer Blackwell, sm_120), driver 617.14.
- CUDA compiler: nvcc 13.4, V13.4.59.
- `nvidia-smi` on driver 617.14 prints `CUDA UMD Version: 13.4`, not the older
  `CUDA Version:`; scripts grepping for the old string find nothing
  ([[2026-10-07-pod-host-checks-driver-and-download]]).
- ComfyUI embedded Python: torch 2.12.0+cu130, arch list includes sm_120, so the GPU is fully supported.
- Default `python` on PATH (3.10.11): torch 2.14.0+cpu, with **no CUDA**. Left as is on purpose.
- **GPU Python (added 2026-10-07):** `python-gpu` (a launcher in `~/.local/bin`, on PATH)
  runs `E:/AI/envs/gpu-py312`: Python 3.12.13, torch 2.14.1+cu130, torchvision
  0.29.1+cu130, numpy. Smoke test: sees the RTX 5090 at sm_120, about 223 TFLOPS on
  an 8192² fp16 matmul. Add packages with
  `uv pip install --python E:/AI/envs/gpu-py312/Scripts/python.exe <pkg>`.

## Studio relevance

Decided 2026-10-07 (the Director): keep the default `python` as it is and use
`python-gpu` for GPU scripts. ComfyUI keeps its own embedded Python. Re-measure
after driver or toolkit upgrades.

## Claims

- [verified] The default python's torch is a CPU-only build (2.14.0+cpu). (via: python -c "import torch" on the rig, 2026-10-07)
- [verified] python-gpu runs torch 2.14.1+cu130 with CUDA available on the RTX 5090 (sm_120), about 223 TFLOPS fp16 matmul. (via: smoke test on the rig, 2026-10-07)
- [verified] ComfyUI's torch 2.12.0+cu130 includes sm_120 in its arch list. (via: ComfyUI embedded python on the rig, 2026-10-07)

## Sources

- [rig] nvidia-smi --query-gpu=name,driver_version,compute_cap
- [rig] nvcc --version
- [rig] python-gpu -c "import torch" with an 8192x8192 fp16 matmul timing
- [rig] E:/AI-Models/ComfyUI_windows_portable/python_embeded/python.exe -c "import torch"
- [rig] python -c "import torch" (default Python 3.10 on PATH)
