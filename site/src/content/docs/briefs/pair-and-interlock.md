---
title: Where should this request run? NVIDIA PAIR and interlock
description: NVIDIA's new Personal AI Router spreads requests across the machines on a home network. The studio's interlock decides between devices inside one machine, from measurements. PAIR's own list of limits reads like a list of questions interlock has measured answers to.
date: 2026-10-13
status: research
shelf: not yet measured here (our own figures are cited from their receipts)
---

## The question

Once you run more than one local model, every request raises the same question: where should it run? NVIDIA
answered it this week with [PAIR](https://github.com/NVIDIA/Personal-AI-Router), the Personal AI Router. Its
1.0.0 release came out on 13 October 2026 under the Apache-2.0 licence. The studio has been answering the same
question for a month with its own router, interlock, from a different direction. Putting the two side by side
shows what each one knows, and what neither can see.

## What PAIR is

PAIR joins the computers on one local network into a cluster.
- **One front door for local applications:** each machine runs a proxy that local apps talk to as if it were
  Ollama, an OpenAI-compatible server or the Anthropic Messages API.
- **Each request goes to one machine** that has the requested model and a running engine. The engine can be
  Ollama, LM Studio or llama.cpp.
- **It works across operating systems:** Windows, Linux and macOS machines can all be paired together.
- **Prompts stay on your network** when every part is local. Machines join a cluster with a six-digit PIN.
- **Traffic between paired machines** uses mutual TLS. The plaintext side answers only the local machine.

What PAIR deliberately does *not* do matters as much:
- it doesn't pool GPU memory;
- it doesn't split one model across machines;
- it doesn't divide one request between nodes.

It's a traffic director for independent requests. It doesn't make one big GPU out of several small ones.

## How PAIR decides

PAIR's architecture document is unusually candid about its scheduler. Two mechanisms work in sequence:
- **The capability gate:** a request only goes to machines that advertise the model it names.
- **The ranking:** among those machines, PAIR orders them by *pending work plus GPU pressure*. Pending work
  counts the jobs queued or running. GPU pressure is the busiest GPU's utilisation, smoothed and bucketed into
  0 to 3 units at 40%, 70% and 85%. Ties break on pressure, then on the node's ID.

The same document lists what this ranking can't see:
- **Pressure, not capacity:** the GPU model, the free VRAM and measured latency aren't inputs.
- **Every job counts as one:** a three-token reply and a long generation weigh the same.
- **Whether the model is already loaded isn't considered:** a request can go to a machine that must cold-load
  the model while another holds it warm.
- **On a machine with several GPUs,** only the busiest one is seen.

Its roadmap names the next steps:
- KV-cache-aware scheduling;
- request queuing;
- "more scheduler variables".

## What interlock does instead

[interlock](https://github.com/mcp-tool-shop-org/rnd/blob/main/instruments/switchyard.md) (formerly switchyard)
works inside **one** machine: an RTX 5090, an Intel NPU, an Intel integrated GPU and the CPU. Each speaks to a
different engine. Instead of reading live load, it routes from **measured receipts**. Every routing fact comes
from a pre-registered experiment, with its rules written down before the run.

Read against PAIR's list of limits, interlock's experiments measure exactly what PAIR's ranking leaves out:

| PAIR's ranking doesn't see… | …interlock measured |
|---|---|
| whether a model is warm, and what a cold load costs | **E1:** what a cold load costs on each Intel device, in units of that device's own warm call, and when a model should stay resident |
| capacity: how much context a model can hold before it spills out of VRAM | **E5:** for each of six local 5090 models, the largest context window that stays fully resident. Four hold their full trained window; gemma4:31b holds 86016 of its 262144, and granite4.1:30b 43008 of its 131072 |
| whether two workloads slow each other down | **E4b:** running the 5090 beside the NPU or the iGPU changes its decode rate by under 1.4%, and the Intel devices' latency by at most about 5%, all inside a pre-registered ±10% band ([the E4b results](/rnd/newsletter/issue-04/)) |

E4b is the clearest example. PAIR's whole model assumes a busy GPU is a slower GPU, which is reasonable for one
device. interlock asked a narrower question: when two *different* devices share a machine, do they get in each
other's way? Within the noise we fixed in advance, they don't. So a router can treat them as independent lanes.

## Where each one fits

- **PAIR fits** when you own several machines and want their models to look like one service, with no thought
  about where each request lands. Its candour about its own limits is a model for how routers should document
  themselves.
- **interlock fits** when you want to know which device a task belongs on and why, with a receipt behind every
  rule. It's built for one machine with very different devices in it, and it routes from evidence, not from live
  load.
- **They don't compete.** A cluster of PAIR nodes could each run something like interlock internally. PAIR would
  pick the machine, and interlock the device within it.

## For the studio

- **Not on the studio rig today.** PAIR's port map gives its Ollama-compatible proxy port 11434 and moves Ollama
  itself to 11435 or above. On our machine 11434 is the 5090's Ollama server, which interlock's runs measure
  and its supervisor restarts by that address. Installing PAIR would move the server those runs depend on.
- **Worth a second look if the studio pairs another machine.** A second workstation alongside the 5090 rig is
  exactly PAIR's case. Before any install we'd run our own probe on it:
  - its licence (Apache-2.0, confirmed);
  - what its "telemetry" code does. The architecture shows host and GPU telemetry exchanged between paired
    nodes, not sent outside;
  - its security notes for the local network.
- **PAIR's limits are a to-do list for us.** Our E1 and E5 data answer the "warm or cold" and "capacity"
  questions for one machine. A router could use those receipts to break PAIR-style ties well.

## Caveats

- **PAIR hasn't run here.** Everything about it comes from its README and architecture document at v1.0.0.
- **interlock's figures come from its own committed receipts.** E5's card was completed on 13 October, after
  the spill rule was fixed and three models re-measured; rnd keeps trimmed copies of both runs. E1's per-device
  numbers are in interlock's receipts and aren't repeated here.

## Sources

- [NVIDIA/Personal-AI-Router](https://github.com/NVIDIA/Personal-AI-Router): the README and `docs/architecture.mdx` at v1.0.0 (2026-10-13), Apache-2.0
- [NVIDIA technical blog: NVIDIA PAIR](https://developer.nvidia.com/blog/nvidia-pair-virtual-inference-router-expands-available-compute-on-your-local-network/)
- [interlock's record in rnd](https://github.com/mcp-tool-shop-org/rnd/blob/main/instruments/switchyard.md): E1, E4b and E5, with links to their receipts
- [E4b: the 5090, NPU and iGPU run free together](https://github.com/mcp-tool-shop-org/rnd/blob/main/entries/2026/2026-10-12-e4b-block-2.md)
- [E5: how much context each local model holds on the 5090](https://github.com/mcp-tool-shop-org/rnd/blob/main/entries/2026/2026-10-13-e5-fill-card.md)
