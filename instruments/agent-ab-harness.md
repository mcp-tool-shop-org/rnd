---
id: agent-ab-harness
title: agent-ab-harness — paired A/B runs of a coding agent in a sandbox
date: 2026-10-13
kind: instrument
relevance: act
fields: [agent-tooling]
tags: [instrument, experiments, claude-code, sandbox, ab-test]
instrument_status: shipped
invoke: "`python experiments/agent-ab-harness/run.py --probe|--pilot|--replay …`, run as root inside the Docker sandbox `atlas-pilot` (see [[docker-sandboxes]]). The probe must pass before any counted run. Plan routes draw on the Director's plan and need his go; the local route needs a GPU grant from the Publisher."
when: "An experiment compares a coding agent with and without one change (an MCP server, a prompt note, a model route) on read-and-answer repository tasks with fixed keys. Design it with the A/B experiment template first, and have an outside model review the design before any run."
where: "experiments/agent-ab-harness/ (README, run.py, grade.py, example inputs); tests in tests/test_agent_ab_harness_run.py and tests/test_agent_ab_harness_grade.py; design template on the rnd site, handbook › A/B experiments"
---

## Summary

The harness runs paired trials of Claude Code (pinned CLI, headless) on a fresh copy of a pinned repository checkout per run.
- **Containment:** an unprivileged user in a mountless Docker sandbox, checked by a sentinel probe.
- **Starts:** each run's start is checked against its arm.
- **Records:** token totals, task wall time, tool use and cost.
- **Grading:** each answer is graded against a key fixed before the run.
- **Stops:** the whole run stops on a containment or measurement defect.
- **Replay:** recorded streams can be re-checked offline.

## What it can and can't compare

- **It can compare:** one agent with and without an MCP server, a prompt note, or a different plan model. The rest of the setup is held the same.
- **It isn't a fair test of local models against Claude.** The agent is Claude Code, whose system prompt and tool conventions are built for Claude models. A local model behind Ollama's Anthropic-compatible endpoint is a guest in that runtime. Compare local and cloud setups as each would really be deployed.
- **Tasks are read-and-answer.** Writing code would need hidden tests per task, which the harness doesn't run.

## Setup facts it depends on (rig, 2026-10-13)

- [[2026-10-13-claude-code-read-deny-rules-do-not-stop-a-grep-walk]]: containment is by OS permission, not deny rules.
- [[2026-10-13-claude-code-starts-a-turn-before-mcp-servers-connect]]: arm B holds its first message until the server connects.
- [[2026-10-13-nemotron-lightning-needs-its-context-set-for-claude-code]]: the local route runs at a pinned 131k context.
