---
id: 2026-11-24-showing-every-simulation-event-what-a-deep-research-audit-fo
title: Showing every simulation event: what a Deep Research audit found (seed 60)
date: 2026-11-24
kind: finding
relevance: act
fields: [game-design, testing]
tags: [ai-rpg-stage, ai-rpg-engine, seed-60, harvest]
---

## Summary

The studio's Godot client (the "stage") draws what the RPG engine decides. The engine emits a documented vocabulary of
events, but the stage renders only five of them, and it quietly ignores the rest. We asked a Gemini Deep Research run how
a decoupled turn-based client should:
- present every simulation event;
- fail loudly when something is missing;
- be tested headlessly in CI.

The report is `[aggregator]` AI output with 170 cited sources. We compared it with the stage at `c25ed2b` and the engine
at `03342f5`; its cited papers and talks were not read for this entry.

It also explains a quiet failure we found in our own CI. The engine logged every non-player character's behaviour profile
as unresolved, so all four stood still. The load still succeeded, and the stage's CI stayed green.

## Key points

- **Never drop an unknown event in a shipped build.** Apply its state change, then show a generic placeholder and log it.
  In development and CI, an event type with no handler should fail the build.
- **An unresolved behaviour profile is a load failure in development.** In an interactive release build it should still
  load, but with a visible fault. A brain that never resolves leaves a character standing still, and a log line alone is
  ignored.
- **Test presentation by its observable effect.** Assert that the sentence reaches the transcript, or that the scene
  changes, rather than that a handler ran. The stage's test harness already works this way, and already fails any test that
  asserts nothing.
- **Keep the contract asymmetric.** Commands are strict and events are additive-only. That matches the engine's contract;
  the fault is the client's silent tolerance, not the contract.
- **Defer what is not needed yet:**
  - an interface-definition language;
  - block envelopes with causal parents;
  - rasterised golden frames;
  - vision-model checks;
  - a test framework.
- **Headless Godot can exit 0 after a script error,** so CI must scan the output for error lines. This is a claim from a
  secondary write-up that we have not yet checked.

## Studio relevance

### What it contradicts in our design (read first)

| Finding | ai-rpg-stage `c25ed2b` / ai-rpg-engine `03342f5` | Decision (2026-11-24) |
|---|---|---|
| Unknown events must not vanish | The stage renders five event types and returns nothing for the rest | One transcript line, in a distinct style, naming the event type and its payload keys. The bespoke list stays as the list of custom handlers |
| Unhandled events fail CI | Nothing fails | A manifest test marks every documented event type `handled`, `no-visible-effect (reason)` or `todo (owner, expiry)`. It fails on a missing type, an expired `todo`, or a `handled` type that changes nothing when replayed |
| An unresolved profile fails the load in development | Unresolved profiles are dropped and the load succeeds | A load option, `fail` or `warn`: development builds and CI fail, release builds load with an on-screen warning. The engine library defaults to `warn`, so existing hosts keep loading |
| The client must know every event type | No machine-readable event list | The engine exports its event types as a constant, tested against its documented list |

### Decisions and actionables

1. The engine side (the load option and the event list) is in the first build now in progress.
2. The stage side follows once the engine changes merge:
   - pass profiles at load;
   - fallback rendering;
   - the manifest test, with every type seeded as `todo` expiring 2027-01-15, except the five handled ones;
   - CI failing on any dropped-profile line.
3. **Deferred:**
   - a 20-tick liveness check, which needs a per-profile expectation, since a passive character may rightly do nothing;
   - timed parries against "the client decides nothing";
   - optional summary and cause fields on events.

   All of these wait for combat work.

## Claims

- [verified] The stage lists five rendered event types and returns early for any other type (via: `stage/session.gd:38-44` and `:149-150` in mcp-tool-shop-org/ai-rpg-stage at c25ed2b, read by R&D, 2026-11-24)
- [verified] In the engine, an unresolved behaviour profile is reported as a structured error, but dropped fields do not flip the load's success flag (via: `packages/content-schema/src/intake.ts:156-157` and `:162-163` in mcp-tool-shop-org/ai-rpg-engine at 03342f5, read by R&D, 2026-11-24)
- [verified] Stage CI run 45243001881 succeeded while logging an unresolved `aiProfile "passive"` for each of its four non-player characters, twice each (via: `gh run view 45243001881 --log`, read by R&D, 2026-11-24)
- [verified] The engine's contract makes commands strict and events tolerant and additive-only (via: `docs/contract-v1/CONTRACT.md:268` and `:275-279` at 03342f5, read by R&D, 2026-11-24)
- [verified] The engine documents 39 event types in a table (via: `docs/handbook/appendix-a-event-vocabulary.md` at 03342f5, rows counted by R&D, 2026-11-24)
- [unverified] Headless Godot 4.7.2 exits 0 after a script error (from a secondary write-up cited by the report; to be checked with a deliberate error in CI)
- [unverified] The report's figures from game-testing papers and talks (GLIB, EA SEED, VideoGameQA-Bench) (not read; background only)

## Sources

- [aggregator] https://gemini.google.com/ — Gemini Deep Research (Gemini 4 Carbon, High), 2026-11-24: "Architecture, Feel, and Headless Verification for a Decoupled 2.5D Turn-Based RPG"
- [primary] https://github.com/mcp-tool-shop-org/ai-rpg-stage — the Godot client, read at c25ed2b
- [primary] https://github.com/mcp-tool-shop-org/ai-rpg-engine — the engine's content intake, contract and event vocabulary, read at 03342f5
- [primary] https://www.rfc-editor.org/rfc/rfc9413 — Thomson and Schinazi (2023), Maintaining Robust Protocols (RFC 9413) (the report's reading of tolerant events; not re-read for this entry)
