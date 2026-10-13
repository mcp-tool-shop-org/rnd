---
id: 2026-10-13-atlas-testing-os-rnd-buildup
title: Atlas, testing-os, housekeeping and rnd — the build-up program
date: 2026-10-13
kind: decision
relevance: act
fields: [studio-tooling]
tags: [atlas, testing-os, housekeeping, interlock, ci]
---

## Summary

On 2026-10-13 the Director approved a program to build up Atlas and testing-os, make CI failure output say what broke and how to fix it, and connect rnd to the fleet the way housekeeping connects to Atlas. R&D rules on each item and reviews it. The testing-os session builds Atlas and testing-os. R&D builds rnd's own parts. The housekeeping side goes through the Publisher.

## Key points

**The model being copied: housekeeping and Atlas.**
- Atlas works offline, one repository at a time, and records how each repository is built (its map, committed in the repository).
- Housekeeping is online and org-wide, holds the `gh` token, and records what GitHub says now: settings, red runs and cost. It collects each repository's committed map by blob id, checks map health against the org rule (no map, no check in CI, engine behind), and ties a red run's failed step to its door.
- Its findings stay private.

**The items, in order:**
1. **CI failure output (Atlas slice AM-6, approved).** `atlas check` emits GitHub annotations for each failure (`::error` with the file) and each notice, plus a step summary with the exact fix lines. Output outside Actions is unchanged. Required before release: one live failing run that records what the checks tab, the PR diff and GitHub's failure email actually show.
2. **A house style for CI failure output.** E5's preflight, rnd's `check` and other fleet validators report the same way: a code, one sentence, what changed, what to do, as annotations and a summary.
3. **rnd collects experiment records.** Each tool repository already commits its pre-registered specs and run records (interlock's receipts) the way each repo commits its map. An `rnd` command reads them at a pinned commit, trims private fields, runs the identity scan, and keeps the source sha256. This replaces the hand copy of E4b's data (rnd #2). `experiments/charts/make_charts.py` already reads sibling repos at pinned commits.
4. **A shared run-record format in testing-os.** E4b and E5 built pre-registration locks, run records, a run lifecycle with quarantine, and fail-closed preflights. testing-os holds that record format as a schema beside its existing eight, so interlock, rnd and later experiments validate alike.
5. **Shared defect classes.** R&D's classes (for example `test_fake_hides_platform`) become a field on testing-os findings. rnd counts classes over time across the fleet and reports them.
6. **Instrument health.** Each rnd instrument declares how it's invoked and where it lives. A check flags an instrument whose repo is gone, whose pin is behind, or that has produced no run record in a set time. Housekeeping runs it privately, and rnd shows a public summary.
7. **More static checks in testing-os,** for the defect families interlock hit this week:
   - an uncaptured subprocess output that is then read, or a live seam defaulting to a stub (ruled earlier);
   - validation that runs only after long work (E5's home-path refusal at write time);
   - exact equality between two different live measurements (E5's adapter match).
8. **R&D uses `atlas mcp` in its own reviews.** That gives real use data for the pre-registered atlas-mcp-utility experiment, which runs only with the Director's go on its token budget.

**Already in place:**
- rnd #3: the `datapacks` part, and the `atlas` and `testing-os` instruments;
- the AM slice approved (testing-os #156);
- interlock's run lifecycle and fail-closed preflights as the working example for item 4.

## Studio relevance

The goal is that a red CI run tells the Director what broke and the one-line fix, and that every measurement and every defect lands in one place with provenance. Items 3 to 6 make rnd a collector for the fleet, as housekeeping is for Atlas.

## Claims

- [verified] `atlas check` emitted no GitHub workflow commands and wrote no step summary before slice AM (via: R&D's read of packages/atlas in testing-os at f34fca0b, 2026-10-13)
- [verified] housekeeping collects each repository's committed Atlas map by blob id and reports map health against the org rule (via: the housekeeping hand-off and its HK1/HK2 merges, 2026-09-30)

## Sources

- [primary] https://github.com/dogfood-lab/testing-os/pull/156 — the AM slice and R&D's ruling
- [primary] https://github.com/mcp-tool-shop-org/rnd/pull/3 — the datapacks part and the two instruments
