---
id: docker-sandboxes
title: docker-sandboxes — isolated machines for agent experiments (Docker Sandboxes, sbx)
date: 2026-10-13
kind: instrument
relevance: act
fields: [agent-tooling, studio-tooling]
tags: [instrument, docker, sandboxes, sbx, isolation, cloud, runpod]
instrument_status: planned
invoke: "sbx 0.48.0, installed per user on the rig (winget Docker.sbx; needs Windows Hypervisor Platform on). Drive a sandbox headless with `sbx exec [-w DIR] SANDBOX claude -p …` (from Git Bash set MSYS_NO_PATHCONV=1); `sbx ls`, `sbx stop` (keeps the tools), `sbx rm` (cannot be undone). Local sandboxes are free; `sbx --cloud` runs Docker-managed microVMs on pay-as-you-go compute, with a Sandboxes API and SDK. Files go in by git clone, `git archive` or `sbx cp`."
when: "An open-model agent experiment needs many clean, identical attempts that must not touch each other or the rig, or something must run code a stranger wrote. Models are local or RunPod only, never a paid model API (Director, 2026-10-13). GPU work stays on the rig or RunPod (offrig): cloud sandboxes have no GPU."
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

- **Clean attempts for open-model agent arms.** Each attempt gets a fresh machine:
  - the agent kit pinned;
  - the repositories cloned at their pinned commits;
  - Atlas started from the release.

  Then it's thrown away. That's the isolation the atlas-mcp-utility experiment otherwise builds by hand with per-attempt cache roots (amendment 4). It also keeps those runs off the rig while interlock holds GPU grants. The Claude arms run in a local sandbox on the Director's plan (atlas-mcp-utility amendment 7).
- **Paired with RunPod.** A sandbox runs the agent on CPU, and a RunPod pod (through offrig) serves an open model on a GPU. That covers an open-model arm without loading the 5090.
- **Running strangers' code.** A model-written script, or a repository under review, can run in a machine that holds none of the studio's secrets.

## The $250 offer (checked 2026-10-13)

- **What it is:** a one-time $250 compute credit for new Docker Agentic Platform signups from 2026-09-22 to **2026-10-31, 11:59 PM PT**. It replaces the standard $25. One per person and account.
- **What it pays for:** cloud sandbox compute only, billed by the second, including setup, idle time and retries. Hourly rates run from $0.070 (Micro) to $1.118 (XL). That's about 220 hours at the largest size, or 3,500 at the smallest.
- **Not covered:** model use. The studio's models are local or on RunPod, never a paid model API, so the model side is RunPod's GPU time through offrig.
- **Expiry:** six months after it's claimed. Unused credit is forfeited.
- **A card is required at signup,** and charged only for use beyond the credit. The docs name **no spending limit, budget alert or hard cap**: their only cost control is to stop or delete sandboxes. So every harness sets a time-to-live and deletes its sandboxes, and the console's usage page is checked after each run.

## What the console showed at signup (the Director's screen, 2026-10-13)

The Director signed up on 2026-10-13, inside the offer window. The account's Docker Agentic Platform Compute is active.
- **The launcher's kits:** claude, codex, copilot, antigravity, opencode, hermes-agent, shell, and public kits.
- **The claude kit runs on an Anthropic API key,** billed per token outside a Claude plan. The studio doesn't use it (see the next section).
- **The defaults:**
  - **network:** "Open access". Restrict egress for experiment runs.
  - **tools:** none added.
  - **compute:** medium, at **$0.28/hr** while running, billed per second. That's about 890 medium hours on the $250.
  - **a stop after 1 hour:** the time-to-live the docs didn't price.
- **Repository access** is through a GitHub token. Use a fine-grained, read-only token scoped to the experiment's repositories.
- **The credit should run until about 2027-04-13,** six months from the claim. That needs confirming on the console's Usage & billing page.

## Which model a sandboxed agent uses (the Director's ruling, 2026-10-13)

**No Claude API, and no other paid model API.** A sandbox never runs the claude kit with an Anthropic API key, and never takes `sbx secret set anthropic`, which is the API-key path. Three routes are allowed:
- **The claude kit signed in with `/login` on the Director's plan,** in a local sandbox. The sign-in is held on the host and never enters the sandbox: the init event shows `apiKeySource: none`. Runs share his plan's usage limits.
- **An open-model kit, or Claude Code itself pointed at an open model.** `sbx/claude-ollama-kit` runs Claude Code with `ANTHROPIC_BASE_URL` at the host's Ollama (`host.docker.internal:11434`), which answers `/v1/messages`. Its network is opened to that one host port only. The studio's fork is at `E:/AI/sbx-kits/claude-ollama-local`. Each run needs a GPU grant, since the model loads on the 5090.
- **A model served on RunPod through offrig,** for a cloud sandbox.

| The experiment | The agent runs in | The model |
|---|---|---|
| Claude is the subject (the atlas-mcp-utility ladder's Claude arms) | the local sandbox `atlas-pilot`, mountless (amendment 7) | Claude Code on the Director's plan, through the claude kit's `/login` |
| Open-model agent runs, such as Atlas with a local coder model, or dataset generation | a cloud sandbox, on the credit | a RunPod pod serving the model through offrig, priced first. The agent kit (opencode, hermes-agent or shell) points at the pod's endpoint, and the 5090 stays free. |
| Small, quick checks, or an open-model arm on the rig | a local sandbox, free | local Ollama on the 5090 through the claude-ollama kit, under a grant |

- **Never expose the rig's Ollama to a cloud sandbox.** That would open the rig to the internet. A local sandbox reaches it through `host.docker.internal`, and nothing else does.
- **Not yet tested:** whether a local sandbox reaches an Ollama bound to 127.0.0.1 on the host.
- **No Ollama Cloud,** per Standing Rule 1.
- **offrig's project cap ($5, $1.96 left on 2026-10-13)** covers verification batches, not a sustained open-model experiment. That needs a priced plan and the Director's go to raise the cap.

## Status and conditions (R&D, 2026-10-13)

- **Planned until the first pilot run.** The Director raised it on 2026-10-13, to pair with RunPod. The same day, sbx was installed and the mountless `atlas-pilot` workspace built for the atlas-mcp-utility experiment (its amendment 7). The setup is written up in [[2026-10-13-docker-sandboxes-on-the-rig-from-signup-to-a-pinned-pilot-wo]].
- **The account is his:** he signed up on 2026-10-13, with a card on file. R&D doesn't run sandboxes or enter keys without his go.
- **The first use waits for the Atlas build-up's release,** like every other test. It would be one pilot attempt of an open-model arm in a cloud sandbox, against a model on RunPod. It would measure setup time, cost per attempt, and whether the pinned kit and Atlas behave as on the rig. Any arm that would have used Claude in a sandbox becomes an open-model arm on RunPod.
- **Unknown until tried:**
  - whether a cloud sandbox can reach a RunPod endpoint under a network policy tighter than "Open access", with the endpoint's auth header kept in the cloud secret store;
  - which open-model kit (opencode, hermes-agent or shell) works best against that endpoint;
  - how many sandboxes can run at once;
  - the vCPU and memory behind each size.
