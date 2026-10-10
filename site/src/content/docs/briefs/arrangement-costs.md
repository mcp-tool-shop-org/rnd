---
title: What does a Kimi-K3 piano arrangement cost?
description: Two hymn arrangements by Kimi-K3 through OpenRouter cost $0.30 and $1.01. offrig budgets each call at its worst case of about $3.00, so it commits 3–10× what it spends.
date: 2026-10-08
status: measured
shelf: pending (readouts-internal)
---

## The question

The Director allowed one paid use of OpenRouter: piano arrangements for ai-jam-sessions, by Kimi-K3 only, with
the cost estimated first and recorded after. What does one cost, and how close is offrig's pre-spend budget?

## What we found

| arrangement | tokens in | tokens out | cost (OpenRouter's figure) | wall time |
|---|---|---|---|---|
| Amazing Grace | 1,728 | 19,510 | $0.297834 | 196 s |
| America the Beautiful | 1,956 | 67,147 | $1.013073 | 528 s |

- **Output dominates the cost.** Kimi-K3's output costs $13–15 per million tokens, against $0.67–0.72 for input,
  depending on the OpenRouter provider (read from OpenRouter's public listing, 2026-10-08).
- **offrig budgets the worst case:** 200,000 output tokens at the most expensive provider's rate, about $3.00
  per call. For these two arrangements that's 3–10× the actual spend. That's deliberate: the budget is a
  ceiling checked before spending, not a forecast.

## Caveats

- Two arrangements. Arrangement length varies a lot (19.5k vs 67k output tokens).
- Provider prices change. The per-provider split was read once and isn't committed; offrig's design doc records
  only the ranges.

## Receipts

- `mcp-tool-shop-org/ai-jam-sessions`:
  - `src/vocal/arrangements/source/amazing-grace-kimi-k3/meta.json` (eeebfaa);
  - `.../america-the-beautiful-kimi-k3/meta.json` (3661438);
  - produced by `scripts/arrange-hymn.ts`.
- `mcp-tool-shop-org/offrig` 06aa1e3: `docs/sidecar-design.md`, section "The OpenRouter lane".
