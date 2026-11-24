---
id: 2026-11-24-authored-data-that-never-reaches-play-what-a-deep-research-a
title: Authored data that never reaches play: what a Deep Research audit found (seed 59)
date: 2026-11-24
kind: finding
relevance: act
fields: [studio-tooling, software-design]
tags: [world-forge, ai-rpg-engine, seed-59, harvest]
---

## Summary

World Forge is the studio's world-authoring tool. It exports worlds that the RPG engine loads. An earlier audit claimed
that most authored fields never reach play. We asked a Gemini Deep Research run how an authoring tool and a deterministic
simulation should stay aligned:
- what to do with fields the engine does not use;
- how to version the contract between them;
- how to test it across releases.

The report is `[aggregator]` AI output with 193 cited sources. We compared it with World Forge at `30d067b` and the engine
at `03342f5`; its cited studies were not read for this entry.

The picture is better than the audit said. The engine already names every field it drops and gives a reason. The gap is
that neither the tool nor its exporter shows those reasons to the author. The audit's headline count of live fields does
not reconcile with any file we could find.

## Key points

- **Drops are not silent in the engine.** Intake records each dropped field with a reason:
  - evaluated but not mapped;
  - session-scoped;
  - no runtime field.

  The fix is to surface those reasons where authors work, not to add another read audit.
- **Keep the strict gate.** The report leans toward tolerant reading. Our engine's gate refuses unknown keys by design,
  citing the fail-loudly reading of RFC 9413 and game precedents (Factorio, Minecraft, Paradox). That stays, plus a
  capability list the tool can show.
- **Some "dead" groups are host-wired, not dead.** Progression trees, the build catalog and the ruleset are session-scoped:
  the host reads them outside the content hash. Dialogue is validated and taken by the dialogue module from pack config.
- **Test the published tool against the published engine.** Nothing in either repo's CI loads the released exporter's
  output into the released engine. The report's remedy, a cross-package matrix with golden worlds, fits our gap.
- **Measure reach before removing anything.** A field-reach probe changes each field in a small world, plays a seeded
  turn script and compares a hash of the observable state. It would replace the unverified "77 live fields" with a real
  count.

## Studio relevance

### What it contradicts in our design (read first)

| Finding | World Forge `30d067b` / ai-rpg-engine `03342f5` | Decision (2026-11-24) |
|---|---|---|
| Tolerant reading discards fields silently | The engine names every drop and its reason, and dropped fields never flip the load's success flag | Show the reasons to authors (exporter report, tool UI). No new engine read audit |
| Move to tolerant reading | The gate is strict by design and refuses unknown keys | Keep the strict gate; add only a capability list for the tool |
| 90 + 223 + 77 field split | The export table's tally is 92 with no channel and 297 carried (277 lossless, 20 approximated), 389 in all; no file defines the 77 | Use the table; replace the 77 with a field-reach probe |
| Release-to-release breakage | No CI loads a published export into the published engine | A cross-repo CI job (export, engine load gate, stage attach, moves) and a release gate on published versions |

### Decisions and actionables

1. **Now:**
   - the exporter emits factions and per-entity AI, so authored behaviour reaches play (to the Director first, as World
     Forge work);
   - the release gates above.
2. **Then a tiered rule per field group:**
   - mark unreached fields "not simulated" in the tool, from a generated list so the list cannot drift;
   - route the groups that close the play loop and already have a seam (progression, connections);
   - remove a group only after it has stayed marked through one release.
3. The studio's World Forge boot test on 2026-11-24 loaded a fresh export in the published engine and played moves and
   dialogue with no errors. It also found that the previous published exporter's output is refused by the engine, which
   is the release gap above. A new World Forge release ships from main.
4. **Filler:** Petri-net reachability, localization ids, Cambria-style lenses and the report's post-mortem triage.

## Claims

- [verified] Engine intake records each dropped field with a reason, and dropped fields do not flip the load's success flag (via: `packages/content-schema/src/intake.ts:85`, `:162-163` and `:520` in mcp-tool-shop-org/ai-rpg-engine at 03342f5, read by R&D, 2026-11-24)
- [verified] Progression trees, the build catalog and the ruleset are session-scoped keys (via: `packages/content-schema/src/intake.ts:509` at 03342f5, read by R&D, 2026-11-24)
- [verified] The content gate refuses unknown keys by design and cites Factorio, Minecraft, Paradox and RFC 9413 (via: `packages/content-schema/src/gate.ts:11-14` and `:321` at 03342f5, read by R&D, 2026-11-24)
- [verified] World Forge's export table tallies 92 fields with no channel, 277 carried losslessly and 20 approximated (via: `docs/c0-alignment/export-table.md:5` in mcp-tool-shop-org/world-forge at 30d067b, read by R&D, 2026-11-24)
- [verified] Exports from the previous published World Forge (4.9.1) are refused by the published engine's loader, on the encounter type and on item placements without an entity id (via: the studio's World Forge boot test, 2026-11-24)
- [unverified] The report's split of 90 vanishing, 223 discarded and 77 live fields (no file we read defines the 77, and the parts do not reconcile with the export table)
- [unverified] The report's figures on silent misconfigurations (Zhang et al., OOPSLA 2021) and removable configuration knobs (Xu et al., FSE 2015) (cited by the report; papers not read)

## Sources

- [aggregator] https://gemini.google.com/ — Gemini Deep Research (Gemini 4 Carbon, High), 2026-11-24: "Aligning World Authoring and Deterministic Simulation in an AI-Agent RPG Pipeline"
- [primary] https://github.com/mcp-tool-shop-org/world-forge — the authoring tool and its AI RPG exporter, read at 30d067b
- [primary] https://github.com/mcp-tool-shop-org/ai-rpg-engine — the engine's content intake and gate, read at 03342f5
- [primary] https://www.rfc-editor.org/rfc/rfc9413 — Thomson and Schinazi (2023), Maintaining Robust Protocols (RFC 9413) (cited by the engine's gate and by the report; not re-read for this entry)
