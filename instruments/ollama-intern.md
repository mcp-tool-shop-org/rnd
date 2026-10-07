---
id: ollama-intern
title: ollama-intern — bulk analysis on local models
date: 2026-10-07
kind: instrument
relevance: reference
fields: [studio-tooling, local-llm]
tags: [instrument]
instrument_status: shipped
invoke: "MCP tools mcp__ollama-intern__* (local Ollama only)"
when: "Bulk summarising, extracting or classifying a large pile of source text without spending Claude context."
where: "npm ollama-intern-mcp"
---

## Summary

42 job-shaped tools that delegate analysis to a local Ollama model. Standing Rule 1 (2026-09-29): never route to Ollama Cloud models; local models only.

## Studio relevance

Good for first-pass digestion of long sources before writing an entry. Record which local model produced any verdict.
