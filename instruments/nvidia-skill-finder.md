---
id: nvidia-skill-finder
title: NVIDIA skill finder (external, not installed)
date: 2026-10-07
kind: instrument
relevance: reference
fields: [agent-tooling, gpu-computing]
tags: [instrument]
instrument_status: planned
invoke: "Not installed. Install (needs the Director's approval): npx skills add nvidia/skills --skill nvidia-skill-finder --agent claude-code --global --yes"
when: "NVIDIA-flavoured work (CUDA, TensorRT, Omniverse, NIM, drivers) where a vendor skill might already exist."
where: "github.com/NVIDIA/skills · local mirror: catalogs/nvidia-skills (rnd catalog list)"
---

## Summary

An 8 KB router skill. It checks the live NVIDIA catalogue, recommends at most three skills with install commands, and never installs without approval. Until it is installed, `rnd search` over the mirrored catalogue does the same lookup offline.

## Studio relevance

See [[2026-10-07-nvidia-agent-skills-catalog]].
