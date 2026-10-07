---
id: 2026-10-07-nvidia-agent-skills-catalog
title: NVIDIA Agent Skills catalogue (NVIDIA/skills)
date: 2026-10-07
kind: catalog
relevance: act
fields: [agent-tooling, gpu-computing]
tags: [nvidia, skills, claude-code, catalogue, skill-finder]
---

## Summary

NVIDIA publishes 398 verified agent skills in the standard SKILL.md format (Claude Code, Codex, Cursor), grouped into 18 lanes. The whole catalogue is mirrored in this seat at `catalogs/nvidia-skills`, pinned to a commit and rated for studio fit. Browse it with `rnd catalog lanes` / `rnd catalog list --fit direct|adjacent`.

## Key points

- Licence: Apache-2.0 (code) and CC-BY-4.0 (skill text). Each skill folder carries a signature file (`skill.oms.sig`).
- `skills.sh.json` is the machine-readable lane map; the largest lanes are Vision AI (88), Training AI (72) and Networking (58).
- Most of the catalogue is enterprise or data-center work: DOCA networking, Jetson BSPs, TAO training, BioNeMo, medical imaging.
- Gaming lane: rtx-remix-modding (remaster classic games through the Remix Toolkit MCP), g-assist-mcp-skill (read/change this machine's GPU and display settings) and nvidia-app (drivers).
- Closest to the studio: nvidia-skill-finder (the router), the TileGym cuTile kernel kit, warp-eval, data-designer (synthetic datasets), Nemotron speech/voice, NeMo Retriever, rag-eval, and the TAO CLIP/embedding/depth skills for dataset curation.
- `nvidia-skill-finder` is a recommend-only router: it checks the live catalogue, suggests at most three skills, and asks before installing. Registered as instrument [[nvidia-skill-finder]].

## Studio relevance

Decision for the Director: install `nvidia-skill-finder` globally for Claude Code (one small skill whose trigger fires on CUDA, GPU, TensorRT, Omniverse and similar work), or keep using the offline mirror here via `rnd search`. Do not bulk-install the catalogue: 398 skills would crowd every session's skill list. Two NeMo-RL skills (auto-research, session-memory) are worth reading as patterns for this seat and for loadout-os.

## Claims

- [verified] The catalogue holds 398 unique skills in 18 lanes at commit 67a13c0b. (via: rnd catalog sync over the GitHub API, 2026-10-07)
- [verified] nvidia-skill-finder never installs a skill without explicit user approval. (via: the skill's own SKILL.md, read 2026-10-07)

## Sources

- [primary] https://github.com/NVIDIA/skills — NVIDIA/skills repository
- [primary] https://build.nvidia.com/skills — NVIDIA skills catalogue page
- [primary] https://raw.githubusercontent.com/NVIDIA/skills/main/skills.sh.json — lane map
