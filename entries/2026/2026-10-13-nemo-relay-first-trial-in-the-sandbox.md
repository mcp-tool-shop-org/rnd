---
id: 2026-10-13-nemo-relay-first-trial-in-the-sandbox
title: "NeMo Relay's first trial: it traces Claude Code in the sandbox at no measurable cost, and sends nothing of its own"
date: 2026-10-13
kind: finding
relevance: act
fields: [agent-tooling]
tags: [nemo-relay, tracing, claude-code, sandbox]
---

## Summary

NeMo Relay 0.10.1 ran in the `atlas-pilot` Docker sandbox, wrapping the pinned Claude Code 2.1.197 in transparent mode, as the unprivileged run user, with Haiku on the plan. It answered a repository question correctly and wrote its trace to local files only. A run without Relay, on the same task, cost the same and took the same time. The sandbox's network log shows that Relay sent nothing of its own: the only hosts reached during its runs were Anthropic's.

## Setup that worked

- **Install:** `uv venv /opt/nemo-relay`, then `uv pip install nemo-relay==0.10.1 nemo-relay-cli-bin==0.10.1`. The image's Python has no `venv` module, so uv is needed.
- **Config:** in the run user's `~/.config/nemo-relay/`:
  - `config.toml` sets `[upstream] anthropic_base_url` and `[agents.claude] command` (the pinned CLI's path);
  - `plugins.toml` enables the observability component (`version = 4`), with ATOF and ATIF file sinks in a local directory and OpenTelemetry off.
- **Run:** `nemo-relay run --agent claude -- -p …`, with the prompt on stdin.
  - The `-- ` before stdin matters: Claude Code's variadic flags otherwise swallow a prompt passed as an argument.
  - Transparent mode adds its hooks through a temporary plugin directory and overrides only `ANTHROPIC_BASE_URL` for that process. The user's Claude Code settings are unchanged.
- **Before the run:** no `OTEL_EXPORTER_OTLP_*` variable was set, so nothing could export by default.

## Findings

- **Overhead:** none measurable in one pair. With Relay: $0.501 at API rates, 7.6 s, 3 turns. Without: $0.524, 7.8 s, 3 turns.
- **Network:** the sandbox proxy's log, read before and after each run, showed only `api.anthropic.com` and `mcp-proxy.anthropic.com` (Claude Code's own) during the Relay runs. A Relay launch against a closed upstream added no outbound attempt of any kind.
  - The log also holds 31 blocked attempts to a Datadog intake host, made before the trial at the same second as the sandbox's own Ubuntu and Docker package traffic. They didn't recur during any Relay or control run.
- **Trace size:** a three-turn run produced about 0.5 MB of ATOF events and a 1 MB ATIF trajectory, with full payloads off. Each recorded user step repeats the CLI's system reminders, so traces need trimming before they leave the rig.
- **What it captured that a stream log shows less plainly:** against a closed upstream, the trajectory recorded each re-sent request as its own timestamped step, 7 in 34 seconds. Retries like these are the kind of wasted work the trial is meant to find.
- **One unexplained cost note, not Relay's:** both runs, with and without Relay, read nothing from the prompt cache and wrote everything at the 1-hour rate. That made them about five times the cost of the same task run under the agent A/B harness's flags. Worth a look before pricing plain `claude -p` runs.

## Studio relevance

The trial's setup conditions are met: transparent mode only, nothing leaving the machine except the agent's own provider traffic, plan or local models only, and traces kept local.

**Next:** the trial itself, per the instrument. Wrap a harness where wasted work has already cost us (E5's prefix-fit search, a dogfood-swarm wave, or the role-set generators), and ask whether the trace finds waste our receipts and stream logs miss. Design it from a template first. Those harnesses aren't Claude Code runs, so they need Relay's Python API rather than the CLI wrapper.

## Claims

- [verified] NeMo Relay 0.10.1 in transparent mode wraps Claude Code 2.1.197 in the sandbox and writes ATOF and ATIF to local files with OpenTelemetry off. (via: the trial run, 2026-10-13)
- [verified] During Relay runs, the sandbox proxy saw no outbound host other than Anthropic's. (via: `sbx policy log` before and after each run, 2026-10-13)
- [unverified] Relay adds no meaningful cost or time to a Claude Code run. One pair only.
- [verified] Re-run once on 2026-10-20 (Relay 0.10.1, Claude Code 2.1.197, OpenTelemetry off), Relay wrote ATOF events and an ATIF trajectory to local files, and under sbx's Balanced policy the before-and-after `sbx policy log` showed no host other than Anthropic's (api.anthropic.com, mcp-proxy.anthropic.com, platform.claude.com). This is what one run did, not what the policy forbids: Balanced allows other AI-service hosts. (via: R&D's re-run, b4-policylog-before/after.json and b4-start.txt, 2026-10-20)
- [verified] Relay's local ATOF event file carries account identity (the signed-in account's email address) even with `enable_full_payloads = false`. Treat ATOF files as private. (via: the identity scan of R&D's re-run output, 2026-10-20; the value is not recorded here)

## Sources

- [rig] Trial runs in the Docker sandbox `atlas-pilot`, 2026-10-13
- [rig] R&D's re-run in `atlas-pilot`, 2026-10-20 (receipts hashed in jobB/SHA256SUMS.txt)
- [primary] https://docs.nvidia.com/nemo/relay/latest/nemo-relay-cli/claude-code — transparent mode, hooks, gateway, outbound calls
- [primary] https://docs.nvidia.com/nemo/relay/configure-plugins/observability/configuration — the plugins.toml shape
