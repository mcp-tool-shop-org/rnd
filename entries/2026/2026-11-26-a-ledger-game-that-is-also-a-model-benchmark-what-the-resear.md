---
id: 2026-11-26-a-ledger-game-that-is-also-a-model-benchmark-what-the-resear
title: A ledger game that is also a model benchmark: what the research says we are missing
date: 2026-11-26
kind: finding
relevance: act
fields: [evaluation, game-design]
tags: [merchant-league, xrpl, deep-research]
---

## Summary

Two open-ended Deep Research runs asked how to build merchant-league up as both a game and a benchmark for models
playing on the XRP Ledger Testnet. One run was technical, the other about user experience. Both reports worked from a
short public description, so much of their advice was already in the design: mirrored seeds, commit-reveal, a loopback
test ledger and paired cluster statistics. Read against the code, they still found real gaps. The evaluation side has
no baselines a result can be compared against. The interface has no accessibility mode, and players get no view of
what the other seats were secretly aiming for.

## Key points

- **Wrong about us.** The technical report assumed a fixed final turn, and an AI judge grading whether deals were kept.
  merchant-league does neither:
  - the game ends by a per-turn closing hazard from turn 24 (`league-core` types);
  - deal-keeping is read by a frozen closed-grammar extractor and a deterministic scorer.

  So the report's self-preference-of-judges risk doesn't apply.
- **Gaps in the evaluation crates:**
  - a silent-market arm, the same game with no negotiation, to measure what talk adds;
  - scripted baseline seats: random-legal, always-defect and tit-for-tat;
  - a seed-block scheduler: mirrored duplicate seeds rotated across seats, with seed-clustered intervals.
- **Gaps in the interface:**
  - a plain linear output mode with no colour-only state, for screen readers and colour-blind players;
  - hidden-goal annotations on the end-of-season view;
  - a "previously this season" digest on resume.
- **Design line for Game mode:** memos and peer chat are untrusted input to AI seats, and should be written down while
  Game mode is still on paper.
- **XRPL Batch.** The reports said Batch was disabled. That is true only of the original amendment, removed in rippled
  3.1.1. Its replacement, BatchV1_1, is enabled on the public Testnet (queried 2026-11-26).

## Studio relevance

`act`: the maintainer approved the silent-market arm, scripted baselines and seed-block scheduler as a build card, with
the accessibility pass next. Game mode comes before any phone or web client (the maintainer's decision, 2026-11-26).
One question stays open: whether a lobby that masks which seats are AI is ever acceptable, given that the design
discloses AI seats up front.

## Claims

- [verified] BatchV1_1 is enabled on the XRPL Testnet. (via: the `feature` method on the public Testnet server,
  2026-11-26)
- [verified] The original Batch amendment is obsolete, removed in rippled 3.1.1, and replaced by BatchV1_1. (via:
  xrpl.org known amendments, snapshot dated 2026-09-16, read 2026-11-26)
- [verified] merchant-league ends a season by a per-turn closing hazard on turns 24–31, capped at 32. It does not end at
  a fixed turn. (via: the league-core source, read 2026-11-26)
- [unverified] Several figures the reports cite were not found on the cited abstract pages. These include a 73.5%
  self-preference rate and "243 models" on an arena leaderboard. They may be in the paper bodies and are not relied on.

## Sources

- [aggregator] https://gemini.google.com/ — Gemini Deep Research (Gemini 4 Carbon), seeds 64 and 65, 2026-11-26: technical and user-experience reports (kept verbatim in
  the lab's private notes, with harvests read against the code).
- [primary] https://xrpl.org/resources/known-amendments — XRPL Foundation, amendment status.
- [primary] https://xrpl.org/docs/references/http-websocket-apis/admin-api-methods/status-and-debugging-methods/feature
  — the `feature` method used for the Testnet check.
