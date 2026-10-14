---
id: 2026-10-13-nemotron-lightning-needs-its-context-set-for-claude-code
title: "nemotron-3.5-lightning under Claude Code needs a 131k context; Ollama's default 32k cripples it"
date: 2026-10-13
kind: finding
relevance: act
fields: [local-models, agent-tooling]
tags: [ollama, nemotron, claude-code, context]
---

## Summary

Run as Claude Code's model through Ollama's Anthropic-compatible endpoint, `nemotron-3.5-lightning` loaded at Ollama's
default context of 32,768 tokens. Claude Code's system prompt and tools take about 25,000 to 28,000 of that. On a short
code-reading task it answered 1 of 4 runs correctly. A derived model with `num_ctx` 131072 answered 11 of 12 runs on a
small task set, the same 4 of 4 on that task included. It fits the RTX 5090 fully resident, peaking near 28 GB.

## Key points

- **Make the derived model:** a Modelfile with `FROM nemotron-3.5-lightning:latest` and `PARAMETER num_ctx 131072`,
  then `ollama create`.
- **Fit check:** `size_vram` equals `size` on load, with a peak of 27,862 MiB. A 65,538-token prompt peaked at 27,986
  MiB and stayed fully resident.
- **Check what loaded:** Ollama's `/api/ps` reports `context_length` per loaded model. `/api/show` reports the `num_ctx`
  parameter without loading anything.
- **Costs:** there's no prompt caching on this route, so every turn re-sends the whole context, about 0.1 to 0.4
  million input tokens a run. Ollama's Anthropic endpoint reports no output tokens. Price it by wall time and GPU time.
- **The task set was small and not a benchmark.** The finding is the context setting, not a model ranking.

## Studio relevance

Any local model behind Claude Code needs its context raised past the CLI's own overhead before its answers mean
anything. Set it in a derived model and verify it from `/api/ps`.

## Claims

- [verified] At Ollama's default 32,768 context, nemotron-3.5-lightning under Claude Code 2.1.197 answered 1 of 4 runs of one code-reading task correctly; at 131,072 it answered 4 of 4. (via: the local runs in `atlas-pilot`, 2026-10-13)
- [verified] The 131k variant stays fully resident on the RTX 5090, peaking near 28 GB. (via: the Publisher's fill check, 2026-10-13)

## Sources

- [rig] Local runs and a fill check on the rig, 2026-10-13
