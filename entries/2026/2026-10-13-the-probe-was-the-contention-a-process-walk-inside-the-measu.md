---
id: 2026-10-13-the-probe-was-the-contention-a-process-walk-inside-the-measu
title: The probe was the contention: a process walk inside the measured window
date: 2026-10-13
kind: finding
relevance: act
fields: [benchmarking]
tags: [interlock, defect-class, instrument_perturbs_measurement, psutil, windows]
---

## Summary

interlock's shared runner (`run_interleaved`) opens a slot probe around every measured call. The probe exists to
record what else was busy on the machine, so a noisy slot can be explained. Its reader ranked the busiest other
processes by walking every process through psutil. On the rig that walk takes about 2.5 s. It ran once just before
each call and then back to back during it, keeping about one core busy on the same CPU and iGPU that some arms are
timed on. The instrument was the contention it was built to detect. The Publisher found it on 2026-10-13 through a
watcher test that overran its bound. No committed receipt is affected.

## Key points

- **Measured on the rig** (the Publisher, 2026-10-13, 497 processes): `_top_other` took 2.40, 2.12 and 2.46 s, and
  one `read_slot` 2.51 s.
- **Where it ran:**
  - `SlotProbe.open()` takes one synchronous sample right before the call;
  - a thread samples every 1 s while the call is in flight;
  - each sample walked every process (`process_iter`, then `cpu_percent` and `name` per process).
- **The ranking also said little:** "System Idle Process" and "System" ranked as the top "other" processes.
- **Exposure:**
  - the E1–E4 receipts predate the `top` field;
  - E4b and E5 use their own runners;
  - it matters before any shared-runner rerun.
- **The ruling** (R&D, 2026-10-13): fix it, keep the ranking, and move it out of the window.
  - Inside the window, read only system-wide counters (total CPU, RAM, disk).
  - After the call, and only for a slot whose CPU passed 30% (the only case the summary keeps names), rank
    processes from two snapshots about 1 s apart. Record it as `top_after_call`.
  - Always exclude pid 0, and keep excluding the run's own process tree.
  - Tests: one that fails today (the in-window samples never call the walk); one that the ranking appears only
    above 30%; one that pid 0 never appears.
  - One rig reading of the per-sample cost goes in the PR.

## Studio relevance

A new defect class, `instrument_perturbs_measurement`: the harness's own observation competes for the resource it
measures. It belongs beside [[2026-10-12-test-fakes-hide-the-platform]].
- **The check for reviews:** ask what every probe, sampler and watcher does while a measured call is in flight,
  and what it costs on the rig, not on a test fake.
- The fake slot reader in interlock #108 kept the test bound honest, but only a rig reading showed the cost.

## Claims

- [verified] On the rig with 497 processes, one `_top_other` process walk took 2.12–2.46 s and one `read_slot` 2.51 s. (via: the Publisher's rig reading, 2026-10-13)
- [verified] The slot probe takes one synchronous sample in `open()` before the measured call, then samples every 1 s on a thread until `close()`, and every sample called the process walk. (via: R&D reading interlock `src/interlock/harness/watch.py` and `runner.py` on main, 2026-10-13)
- [verified] The slot summary keeps top-process names only when the slot's CPU maximum passed 30%. (via: R&D reading `summarize_slot`, 2026-10-13)
- [unverified] The walk is slow because on Windows psutil cannot open some processes directly, and its fallback for those reads a snapshot of every process each time. (R&D's hypothesis; not measured)
- [unverified] "System Idle Process" (pid 0) ranks first because its CPU figure counts idle time. (R&D's reading of the observed ranking; psutil documentation not checked)

## Sources

- [rig] the Publisher's timing of `_top_other` and `read_slot` on the rig, 2026-10-13
- [primary] https://github.com/mcp-tool-shop-org/interlock/blob/main/src/interlock/harness/watch.py — `_top_other`, `read_slot`, `SlotProbe`, `summarize_slot`
- [primary] https://github.com/mcp-tool-shop-org/interlock/blob/main/src/interlock/harness/runner.py — where the runner opens the probe around `adapter.run`
- [user] The Publisher's report, and interlock #108 (test-only: a fake slot reader), 2026-10-13
