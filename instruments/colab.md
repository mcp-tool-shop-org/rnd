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
- **Re-measure with** [`scripts/colab/rates.sh`](https://github.com/mcp-tool-shop-org/rnd/blob/main/scripts/colab/rates.sh)
  (`GPUS="T4 L4 A100" ./rates.sh`, in WSL). It runs
  [`probe.py`](https://github.com/mcp-tool-shop-org/rnd/blob/main/scripts/colab/probe.py) on each card under an outer
  `timeout`, stops every session, and ends by listing any session still alive.
- **Cards were available on request** at that hour. The A100 came as 40 GB, and Pro+ likely never assigns
  80 GB (see the rules below).

## Rules of use

- **Teardown, three layers** (see `experiments/colab-bottlenecks`):
  1. **In the VM:** a watchdog thread with a hard deadline calls `google.colab.runtime.unassign()`, as does the
     script's top-level `finally`.
  2. **On the host:** `timeout --signal=SIGINT --kill-after=15s <secs> colab run …`.
  3. **Afterwards:** check that `colab sessions` is empty, and `colab stop` until it is. `colab run` swallows its
     own teardown errors, so its exit isn't proof of release.

  An idle session still spends units (a CPU session was seen at about 0.08 units an hour).
- **`--timeout` isn't a hang guard.** In 0.7.4 it sets one deadline at the call's start (not an inactivity
  timer), and the client never raises on it while output is pending. A kernel that never goes idle hangs the
  client forever, and a run that outlives the deadline may still fail its final reply fetch. Set it above the
  expected run time plus a margin on every `colab run`, and rely on the three layers for hangs.
- **Read the rate during a session, and the balance after it.** The balance only moved after the session ended.
- **Each card type is its own machine line.**
  - Record the card and memory from nvidia-smi, the driver, CUDA, `COLAB_RELEASE_TAG` (the image), Python, the
    Ollama or torch version, and the host CPU (`/proc/cpuinfo` model name) and RAM at the start of every session.
  - Assert the card in the first seconds, and on a mismatch call `runtime.unassign()` and record "card not
    available".
  - The image can't be pinned from the CLI, so a change in `COLAB_RELEASE_TAG` mid-study is a recorded machine
    line change.
  - An A100 comes as 40 GB. For 80 GB, request `--gpu H100` (its rate isn't measured yet).
- **T4:** request `--high-mem`. The default shape's 12.7 GB of host RAM can fail shard loading.
- **Python:** build the stack in a `uv venv`. Never pip into the image's system Python.
- **Weights:** pull from Hugging Face or the Ollama registry to `/content`. Never run Ollama's model store from the
  Drive mount.
- **CUDA:** the driver is 580.82 (CUDA 13.0). Our `experiments/cloud-cu134` record ran the 13.4 nightly on a 13.0
  driver (580.159) and passed Triton JIT, `torch.compile` and CUDA graphs on sm_80 and sm_100. Run
  `cu134_probe.py` once per Colab card type (T4 sm_75 and L4 sm_89 are untested) before relying on it.
- **`google.colab.ai` doesn't work from the CLI.** It needs a secret that only the browser front end serves.
  - It works from a notebook in the Colab UI.
  - The official `googlecolab/colab-mcp` drives a notebook in a browser tab, so it's a likely route for scripted
    use, untested.
  - It's free per call; only the VM's rate is spent.
  - Comparison arms that need it never run through `colab run`.
- **Cost receipts:** each job records the card type, the units-per-hour rate, the balance before and after, the
  wall time and the units per task. Every design names a unit budget per phase for the Director's approval.
  Reaching the cap halts the run before the next task, and checkpointed work is kept.
- **Containment:** no tokens or secrets on the VM. Results come back through `colab download`, and VM output is
  untrusted.
- **What stays on the rig:** ASPIRE, interlock's measurement runs, and the fill and capacity searches. They
  measure the 5090 itself.
