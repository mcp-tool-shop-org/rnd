---
id: nemo-relay
title: nemo-relay — tracing what an agent actually did (NVIDIA NeMo Relay)
date: 2026-10-13
kind: instrument
relevance: watch
fields: [agent-tooling, studio-tooling]
tags: [instrument, tracing, nemo-relay]
instrument_status: planned
invoke: "Not installed yet. Planned trial: `nemo-relay claude …` (transparent mode, a per-run gateway on 127.0.0.1) or `nemo-relay codex|pi`; Python/Node/Rust/Go APIs for our own harnesses (pip nemo-relay, nemo-relay-cli-bin). Never the persistent install, which rewrites Claude Code's settings for every session."
when: "A run passed or failed and the question is how it got there: which model and tool calls it made, where it retried, recovered, gave up or wasted work, and whether a harness change actually reduced that."
where: "github.com/NVIDIA/NeMo-Relay (Apache-2.0) · docs.nvidia.com/nemo/relay · skills mirrored in catalogs/nvidia-skills (family nemo-relay)"
---

## Summary

NeMo Relay is NVIDIA's open-source (Apache-2.0) instrumentation layer for agents. It places an agent's sessions, turns, model calls and tool calls into a hierarchy of scopes, and records each lifecycle event. The results come out three ways:
- **ATOF:** the raw event stream;
- **ATIF:** a step-by-step trajectory that people can read;
- **OpenTelemetry:** spans, viewable in standard tools.

The CLI wraps Claude Code, Codex and pi directly. Hermes and OpenClaw have their own integrations, and there are Python, Node.js, Rust and Go APIs for instrumenting a harness by hand.

## What it would measure for the studio

- **Wasted work inside a run:**
  - retries;
  - repeated or redundant tool calls;
  - error-then-recover loops;
  - a run that stopped early.
- **Before and after a harness change:** the same tasks traced under each version, compared on calls, tokens and time per successful task.

## What it does not measure

- **Whether an answer is right.** That stays with the experiment's own grader.
- **Anything outside the agent's own calls.** A GPU's memory, a device's clocks and the rig's load stay with interlock's receipts.

## Status and conditions (R&D, 2026-10-13)

Planned, not installed. The Director approved adding it to the toolset.

**First trial:** a small pre-registered one, after the atlas-mcp-utility pilot. Run it on harnesses where wasted work has already cost us:
- E5's prefix-fit search, which once made thousands of count calls;
- a dogfood-swarm wave;
- the role-set generators.

The trial asks whether a Relay trace finds waste that our receipts and stream logs miss, and at what setup cost.

**Conditions:**
- transparent mode only;
- verify on the rig, before relying on it, that nothing leaves the machine except the agent's own provider traffic;
- local models or plan-covered agents only, under the standing rules;
- traces stay out of public repos unless they've been trimmed.

**Not in the atlas-mcp-utility pilot.** Its hooks and proxy would change the isolated conditions that experiment pre-registered.

See [[2026-10-13-nvidia-nemo-relay-tracing-agent-harnesses-claude-code-includ]].
