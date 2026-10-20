---
id: 2026-10-13-claude-code-starts-a-turn-before-mcp-servers-connect
title: "Claude Code starts a print-mode turn before its MCP servers connect, on Anthropic's endpoint"
date: 2026-10-13
kind: finding
relevance: act
fields: [agent-tooling]
tags: [claude-code, mcp, headless]
---

## Summary

In headless print mode (`-p` with stream-json input), Claude Code talking to Anthropic's endpoint starts the first turn
as soon as the message arrives, without waiting for its MCP servers to connect. The turn's start event shows the
server `pending`, and none of its tools are offered to the model for that turn. They appear only from the next turn.
Holding the first message about 3 seconds after starting the CLI was enough for the server to connect. The studio's
harness holds it for 10.

**Re-probed 2026-10-20.**
- **2.1.197:** reproduced. The server is `pending`, with no tools, when the message arrives at once, and `connected`,
  with its 7 tools, after a 10 s hold.
- **2.1.280:** `connected`, with its tools, at the first turn with no hold, in 3 of 3 starts. The init event marks the
  server `"source": "dynamic"`.
- So 2.1.280 waits for the server, or connects it in time. The 2026-10-13 note that 2.1.280 was also `pending` didn't
  reproduce. It stays below, marked disputed.
- Hold the message anyway on 2.1.197, and check `mcp_servers` on any version.

## Key points

- **Seen on 2.1.197** (2026-10-13, and reproduced 2026-10-20), with a local MCP server (`atlas mcp`) in a Docker sandbox. Reported on 2.1.280 on 2026-10-13 too, but not reproduced on 2026-10-20 (see the claims).
- **It's the endpoint, not the sign-in.** With no sign-in at all, against Anthropic's endpoint, the start was still
  `pending`. With `ANTHROPIC_BASE_URL` pointing elsewhere (a closed port, or Ollama), the server was `connected` with its
  tools at the start.
- **Asked to list its tools, the model named only the four built-ins.** The MCP tools weren't on offer.
- **The fix:** wait a few seconds after starting the CLI before sending the first message. Then check the start event:
  the server must be `connected`, with its tools listed.

## Studio relevance

Any headless Claude Code run that relies on an MCP server in its first turn (kickoffs, CI agents, swarms) may silently
run without it. Hold the first message, and check `mcp_servers` in the init event.

## Claims

- [verified] On Anthropic's endpoint, a headless run's first turn starts with its MCP server `pending` and none of its tools. (via: a plan-route start of claude-haiku-5-5 in `atlas-pilot`, and starts with no sign-in, 2026-10-13)
- [verified] A 3 s or 10 s hold before the first message gives a `connected` start with the server's tools. (via: starts in `atlas-pilot`, 2026-10-13)
- [verified] On Claude Code 2.1.197, the plan route, a start with no hold has the Atlas server `pending` and offers 0 of its tools; with a 10 s hold it is `connected` and offers 7. (via: R&D's re-probe in `atlas-pilot`, b1-pin-0.jsonl and b1-pin-10.jsonl, 2026-10-20; also /root/plan-haiku-start.jsonl of 2026-10-14, recovered from the sandbox)
- [verified] On Claude Code 2.1.280, the plan route, the Atlas server is `connected` with its 7 tools at the first turn with no hold, in 3 of 3 starts. (via: R&D's re-probe b1-cur-0.jsonl and b1rep-cur-0-1/2.jsonl, 2026-10-20)
- [disputed] Claude Code 2.1.280 also starts the first turn with the MCP server `pending`. Reported 2026-10-13; not reproduced in 3 starts on 2026-10-20 (the claim above).

## Sources

- [rig] Start-event captures in the Docker sandbox `atlas-pilot`, 2026-10-13
- [rig] R&D's re-probe in `atlas-pilot`, 2026-10-20: 6 plan-route starts of claude-haiku-5-5 (receipts in R&D's private store, hashed in jobB/SHA256SUMS.txt)
