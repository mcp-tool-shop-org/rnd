---
id: 2026-10-13-nvidia-nemo-relay-tracing-agent-harnesses-claude-code-includ
title: "NVIDIA NeMo Relay: tracing agent harnesses, Claude Code included"
date: 2026-10-13
kind: tool
relevance: act
fields: [agent-tooling]
tags: [nemo-relay, tracing, atlas-mcp-utility]
---

> **Note (2026-10-13):** the atlas-mcp-utility experiment this entry refers to was withdrawn as badly designed. Only its harness remains, and it is unvalidated. No result from that experiment should be cited.

## Summary

NeMo Relay is NVIDIA's instrumentation layer for agents. It wraps an agent's model and tool calls in nested scopes (session, turn, model call, tool call) and emits three kinds of output:
- ATOF, a raw stream of lifecycle events;
- ATIF, a step-by-step trajectory meant for people to read;
- OpenTelemetry spans, which can be viewed in tools such as Arize Phoenix.

NVIDIA's tutorial is built around one argument: a passing check doesn't show how an agent got there. Traces show whether it recovered from a tool error, gave up early, retried, or made extra model calls. They also show what a harness change actually did across repeated runs.

The Relay CLI wraps Claude Code, Codex and pi directly (`nemo-relay claude`). Hermes ships with Relay built in.

## Key points

- **Two modes, both local:**
  - **Transparent run:** `nemo-relay claude …` starts a gateway on a dynamic `127.0.0.1` port for that run only. The agent's provider traffic goes through the gateway to the upstream API (Anthropic by default).
  - **Persistent install:** this wires Claude Code to a shared local gateway on `127.0.0.1:47632`. That changes the agent's own configuration for every session.
- **The tutorial's example task** uses Nemotron through an NVIDIA Build API key. Relay itself doesn't need that key, and the gateway's upstream can be overridden.
- **Licence: Apache-2.0,** for both NVIDIA/NeMo-Relay and NVIDIA/NeMo-Relay-Plugins. The repository's "telemetry" hits are its adaptive plugin's own metrics, and nothing read so far shows it phoning home. That stays unverified until a trial watches its network traffic on the rig. NVIDIA's skills catalogue is mirrored in this library as family `nemo-relay` (10 skills, fit "adjacent").
- **The catalogue's earlier fit note:** compare it against Role OS and swarm receipts before adopting anything.

## Studio relevance

- **The atlas-mcp-utility pilot:** not now. The pilot is pinned and isolated:
  - user hooks are off;
  - every call's tokens and tool use are already captured from the CLI's own stream;
  - a run's start is checked against its arm.

  Relay would add hooks and a proxy between the agent and the API, which would change the conditions under test and undo the isolation work in amendment 2.
- **Added to the toolset** (`instruments/nemo-relay.md`, status planned) on the Director's word, 2026-10-13.
- **After the pilot, worth a small pre-registered trial** on studio harnesses where wasted work has already cost us, for example:
  - E5's prefix-fit search, which made thousands of count calls before #70;
  - the dogfood-swarm waves;
  - the role-set generators.

  The question would be whether a Relay trace finds waste that our receipts and stream logs miss, at what setup cost.
- **Conditions for any trial:**
  - transparent mode only, with no persistent install that rewrites Claude Code settings;
  - licence and telemetry checked first;
  - local models or a plan-covered agent only, under the standing rules;
  - traces stay off any public repo unless they've been trimmed.
- **An idea from the tutorial for the pilot report:** cost per successful task. It can be reported descriptively from the pilot's own data, labelled post hoc, without Relay.

## Claims

- [verified] The NeMo Relay CLI's documented transparent runs include `nemo-relay claude` (Claude Code), `nemo-relay codex` and `nemo-relay pi`, each with a gateway on a dynamic 127.0.0.1 port; persistent installs share a native gateway on 127.0.0.1:47632 (via: docs.nvidia.com/nemo/relay/nemo-relay-cli/basic-usage, read 2026-10-13)
- [unverified] Relay emits ATOF events, ATIF trajectories and OpenTelemetry spans; Hermes integrates it natively (aggregator summaries of NVIDIA's tracing tutorial)
- [verified] NeMo Relay and NeMo Relay Plugins are licensed Apache-2.0 (via: GitHub API, repos NVIDIA/NeMo-Relay and NVIDIA/NeMo-Relay-Plugins, 2026-10-13)
- [unverified] Relay sends no telemetry to NVIDIA when run locally

## Sources

- [primary] https://docs.nvidia.com/nemo/relay/nemo-relay-cli/basic-usage — the CLI's integrations and gateway modes
- [primary] https://docs.nvidia.com/nemo/relay/nemo-relay-cli/hermes — the Hermes integration
- [primary] https://docs.nvidia.com/nemo/relay/instrument-applications/about — instrumenting applications
- [aggregator] https://prismix.dev/news/cd3206004eeb — summary of "Tracing Agent Harness Behavior with NVIDIA NeMo Relay"
- [aggregator] https://quantumzeitgeist.com/?p=357425 — news summary
- [primary] https://github.com/NVIDIA/skills — the `nemo-relay` skill family (mirrored in this library's catalogs/nvidia-skills)
