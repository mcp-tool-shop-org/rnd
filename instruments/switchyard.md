---
id: switchyard
title: switchyard — the device-aware model router (in build)
date: 2026-10-09
kind: instrument
relevance: act
fields: [studio-tooling, gpu-computing]
tags: [instrument, router, npu, openvino, offrig]
instrument_status: planned
invoke: "Not built yet. Planned: `switchyard route --task <t> [--min-<metric> x] [--max-latency-ms y] --json`; `switchyard run <spec>` for pre-registered experiments; `switchyard table`."
when: "Choosing which model, engine, device (NPU / iGPU / CPU / 5090 / rented GPU) and settings to use for a task, from measured receipts; or running a pre-registered device experiment that fills a gap in the routing table."
where: "github.com/mcp-tool-shop-org/switchyard (internal, going public as a prototype) · clone E:/AI/switchyard"
---

## Summary

A dispatcher: given a task and its constraints, it picks the model, engine, device and settings from a routing
table where **every row cites a receipt**, and explains the choice. OpenVINO's AUTO picks a device for a model you
already chose; nothing picks the model. That gap is the product.

Ordered by the Director on 2026-10-09 ("start building this out, so that we can start running experiments to get
the data we need"). **Grok** builds the core; **Kimi** owns the Intel lane (the OpenVINO adapter, experiments
E1–E3); R&D reviews every PR; the Publisher holds the devices and merges.

## Key points

- **Experiment-first.** A pre-registered harness produces routing rows. The first experiments:
  - E1: cold vs warm start, per device;
  - E2: Qwen3-Embedding-0.6B on the Intel devices;
  - E3: small OpenVINO LLMs on the NPU and iGPU;
  - E4: NPU/iGPU/5090 contention;
  - E5: "fill the card", the largest context per model that stays fully on the GPU.
- **It imports what exists:** the calibration chain, the math ladder, and the npu-probe and NLI-floor receipts.
- **The tie-in with offrig:** it reads calibrate runs and budget JSON (v1). It emits a versioned route
  decision, with offrig plan suggestions for remote routes. It **never** rents, sets caps or opens offrig's
  store, and a verify route needs a matching calibration receipt.
- **Guards:** a 5090 step needs a Publisher grant, an NPU step a ledgered session; the 15-minute rest; the
  device resolver refuses `GPU.1` (the 5090 in OpenVINO) and decides Intel by vendor id.
- **Design draft:** a self-repairing runner with an allowlist of measurement-neutral repairs, a fingerprint
  checked around and between repairs, and escalation for everything else. Reviewed by Kimi.
- **The bar:** 90% coverage before a 0.1.0 prototype release. Going public is the Director's call.

## Studio relevance

The router is the product the NPU and verifier work points at: the right model on the right device, from
receipts, not guesses. The brief lives in R&D's memory (`switchyard-router-buildout-handoff.md`, with Kimi's
`kimi-switchyard-intel-lane-handoff.md`) and is snapshotted into the repo's `docs/handoff/`.

## Sources

- [primary] switchyard Phase 0 pull request, 2026-10-09 — https://github.com/mcp-tool-shop-org/switchyard/pull/1
