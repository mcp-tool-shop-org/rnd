---
title: How do we see what an agent actually did?
description: A passing check says an agent got the right answer, not how it got there. NVIDIA's NeMo Relay traces every model and tool call. We measured it inside our local-model harness. It records everything faithfully but costs too much client time per call for counted runs, so it stays a debugging tool.
date: 2026-10-14
status: interim
shelf: not yet (the debug-only build is still to land)
---

## The question

The studio runs a lot of agents:
- Claude Code sessions that build and review the tools;
- swarms that audit repositories;
- harnesses that drive local models through hours of measurements.

When one of them passes, we know it got the right answer. We don't know whether it got there cleanly, or after
three retries, a recovered tool error and a pile of calls it didn't need. Those hidden costs add up. In October
one of our own measurement harnesses spent over 30 minutes making thousands of token-count calls before
anyone noticed, because nothing in its output showed the waste.

So: is there a cheap way to see the path, not just the result?

## What NeMo Relay is

[NeMo Relay](https://github.com/NVIDIA/NeMo-Relay) is NVIDIA's open-source instrumentation layer for agents,
licensed Apache-2.0. It sits around an agent's work and records it as a tree of scopes:
- the session;
- each turn;
- each model call;
- each tool call.

It keeps the timing, the errors, the retries and the tokens at every level. That record comes out in three
forms:
- **a raw event stream (ATOF):** for machines;
- **a step-by-step trajectory (ATIF):** for people reading what happened;
- **OpenTelemetry spans:** viewable in standard tracing tools.

It's built to be cheap to try:
- the command-line tool wraps an agent in one line, and Claude Code, Codex and pi are supported directly;
- Hermes has it built in;
- there are libraries for Python, Node.js, Rust and Go for wrapping a harness of your own.

NVIDIA's tracing tutorial makes the case we care about. Run the same tasks before and after a change to an
agent's harness, and compare the traces, not just the pass rate. A change that keeps the pass rate but halves
the retries is a real improvement, and only a trace shows it.

## Where it fits the studio

- **Finding waste in our harnesses.** The October count-call blow-up would have shown in a trace as thousands
  of identical calls. So would a swarm agent re-reading the same files, or a generator retrying a refused
  output.
- **Judging harness changes on more than pass rates.** Calls, tokens and time per successful task, before and
  after.
- **Agent debriefs, with evidence.** We now ask every agent after a task what slowed it down. A trace would
  show whether its account matches what it actually did.

## Where it doesn't fit yet

- **Not inside a pre-registered experiment that's already pinned.** Our current experiment, which asks whether
  the Atlas sidecar helps agents, isolates its agents carefully, with no hooks and nothing between the agent
  and its model. Relay works by adding hooks and a local proxy. Adding it mid-experiment would change the very
  conditions being measured. That experiment already records every call from the agent's own output.
- **Not as a permanent install on the studio machine.** Relay's persistent mode rewrites the agent's settings
  for every session. We'll only use its per-run mode, which starts a private gateway for one run and leaves
  nothing behind.

## What we measured: Relay inside interlock (October 2026)

interlock is our harness for measuring local models: it drives them through Ollama on the RTX 5090 and writes a
receipt for every measurement. The first trial asked whether Relay could trace interlock's model calls **without
changing what interlock measures**. It was pre-registered, with its analysis frozen before any run, and reviewed by
an outside model from a different family at each step.

**Stage 0 (code and tests on fakes):** Relay's trace answered five diagnostic questions about a run that our
receipts couldn't. It also stayed within a per-call size and time budget, set against a native event log of
our own. It passed.

**Stage 1 (the 5090, 30 traced-against-untraced triples per call pattern):** the frozen analysis said **no**.
- **The model's numbers didn't move.** Decode speed, prompt speed and latency all tested equivalent with tracing on.
  The traces leaked nothing: no prompt text, no paths, no names.
- **The client-side cost failed its gate.** Each traced call costs about 0.27 ms more on our side. That is Relay's
  own per-call work, run on a CPU waking from the rest between measurements. Per two-call measurement that is
  0.55–0.68 ms, against a hard budget of 0.5 ms. A CPU-only bench with the same rests reproduces the live figure,
  so a rerun wouldn't change it.
- **The request count was off by exactly one in every step.** We traced it to our own harness: a card check runs
  before tracing starts. Every request was accounted for. The companion arm also showed three stray spans, for the
  same kind of reason: a teardown call ran after its measurement window closed.

**The decision:** Relay stays in interlock as an **opt-in debugging tracer**, never on counted runs. Traced runs
are marked and kept out of the routing table. The pre-registered rule said an off-count means reject. This
decision departs from it on purpose, because the off-count was our harness's fault. It is recorded as a dated
amendment, not a re-reading. Before adoption, the harness fixes and a deterministic counting test have to land
and pass review. No further GPU or NPU time is planned for Relay.

## The trial we'd still like

A small, pre-registered trial after the current experiment's pilot, on harnesses where waste has already cost
us:
- the measurement search that made the count calls;
- one wave of a repository-audit swarm;
- the puzzle generators.

**The question:** does a Relay trace find wasted work that our own logs and receipts miss, and what does
setting it up cost?

**Before anything runs:**
- we confirm on the rig that it sends nothing out except the agent's own model traffic. The code is open and
  the licence is clear, but we check rather than assume;
- traces stay out of public repositories unless they've been trimmed.

## Caveats

- **Measured on one rig, with one model, through one harness.** The client-time cost is specific to Relay's
  per-call work on this CPU and this measurement design. It says nothing about Relay's value for tracing whole
  agents, where a fraction of a millisecond per call doesn't matter.
- **The agent-tracing trial below hasn't run.** Its parts of this page still come from NVIDIA's documentation,
  repository and tutorial.
- **The tutorial's example task uses an NVIDIA-hosted model with an API key.** Relay itself doesn't need one.
  Our trial would trace local models or agents already covered by our Claude plan.

## Sources

- [NVIDIA/NeMo-Relay](https://github.com/NVIDIA/NeMo-Relay): the repository (Apache-2.0)
- [NeMo Relay CLI: basic usage](https://docs.nvidia.com/nemo/relay/nemo-relay-cli/basic-usage): the agents it wraps, and its per-run and persistent modes
- [Instrumenting applications](https://docs.nvidia.com/nemo/relay/instrument-applications/about)
- The interlock trial: `experiments/interlock-relay/` in this repository: the design (with amendment v3.2), stage
  0's record, and stage 1's frozen analysis, its output, and the result note
- rnd's library entry and its instrument file: `entries/2026/2026-10-13-nvidia-nemo-relay-tracing-agent-harnesses-claude-code-includ.md` and `instruments/nemo-relay.md`
