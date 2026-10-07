---
id: 2026-10-07-uv-extra-index-priority-cpu-torch
title: "uv gotcha: --extra-index-url outranks --index-url, so Windows gets CPU torch"
date: 2026-10-07
kind: finding
relevance: reference
fields: [python, developer-tools, gpu-computing]
tags: [uv, pytorch, cuda, windows, packaging, gotcha]
---

## Summary

The first attempt at the studio's GPU Python environment installed with
`uv pip install torch==2.14.1 --index-url https://download.pytorch.org/whl/cu130 --extra-index-url https://pypi.org/simple`
and quietly got `torch 2.14.1+cpu`. uv searches `--extra-index-url` indexes
*before* `--index-url`, so the PyPI wheel won, and PyPI's Windows torch has no CUDA.

## Key points

- In uv, extra indexes take priority over the default index. That is the reverse
  of what many people expect from pip habits.
- The install exits 0 and imports fine. Only `torch.cuda.is_available()` (or the
  `+cpu` version suffix) gives it away.
- Fix: install torch-family packages from the CUDA index alone, and pin the local
  version, e.g. `"torch==2.14.1+cu130" "torchvision==0.29.1+cu130" --index-url https://download.pytorch.org/whl/cu130`.
  Install everything else in a separate command.
- Always end a GPU environment install with a check that `torch.cuda.is_available()`
  is True and that `torch.version.cuda` is set.

## Studio relevance

Applies to every Windows venv that needs CUDA torch: the GPU Python
([[2026-10-07-robot-rig-cuda-stack]]), project venvs, and any pod image built with uv.

## Claims

- [verified] uv with --index-url (cu130) plus --extra-index-url (PyPI) resolved torch 2.14.1 to the +cpu build on Windows. (via: install on the Robot rig, 2026-10-07)

## Sources

- [rig] uv pip install into E:/AI/envs/gpu-py312, 2026-10-07; reinstall with the CUDA index alone fixed it
- [primary] https://docs.astral.sh/uv/concepts/indexes/ — uv documentation on index priority
