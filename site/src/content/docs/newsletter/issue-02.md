---
title: Puzzles with one answer, and a pod that never got ready
description: Two days of building the verifier's training data, and what a hung GPU pod changed in offrig.
issue: 2
date: 2026-10-11
highlights:
  - "<strong>Every Stage 1 puzzle is now solved by a program</strong>, and every defect a reader finds gets a class name."
  - "<strong>A rented pod looked ready and wasn't.</strong> offrig 1.1.0 waits for one real completion before it says ready."
  - "<strong>CUDA can be pinned:</strong> a profile can name exact host CUDA versions, or the version its software was built for."
  - "<strong>A slow start on the CPU</strong> wasn't reproduced by any storage or scheduling probe. It stays open."
---

Every claim below links to a brief or to the record it came from. Interim results are labelled as interim.

## The verifier's training data

ASPIRE is teaching Qwen3-8B to be a verifier before any domain training. Generated items needed a reader: of
49 candidates from a 235B writer, 15 passed as written. Hand-built batches did too: of 120, 91 passed. A
program now solves every logic puzzle and refuses any that has two answers, a spare clue, or a clue that gives
the answer away. Passing it isn't enough, though. Puzzles bent to fit the solver, and the same puzzle under new
names, were found by reading, then by a script. Each defect now gets a class name, so the checks can move from
people into tools.
→ [How is the verifier's training data checked?](../../briefs/verifier-training-data/)

## A pod that never got ready

On 2026-10-11 a rented pod's engine logged that startup had finished, then deadlocked. Its health check stayed
down while its model list answered, so the old readiness check passed. The run wrote nothing and cost $2.80.
offrig 1.1.0 now calls a recipe ready only when one completion returns an answer. It reports a hang after
3 minutes and leaves the pod up for a person to decide. That pod sat on a CUDA 13.2 host where the working runs
had used 13.0. That isn't shown to be the cause, but a profile can now pin the exact host CUDA versions.
These paths are tested against fakes and haven't been re-run on a rented pod.
→ [offrig on GitHub](https://github.com/mcp-tool-shop-org/offrig)

## CUDA, by the version the software needs

A profile can also say which CUDA its software was built for, such as 13.4 for a PyTorch nightly. Its rented host
must then be at least the oldest of that major version (13.0). That follows NVIDIA's minor-version compatibility,
and it matches what our CUDA 13.4 runs measured on RunPod's 13.0 hosts.
→ [Can the studio train on CUDA 13.4?](../../briefs/cuda-13-4/)

## Also

- **Phi-3.5-mini's first three CPU calls ran at about 7 tokens a second, then 21.** Neither a cold read from USB
  or NVMe nor any CPU scheduling setting reproduced it. It's recorded as open, and the next run samples the
  machine once a second through every call.
  → [switchyard](https://github.com/mcp-tool-shop-org/switchyard)
- **A seeding bug in the critic heads.** Dropout drew from an unseeded generator, so a head depended on the
  heads trained before it. The step-4 conclusions stand, because they rest on confidence intervals. The fix seeds
  the whole of training.
