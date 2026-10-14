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

## Key points

- **Seen on 2.1.197 and 2.1.280**, with a local MCP server (`atlas mcp`) in a Docker sandbox.
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

## Sources

- [rig] Start-event captures in the Docker sandbox `atlas-pilot`, 2026-10-13
