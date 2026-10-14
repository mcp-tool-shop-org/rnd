---
id: 2026-10-13-docker-sandboxes-on-the-rig-from-signup-to-a-pinned-pilot-wo
title: "Docker Sandboxes on the rig: from signup to a pinned pilot workspace"
date: 2026-10-13
kind: finding
relevance: act
fields: [agent-tooling, studio-tooling]
tags: [docker, sandboxes, sbx, isolation, claude-code, ollama, atlas-mcp-utility, windows]
---

> **Note (2026-10-13):** the atlas-mcp-utility experiment this entry refers to was withdrawn as badly designed. Only its harness remains, and it is unvalidated. No result from that experiment should be cited.

## Summary

In one afternoon on 2026-10-13, the studio went from a Docker signup to a mountless, pinned Linux workspace where the
atlas-mcp-utility experiment's agents will run. It's driven headless from a Claude session, and its model runs on the
Director's plan with no API key anywhere.

The steps, in order:
1. Turn on a Windows feature.
2. Install the `sbx` CLI per user.
3. Sign in once and choose a network policy.
4. Pick a model route that pays no per-token API.
5. Build the workspace with exactly the pinned tools.

Two things in the image would have broken the experiment if they had gone unnoticed: a self-updating Claude Code, and a
kit that turns permission prompts off.

## Key points

**Setting up the rig:**
1. **Windows Hypervisor Platform** must be on for `sbx`. It was off. Turning it on takes an admin PowerShell and a
   restart.
2. **`sbx` 0.48.0 installs per user** through winget (`Docker.sbx`), with no admin, into
   `%LOCALAPPDATA%\DockerSandboxes\bin`. winget verified the installer's hash.
3. **The first `sbx run`** does a device-code sign-in to Docker, then asks for a network policy: Open, Balanced or
   Locked Down. The studio chose **Balanced**: deny by default, common development hosts allowed.

**The model, under the Director's ruling of no paid per-token API:**
- **The claude kit's welcome screen offers an Anthropic API key.** That's ruled out, and so is `sbx secret set
  anthropic`, which is the same path.
- **The route that works:** the claude kit with **`/login` on the Director's plan**. The sign-in is done on the host,
  and Docker's credentials documentation says the token never enters the sandbox. The CLI's init event shows
  `apiKeySource: none`, and runs share the plan's usage limits.
- **An open-model route:** `sbx/claude-ollama-kit` runs Claude Code itself, with `ANTHROPIC_BASE_URL` set to the host's
  Ollama (`host.docker.internal:11434`) and a dummy token.
  - Every model alias maps to one Ollama model, and the network is opened to that one host port only.
  - The studio forked it (upstream Apache-2.0 at `96a0e00`) for `nemotron-3.5-lightning`: tool use, a 131k context,
    about 24 GiB.
  - Ollama 0.35.1 answers `/v1/messages`. That was checked with a missing model name, so nothing loaded.
  - Each run needs a GPU grant. Whether the sandbox reaches an Ollama bound to 127.0.0.1 is still untested.

**Driving it from a Claude session:**
- `sbx exec [-w DIR] SANDBOX claude -p "…"` returns the reply to the calling session.
- Computer use refuses typing into terminal windows, so `exec` is the way to drive a sandbox, not a terminal.
- From Git Bash, set `MSYS_NO_PATHCONV=1`, or a path like `/e/AI/...` is rewritten to `E:/AI/...` on its way in, and
  fails.

**The pilot workspace, `atlas-pilot`:**
- **Mountless:** no host folder is visible inside at all.
- **Two traps in the image:**
  - Its own Claude Code is 2.1.296 and updates itself. The experiment's pinned 2.1.197 is installed separately in
    `/opt/claude-pin`, put first on PATH, and checked at every start.
  - The kit seeds the sandbox user's `~/.claude/settings.json` with `defaultMode: bypassPermissions`. The harness runs
    with `--setting-sources local`, and its start check now refuses any run whose permission mode isn't `default`.
- **The rest:** Atlas 1.26.0 in `/opt/atlas-tools`, an empty `/work`, and the experiment brought in by `git archive`.
  The harness's pin check passes against it.
- **Medium effort:** `--effort medium` is accepted by the pinned CLI, but the init event doesn't echo it, so the
  harness records it from the command.

**Cost:**
- Local sandboxes are free.
- Cloud sandboxes cost **$0.28/hr** at medium, billed per second, and stop after 1 hour by default. A short
  time-to-live is the only cost control Docker documents.
- Runs on the plan share its usage limits.

**Housekeeping:** `sbx ls`, `sbx stop` (keeps the installed tools) and `sbx rm` (can't be undone).

## Studio relevance

**A mountless local sandbox is stronger containment than deny rules.** Permission rules over trees an agent could
otherwise reach leak (see [[2026-10-13-claude-code-read-deny-rules-do-not-stop-a-grep-walk]]). In a mountless sandbox the
operator's trees don't exist. Inside it, what held on the rig on 2026-10-13:
- **Containment by OS permission.** The harness runs as root. Each agent runs as an unprivileged user (`amu`) with no
  sudo, an emptied home and a fresh placeholder sign-in file per attempt. Everything else (the experiment files, other
  runs, other homes) is root-only.
- **The plan route:** the claude kit's `/login`, with the real token swapped in at the sandbox proxy. Every run's start
  is checked for `apiKeySource: none` and permission mode `default`.
- **The local-model route:** the network policy rule that works is `localhost:11434`. The kit's own
  `host.docker.internal:11434` didn't match the filter. The CLI still uses `http://host.docker.internal:11434` as its
  base URL.
- **Prices:** local sandboxes are free, and cloud sandboxes cost $0.28/hr at medium. Short Claude Code runs on the plan
  cost cents each at API rates, and a dozen of them didn't move the plan's weekly usage panel.

**What to watch:**
- The image's self-updating CLI. Pin it separately, and check the version at every start.
- The kit's own settings. Exclude them, and prove it from the init event.
- The sandbox VM's CPU load on the rig. No run overlaps an interlock measurement grant.

**Instrument:** [[docker-sandboxes]].

## Claims

- [verified] `sbx` requires Windows Hypervisor Platform, which was off on the rig and needed an admin enable and a restart. (via: the Publisher's setup on the rig, 2026-10-13)
- [verified] `sbx` 0.48.0 installs per user via winget `Docker.sbx` without admin, with the installer's hash verified. (via: the Publisher's setup on the rig, 2026-10-13)
- [verified] The claude kit signed in with `/login` on a Claude plan starts with `apiKeySource: none`. (via: the init event of the check call in `atlas-pilot`, 2026-10-13)
- [verified] The `atlas-pilot` image ships Claude Code 2.1.296, which updates itself; a separately installed 2.1.197 in `/opt/claude-pin` answers a pinned check call. (via: the Publisher's setup and check call, 2026-10-13)
- [verified] The kit seeds `~/.claude/settings.json` with `defaultMode: bypassPermissions`. (via: the Publisher's read of the sandbox, 2026-10-13)
- [verified] Ollama 0.35.1 answers `/v1/messages`. (via: a request with a missing model, so nothing loaded; the Publisher, 2026-10-13)
- [verified] Claude Code 2.1.197 accepts `--effort medium`, and its init event does not report the effort. (via: the check call in `atlas-pilot`, 2026-10-13)
- [unverified] The OAuth token is held on the host and never enters the sandbox. (Docker's credentials documentation; consistent with `apiKeySource: none`, not inspected directly)
- [unverified] A local sandbox can reach an Ollama bound to 127.0.0.1 on the host. (untested)

## Sources

- [primary] https://docs.docker.com/ai/sandboxes/ — Docker Sandboxes documentation (local and cloud, the `sbx` CLI, agents)
- [primary] https://docs.docker.com/reference/cli/sbx/ — the `sbx` CLI reference
- [rig] the Publisher's setup of `sbx` and `atlas-pilot` on the rig, with one check call, 2026-10-13
- [user] The Director's rulings of 2026-10-13: no paid per-token model API; medium effort for the pilot
