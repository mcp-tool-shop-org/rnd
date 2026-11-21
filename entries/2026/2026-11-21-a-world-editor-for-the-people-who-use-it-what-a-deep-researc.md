---
id: 2026-11-21-a-world-editor-for-the-people-who-use-it-what-a-deep-researc
title: "A world editor for the people who use it: what a Deep Research report found (seed 49)"
date: 2026-11-21
kind: finding
relevance: act
fields: [game-design, studio-tooling]
tags: [world-forge, world-authoring, seed-49, harvest]
---

## Summary

World Forge is the studio's browser editor for 2D and 2.5D RPG worlds. A Gemini Deep Research run was asked what keeps the
people who use such an editor fast and in flow, which patterns were tried and dropped, how to report errors without
breaking flow, how to help authors who return after weeks away, how to measure improvement when only a handful of people
use the tool, and what we had not thought to ask. The report names four bottlenecks:
- direct manipulation that answers in about a tenth of a second, and jumps into play in under a second;
- editing in place and from the keyboard, with no chains of modal dialogs;
- error feedback that does not block, so an unfinished world can still run;
- automatic "pick up where you left off" support.

The report is `[aggregator]` AI output. A harvest agent (an AI model) listed 16 of its claims and checked all 16: 3 by
recomputing locally, 6 at the source page (through a fetch tool that returns a model-written reading of the page, not the
raw page) and 7 only through search-result summaries (three PDFs came back unreadable); one of the 6 was checked partly
at its page and partly through a summary. 8 were confirmed, 6 partly and 2
not found; none was found wrong. Many other claims, mostly 2026-dated items, were not checked. The report itself says no
long-running study of multi-hour flow in a combined world-and-story editor exists, and that its resumption and
agent-oversight claims are extrapolated from software engineering.

## Key points

- **Unfinished work is not an error.** The report wants a calm, tiered pipeline: no modal popups, a visible "hole" marker
  for unassigned targets, a quiet counter, and a separate export gate that splits failures from warnings. A false green at
  export is the worst case.
- **A "why didn't this happen" inspector.** Click an absent character or hidden choice and see the evaluated conditions.
  The Whyline research supports this: its project page reports 40% more of the task completed and debugging about 7.8
  times faster.
- **Returning authors.** A "welcome back" view: what changed since the last session, open to-dos, an optional note left at
  quit. Parnin and DeLine (2010) report that automatic cues gave twice the success of note-taking alone in resuming a
  programming task.
- **Agent changes arrive as reviewable proposals,** with per-object provenance (who made or changed this, and whether it
  was reviewed).
- **Names and ids are two things.** A readable name plus an immutable id, so renames never break references.
- **Property sheets with reference jumping,** including a list of everything that points at an item.
- **Measure differently with few authors.** Group tests are nearly useless at four people: the report computes about a
  one-in-five chance of detecting even a large effect (20.5% power, confirmed by recomputation). It recommends predictive
  modelling, repeated single-person experiments and passive logging, and warns against trusting self-reported speed: in a
  2025 trial, experienced developers believed AI made them 20% faster and were measured 19% slower.
- **Keystroke-level modelling** puts an in-place, hotkey-driven placement at about 8.5 s against about 25 s through nested
  pickers. The arithmetic checks out, but the step lists are the report's own assumptions, not measurements.
- **A warning, not a fact:** the report says Godot generates resource ids non-deterministically across machines. The cited
  page does not say that (see Claims), so the report's exporter advice built on it is unsupported.

## Studio relevance

### What it contradicts in our design (read first)

| Finding | Our design today (checked at 023ff9a) | Decision |
|---|---|---|
| Unfinished work is not an error | A new world opens red: `packages/schema/src/validate.ts:489-490` pushes "At least one spawn point is required" into the error list (re-read at 023ff9a). A planned fix already makes the export dialog's readiness label truthful (a walkthrough saw "Ready" for a world the engine refuses; not re-checked) | Contradicted, in part. Proposed addendum to the readiness fix: a new, unfinished world shows its gaps as to-dos, not errors. Red is kept for what the engine or exporter would refuse. Each check is named by when it applies: on edit, on save or on export |
| A "why didn't this happen" inspector | Not planned | Gap. Decided 2026-11-21: it joins Play from Here, second in the order of new editor features, shown where the engine can explain the outcome. It needs Play from Here's rule evaluation, and so the engine sidecar |
| Returning-author summary | Only an autosave-history fix is planned | Gap, and the central scenario. A summary of what changed since the last session (from the visual diff), the open to-dos and an optional note left at quit is added, fifth in the order of new editor features. Task-scoped saved contexts and map pins are not proposed: their evidence was not checked |
| Proposal layers and per-object provenance | A visual diff on the map is planned; no provenance tags | Belongs to the agents track. Per-object provenance (a person or which agent; reviewed or not) comes out of the command layer's operation log and is folded in with seed 50 |
| Readable name plus immutable id | Default friendly names are planned, and stable ids are decided | Consistent. The ids work keeps display name and id as separate fields: names editable, ids never changed and never reused. The report's Godot id claim is not cited (not found) |
| Property sheets with "used by" | Only the asset panel computes unreferenced items (`packages/editor/src/panels/AssetPanel.tsx:37-63`, re-read at 023ff9a) | Additive. The property-sheet work gets a "used by" list of incoming references. The same reference index should feed the planned delete question, so it can name what would be stranded |
| Blocking dialogs only for irreversible destruction | Asking before a delete strands content is planned | No change: stranding content is that case. A plain delete stays undoable and asks nothing |
| Controls beside the selected object | Details need Enter or double-click | No change now. The evidence is a book excerpt that was not read; the real defect is fixed by "selection shows its properties", and panel placement becomes a question for measurement |
| Sub-second jump into any world state | Play from Here is planned | Decided 2026-11-21, the order of new editor features: the visual diff; Play from Here, with the inspector where the engine can explain the outcome; keyboard placement and a command palette; property sheets with "used by"; the returning-author summary. The report ranks edit-to-play delay first; the diff goes first because agent review, provenance and the returning-author summary all build on it |
| Few-author measurement | The measurement plan used five-user rounds plus time to review, undo rate and fixes after export | Changes it. Five-user rounds stay only for first-run onboarding. Main measures: local logging that is never sent (undo bursts, time to first real edit after an absence, time to review a change) and alternating-treatment comparisons with the Director as the expert author (decided 2026-11-21, with the session count and length set before it starts), read with a nonoverlap statistic. Self-reported speed is not used |
| One file per map, engine files disposable | One file per map is a pending direction pick | Supports the pick. For the Godot lane, read Godot's own UID documentation before designing id handling |
| Keyboard-first placement | Place-at-cursor and a command palette are planned | Agrees; stays in the second list. Measure our own placement cost before ranking by the report's figures |

### Decisions and actionables
1. Decided 2026-11-21: propose the "gaps are to-dos" addendum to the truthful-readiness fix.
2. Decided 2026-11-21: the order of new editor features is final: the visual diff; Play from Here, with the inspector where
   the engine can explain the outcome; keyboard placement and a command palette; property sheets with "used by"; the
   returning-author summary.
3. Decided 2026-11-21: the measurement plan is rewritten around local logging and single-author comparisons before it is
   carded, with the Director as the expert author.
4. Decided 2026-11-21: the ids work keeps display name and id separate, and the delete question and "used by" list share one reference index.

## Claims

- [verified] The keystroke-level model arithmetic in the report is right: 7M+12P+13BB = 25.25 s, 3M+1P+1H+15K = 8.55 s, a ratio of 2.95, about 33.4 minutes over 120 placements. The operator values and the step lists themselves are not checked (via: local recomputation by the harvest agent, 2026-11-21)
- [verified] A paired t-test with N = 4, dz = 0.8, alpha 0.05 has about 20.5% power, and dz = 2.13 gives 80% (via: 200,000-trial simulation by the harvest agent, 2026-11-21)
- [verified] The Nielsen-Landauer arithmetic gives 77.3% and 34.4%, and a Tau standard error of 0.298 for 8 plus 8 sessions. The report's p values and the model itself were not read (via: local recomputation by the harvest agent, 2026-11-21)
- [verified] The METR trial: 16 experienced developers, 246 issues, forecast 24% faster, believed 20% faster, measured 19% slower (via: arXiv:2507.09089 abstract, read by the harvest agent, 2026-11-21)
- [verified] The Whyline project page reports 40% more of the task completed and average debugging time cut by a factor of about 7.8. The base counts are not given (via: the Whyline project page, read by the harvest agent, 2026-11-21)
- [verified] Parnin and DeLine 2010: automatic cues gave twice the success rate of note-taking alone for resuming interrupted programming tasks. No sample sizes in the abstract (via: Microsoft Research abstract, read by the harvest agent, 2026-11-21)
- [verified] Unreal's Paper 2D tilemaps are labelled experimental with a caution about shipping (via: Epic docs, read by the harvest agent, 2026-11-21)
- [unverified] Valve's wiki warns that the Portal 2 Puzzle Maker's export gives hard-to-edit logic and unoptimised brushwork. A search-result summary of the wiki agreed (the page returned 403); the 1,750-entity figure comes from community pages, not Valve's
- [unverified] A Tiled terrain set can hold up to 254 terrains. A search-result summary of the manual agreed; the page was not read. The cliff limitation is community advice, not found in the manual's summary
- [verified] LDtk's auto-layers page covers the Shift+R raw integer grid view and layers that read from one IntGrid (via: LDtk docs auto-layers page, read by the harvest agent, 2026-11-21)
- [unverified] LDtk saves one `.ldtkl` file per level to avoid merge conflicts. A search-result summary supports the separate files; the merge-conflict motive was not found
- [unverified] Liu and Heer 2014: 500 ms of added delay reduced exploratory actions, and a third of users did not notice. The 500 ms effect is repeated by citing papers; the exact conditions and the one-third figure were not found (PDF unreadable)
- [unverified] Robertson and colleagues 2004: negotiated cues beat immediate popups on comprehension and bug fixing, and a 2006 follow-up found high-intensity negotiated cues hurt as much. The direction is supported by a search summary; the numbers and the follow-up's result were not read
- [unverified] Barik 2017: 55 developers, 13 to 25% of fixations on error messages, 53 of 55 chased a wrong fix. Summaries say 56 participants and share of time, not fixations; the p value, R-squared and 53-of-55 were not found
- [unverified] Parnin and Rugaber: about 10,000 sessions, 85 developers, in about 30% of sessions more than 30 minutes before the first edit. A summary supports 10% resuming within a minute; the 30% figure was not found
- [unverified] Godot 4 generates resource ids non-deterministically across machines and branches, causing merge conflicts. Not found: the cited article covers `.uid` sidecars for scripts and shaders and says a central id database would have frequent merge conflicts, so per-file sidecars were chosen
- [unverified] Code Bubbles cut task completion time by 33.2%. The exact figure was not found; a summary supports improved understanding and less navigation
- [unverified] Mark and colleagues' 23 minutes 15 s, Kersten and Murphy's 84.17%, Akers and colleagues' flaw rate, the 2026 CD Projekt modder statement, the Witcher 3 and Disco Elysium items, the Chrono Trigger and Suikoden II interview claims, the book-excerpt claim about eye movement while jumping, and the 28% false-edit figure; none was checked

## Sources

- [aggregator] https://gemini.google.com/ — Gemini Deep Research (Gemini 4 Carbon), 2026-11-21: report "Designing a High-Flow World and Level Authoring Editor for 2D and 2.5D Role-Playing Games" (seed 49, prompt sha256 prefix 3223d3f6)
- [primary] https://arxiv.org/abs/2507.09089 — Becker, Rush, Barnes, Rein (METR), Measuring the Impact of Early-2025 AI on Experienced Open-Source Developer Productivity (2025)
- [primary] https://www.microsoft.com/en-us/research/publication/evaluating-cues-for-resuming-interrupted-programming-tasks/ — Parnin and DeLine, Evaluating Cues for Resuming Interrupted Programming Tasks (CHI 2010)
- [primary] https://www.cs.cmu.edu/~NatProg/whyline.html — Ko and Myers, the Whyline (project page)
- [primary] https://godotengine.org/article/uid-changes-coming-to-godot-4-4/ — Godot Engine, UID Changes Coming to Godot 4.4 (2025)
- [primary] https://dev.epicgames.com/documentation/unreal-engine/paper-2d-tile-sets-and-tile-maps-in-unreal-engine — Epic Games, Paper 2D Tile Sets and Tile Maps
- [primary] https://developer.valvesoftware.com/wiki/Portal_2_Puzzle_Maker — Valve, Portal 2 Puzzle Maker (developer wiki; read only through a search summary)
- [primary] https://ldtk.io/docs/general/auto-layers/ — Sébastien Bénard, LDtk documentation, auto-layers
- [primary] https://doc.mapeditor.org/en/stable/manual/automapping/ — Tiled manual, Using Terrains and Automapping (read only through a search summary)
- [primary] https://github.com/mcp-tool-shop-org/world-forge — World Forge, the code checked (commit 023ff9a)
