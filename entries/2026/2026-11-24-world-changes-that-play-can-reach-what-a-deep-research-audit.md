---
id: 2026-11-24-world-changes-that-play-can-reach-what-a-deep-research-audit
title: World changes that play can reach: what a Deep Research audit found (seed 58)
date: 2026-11-24
kind: finding
relevance: act
fields: [game-design, testing]
tags: [ai-rpg-engine, seed-58, harvest, simulation]
---

## Summary

The RPG engine can re-dress a place when its district's fortunes change: a zone can become Damaged, Ruined or Occupied, and
the client draws it differently. Our engine notes record that nothing a player does triggers these changes today. Only a
debug shock switch does. We asked a Gemini Deep Research run how to make simulated world changes reachable in ordinary
play, keep them readable to the player, and prove reachability in CI without a human.

The report is `[aggregator]` AI output with 179 cited sources. We compared it with the engine at `03342f5`; its cited
studies were not read for this entry, and its simulation figures cite no source we could open.

Our measurement is harsher than the report's. Damaged needs a 20-point drop below a district's baseline, but stability is a
mean of zone values that default to 5, so the drop available is about 5. Occupied needs a 25-point morale drop, which
defeats can only reach if one district absorbs a defeat every few rounds.

## Key points

- **The thresholds sit outside the scale.** A threshold that the reachable range cannot meet is dead code that looks alive.
  The report proposes an interval check that fails when a threshold lies outside the reachable range of its scale. That
  single check would have caught this defect.
- **Feed change from play, not from defeats alone.** The report advises decoupling world change from party wipes and from
  individual battles. Our own design choice is a per-district damage accumulator on the existing 0-100 pressure scale, fed
  by hostile pressure the player leaves unanswered.
- **Keep thresholds relative to a baseline.** The report suggests absolute bands. Our engine tried absolute cut-offs once,
  and they flagged every zone in every pack as ruined on the first tick, so the baseline-relative contract stays.
- **Add hysteresis.** An exit band and a dwell time, saved with the game, stop a district flipping back and forth.
  Pausing recovery while a district is under hostility is a cheap local rule.
- **Prove reachability with seeded play.** The proof is many seeds and several scripted policies (do nothing, fight
  everything, defend), with assertions of "sometimes Damaged" and "sometimes Occupied". It also needs a red control (the
  producer removed, so zero events) and a green control (a synthetic shock). The debug shock never counts as a pass.
- **Its PRNG-isolation advice does not apply here.** Zone-state derivation uses no randomness in our engine.

## Studio relevance

### What it contradicts in our design (read first)

| Finding | ai-rpg-engine `03342f5` | Decision (2026-11-24) |
|---|---|---|
| Damaged and Ruined must be reachable | A 20-point drop below a baseline, on a stability mean of zone values that default to 5 | A per-district damage accumulator on the 0-100 pressure scale, fed by unanswered hostile faction pressure. Damaged and Ruined derive from it. The baseline-relative contract and the client's dressing tags stay |
| Occupation should come from sustained pressure, not wipes | -3 morale per defeat, recovery toward 50 each round, and a 25-point drop | A hostile faction whose pressure in a district stays above a threshold, unanswered, for a dwell of N rounds takes control, recorded as the cause. Answering it (defeating its units there, or resolving its pressure event) resets the dwell. Defeats alone no longer occupy a district |
| Use absolute bands | Absolute cut-offs were tried and flagged every zone as ruined | Rejected; keep baseline-relative thresholds |
| Hysteresis | Any crossing emits at once, with no exit band or dwell | An exit band and a dwell, saved with the game, and a cap on flips per 60 rounds |
| Prove reachability with SMT | The repo already has seeded reachability suites | Rejected; a seeded harness (200 seeds × 3 policies, red and green controls, an interval check) instead. Today's unreachable result is pinned as a baseline row |

### Decisions and actionables

1. The accumulator, occupation by sustained pressure, the hysteresis and the harness are one queued engine build. Its
   tunables live in pack config.
2. The first defaults are set so the harness shows a clear spread:
   - doing nothing lets at least one district fall in most seeds within 60 rounds;
   - defending keeps occupation under 5% of seeds;
   - fighting everything lands somewhere between.
3. How it feels is judged in play, not by the harness.
4. **Filler:** PRNG substream redesign, SMT, ASP or Petri-net tooling, and the report's game anecdotes.

## Claims

- [verified] Damaged needs a stability drop of 20 below the district's baseline, Ruined 40, and Occupied a morale drop of 25 (via: `packages/modules/src/zone-state.ts:114-123` in mcp-tool-shop-org/ai-rpg-engine at 03342f5, read by R&D, 2026-11-24)
- [verified] District stability is recomputed as the mean of its zones' stability values, which default to 5 (via: `packages/modules/src/district-core.ts:391-400` and `:72` at 03342f5, read by R&D, 2026-11-24)
- [verified] Each defeat lowers a district's morale by 3, and morale drifts back toward 50 every round (via: `district-core.ts:206-209` and `:366-372` at 03342f5, read by R&D, 2026-11-24)
- [verified] Absolute cut-offs were tried first and reported every zone in all 12 packs as ruined on the first tick, 62 events in all (via: `packages/modules/src/zone-state.ts:84-92` at 03342f5, read by R&D, 2026-11-24)
- [verified] The engine's own notes record that the zone-state change has no producer reachable from play (via: `packages/cli/src/sidecar-command.ts:409-418` at 03342f5, read by R&D, 2026-11-24)
- [unverified] The report's reachability percentages and the claim that one extra random roll shifts 83% of events come from its own simulations, cited to no source we could open. Treat them as hypotheses.

## Sources

- [aggregator] https://gemini.google.com/ — Gemini Deep Research (Gemini 4 Carbon, High), 2026-11-24: "Engineering Reachable, Legible, and Regression-Safe World Simulations for a Turn-Based RPG"
- [primary] https://github.com/mcp-tool-shop-org/ai-rpg-engine — the engine's zone-state and district modules and the sidecar, read at 03342f5
