---
id: 2026-11-21-world-authoring-for-story-driven-2-5d-rpgs-what-a-deep-resea
title: "World authoring for story-driven 2.5D RPGs: what a Deep Research report found (seed 46)"
date: 2026-11-21
kind: finding
relevance: act
fields: [game-design, studio-tooling]
tags: [world-forge, world-authoring, seed-46, harvest]
---

## Summary

World Forge is the studio's world-authoring tool for 2D and 2.5D RPGs: a browser editor plus export lanes for the
studio's runtime engine, Unreal Engine 5 and Godot 4. This entry is about the runtime-engine lane. A Gemini Deep
Research run was seeded with a question that named nothing of ours. It covered:
- how story-driven RPG worlds are authored: what the reference games did, and how spatial and temporal state is kept;
- how exploration is structured;
- how one world feeds several engines;
- where local models help.

The report is `[aggregator]` AI output. A harvest agent (an AI model) listed 22 of its claims. It checked 14 of them:
11 at the source page and 3 through search-result summaries, with 9 confirmed and 5 partly. The other 8 were not
checked, nor were the report's many other figures or most of its source registry. R&D then re-read several sources
itself, and checked each finding that bears on our design against World Forge's code at commit 023ff9a and its
in-flight step-1 branch.

## Key points

- **One source of truth for the contract between tool and engine.** The report's multi-engine pattern keeps all runtime
  simulation in one engine-free core, with a thin presentation shell per engine. Applied to an authoring tool, the same
  idea means one source of truth for the contract between the tool and each engine.
- **Ids that never change and are never reused.** Ids that survive renames, with tombstones for removed ones, underpin
  saves, localisation and merges. Examples: Larian's Osiris compiler ignores the readable prefix of an id, and Yarn
  Spinner tags every line with an id.
- **Check the contract by machine, before building scenes.** Choice of Games' Randomtest tool plays a game at random
  many times; its documentation recommends 10,000 runs or more. The report adds a nightly headless fuzzer.
- **Put the consumer's own validator in the loop** for anything generated.
- **Layered world states:** a base map plus sparse overrides per story state, never cloned maps. The report names
  OpenUSD sublayers and variants, and Unreal data layers.
- **Exploration as a mission graph plus a space graph,** with cycles and lock-and-key checks. Dead Cells, for example,
  places hand-built rooms on a designer-drawn graph.
- **Local models emit structure, not coordinates.** Per three preprints, which were not checked, small models fail at
  raw positions and graph layout. So models should emit graphs and constraints, and deterministic code places them.
- **Build a thin playable slice first,** and attach everything else to it. The studio decided against this for now; see
  Studio relevance.

## Studio relevance

### What it contradicts in our design (read first)

| Finding | Our design today (checked at 023ff9a and the step-1 branch) | Decision |
|---|---|---|
| One source of truth for the tool-engine contract | World Forge keeps hand-made copies of two engine lists, the hashed keys and the encounter types; the step-1 stage script imports the third, the pack keys, from the engine. The copies had drifted | Kept for now under a written rule (engine first, then the copy, in the same cycle), with tests pinning the remaining copies. The next step generates the lists from the installed engine at build time; only the browser-safe hasher stays a copy, with its equivalence test |
| Contracts checked by machine on every commit | The contract test on the in-flight step-1 branch pins one engine release, and no job is scheduled. So a new engine release goes unseen, as an older pin did | A weekly job moves the engine pin on a branch, runs CI on it and opens an issue for review |
| The consumer's validator in the loop | The command-line entry point (`world-forge-export --validate-only`) runs World Forge's own checks, and the step-1 branch adds one mirrored engine rule (the engine's encounter types); it imports nothing from the engine | It will run the engine's real gate and intake as a dry run, and list what the engine drops |
| A thin playable slice first | Many editor features have no trigger or no reader, and no exported world has been played yet | Not now. The contract pipeline and the editor's own defects come first. The list of disconnected features stays as a record |
| Ids that never change | Item placements had no ids (being fixed); no tombstones exist | Decided 2026-11-21: stable ids with a retired-id list come first among the data-model changes, after the editor's own fixes. Nothing already saved is renumbered |
| Layered states, split files, narrative facts | No story-state model; one project file; no quests or facts authored | Decided 2026-11-21: one file per map, then story-state layers, after stable ids. Who authors narrative facts is decided after a further research report |

### Decisions and actionables
1. The contract is kept by machine: a weekly engine bump, a validator that runs the engine's real gate, and engine lists
   generated at build time instead of copied by hand.
2. The editor's own defects are fixed next, before any new feature.
3. Then the data model, in order: stable ids with a retired-id list, one file per map, and story-state layers.

## Claims

- [verified] Yarn Spinner tags lines with `#line` ids for localisation, and adds them when they are missing (via: Yarn Spinner docs, read by the harvest agent, 2026-11-21)
- [verified] LDtk can save each level to its own `.ldtkl` file in a sub-folder, beside the project file (via: LDtk docs page "Optional separate levels", read by R&D, 2026-11-21)
- [verified] Unreal's World Partition saves each actor to its own file, and streaming can be switched off (via: Epic docs, read by the harvest agent, 2026-11-21)
- [verified] Larian's Osiris ignores the text before a GUID when that text has no "-"; goals have INIT, KB and EXIT sections; the goals of the active mods are sorted alphabetically into one story, and the rules of active goals run in it from top to bottom (via: Larian's Osiris Overview page, read by R&D, 2026-11-21)
- [verified] Dead Cells places hand-built rooms onto a designer-drawn concept graph (via: deepnight.net, read by the harvest agent, 2026-11-21)
- [verified] Skyrim's dungeons used two kit artists, eight level designers and seven kits for 300+ dungeons (via: Game Developer, read by the harvest agent, 2026-11-21)
- [verified] The Dragon Quest III HD-2D remake uses no special engine and no pixel art in its backgrounds (via: Siliconera interview, read by the harvest agent, 2026-11-21)
- [verified] Ordering partly overlapping rules by source position makes reordering files change behaviour (via: Plotkin's essay, read by the harvest agent, 2026-11-21)
- [verified] At 023ff9a, World Forge's CI has no scheduled workflow, and its command-line entry point (`cli.ts`) imports nothing from the engine (via: R&D read of world-forge 023ff9a, 2026-11-21)
- [unverified] Choice of Games runs 10,000 to 30,000 random playthroughs and gates publication on them. The cited page recommends 10,000 or more and states no gate
- [unverified] Small and mid-sized models collapse on raw coordinates and planar graph layout (three preprints, not checked)
- [unverified] Godot deprecated TileMap in 4.3. The stable TileMap class page confirms the deprecation, not the version

## Sources

- [aggregator] https://gemini.google.com/ — Gemini Deep Research (Gemini 4 Carbon), 2026-11-21: report "Authoring Story-Driven RPG Worlds" (seed 46, prompt sha256 prefix 636647c1)
- [primary] https://docs.yarnspinner.dev/write-yarn-scripts/advanced-scripting/tags-metadata — Yarn Spinner, tags and metadata
- [primary] https://ldtk.io/docs/game-dev/json-overview/optional-separate-levels/ — LDtk, Optional separate levels
- [primary] https://dev.epicgames.com/documentation/en-us/unreal-engine/world-partition-in-unreal-engine — Epic Games, World Partition in Unreal Engine
- [primary] https://docs.larian.com/Osiris_Overview — Larian Studios, Osiris Overview (Divinity Engine Wiki, 2019)
- [primary] https://docs.godotengine.org/en/stable/classes/class_tilemap.html — Godot Engine, TileMap class reference
- [primary] https://deepnight.net/tutorial/the-level-design-of-dead-cells-a-hybrid-approach/ — Sébastien Bénard, The Level Design of Dead Cells (2020)
- [primary] https://www.gamedeveloper.com/design/skyrim-s-modular-approach-to-level-design — Joel Burgess, Skyrim's Modular Approach to Level Design (2013; slides with Nate Purkeypile)
- [primary] https://www.siliconera.com/interview-preparing-a-hd-and-2d-dragon-quest-iii-remake/ — Jenni Lada, Interview: Preparing a HD and 2D Dragon Quest III Remake (2024), with Masaaki Hayasaka
- [primary] https://eblong.com/zarf/essays/rule-based-if/ — Andrew Plotkin, Rule-Based Programming in Interactive Fiction (2009)
- [primary] https://www.choiceofgames.com/make-your-own-games/testing-choicescript-games-automatically/ — Choice of Games, testing ChoiceScript games automatically
- [primary] https://github.com/mcp-tool-shop-org/world-forge — World Forge, the code checked (commit 023ff9a)
