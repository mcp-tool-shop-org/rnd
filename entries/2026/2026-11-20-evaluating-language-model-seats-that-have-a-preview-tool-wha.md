---
id: 2026-11-20-evaluating-language-model-seats-that-have-a-preview-tool-wha
title: Evaluating language-model seats that have a preview tool: what a Deep Research report found (seed 42)
date: 2026-11-20
kind: finding
relevance: act
fields: [evaluation]
tags: [merchant-league, agent-evaluation, seed-42, harvest]
---

## Summary

In Merchant League, a multiplayer trading game, some seats are played by open-weight language models. A model seat may
call a "what-if preview" tool before it commits its orders; the tool applies the public rules to that seat's own
candidate orders only. Before the first evaluation games, we asked a Gemini Deep Research run how to design and record
such evaluations when only tens of games are affordable. The report is `[aggregator]` AI output; a harvest clerk
fetched 14 of its papers (abstracts only) and recomputed its power arithmetic.

Its central advice changes our plan: do not compare whole games with the tool on against games with it off, because
one different word on the first turn sends the games down different paths, so shared seeds pair poorly. Compare the
tool's effect at frozen game states instead.

## Key points

- **Frozen-state branching.** Save the state just before a seat acts, then run that one decision three ways: tool off,
  a control with the same extra wording and room to think but no tool, and tool on, all against the other seats'
  recorded orders. The control separates the tool's effect from the effect of extra words and extra reasoning.
- **Duplicate tables.** For whole games, rotate one focal seat through every chair against fixed opponents on the same
  seeds, and add all-off and all-on tables to separate a seat's own gain from what the tool does to the table.
- **Measure near the decision first.** Rejected orders and single-turn regret before season wealth, which is too noisy
  for tens of games. Report with a bootstrap over seed blocks.
- **Pin the serving stack.** One GPU model, prefix caching off, a generous output limit, and logging of token ids,
  finish reason, and weight and template hashes. Cross-GPU numerical drift, prefix-cache divergence and 4-bit
  quantisation each change decisions measurably.
- **Power.** 16 games per arm unpaired detects about a one-standard-deviation effect; 24 paired seeds at a correlation
  of 0.5 detect about 0.55. The correlation is a guess until measured.
- **Its first plan.** A free pre-flight (pinned stack, token-id identity on a repeated game, behaviour past the call
  limit, truncation visible), then 12 tool-off games yielding about 144 frozen states run three ways, with a larger
  whole-game step only if that shows something.

## Studio relevance

### What it contradicts in our design (read first)

| Finding | Merchant League today | Decision |
|---|---|---|
| Whole-game tool-on against tool-off comparisons pair poorly | The plan was to run games with the tool on and off | A frozen-state design is the candidate for the first evaluation; scope goes to the Director |
| A wording-and-thinking control arm is needed to isolate the tool | Two arms exist: tool off and tool on (wording r1, now r2) | A control arm would be a new pinned wording row; not built |
| Pre-act state snapshots and replay are needed | The relay records every request and reply, but not a reloadable game state | A snapshot writer and loader would be a new card |
| finish_reason, truncation, serving flags and cache settings should be logged | Raw replies are kept, so finish_reason is in the body; serving flags are not recorded (not checked in full) | To be checked before the first run |
| Tool rounds should not be replayed into later turns | Already the rule | No change |

### Decisions and actionables

1. The evaluation design (frozen states, a control arm, and what defines regret) goes to the Director as new scope.
2. Nothing is built until he decides; the next build card for the relay is unchanged by this report.

## Claims

- [verified] Results from the same model differ across GPU types by up to about 9% (via: abstract of the cited study, fetched by the harvest clerk, 2026-11-20)
- [verified] Comparing 16 games against 16 unpaired detects an effect of about 1.02 standard deviations, and 24 paired seeds at correlation 0.5 about 0.55 (via: recomputed by the harvest clerk, 2026-11-20)
- [unverified] Tool-using agents skip or ignore tool results in 53% to 60% of cases (the report's figure; not on the abstract pages read)
- [unverified] The seat-to-seat correlation in our game is 0.3 to 0.5 (the report's guess; not measured)

## Sources

- [aggregator] https://gemini.google.com/ — Gemini Deep Research (Gemini 4 Carbon, High), 2026-11-20: report on evaluating language-model agents in a multiplayer trading game
