---
id: 2026-10-12-e4-npu-static-shape
title: E4 NPU arms needed a static shape
date: 2026-10-12
kind: finding
relevance: reference
fields: [local-inference]
tags: [switchyard, npu, openvino]
---

## Summary

Once the token count was fixed, E4's re-run measured its three 5090-alone rows in seconds. It then stopped at the first
NPU arm, which refused with "the NPU needs a static_shape BxL". The NPU compiles fixed shapes only, and E4's spec
gave its NPU arms none. A dated amendment (switchyard #66) set `static_shape` "1x256" on both NPU arms. No NPU row had
been measured, and E4 re-runs whole on the amended spec.

## Key points

- **Failure:** the spec omitted a field that the OpenVINO adapter requires on the NPU. The adapter refused before
  measuring, which is the designed behaviour.
- **Fix (#66):** a static shape of batch 1 and length 256 on `npu-alone` and `npu-with-5090`, with a dated amendment
  line in the spec header.
- **Why 256 fits:** the runner fits each model's prefix with that model's own tokenizer, so bge-base gets its own
  256-token prompt. Both NPU arms share the shape and the text, so the alone and paired arms compare like with like.
- **Check on the rows:** `truncated_tokens` should be 0, or 1 if the final `[SEP]` is cut. Anything larger is a
  failed step.
- **Handling:** the partial 5090 rows were moved out of `receipts/`, so no pair mixes two spec versions.

## Studio relevance

A spec review should check each arm against its adapter's required fields before device time. E1 already carried
the field, and E4 didn't. No change to the tools was needed: the adapter refused correctly.

## Claims

- [verified] E4's re-run stopped at the first NPU arm with the static-shape refusal, before any NPU row (via: the Publisher's run report and the receipts, 2026-10-12)

## Sources

- [primary] https://github.com/mcp-tool-shop-org/switchyard/pull/66 — the amendment and its R&D review
