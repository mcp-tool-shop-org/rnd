---
id: 2026-10-07-pod-host-checks-driver-and-download
title: Rented GPU pods — the driver and download speed vary per host, so check both first
date: 2026-10-07
kind: rig-fact
relevance: act
fields: [ai-infrastructure, gpu-computing]
tags: [runpod, offrig, driver, vllm, cuda-13, download-speed, huggingface, nvidia-smi, host-check]
---

## Summary

Measured on rented RunPod hosts by aspire-si on 2026-10-07. Two properties that
decide whether a paid run can succeed vary per *host*, not per GPU type:

- the NVIDIA driver;
- /workspace and Hugging Face download speed.

Check both in the first 30 seconds, before installing or downloading anything.

## Key points

- **Driver vs current wheels:**
  - `pip install vllm` (0.31.0) pulls torch 2.13.0+cu130, which needs an R580+
    driver ([[2026-10-07-cuda-13-on-rented-pods]]);
  - an A100-SXM4-80GB host on driver 570.195.03 (CUDA 12.8) refused to
    initialise torch ("driver too old");
  - another A100 on 580.126.16 worked, and the RTX PRO 6000 hosts had 580.x.
- **nvidia-smi output changed:** newer drivers print `CUDA UMD Version: 13.4`
  where older ones printed `CUDA Version:`. Parsers must accept both. The Robot
  rig's driver 617.14 prints the UMD form.
- **Download speed varies within one data centre (eur-is-2):**

  | pod | /workspace write | one HF stream | outcome |
  |---|---|---|---|
  | slow RTX PRO 6000 | 32 MB/s (network filesystem) | 1.9 MB/s | 26 GB in 31 min; run missed its cap, $1.65 lost |
  | an hour later, same filesystem | 238–540 MB/s | 59–74 MB/s | ~65 GB of Qwen 32B in about 2 min |

- **The gate:** aspire-si's `examples/sft-experiment/host_check.py --speed`
  measures driver, GPU and both speeds in about 30 s before any download.

## Studio relevance

Every offrig job profile and every pod image should:

1. read the driver from `nvidia-smi`, accepting both print forms, and refuse a
   CUDA 13 wheel below R580;
2. measure the /workspace write rate and one HF stream before downloading
   weights.

Abort and re-rent rather than paying for a slow host. This hardens the "check
the test bed before paying" rule.

## Claims

- [verified] torch 2.13.0+cu130 (pulled by vllm 0.31.0) failed with "driver too old" on an A100 host with driver 570.195.03 and worked on one with 580.126.16. (via: aspire-si pod runs, reported by session A 2026-10-07)
- [verified] Within data centre eur-is-2, /workspace write speed ranged from 32 MB/s to 238–540 MB/s an hour apart. (via: aspire-si pod runs, reported by session A 2026-10-07)
- [verified] Driver 617.14 on the Robot rig prints "CUDA UMD Version" rather than "CUDA Version". (via: session A report, and a grep for "CUDA Version" on the rig returning nothing, 2026-10-07)

## Sources

- [rig] aspire-si rented-pod runs on 2026-10-07, measured by session A
- [primary] https://github.com/mcp-tool-shop-org/aspire-si/blob/main/examples/sft-experiment/host_check.py — host gate
- [primary] https://github.com/mcp-tool-shop-org/aspire-si/blob/main/docs/runs/2026-10-07-next-runs-plan.md — run plan
