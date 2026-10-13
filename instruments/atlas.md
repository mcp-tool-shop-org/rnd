---
id: atlas
title: atlas — a repository's map, checked in CI and served to agents
date: 2026-10-13
kind: instrument
relevance: reference
fields: [studio-tooling, agent-tooling]
tags: [instrument]
instrument_status: shipped
invoke: "npx --yes @dogfood-lab/atlas@<pin> map|check|explain|gaps|mcp  (npm @dogfood-lab/atlas; fleet pin 1.24.0, latest 1.26.0); MCP tools mcp__atlas__* in a session started inside a mapped repo"
when: "The question is how a repository works: what a file or part is, what a change reaches, where work comes in, what no test reaches, or what will break a workflow before it runs."
where: "E:/AI/testing-os/packages/atlas · github.com/dogfood-lab/testing-os"
---

## Summary

Atlas reads a git repository and writes `atlas/`: a page (`README.md`), the same sections as data (`page.json`), every tracked file in its part with the edges between parts (`structure.json`), and what changes together over 180 days (`statistics.json`). Nothing on the page is written by a person except the one-line summary. `atlas check` runs in CI and fails when the committed map no longer matches the tree. `atlas mcp` answers an agent over stdio with seven tools that never write to the repository, and each answer names the snapshot it used. It starts from the committed map. `atlas_refresh` maps the working checkout anew in a background process, into a cache outside the repository (`%LOCALAPPDATA%\atlas` on Windows), and swaps that snapshot in when it finishes. From then on, answers describe the checkout as it was refreshed, not the committed map. A refresh is a full map run, CPU and disk, so it waits while a measurement holds a GPU grant.

## Studio relevance

Every org repository that runs workflows keeps a map, made by one pinned engine (org rule, 2026-09-30). For a question about how a fleet repo works, start from its `atlas/README.md`, then `explain <path>`. In a PR review, the regenerated map's "What changed" section shows what the change reaches.

## What it measures

- **Parts and imports:** JavaScript, TypeScript, TSX, Python, Rust and GDScript, parsed with tree-sitter and resolved the way the runtime resolves them.
- **Doors:** workflows, published commands, packages, sites and apps, with each job's runtime.
- **Landing places:** the tracked paths code writes and reads, with how each writer and reader was found (`ast`, `config`, `text` or `weak`).
- **Test reach:** what CI runs and which files tests import, run or discover (`gaps`, rules G1 to G6).
- **Workflow breakage notices:** D1, a Node pin the tool a step runs does not accept; D2, `npm ci` from a lockfile missing the job platform's native binding.
- **Co-change:** what changes together in git history.

## What it does not measure

- **Runtime behaviour:** it never runs the code or the tests. Reach is not proof a test exercises a file, so it says "no test imports or runs this", never "untested".
- **Paths built at run time:** writes and reads whose path is built at run time are counted, not named.
- **Other languages:** a repo in any other language gets a door-only map, covering its workflows but not its parts or imports.
- **Shallow clones:** refused, because a map made from one loses its history.
- **Its own value:** whether agents do better with `atlas mcp` has not been measured. The experiment is in R&D's queue (below).

## Known friction

A folder with no part in `atlas/boundaries.yaml` reddens main on every new file in it (`ATLAS_UNASSIGNED_NEW`). Between 2026-09-30 and 2026-10-13 it hit at least five repositories, among them interlock's `receipts/` (twice). rnd's `datapacks/` had the same gap. The local fix is one boundary per folder.

## In build (R&D rulings, 2026-10-13)

- `check` prints the exact boundary lines to add.
- `map` warns about a top-level folder with no part.
- `check` says when the map predates staged files.
- A pre-registered experiment, `experiments/atlas-mcp-utility/`, measuring agents with and without `atlas mcp`. It was pre-registered on main on 2026-10-13 (rnd #5), after R&D's blind key audit: 15 of 15 keys confirmed after amendment 1. The Director approved the pilot only (4 pairs plus 2 repeats, run on his Claude plan, with a 30M-token ceiling). The full run waits for his go on the pilot report.
- The exit test: a replay of the 2026-09-30 triage.
- Cross-repository queries through the `repo` argument, after one security review.
