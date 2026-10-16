---
id: colab
title: Colab Pro+ — prepaid cloud GPUs for experiments
date: 2026-10-16
kind: instrument
relevance: act
fields: [studio-tooling, gpu-computing]
tags: [instrument]
instrument_status: planned
invoke: "google-colab-cli: `colab run --gpu A100 script.py [args]` (fresh VM, run, fetch outputs, tear down); `colab usage` for the balance"
when: "An experiment needs a GPU and isn't pinned to the rig's machine line. Use Colab's prepaid units before paying for RunPod when the GPU fits."
where: "github.com/googlecolab/google-colab-cli (Apache-2.0); Linux and macOS only, so on the rig it runs in WSL Ubuntu"
---

## Summary

`google-colab-cli` is Google's command-line tool for Colab runtimes.
- **Runtimes:** it starts CPU, GPU (T4, L4, G4, A100, H100) and TPU (v5e1, v6e1) machines.
- **Code:** it runs local scripts or notebooks on them, and moves files in and out.
- **The one-shot form:** `colab run` provisions a machine, runs a script, returns the outputs and releases the
  machine.

The studio holds a Colab Pro+ subscription with prepaid compute units. On 2026-10-16 the balance was about 1,208
units.

## Studio relevance

- **Approved for experiments (Director, 2026-10-16), and meant to be used.** The units are prepaid, not a
  per-token API, so the no-paid-API rule doesn't bar them.
- **Order of reach for a GPU:**
  1. the 5090, under a grant;
  2. Colab units, when the job fits Colab's GPUs;
  3. RunPod through offrig, for a model too big for Colab or a job that needs a pod's control.
- **Not for ASPIRE card runs.** Those are pinned to the 5090's machine line.
- **Good fits:** embedding trials, small fine-tunes and evaluations, batch inference on open models, and overflow
  work when the card is busy.

## Before first use (planned, not done)

- Install the CLI in WSL Ubuntu (`uv tool install google-colab-cli`), and authenticate the Director's Google
  account. That sign-in is the Director's to do.
- Check `colab usage` against the Resources page, and record each GPU's unit rate here. Use measured rates, never
  guessed ones.
- **Every job ends with `colab stop`, or uses `colab run`, which tears down by itself.** An idle session still
  spends units: a CPU session was seen using about 0.08 units an hour.
- Downloads onto a VM follow the same rules as on the rig: no secrets on the VM, and results come back through
  `colab download`.
