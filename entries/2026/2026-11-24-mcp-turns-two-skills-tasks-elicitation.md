---
id: 2026-11-24-mcp-turns-two-skills-tasks-elicitation
title: MCP turns two — Skills over MCP (beta), Tasks and Elicitation (GA) in Claude and Claude Code
date: 2026-11-24
kind: release
relevance: watch
fields: [developer-tools, agents]
tags: [mcp, claude-code, skills, tasks, elicitation, file-uploads, spec-2026-07-28]
---

## Summary

Anthropic's 2026-11-24 product update for MCP's second birthday. In Claude and Claude Code: **Skills over MCP** is a public beta
(on by default for Pro, Max and Ultra; Team once an admin enables it; Enterprise later); **Tasks** and **Elicitation** are generally
available (Pro, Max and Ultra; rolling out to Team and Enterprise); **File Uploads** (files passed to a server without going through
the context window) is "rolling out soon" from an experimental extension repo. It names the 2026-07-28 MCP spec revision, called
"stateless" but not defined further in the article. The article does not mention the API or Managed Agents for any of these.

## Key points

- **Skills over MCP (spec: SEP-2640, marked Final; extension spec in the ext-skills repo, beta).** A server declares `resources`
  plus the extension `io.modelcontextprotocol/skills` (optional `directoryRead`) and MUST implement `skills/list` and `skills/get`;
  files are served with `resources/read`. A skill is a directory with a `SKILL.md` (Agent Skills format) and supporting files; list
  entries carry a `skill://…` URI, the frontmatter, and a file manifest with sha256 digests and sizes. Limits: SHOULD NOT exceed 512
  files or 16 MiB. Hosts MUST NOT prefetch; they read SKILL.md only when a skill is selected, verify digest and size, and treat skill
  content as untrusted. Host code execution and `allowed-tools` need per-skill user approval; a persisted approval binds to the
  file URIs and digests and is revoked when they change; same-named skills from two servers must not silently replace each other.
  Skill-level enable/disable controls in Claude Code: not found (only server-level ones were found: the `/mcp` panel,
  `enabledMcpServers` / `disabledMcpServers`, managed policy, workspace trust). [unverified]
- **Tasks (extension `io.modelcontextprotocol/tasks`).** The server advertises it in its `server/discover` result; the client opts in
  per request via `params._meta` client capabilities, and a supported request such as `tools/call` may then answer with a
  `CreateTaskResult` (`resultType: "task"`, a `taskId`) instead of the normal result. States: `working`, `input_required`, `completed`,
  `failed`, `cancelled` (the last three terminal). Methods: `tasks/get` (poll, honouring `pollIntervalMs`), `tasks/update` (answers to
  `inputRequests`), `tasks/cancel` (cooperative: acknowledged, honoured when possible; the task may still end not-cancelled). Fields:
  `ttlMs`, `pollIntervalMs`. The spec also allows push via `notifications/tasks` after `subscriptions/listen`. Keep-alive field: not
  found. Minimum SDK versions: not found. [unverified]
- **Claude Code as a Tasks client** (from its MCP docs, read partly from a model summary of the long page, so [unverified]): it
  **polls only** (`tasks/get`; it does not use `tasks/result`, `tasks/list` or `notifications/tasks`); `pollIntervalMs` is clamped to
  250-30000 ms (default 2000; 1000 minimum in cloud); servers should keep `ttlMs` at least an hour; a task's wall-clock limit defaults
  to about 28 hours (per-server `timeout` or `MCP_TOOL_TIMEOUT`); idle timeout 5 min for HTTP/SSE/WebSocket and 30 min for stdio;
  `tasks/cancel` is sent when Claude or a person stops the task while connected, not on exit. Versions quoted: Tasks from Claude
  Code v2.1.304, with later fixes up to v2.1.331; protocol revision 2026-07-28 required.
- **Elicitation:** GA; spec at the 2026-07-28 revision (client/elicitation).
- **File Uploads:** `modelcontextprotocol/experimental-ext-file-uploads`; Claude-side docs under connectors/building/files.

## Studio relevance

`watch`. Content only; no build card until the Director asks for one.
- **offrig** is the clearest fit for Tasks: a RunPod sizing run is a 20-60 minute operation that today is polled by hand with
  `offrig_job` and watched from a background shell. As a task, Claude Code would poll it itself (`tasks/get`), show its state, and send
  `tasks/cancel` on a stop. The fit has limits to check first: cancellation is cooperative and Claude Code does **not** send
  `tasks/cancel` on exit, so offrig's own watchdog and shutdown-on-every-exit-path stay the money guard, not the task protocol; and the
  28 h wall-clock default is far above our plan deadlines, which must stay offrig's.
- **ollama-intern**'s bulk jobs (packs, corpus indexing) are a similar fit for long operations.
- **Skills over MCP** could let the offrig, atlas and ollama-intern servers carry their own runbooks (today kept as local Claude Code skills),
  versioned with the server and digest-pinned. The approval-bound-to-digest rule matches how we pin kit files; the "untrusted content"
  rule means a server skill can't carry standing rules that override the studio's.
- Contradiction with our current design: none found; our long-running tools predate Tasks and simply poll. Spec vs host gap worth
  remembering: the spec has push notifications, Claude Code uses polling only.

## Sources

- [user] shared by the Director (relayed by the Publisher), 2026-11-24
- [primary] https://claude.com/resources/articles/skills-over-mcp-tasks-and-more — the announcement, 2026-11-24
- [primary] https://modelcontextprotocol.io/extensions/skills/overview — Skills over MCP overview
- [primary] https://modelcontextprotocol.io/extensions/tasks/overview — Tasks overview
- [primary] https://modelcontextprotocol.io/specification/draft/server/discover — extension negotiation via `server/discover`
- [primary] https://modelcontextprotocol.io/specification/2026-07-28/client/elicitation — Elicitation spec
- [primary] https://code.claude.com/docs/en/mcp — Claude Code MCP docs (skills from MCP servers; MCP tasks for server authors);
  only part of the page was read verbatim
- [primary] https://github.com/modelcontextprotocol/experimental-ext-file-uploads — File Uploads extension repo (not opened)
