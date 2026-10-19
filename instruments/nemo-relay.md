---
id: nemo-relay
title: nemo-relay — tracing what an agent actually did (NVIDIA NeMo Relay)
date: 2026-10-13
kind: instrument
relevance: watch
fields: [agent-tooling, studio-tooling]
tags: [instrument, tracing, nemo-relay]
instrument_status: shipped
invoke: "Installed in the Docker sandbox `atlas-pilot` at /opt/nemo-relay (0.10.1, by uv). Run as the run user: `nemo-relay run --agent claude -- -p … < prompt` with `~/.config/nemo-relay/config.toml` (upstream, the pinned CLI path) and `plugins.toml` (observability v4, ATOF and ATIF file sinks, OpenTelemetry off). Transparent mode only; never `nemo-relay install`, which rewrites Claude Code's settings for every session. Python/Node/Rust/Go APIs for our own harnesses (pip nemo-relay)."
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

Installed in the sandbox on 2026-10-13, and the setup conditions below were checked there: see [[2026-10-13-nemo-relay-first-trial-in-the-sandbox]]. The Director approved adding it to the toolset.

**First trial (next):** a small pre-registered one, designed from a template. Run it on harnesses where wasted work has already cost us:
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

## 0.10.0's release notes, for the trial (read 2026-10-13; flagged by the weekly watch)

- **Local trace files.** Spans can be written as OTLP JSON Lines or length-delimited protobuf files, alongside or
  instead of a remote collector. A trial needs no collector, and the traces never leave the rig, which meets the
  condition above directly.
- **Automatic OTLP export from the standard environment variables.** If an `OTEL_EXPORTER_OTLP_*` endpoint variable
  is set in the environment, Relay starts exporting to it. A trial must check that none is set on the rig before the
  first run, or traces could go wherever such a variable points.
- **Permission-policy marks for Claude Code.** Matched permission requests get a `nemo_relay.permission.policy_decision`
  mark, linked to the tool call. A `pass` means only that Relay didn't block the request. It doesn't mean a user
  approved it, or that it ran. Useful beside our own isolation checks, never in place of them.
- **Breaking changes that don't touch us yet:**
  - observability configuration requires `version = 4`;
  - native plugins need ABI v7;
  - `gen_ai.usage.cache_creation.input_tokens` is now `gen_ai.usage.cache_write.input_tokens`.

  A trial starts on 0.10.0's format, so none of these needs a migration. A token-cost reader must use the new
  field name.

## 0.10.1 and 0.10.2 (read 2026-10-19 from the GitHub release notes and docs/about-nemo-relay/release-notes; flagged by the weekly watch)

- **The sandbox already runs 0.10.1** (the invoke line above). The weekly watch's summary put 0.10.1's changes under
  0.10.2. The primary notes place them as follows.
- **0.10.1** (2026-10-14):
  - daemon workers run the full LLM middleware;
  - fail-closed hooks now block (exit `2`) when delivery fails or no credential is available;
  - Anthropic streaming content-block storage is bounded;
  - dynamic plugins that fail trust verification are skipped;
  - plugin and remote HTTP error statuses are preserved.
  - Its compatibility notes concern hook credentials (`NEMO_RELAY_CLIENT_TOKEN`), refreshing installed hooks,
    responses rewritten by daemon middleware, Pi upstreams, and error handling that relies on generic statuses.
- **0.10.2** (2026-10-14), fixes only:
  - layered configuration restored for daemon workers;
  - upstream URLs validated;
  - managed daemon hooks delivered without the system proxy;
  - PII trajectory metadata preserved;
  - rustls bumped.
- **What touches us:** nothing yet. The trial uses `nemo-relay run` in transparent mode with file sinks. It installs
  no hooks, runs no daemon and has no fail-closed policy, which is where every behaviour change above lives.
  - Stay on 0.10.1.
  - Bump to 0.10.2 only with a daemon or hooks in use, and re-read the migration guide then.

See [[2026-10-13-nvidia-nemo-relay-tracing-agent-harnesses-claude-code-includ]].
