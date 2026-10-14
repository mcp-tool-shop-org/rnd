---
title: Docker Sandboxes on the rig, from signup to a pinned workspace
description: In one afternoon the studio went from a Docker signup to a mountless Linux workspace that runs Claude Code on a plan, with no API key, pinned for an experiment. Two defaults in the image would have broken it.
date: 2026-10-13
status: measured
shelf: stays in rnd (studio tooling)
---

## The question

The atlas-mcp-utility experiment (withdrawn on 2026-10-13 as badly designed; its harness is now the reusable agent A/B harness) asked whether Atlas's MCP sidecar helps coding agents answer questions about
repositories. Its agents must not see anything but the repository in front of them: not the operator's files, not
memory notes, not other repositories that discuss the answers.

On the rig, that was a set of deny rules over trees the agent could otherwise reach. The question was whether a
Docker Sandbox could do better, without paying for model calls by the token.

## What we found

**Getting `sbx` onto Windows takes three steps:**
1. **Windows Hypervisor Platform has to be on.** It was off. Turning it on takes an admin PowerShell and a restart.
2. **`sbx` installs per user, with no admin,** through winget (`Docker.sbx`, version 0.48.0). winget checked the
   installer's hash.
3. **The first `sbx run` signs in to Docker** with a device code, then asks for a network policy. We chose
   **Balanced**: deny by default, with common development hosts allowed.

**The model, with no per-token API.** The studio's rule is that experiments never pay a model API by the token. The
claude kit offers an Anthropic API key at the start, and that's the one thing we don't do. Two routes stay inside the
rule:
- **Claude Code signed in with `/login` on a Claude plan.** The sign-in is held on the host, and the CLI's start
  reports `apiKeySource: none`. Runs count against the plan's usage like any other session.
- **Claude Code pointed at a local model.** Docker's `claude-ollama-kit` sets `ANTHROPIC_BASE_URL` to the host's
  Ollama, which answers the same `/v1/messages` API. The kit maps every model name to one local model, and opens the
  network to that one host port only. Each run then needs the GPU, so it's scheduled like any other GPU job.

**Driving it from a Claude session.** `sbx exec SANDBOX claude -p "…"` returns the reply to the calling session. A
session can't type into a terminal window, so `exec` is the way in. From Git Bash, set `MSYS_NO_PATHCONV=1`, or a path
like `/e/AI/...` is rewritten on its way in.

**The workspace (`atlas-pilot`) mounts no host folder at all.** Two defaults in the image would have broken the
experiment if nobody had looked:

| default | why it matters | what we did |
|---|---|---|
| Claude Code 2.1.296, which updates itself | the experiment pins 2.1.197; a version that changes mid-run changes the subject | the pinned CLI installed separately, first on PATH, auto-update off, and the version checked at every start |
| the kit's settings turn permission prompts off (`bypassPermissions`) | an agent that's never asked can do anything its tools allow | the harness ignores user settings (`--setting-sources local`), and every start must report `default` permissions or the run stops |

The same start check now refuses any run that signs in with an API key. So the cost rule is enforced by the harness,
not just written down.

**What it costs.** Local sandboxes are free. Cloud sandboxes cost $0.28 an hour at the medium size, billed by the
second, and stop after an hour by default. Docker documents no spending cap, so a short time limit on each sandbox is
the only brake.

## Caveats

- **Only the setup is done; nothing graded has run.** The experiment's first probe, which plants secrets beside the
  answer keys and asks an agent to reach them by every route, hasn't run. It waits for the Atlas release, like
  everything else in the experiment.
- **Two things are still untested:** whether a sandbox reaches an Ollama bound to `127.0.0.1` on the host, and whether
  Balanced lets the harness clone from github.com.
- **"The token never enters the sandbox" comes from Docker's documentation.** It's consistent with what the CLI
  reports, but nobody inspected the sandbox for it.

## Receipts

- The harness, `experiments/agent-ab-harness/run.py`, tested in `tests/test_agent_ab_harness_run.py`, documented as the agent-ab-harness instrument.
- The entry, with each claim's source: `entries/2026/2026-10-13-docker-sandboxes-on-the-rig-from-signup-to-a-pinned-pilot-wo.md`.
- The instrument page: `instruments/docker-sandboxes.md`.

## Shelf status

This one stays in rnd. It's studio tooling, not knowledge a readouts base would carry.
