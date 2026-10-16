---
id: colab
title: Colab Pro+ — prepaid cloud GPUs for experiments
date: 2026-10-16
kind: instrument
relevance: act
fields: [studio-tooling, gpu-computing]
tags: [instrument]
instrument_status: shipped
invoke: "google-colab-cli 0.7.4 in WSL Ubuntu: `colab run --gpu L4 script.py [args]` (fresh VM, run, fetch outputs, tear down); `colab usage` for the rate and balance; wrap every `colab exec` in an outer `timeout`"
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

## Set up and measured (2026-10-16)

- **Installed:** `uv tool install google-colab-cli==0.7.4` in WSL Ubuntu.
  - The Director signed in. OAuth scopes: openid, profile, email, cloud-platform, colaboratory, drive.file.
- **Measured rates** (the `colab usage` rate line while each session ran, about 19:00Z):

  | Card | Units/hour | GPU memory | Host |
  |---|---|---|---|
  | T4 | 1.07 | 15,360 MiB | 2 cores, 12.7 GB RAM |
  | L4 | 1.54 | 23,034 MiB | 12 cores, 53.0 GB RAM |
  | A100 (40 GB as assigned) | 5.30 | 40,960 MiB | 12 cores, 83.5 GB RAM |

- **All three VMs:** driver 580.82.07, CUDA 13.0, Python 3.13.15, a 236 GB overlay disk.
- **Cost of the measurement:** 0.41 units (1,208.12 → 1,207.71). Most of it was one L4 session that hung for about
  16 minutes before it was stopped.
- **Cards were available on request** at that hour. A100s come as 40 or 80 GB, so a design that pins 80 GB
  must expect "card not available".

## Rules of use

- **Every job ends with `colab stop`, or uses `colab run`, which tears down by itself.** An idle session still
  spends units (a CPU session was seen at about 0.08 units an hour). After a job, `colab sessions` must be empty.
- **Wrap every `colab exec` in an outer `timeout`.** A call that blocks can hold a GPU session open, and the
  session keeps spending.
- **Read the rate during a session, and the balance after it.** The balance only moved after the session ended.
- **Each card type is its own machine line.**
  - Record the GPU and memory size from nvidia-smi, the driver, CUDA, the Ollama or torch version, and the host's
    CPU and RAM at the start of every session.
  - Refuse a run on a card other than its pin, and record it as "card not available".
- **CUDA:** the driver supports 13.0. NVIDIA's minor-version compatibility runs 13.x runtimes on a 13.0-capable
  driver: offrig's cloud-cu134 probe showed 13.4 on 13.0 hosts. A CUDA 13.4 stack may therefore work without
  cuda-compat, but check it on the first session that needs it before relying on it.
- **`google.colab.ai` doesn't work from the CLI.** It needs a secret that is "only fetched when running from
  the Colab UI". Use it from a notebook in the Colab UI or the VS Code extension. Comparison arms that need it
  run there, not through `colab run`.
- **Cost receipts:** each job records the card type, the units-per-hour rate, the balance before and after, the
  wall time and the units per task. Every design names a unit budget per phase for the Director's approval.
  Reaching the cap halts the run before the next task, and checkpointed work is kept.
- **Containment:** no tokens or secrets on the VM. Results come back through `colab download`, and VM output is
  untrusted.
- **What stays on the rig:** ASPIRE, interlock's measurement runs, and the fill and capacity searches. They
  measure the 5090 itself.
