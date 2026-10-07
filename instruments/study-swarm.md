---
id: study-swarm
title: study-swarm — research-grounded design protocol
date: 2026-10-07
kind: instrument
relevance: reference
fields: [research-method, agent-orchestration]
tags: [instrument]
instrument_status: shipped
invoke: "Say 'study-swarm' (protocol); CLI: npx @dogfood-lab/study-swarm <cmd> (v2.1.0 on npm, not installed globally here)"
when: "A design question is qualitative or a new product layer is being designed and evidence would change the answer."
where: "studio memory: research-grounded-advisor-protocol.md · github.com/dogfood-lab/study-swarm"
---

## Summary

Dispatches 3–5 parallel research agents, one per load-bearing design question, each returning sourced findings (author, year, identifier/URL, one-sentence finding). The advisor then writes a 'Research grounding' section that ties each finding to a design implication. `study-swarm lint` enforces the sourcing standard. The verifier stage (Step 4) is conditional since 2026-09-29: only for specialized claims, suspect citations, or when the Director asks.

## Studio relevance

Findings from a study-swarm should land here as entries (kind: paper or finding), with the dispatch linked, so the evidence outlives the design session.
