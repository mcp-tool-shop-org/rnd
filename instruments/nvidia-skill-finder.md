---
id: nvidia-skill-finder
title: NVIDIA skill finder (installed for Claude Code)
date: 2026-10-07
kind: instrument
relevance: reference
fields: [agent-tooling, gpu-computing]
tags: [instrument]
instrument_status: shipped
invoke: "Claude Code skill nvidia-skill-finder (global, ~/.claude/skills; fires on NVIDIA/CUDA/GPU work). Offline equivalent: rnd search / rnd catalog list"
when: "NVIDIA-flavoured work (CUDA, TensorRT, Omniverse, NIM, drivers) where a vendor skill might already exist."
where: "github.com/NVIDIA/skills · local mirror: catalogs/nvidia-skills (rnd catalog list)"
---

## Summary

An 8 KB router skill. It checks the live NVIDIA catalogue, recommends at most three skills with install commands, and never installs without approval. Installed 2026-10-07 on the Director's go, copied from NVIDIA/skills at commit 67a13c0b (SKILL.md, references/taxonomy-routing.md, skill-card.md) rather than via the third-party `npx skills` installer, so no outside code ran. To update, re-copy those files from a newer commit. `rnd search` over the mirrored catalogue does the same lookup offline.

## Studio relevance

See [[2026-10-07-nvidia-agent-skills-catalog]].
