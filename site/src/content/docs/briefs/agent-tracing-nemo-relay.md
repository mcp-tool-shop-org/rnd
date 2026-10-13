---
title: How do we see what an agent actually did?
description: A passing check says an agent got the right answer, not how it got there. NVIDIA's NeMo Relay traces every model and tool call. Here's what it offers the studio, where it doesn't fit yet, and the trial we've planned.
date: 2026-10-13
status: research
shelf: not yet measured here
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

## The trial we've planned

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

- **Read, not measured.** Everything here comes from NVIDIA's documentation, repository and tutorial. Nothing
  has run on our machines yet, so the status is *research*.
- **The tutorial's example task uses an NVIDIA-hosted model with an API key.** Relay itself doesn't need one.
  Our trial would trace local models or agents already covered by our Claude plan.

## Sources

- [NVIDIA/NeMo-Relay](https://github.com/NVIDIA/NeMo-Relay): the repository (Apache-2.0)
- [NeMo Relay CLI: basic usage](https://docs.nvidia.com/nemo/relay/nemo-relay-cli/basic-usage): the agents it wraps, and its per-run and persistent modes
- [Instrumenting applications](https://docs.nvidia.com/nemo/relay/instrument-applications/about)
- rnd's library entry and its instrument file: `entries/2026/2026-10-13-nvidia-nemo-relay-tracing-agent-harnesses-claude-code-includ.md` and `instruments/nemo-relay.md`
