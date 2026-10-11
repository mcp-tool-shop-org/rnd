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
- **The run path (#31, reviewed 2026-10-10).** Until a778696, `switchyard run` only did dry runs, and E1's
  receipts came from an uncommitted driver calling `run_interleaved`. Neither review caught that.
  - **What #31 adds:** `run_spec` puts the guards in front of that same function: interpreter, spec, flags,
    the blob lock, a receipt-name check, card checks, the rest, card checks again, then `run_interleaved`.
  - **Remaining gap, which blocks E4 only:** the "empty card" check asks only Ollama (`/api/ps`), which
    can't see a torch, ComfyUI or offrig job on the 5090, and a malformed reply reads as empty.
  - **Fixes asked for:**
    - an `nvidia-smi` VRAM ceiling, failing closed (`--query-compute-apps` is useless under Windows WDDM);
    - polling at intervals of 60 s or less during the 15-minute rest, not just at its two ends.
  - E2 and E3 don't touch the 5090, so they can run on #31 as is.
- **OpenVINO IR weights (#32, reviewed 2026-10-10).** E2's first cold load failed with "Empty weights data in bin
  file". The hub fetch took `openvino_model.xml` without its sibling `.bin`; E1 never hit this, because its
  embedders came through the single-file ONNX path.
  - **The fix:** fetch the `.bin` at the same pinned revision, so both files sit in one snapshot directory.
  - **Timing is unaffected:** the download sits outside every timer.
  - **Same pattern later:** ONNX external-data files (`.onnx_data`) would need it too.
- **E2's first run aborted with zero rows (issue #33, ruled 2026-10-10).** The NPU rejected the compiled l512
  binary at execute (`ZE_RESULT_ERROR_INVALID_NATIVE_BINARY`). The compile had succeeded, l128 had passed, and
  the health check afterwards was clean. Only `device_lost` and `hang` were recorded outcomes, and the abort
  flush wrote finished arms only, so in an A-B-A schedule nothing was kept.
  - **New outcome, `native_binary_rejected`:** NPU only, that exact code, at execute after a successful
    compile, and only if that shape hasn't already run in the run. It's scoped to model × device × static
    shape.
  - **What it doesn't do:** skip anything beyond same-key arms, or mark the NPU off.
  - **Replication:** one occurrence is provisional. "Not supported" needs a recurrence in a run with a fresh
    compile cache; if it passes there instead, the shape is flaky and doesn't route.
  - **Any abort** now flushes completed slots as `aborted: true` rows, which never import into the routing
    table.
  - **Implemented:** #34 (harness) and #35 (the E2 amendment; spec blob 69f3e6db → `bd88da4b`), both reviewed
    2026-10-10 and passed. The rerun uses that blob on a commit containing both, under a new run id, after the
    first run's compile cache is cleared and a health check passes.
- **E2's rerun (`e2-2026-10-10b`, issue #36, ruled 2026-10-10):**
  - **The l512 NPU rejection replicated** in a second fresh-cache run (same blob size, driver 32.0.100.5540).
    **Confirmed on the receipts (#37):** code `0x7800000f` at execute, a 1,208,717,446 B blob, compile 31.0 s.
    "Not supported at NPU 1×512 for Qwen3-Embedding-0.6B-fp16-ov on driver 32.0.100.5540"; a driver change
    reopens it.
  - **A CPU arm (8×2048) passed its cold call, then exceeded the fixed 60 s per-call bound at warmup.** That's
    a slow shape, not a stuck device.
  - **The abort flush worked:** 13 aborted rows (CPU 5, iGPU 6, NPU 2) were kept out of the table. The CPU hang
    row must also stay out of the table, since #36 ruled it a slow shape, not a stuck device.
  - **Ruling:** the bound becomes per arm on every device, by amendment to E2 and E3. The cold call is bounded
    at 600 s; warm calls at max(60 s, 3 × the arm's own cold call), capped at 600 s.
  - **Next:** a full rerun (`-10c`) without the l512 arm, then the b8 tail. E3 waits for the bound change,
    since its 8B generate arms would hit 60 s too.
- **E2 reads GO (`e2-2026-10-10c`, #41).** At the decision length, the iGPU embeds in 348.8 ms against the
  CPU's 544.4 ms (ratio 0.64). Parity was valid on all 14 rows.
- **The batch-8 tail (2026-10-10):**
  - **`-10c`:** the NPU compiler refused l512-b8 at compile time (`[NPU_VCL] Compiler returned msg`,
    `0x78000007`, "Target buffer size '2048' does not match source buffer size '256'").
  - **New outcome, `compile_rejected` (#43):** NPU only, raised inside `compile_model`, and both markers
    required. It's scoped like `native_binary_rejected` and never retried. The l512-b8 row was re-recorded
    from the log (#44), holding only the rejection evidence and nothing measured.
  - **`-10d`:** l2048-b8's compile ran 70 min, wrote 0 bytes and grew to 35.3 GB. It was stopped by hand.
    CTRL+C could not interrupt the native compile, so the process was hard-killed and no receipt exists.
    There was no pre-registered compile bound, so this is recorded as an abort, **not** a capability result.
    l2048-b8 has had its one try.
  - **Design flaw found:** under interleaving, l128-b8's repeats waited on l2048-b8's cold, so two runs lost
    l128-b8. The next tail runs arms sequentially, l128-b8 alone.
- **The rest became conditional (maintainer, 2026-10-10; #43, #46).**
  - The 15-minute rest is owed only after a run of over 30 minutes on the same devices that ended less than
    rest_s ago, and only for the remainder.
  - The harness takes the largest amount owed across every earlier receipt. A receipt with no times, or one
    that won't load, counts as long, timed from the file's save time.
  - The 5090 always rests in full: grants are messages, so nothing else enforces the card's rule.
  - #46 tops up a sleep that wakes a fraction of a second early.
- **Harness lessons from the night:**
  - A native compile can't be interrupted from Python, so a compile bound (15 min) and a memory stop
    (88%, sampled every 2 s) need a watcher that saves results and then ends the process.
  - A run-start marker file will make a killed run visible to the rest rule.
  - The NPU genai pipeline cache had to be keyed by compile config, since its KV cache is sized per prompt
    (#45). #42 fixed the genai call shape for NPU list prompts.
- **E3 is parked on memory (2026-10-10).**
  - `-b` stopped on the pipeline-cache bug. `-10c` piled up resident 8B pipelines in steps of 5–15 GB and was
    hard-killed at 89% RAM (95% in the rig monitor's 2-s samples). Neither produced a row.
  - The VRAM watchdog doesn't guard the switchyard environment, so the harness's own stop is the only guard.
  - **Amendment (R&D):** blocks per (model, device, compile config), at most one pipeline resident, a check
    that RAM is released between blocks, a pre-build memory guard, cheapest blocks first, and a descriptive
    drift block at the end. The viability floor and the other pre-registered settings are unchanged.
- **The Shared GPU/NPU Memory Override stays at 57% (36.1 GB)** for the series (maintainer, 2026-10-10). Every
  receipt records it in its environment capture.

## Studio relevance

The router is the product the NPU and verifier work points at: the right model on the right device, from
receipts, not guesses. The brief lives in R&D's memory (`switchyard-router-buildout-handoff.md`, with Kimi's
`kimi-switchyard-intel-lane-handoff.md`) and is snapshotted into the repo's `docs/handoff/`.

## Sources

- [primary] switchyard Phase 0 pull request, 2026-10-09 — https://github.com/mcp-tool-shop-org/switchyard/pull/1
