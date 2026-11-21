---
id: 2026-11-21-one-world-many-engines-over-years-what-a-deep-research-repor
title: "One world, many engines, over years: what a Deep Research report found (seed 48)"
date: 2026-11-21
kind: finding
relevance: act
fields: [game-design, studio-tooling]
tags: [world-forge, seed-48, harvest]
---

## Summary

World Forge is the studio's world-authoring tool for 2D and 2.5D RPGs, with export lanes for the studio's runtime
engine, Unreal Engine 5 and Godot 4. A Gemini Deep Research run was asked how one authored world can stay correct across
several engines for years. It covered:
- how to keep one world right in three engines, and how that fails;
- how to notice upstream engine change early;
- how to version and migrate formats over years;
- where knowledge of what each engine accepts should live;
- how to verify without a human in the loop;
- what we had not thought to ask.

The report is `[aggregator]` AI output. A harvest agent (an AI model) listed 24 of its claims and checked 15: 14 at the
source page and 1 through a search-result summary. 11 were confirmed and 4 partly; none was found wrong. The other 9 were
not checked, nor were most of the report's other figures. The page checks went through a fetch tool that returns a
model-written reading of the page, not the raw page, so treat them as strong but not verbatim. R&D then checked each
finding that bears on our design against World Forge's code at commit 023ff9a.

## Key points

- **Build it like a compiler pipeline, not a file exporter.** The report's pattern is sharded canonical source files with
  stable ids, a strict compiler that checks what every target accepts, lowering to per-engine bundles, and thin native
  importers in each engine. Writing another engine's scene files directly breaks when that engine changes its format:
  Tiled's Godot exporter kept writing the old TileMap node after Godot replaced it (issue 4106, still open).
- **Dumps catch syntax, a golden corpus catches behaviour.** Godot can dump its extension API and check it against a pinned
  file. The report calls that necessary but not enough: a scheduled run of a fixed set of worlds against engine betas
  catches behaviour changes a dump cannot.
- **An exit code of 0 is not a pass.** A community measurement shows headless Godot exiting 0 despite script errors and
  missing import caches. Parse a structured verdict and require that more than zero tests ran.
- **Readable name plus an unchanging unique id.** Larian's compiler ignores the readable prefix of a `Name_GUID` token and
  binds to the id, so renames do not break scripts. LDtk moved toward string ids because integer ids collide across
  branches.
- **Versioning over years:** stamp every file with a schema version per subsystem, write every value explicitly instead
  of omitting defaults, and migrate with a pure command-line step tested on archived worlds. Factorio applies JSON renames
  first, then scripted migrations, and records which ran in the save.
- **Parallel authors need small, canonical files.** One file per room, encounter or dialogue knot, with canonical JSON
  (RFC 8785) so diffs and hashes are stable.
- **Closed objects in schemas.** Open-object JSON Schema lets a misspelt key through to a strict engine.
- **Author narrative logic once** and compile it to one portable form that every engine interprets, rather than
  re-implementing it three times. A large build.
- **Licences matter early.** The report flags a licence on Yarn Spinner's Unreal plugin that bans AI training, and a
  disputed reading of Unreal's EULA against copyleft world data.
- **Honest limits.** Almost no studio ships one title across Godot, Unreal and a home engine, so the evidence comes from
  middleware and multi-platform pipelines; classic-JRPG internals rest on disassemblies and modding notes.

## Studio relevance

### What it contradicts in our design (read first)

| Finding | Our design today (checked at 023ff9a) | Decision |
|---|---|---|
| One compiler checks what every lane accepts before export | Each lane decides alone what to drop; the runtime-engine lane carries pack keys the engine's gate refuses, and a stage script strips them with a hand-copied list | Already the direction for the runtime-engine lane: the validate-only command will run the engine's own gate and intake. A single cross-lane compiler is not adopted now; it is a design question for when the Unreal and Godot lanes get work |
| Machine-extracted lockfiles per engine | Generated lists and a weekly engine bump are planned for the runtime engine only | Same principle, later lanes: Godot's extension-API dump when that lane is carded, Unreal's reflection data likewise. Not now |
| A scheduled canary plus a golden corpus | A weekly bump branch is planned; no golden world exists and no exported world has been played | Adopted for the next pipeline step: the bump branch also exports World Forge's own sample worlds and runs them through the engine's real gate and an intake dry run |
| Exit code 0 is not proof | The validate-only entry point runs World Forge's own checks and imports nothing from the engine | Adopted: the bump job and the validate-only command read the gate's structured result and require more than zero checks. The same rule goes into any later Godot or Unreal headless check |
| Readable prefix plus unique id | Stable ids with a retired-id list were already decided; the id's shape was open | For the ids work: a stable kind prefix plus a unique part. The display name stays a separate field. A slug of the name is not used, because it goes stale on rename. The id is generated once, when the object is created, and stored; it is never derived at export, and test fixtures use fixed ids (technical rulings, 2026-11-21) |
| Canonical, finer-grained files | One file per map is the first split | Partly adopted: deterministic serialization goes in the file-split work, with a stable key order and canonical JSON (RFC 8785) for World Forge's own file hashes; where the engine already defines a hash form, the engine's form wins (a technical ruling, 2026-11-21). Splitting finer than one file per map waits until merge conflicts are measured with agents working in parallel |
| Versioned migration tested on archived worlds | A versioned bundle migration path exists (`packages/editor/src/projects/bundle.ts:134-189`, re-read at 023ff9a). Its migration is an identity step ("No breaking migrations yet") | Partly in place. The ids work brings the first real migration with an archived-worlds corpus test (a world saved at each past schema version must migrate and validate), and explicit values for any field the engine refuses to guess |
| Closed-object schemas | World Forge's project validation has no unknown-key check: in `packages/schema/src`, the only test that flags an unknown key is in the presentation tests (searched at 023ff9a) | Contradicted. Closed-object checking goes with the file-split work: unknown keys are reported by name and kept on load, never silently dropped, and the editor refuses to write a misspelt key. It is measured on the sample and test worlds first, and matters most once agents write files (technical rulings, 2026-11-21) |
| A save-game schema now | Not part of World Forge | Out of scope: saves belong to the engine. The ids work states the guarantee saves need: ids are never reused, so a save naming a retired id can be detected |
| Author narrative logic once, compile to one form | World Forge authors dialogues but the engine drops them; who authors narrative facts was open | Recommended, not scheduled: author narrative facts in World Forge as data, export one engine-neutral compiled form, give the runtime engine the interpreter first. The candidate formats are licence-checked in the studio's registry before any design |
| Only the compiler writes worlds; engine-editor servers read-only | Not yet decided how agents write | Adopted as a rule for the command layer: agents write worlds only through World Forge's checked operations; Godot and Unreal editor servers stay read-only for world data |
| Cross-engine differential walkthroughs | No played world and no trace format | Later: first a single-engine state trace of an exported world, once Play from Here exists |

### Decisions and actionables
1. Decided 2026-11-21: the next pipeline step gets a golden corpus and structured verdicts; an exit code of 0 never counts as a pass.
2. Decided 2026-11-21: the ids work fixes the id's shape (kind prefix plus unique part), separate display names, a first real
   migration, and an archived-worlds test.
3. Decided 2026-11-21: the file-split work adds deterministic serialization and closed-object checking of project files.
4. Decided 2026-11-21: the command layer takes the single typed write path, with engine-editor servers read-only.
5. Recommended, and since done in part: licence checks of ink and Yarn Spinner are recorded in the licence registry
   before any narrative-format design; Unreal's terms are being checked. A further research run on story state informs
   the narrative-facts design, which is scheduled after ids, files and layers.

## Claims

Page checks below were read through an AI fetch tool's summary of the source URL (see Summary), not inspected in the raw page source, unless the line says otherwise.

- [verified] LDtk's unique-identifiers page says integer uids face future deprecation and developers should rely on string iids. The report's "forced LDtk 1.0+" wording is stronger than the page (via: LDtk docs, read by the harvest agent, 2026-11-21)
- [verified] Godot has `--dump-extension-api` writing `extension_api.json` and `--validate-extension-api <file>` comparing against it, flagging argument-count and hash changes; the page frames it as a contributor workflow (via: Godot docs, read by the harvest agent, 2026-11-21)
- [verified] Larian's compiler ignores the readable prefix before a GUID, provided the prefix contains no "-" (via: Larian Osiris Overview, read by the harvest agent, 2026-11-21)
- [verified] Unreal's guidance on asset versioning uses custom versions keyed by a GUID instead of one shared integer. The page text read did not show the CoreRedirects or resave part (via: Epic docs, read by the harvest agent, 2026-11-21)
- [verified] The Yarn Spinner for Unreal README states a licence that forbids training AI models, requires UE 5.4 or later, and calls itself pre-release (via: its GitHub README, read by the harvest agent, 2026-11-21)
- [verified] Tiled issue 4106: the Godot exporter still writes the deprecated TileMap node after Godot 4.3; opened 28 Nov 2024 (UTC), still open; pull request 4420 cross-references it (via: the GitHub issue API, read by R&D, 2026-11-21)
- [verified] A forum post (26 Oct 2026) lists cases where headless Godot exits 0 despite failures, and a reply extends them to 4.4.1 through 4.7.2. It is a community measurement (via: Godot forum post, read by the harvest agent, 2026-11-21)
- [verified] Factorio runs JSON rename migrations before scripted ones and records applied migrations in the save (via: Factorio migrations docs, read by the harvest agent, 2026-11-21)
- [verified] RFC 8785 sorts keys recursively by UTF-16 code units, uses ECMAScript number serialization and errors on NaN and Infinity (via: rfc-editor.org, read by the harvest agent, 2026-11-21)
- [verified] Buf's `WIRE_JSON` breaking-change category catches field renames that plain `WIRE` does not (via: Buf docs, read by the harvest agent, 2026-11-21)
- [verified] LDtk can save levels as separate files (via: LDtk JSON overview, read by the harvest agent, 2026-11-21)
- [verified] Godot has a `Logger` class registered through `OS.add_logger()` whose `_log_error` is called from non-main threads. Narrowed: the page gives no introducing version (via: Godot class docs, read by the harvest agent, 2026-11-21)
- [verified] Godot 4.4 uses per-file `.uid` sidecars, and a missing sidecar falls back to paths. Narrowed: the page says moving files outside the editor gives warnings (via: Godot article "UID Changes Coming to Godot 4.4", read by the harvest agent, 2026-11-21)
- [verified] The glTF 2.0 spec's coordinate convention is +Z forward and -X right (via: Khronos glTF 2.0 spec, first 100,000 of 826,706 characters, read by the harvest agent, 2026-11-21)
- [unverified] Unreal's EULA bars combining the engine with GPL, LGPL (unless dynamic) and CC-BY-SA, and bars public images containing the editor. Read only through search summaries (the page returned 403): the copyleft clause appears there, how far it reaches game assets is disputed, and the image claim was not found. A lawyer should read the live EULA before this is relied on
- [unverified] The Logger class arrived in Godot 4.5; the class page names no version
- [unverified] Moving files outside the editor silently desyncs `uid_cache.bin`; the Godot article says warnings and was not checked on the cache
- [unverified] A glTF loader must refuse an asset listing an unrecognised required extension. Not found in the part of the spec read; the page showed only a weaker "should not be loaded" wording for a similar rule
- [unverified] Godot 4.3 deprecated TileMap for TileMapLayer (GH-89179) and base64 byte arrays arrived as format 4 (GH-89186). The Tiled issue agrees on the deprecation; the Godot sources were not checked
- [unverified] Wasmtime non-LTS releases get two months of support, and two critical October 2026 advisories need relinking; not checked
- [unverified] XGrammar compile times and arXiv 2609.23742 findings on constrained decoding; not checked
- [unverified] Insomniac's 2017 web-tools postmortem, EasyRPG 0.6.0 save breakage and Factorio's silent blueprint-library upgrade; not checked
- [unverified] Unreal headless timings, `-TestExit` exit-code behaviour and the `ValidateAssets` and cook flags; not checked
- [unverified] Cobra Code's Paper2D limits, the Chrono Trigger walk-plane and sprite-priority details, and the Suikoden flag collisions; not checked
- [unverified] UE 5.8 as the last planned 5.x before UE6, UE 5.9 Preview auto-launching an MCP, and the Godot 4.8 beta 4 date; not checked

## Sources

- [aggregator] https://gemini.google.com/ — Gemini Deep Research (Gemini 4 Carbon), 2026-11-21: report "Architecting Long-Lived, Multi-Engine RPG Worlds for an Autonomous AI Studio" (seed 48, prompt sha256 prefix 5e628334)
- [primary] https://docs.godotengine.org/en/4.7/engine_details/development/handling_compatibility_breakages.html — Godot Engine contributors, Handling Compatibility Breakages (4.7)
- [primary] https://docs.godotengine.org/en/stable/classes/class_logger.html — Godot Engine, Logger class reference
- [primary] https://godotengine.org/article/uid-changes-coming-to-godot-4-4/ — Hugo Locurcio, Godot Engine, UID Changes Coming to Godot 4.4 (2025-01-15)
- [primary] https://dev.epicgames.com/documentation/unreal-engine/versioning-of-assets-and-packages-in-unreal-engine — Epic Games, Versioning of Assets and Packages
- [primary] https://www.unrealengine.com/eula/unreal — Epic Games, Unreal Engine EULA (the page returned 403; read only through search summaries)
- [primary] https://ldtk.io/docs/game-dev/json-overview/unique-identifiers/ — Deepnight Games, LDtk docs, unique identifiers
- [primary] https://ldtk.io/docs/game-dev/json-overview/ — Deepnight Games, LDtk docs, JSON overview
- [primary] https://docs.larian.com/Osiris_Overview — Larian Studios, Osiris Overview (Divinity Engine wiki; the old host redirects)
- [primary] https://lua-api.factorio.com/latest/auxiliary/migrations.html — Wube Software, Factorio migrations docs
- [primary] https://www.rfc-editor.org/info/rfc8785/ — Rundgren, Jordan and Erdtman, RFC 8785, JSON Canonicalization Scheme (2020)
- [primary] https://buf.build/docs/breaking/rules/ — Buf, breaking-change rules
- [primary] https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html — Khronos Group, glTF 2.0 specification
- [primary] https://github.com/YarnSpinnerTool/YarnSpinner-UnrealEngine — Secret Lab, YarnSpinner-UnrealEngine README
- [primary] https://github.com/mapeditor/tiled/issues/4106 — Tiled project, issue 4106 on the Godot exporter
- [aggregator] https://forum.godotengine.org/t/things-that-exit-0-in-godot-4-headless-even-though-they-failed-measured-reproducible/145990 — Jakub Hubner, "Things that exit 0 in Godot 4 headless" (2026-10-26), a community measurement
- [primary] https://github.com/mcp-tool-shop-org/world-forge — World Forge, the code checked (commit 023ff9a)
