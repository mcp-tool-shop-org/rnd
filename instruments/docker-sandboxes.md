---
id: docker-sandboxes
title: docker-sandboxes — isolated machines for agent experiments (Docker Sandboxes, sbx)
date: 2026-10-13
kind: instrument
relevance: act
fields: [agent-tooling, studio-tooling]
tags: [instrument, docker, sandboxes, sbx, isolation, cloud, runpod]
instrument_status: planned
invoke: "Not installed yet. The `sbx` CLI: local sandboxes on the rig are free; `sbx --cloud` runs Docker-managed microVMs on pay-as-you-go compute, with a Sandboxes API and SDK for creating them from a harness. Files go in by git clone or `sbx cp` (cloud has no host mounts)."
when: "An experiment needs many clean, identical agent attempts that must not touch each other or the rig: the atlas-mcp-utility ladder's attempts, a coding-agent pilot, or anything that runs code a stranger wrote. GPU work stays on the rig or RunPod (offrig): cloud sandboxes have no GPU."
where: "docs.docker.com/ai/sandboxes · CLI reference docs.docker.com/reference/cli/sbx · release notes docs.docker.com/ai/sandboxes/release-notes (on the weekly watch as docker-sandboxes)"
---

## Summary

Docker Sandboxes run a coding agent in an isolated machine:
- **locally,** on the rig, free, including for commercial use;
- **in the cloud,** in Docker-managed microVMs, each with its own kernel.

One CLI, `sbx`, drives both. Supported agents include Claude Code, Codex, Gemini and OpenCode, plus an agent-less shell.

**Cloud sandboxes:**
- **Billing:** by the second, on pay-as-you-go compute. Model calls are billed by their own provider.
- **No GPU** and no host hardware. CPU and memory only, on `linux/amd64` or `linux/arm64`.
- **No host mounts.** Files go in by `git clone` or `sbx cp`, and come out by `sbx cp`.
- **A time-to-live** and a timeout action on each sandbox.
- **Their own secret store** and their own network policy, with no HTTP path filtering.
- **A Sandboxes API and SDK,** so a harness could create them.

## What it would do for the studio

- **Clean attempts for the atlas-mcp-utility ladder.** Each attempt gets a fresh machine:
  - the CLI pinned;
  - the chain's repositories cloned at their pinned commits;
  - Atlas started from the release.

  Then it's thrown away. That's the isolation the experiment otherwise builds by hand with per-attempt cache roots (amendment 4). It also keeps agent runs off the rig while interlock holds GPU grants.
- **Paired with RunPod.** A sandbox runs the agent on CPU, and a RunPod pod (through offrig) serves an open model on a GPU. That covers an arm whose model isn't Claude, without loading the 5090.
- **Running strangers' code.** A model-written script, or a repository under review, can run in a machine that holds none of the studio's secrets.

## The $250 offer (checked 2026-10-13)

- **What it is:** a one-time $250 compute credit for new Docker Agentic Platform signups from 2026-09-22 to **2026-10-31, 11:59 PM PT**. It replaces the standard $25. One per person and account.
- **What it pays for:** cloud sandbox compute only, billed by the second, including setup, idle time and retries. Hourly rates run from $0.070 (Micro) to $1.118 (XL). That's about 220 hours at the largest size, or 3,500 at the smallest.
- **Not covered:** model API use. An agent's Claude, Codex or other model calls are billed by their provider.
- **Expiry:** six months after it's claimed. Unused credit is forfeited.
- **A card is required at signup,** and charged only for use beyond the credit. The docs name **no spending limit, budget alert or hard cap**: their only cost control is to stop or delete sandboxes. So every harness sets a time-to-live and deletes its sandboxes, and the console's usage page is checked after each run.

## Status and conditions (R&D, 2026-10-13)

- **Planned.** The Director raised it on 2026-10-13, to pair with RunPod.
- **Account creation is his** (a card on file). R&D can't sign up.
- **The first use waits for the Atlas build-up's release,** like every other test. It would be one pilot attempt of the atlas-mcp-utility probe in a cloud sandbox, to measure setup time, cost per attempt, and whether the pinned CLI and Atlas behave exactly as on the rig.
- **Unknown until tried:**
  - how Claude Code authenticates inside a cloud sandbox (an API key, or a Claude plan login);
  - how many sandboxes can run at once;
  - the vCPU and memory behind each size.
