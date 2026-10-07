---
id: aspire-sft-experiment
title: aspire-si experiment kit — dataset build, both-order judging, rented-pod host gate
date: 2026-10-07
kind: instrument
relevance: reference
fields: [machine-learning, evaluation, ai-infrastructure]
tags: [instrument, dataset, llm-as-judge, bootstrap, runpod, host-check]
instrument_status: shipped
invoke: "python examples/sft-experiment/<tool>.py in a clone of aspire-si; host_check.py --speed before any paid pod download"
when: "Building teacher-written datasets, judging pairs without position bias, or gating a rented GPU pod before spending on it."
where: "github.com/mcp-tool-shop-org/aspire-si, examples/sft-experiment/"
---

## Summary

Tools inside aspire-si's `examples/sft-experiment/`:

- **build_dataset**: teacher-written data, with eval-prompt dedupe by embeddings.
- **clean_dataset**: cleans the built data.
- **pairwise_teacher**: A/B judging in both orders.
- **judge_eval**: scores a judge with a prompt-clustered bootstrap.
- **host_check**: GPU, driver, /workspace-write and HF-stream speed gate for
  rented pods, about 30 s.

## Studio relevance

`host_check.py --speed` is the gate described in
[[2026-10-07-pod-host-checks-driver-and-download]]. Run it before downloading
weights on any offrig or RunPod host. `pairwise_teacher` encodes the both-orders
rule from [[2026-10-07-qwen32b-judge-position-bias]].
