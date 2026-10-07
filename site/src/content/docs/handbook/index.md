---
title: Overview
description: The studio's research bench, and how it feeds the verified readouts shelf.
sidebar:
  order: 0
---

Research and Development is the studio's research bench. Findings from any field
come in fast as short Markdown entries. Every source is tagged with its tier, and
every claim says whether anything has checked it. Rig experiments sit beside the
entries they test. One command, `rnd`, searches all of it.

## Bench and shelf

The studio keeps knowledge in two places, and they do different jobs.

| | Research and Development | [readouts](https://github.com/mcp-tool-shop-org/readouts) |
|---|---|---|
| Role | the bench: intake, experiments, open questions | the shelf: verified knowledge bases |
| Pace | an entry in minutes; claims start `unverified` | built and checked by study swarms |
| Shape | Markdown entries, one topic each | one SQLite knowledge base per domain |
| How messy | messy on purpose: disputed claims, dead ends and interim results stay visible | not messy at all: every row is sourced and verified |

The bench is allowed to be messy because it is honest about the mess. An
interim result is labelled interim. A claim no one has checked says so. A claim
that turned out wrong stays, marked `[wrong]` with what showed it, so the next
session does not rediscover it.

## The path to the shelf

1. **Bench.** A finding lands as an entry. Its claims start `[unverified]`.
   Measurements from our own machines go in as `rig` sources, with their harness
   under `experiments/`.
2. **Internal shelf.** When a topic's load-bearing claims hold up, it is built into
   a knowledge base in readouts' private working repo, or added to an existing one.
3. **Public shelf.** A knowledge base is published to the public readouts repo when
   it joins the export allow-list.

From the bench, `rnd readouts` searches every readouts knowledge base read-only,
so one seat reaches both stores.

## Any field

Research here is not limited to the studio's own fields. Each entry keeps two
things apart: what the knowledge is (Summary, Key points) and what it means for
the studio (Studio relevance, plus `relevance: act | watch | reference`).
`reference` is a fine verdict: knowledge worth having even when nothing needs doing.

## In this handbook

- [Getting started](./getting-started/): install, first searches, the wrappers.
- [Filing research](./filing-research/): the entry format, tiers, claims and links.
- [Experiments](./experiments/): how rig measurements are kept so they can be trusted.
- [Command reference](./reference/): every `rnd` command and flag.
- [Architecture](./architecture/): files as the source of truth, the index, the catalogues.
- [Security and trust](./security/): what it touches, and the public-repo hygiene.
