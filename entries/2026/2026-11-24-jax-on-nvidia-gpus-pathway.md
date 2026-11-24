---
id: 2026-11-24-jax-on-nvidia-gpus-pathway
title: Google + NVIDIA learning pathway — scale and serve JAX models on NVIDIA GPUs
date: 2026-11-24
kind: event
relevance: reference
fields: [gpu-computing, ml-training]
tags: [jax, xla, nvidia, gke, profiling, nsight-systems, xprof, sharding, learning-path]
---

## Summary

A Google for Developers learning pathway, made jointly with NVIDIA, that takes a JAX program from a single-GPU start to
multi-GPU training and export for serving. Four videos (Part 1 presented by a Google Cloud AI engineer and an NVIDIA developer
advocate; later parts name no presenters on the page) alternate with eight hosted codelabs, ending in a quiz badge. The page shows
no date, total length or licence, and links no code repository; the codelabs live on Google's codelabs site.

## Key points

- Order: (1) first JAX program on GKE with NVIDIA L4 GPUs, GPU visibility, XLA compilation and host-device transfer cost;
  (2) `jax.jit` tracing and avoiding recompilation; (3) profiling down to CUDA kernels with XProf and NVIDIA Nsight Systems;
  (4) a functional training loop with Optax (AdamW) on Fashion-MNIST; (5) fused attention through cuDNN and NVIDIA
  TransformerEngine; (6) multi-GPU training with `Mesh`, `PartitionSpec` and `NamedSharding`; (7) a decoder-only transformer in
  Flax NNX with Orbax checkpoints, trained on a multi-GPU GKE cluster; (8) AOT compilation, `jax.export` and `jax2tf` for
  TensorFlow Serving.
- Hardware assumed: NVIDIA L4 on GKE; multi-GPU GKE clusters for codelabs 6-7. No other GPU types, no Vertex AI, and no
  LLM-serving stack (vLLM, TensorRT-LLM, Triton, JetStream) on the page.
- The page names no NGC container tag and no JAX version (the session blurb mentions starting from an NVIDIA NGC container).

## Studio relevance

`reference`. The studio's GPU work runs PyTorch, vLLM and llama.cpp, not JAX, and our multi-GPU need is served by RunPod/Colab
single-card windows. Two parts carry over regardless of framework:
- **Codelab 3 (XProf + Nsight Systems down to kernels)** is the same skill our sizing runs need when a window stalls at engine start
  or recompiles; worth reading next time a judge run's time is unexplained.
- **Codelab 2 (recompilation)** is the JAX face of the same failure class as d5c a4 (a JIT build on the pod that ate the window).
Revisit only if a model we need ships JAX/Flax-only (see readouts `tensor-engine-knowledge` → `jax-xla`, which already covers
running JAX under WSL2).

## Sources

- [user] shared by the Director, 2026-11-24
- [primary] https://developers.google.com/learn/pathways/scale-and-serve-jax-models-on-nvidia-gpus — the pathway page (read
  2026-11-24 via a fetch; exact wording approximate)
- [primary] https://codelabs.developers.google.com/jax-gpu-01-getting-started — codelab 1 (codelabs 02-08 follow the same
  pattern: jax-gpu-02-jit-compilation, -03-profiling-debugging, -04-training-loop, -05-attention-gpu, -06-multi-gpu-training,
  -07-transformer-end-to-end, -08-serving-export)
- [primary] https://developers.google.com/learn/pathways/quizzes/scale-and-serve-jax-models-on-nvidia-gpus — the quiz
