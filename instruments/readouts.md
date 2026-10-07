---
id: readouts
title: readouts — the studio's verified knowledge bases
date: 2026-10-07
kind: instrument
relevance: reference
fields: [research-method, studio-tooling]
tags: [instrument, knowledge-base, sqlite, study-swarm]
instrument_status: shipped
invoke: "python -m rnd readouts <words> [--any] [--kb <name>] (search); python -m rnd readouts --list"
when: "Before researching any topic the studio may already have studied: models, engines, training, sprites and animation, vocology and singing, Godot, Blender, Rust, Docker, XRPL, environment assets."
where: "E:/AI/readouts (working repo mcp-tool-shop-org/readouts-internal, private; public mirror mcp-tool-shop-org/readouts)"
---

## Summary

A monorepo of study-swarm-built, verified SQLite knowledge bases: 14 at last count
(asset-library, blender, dimetric, docker, godot, model, open-setting, rust,
sprite-motion, sprites, tensor-engine, training, vocology, xrpl), each with sourced,
verified rows and its own FTS5 index. It is the studio's deep store; this seat is the
broad intake.

`rnd readouts` searches every knowledge base at once, read-only, through each KB's
own full-text table, with prefix matching (`listener` also finds `listeners`).
Words are ANDed; `--any` ORs them for exploration. The checkout location comes from
`$RND_READOUTS` (default `E:/AI/readouts`) or `--root`.

## Studio relevance

Search readouts before dispatching research agents, and tell the agents what it
already covers so they target the gaps. A finding from this seat that has been
verified and is load-bearing can graduate into a readouts KB through a study-swarm
wave.
