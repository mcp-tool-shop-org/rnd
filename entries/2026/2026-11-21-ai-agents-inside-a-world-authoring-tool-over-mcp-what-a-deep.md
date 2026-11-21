---
id: 2026-11-21-ai-agents-inside-a-world-authoring-tool-over-mcp-what-a-deep
title: "AI agents inside a world-authoring tool, over MCP: what a Deep Research report found (seed 50)"
date: 2026-11-21
kind: finding
relevance: act
fields: [agent-tooling, studio-tooling]
tags: [world-forge, seed-50, harvest, mcp, agents]
---

## Summary

World Forge is the studio's browser editor for 2D and 2.5D RPG worlds. The studio plans a command layer that lets AI
agents (language models running on local hardware) change a world through a Model Context Protocol (MCP) server, while
one human director reviews. A Gemini Deep Research run was asked seven questions:
- what works and what fails when agents drive creative tools over MCP;
- how to expose capabilities safely, reviewably and reversibly;
- how a human reviews and controls a shared document;
- security;
- speed and local-model limits;
- evaluation;
- what we had not asked.

The report is `[aggregator]` AI output. A harvest agent (an AI model) listed 27 of its claims and checked 16: 14 at the
source page (through a fetch tool that returns a model-written reading of the page, not the raw page), 1 through a
search-result summary, and 1 page came back empty. 8 were confirmed, 7 partly and 1 not found; none was found wrong.
11 were not checked, and the report itself labels most of its VRAM and latency figures as estimates. The harvest agent
read the whole report but only the first part of its source list. R&D then decided each of the report's 16
contradiction rows, and the Publisher ruled on four world-forge technical calls (recorded below).

## Key points

- **Agents write into a draft, never the live world.** The report's pattern is a draft branch minted by the server, which
  the director reviews and merges. Ink & Switch's Upwelling work uses drafts layered onto a stack; its authors believe
  editing inside a draft is simpler than picking changes, which is their stated belief, not a measured result.
- **Typed, invertible domain commands only.** No raw script execution and no whole-document rewrite on the agent surface.
  A Godot MCP plugin's README says its script and method-call actions are outside the editor's undo.
- **Small fixed tool lists per role,** about 8 to 15 tools, static so the prompt prefix stays cacheable.
- **Tool annotations are hints,** not enforcement: the MCP specification says annotations are untrusted unless the
  server is trusted, so scope must be enforced by the server. The 2026-07-28 specification makes requests stateless.
- **Treat world text and community text as data, never instructions.** MCPTox measures tool poisoning through poisoned
  tool descriptions; in its Table 2 the attack success rate for three Qwen3 sizes rises with thinking mode (for example
  14.0 to 41.8). The report's further idea, thinking off when a local model reads untrusted text, is its own extension.
- **Undo that knows what depends on what.** Selective undo of an old agent change is only safe if no later edit touched
  the same items.
- **Relational placement.** Holodeck found that stating spatial relations for a solver to place beat model-written
  coordinates (0.706 against 0.364), on indoor 3D rooms with a search solver.
- **No click waits on a model.** Nielsen's response-time limits are 0.1 s, 1 s and 10 s; longer work runs in the
  background.
- **Evaluate before shipping write tools.** A fixed task set scored at zero retries, with scope precision, spatial and
  graph checks, and injection canaries.
- **Benchmarks show the gap.** GameDevBench has 333 Godot tasks; one open model scored 5.4% on it. Code4Scene reports that
  34.2% of edits that fully recovered the target still caused unintended changes elsewhere in the scene.

## Studio relevance

### What it contradicts in our design (read first)

| Finding | Our design today (checked at 023ff9a) | Decision |
|---|---|---|
| Agents write into a minted draft | The command layer is planned, not built: agent changes were to arrive as a staged proposal. World Forge has no operation list yet (not re-checked) | Consistent; take the mechanism. A draft is a handle the server mints, scoped to the ids and zones it may touch, with a time limit. Every write tool takes the handle, the director can open the draft while it is written, and merging applies its operations through the command layer's checks |
| Let the reviewer edit the draft before merging | Accept or reject per operation, in the visual diff | Both. Per-operation accept or reject stays, and editing inside the draft is added, since a draft is a branch and a person's edits are logged operations. The review-time measurement compares the two, because "editing beats picking" is unmeasured |
| A CRDT store with movable trees | One local server orders every operation; project copies serve undo today | Not adopted. A CRDT merges replicas that edit offline on different machines. Drafts plus the operation log give branches and undo. Kept: move and reparent operations refuse a move that would make a cycle. Revisit if co-editing across machines becomes a goal |
| Selective undo with a dependency test | Undo by operation is planned; no dependency case | Gap, goes into the operation log: each operation records the ids it read and wrote, and undoing an old operation refuses, naming the later operations that touched those ids |
| Typed commands only, no generic rewrite | The plan counts 31 `updateProject(updater)` side doors to fold into named operations (plan figure, not re-checked) | Agrees; made explicit. The agent surface has no generic rewrite tool, no script or engine-method call and no file write. An equality test (every editor edit equals its operation) proves the side doors are gone |
| A sandboxed script tool for multi-step layouts | Batches with dry run and all-or-nothing apply; no script tool | Not now. A sandbox for model-written code is a large attack surface, as the report's own security section warns, and the code-mode results were not checked. If ever built, it emits only logged operations, with no OS, file or network access, and it waits for the evaluation set |
| Relational placement | Operations take explicit positions | Additive, later. Coordinate operations stay; a relational form (`near`, `inside`, `facing` an id) resolved by a deterministic placer is a later family, measured on our own 2.5D maps first |
| 8 to 15 tools per role | The store declares 135 named actions (plan figure, not re-checked) | Adopted: the MCP server serves fixed, small manifests per role (for example layout, quest wiring, read-only review). The editor keeps all of its operations. Tool names and descriptions are words a model reads, so the Director approves their wording when the tool server is carded (decided 2026-11-21) |
| Validate before mutate | Checks run after the fact on the whole world | Agrees. Checks before apply, with named refusals. Reachability checks (a path to every exit and quest giver, quests that can still be finished) join the validator as to-dos. The engine's gate and intake dry run join the merge checks only after the pipeline's next step, because the engine refuses the runtime-engine export today |
| Story-wise conflicts survive clean merges | One file per map prevents text collisions | Adopted: a draft's scope works as a soft lease. A second draft that would touch a leased id or flag gets a warning when it is created, and whole-world checks run after every merge |
| World text is untrusted input | Hidden instructions in world text, permission scope and runaway edits were listed as open | Adopted; see the security rules below |
| Blast-radius caps and an audit log | Nothing applied silently; which operations may apply directly was open | Decided 2026-11-21: limits are an adjustable feature, not fixed numbers; see the decisions below |
| A server-side localisation lock | Not present | Later, in the narrative-facts work with per-line ids: a line marked frozen for localisation refuses text edits until unfrozen |
| Direct manipulation must never wait on a model | No latency target for agent calls | Adopted as a rule |
| An evaluation task set | No evaluation step in the order of work | Adopted, before any write tool ships |
| One engine-neutral form, compiled per lane | Runtime-engine export carries keys the engine refuses | Already decided in seed 48's work; nothing new |

### Decisions and actionables
1. Decided 2026-11-21: agents write only into drafts, per-operation accept or reject plus in-draft editing, merged through checked operations.
2. Decided 2026-11-21: per-operation read and write sets give undo that knows dependencies.
3. Decided 2026-11-21: the agent surface has no side doors, fixed per-role manifests, and server-enforced scope with annotations as hints only. It targets the MCP 2026-07-28 specification.
4. Decided 2026-11-21, security:
   - world, lore and community text are data, never instructions;
   - a pass with no tools turns untrusted text into structured facts, and agents with write tools never see raw community text;
   - tool definitions are pinned by hash;
   - limits are an adjustable feature, not fixed numbers (decided 2026-11-21): presets run from careful to open, and the default asks before deleting a place or anything else refers to, and before a draft changes more than a moderate number of things, but never blocks ordinary single edits; each draft can be allowed more or less, and per-user defaults live in the settings (the report's "50 entities" is an example, not evidence);
   - only a person can change a limit, never an agent, and the server enforces this; every limit change is logged; the evaluation set includes an agent that tries to exceed its limit and one that tries to change a limit, and both must be refused;
   - each agent role gets one draft and its own manifest;
   - the operation log is append-only and records agent, model, quantisation, adapter, draft, tool and an argument hash;
   - "thinking off for untrusted text" is tested with injection canaries, not adopted as a rule;
   - the design gets one targeted check by another model family once it is final, because security is the specialised case.
5. Decided 2026-11-21: no click waits on a model; agent work runs in the background into its draft with a cancel; inline commands target 1 s, measured on the rig with the chosen local model.
6. Decided 2026-11-21: an evaluation set comes before any write tool ships: about 20 tasks to start, growing toward 50 to 100, scored at zero retries on schema validity and invented-tool rate, draft-scope precision (any change outside scope fails the run), deterministic spatial and graph checks, export checks after the pipeline's next step, and injection canaries. It runs on every change of model, quantisation, prompt or manifest.

Four technical rulings, 2026-11-21, all yes:
- **No CRDT store.** One local server orders every operation. Revisit only if many people need to edit offline at once.
- **A draft's scope as a soft lease, plus a stale-read guard.** Keep the warning when a draft opens over a leased id or flag, and the whole-world checks after every merge. New: at merge, any operation whose read set another merge has written since the draft opened is refused by name (for example `STALE_READ`), naming the merges that touched those ids. Its author re-runs that operation, and the rest of the draft can still merge. Test: two drafts read the same id, the first merges, and the second's stale operation is refused.
- **Relational placement: later, after the tool surface exists.** Measure it on our own 2.5D maps first, since Holodeck's result is from indoor 3D rooms.
- **No script sandbox for now.** The attack surface is too large and the code-mode results were not checked.

Decided 2026-11-21 by the Director: the limits are the adjustable feature above; he approves the tool wording when the
tool server is carded; and his corrections to agent drafts are recorded locally in a form usable for later role-adapter
training (the draft operation, the correction and the outcome; publishing that data is not covered). Also carried into
the narrative-facts work: a "who knows what" continuity critic and the localisation lock.

## Claims

- [verified] Godot's `EditorUndoRedoManager` `create_action` accepts a custom context that overrides the first object's history. Narrowed: the page names `EditorPlugin.get_undo_redo()` as the intended route and shows `EditorInterface.get_editor_undo_redo()` only in an example (via: Godot docs, read by the harvest agent, 2026-11-21)
- [verified] The jp10b godot-mcp-plugin README says its script and method-call actions are outside undo, while other scene edits go through the editor's undo history (via: the GitHub README, read by the harvest agent, 2026-11-21)
- [verified] The MCP 2026-07-28 specification overview describes stateless requests with per-request capability negotiation, and lists Tasks, Skills over MCP and Apps as extensions. Not found on that page: JSON Schema 2020-12, cache hints, and the deprecation of Roots, Sampling and Logging (via: MCP specification overview, read by the harvest agent, 2026-11-21)
- [verified] MCP tool annotations are hints: the blog lists four with defaults, and the specification says they are untrusted unless the server is trusted (via: the MCP blog post and specification overview, read by the harvest agent, 2026-11-21)
- [verified] MCPTox Table 2 reports tool-poisoning success rising with thinking for Qwen3 8B, 14B and 32B (14.0 to 41.8, 5.1 to 27.1 and 23.7 to 58.5), across 1,348 cases, 353 tools, 45 servers and 20 models. The report's explanation of why is its own gloss (via: arXiv:2508.14925, read by the harvest agent, 2026-11-21)
- [verified] Holodeck's layouts from relational constraints plus a search solver score 0.706 against 0.364 for model-written coordinates. Indoor household rooms, and the contrast joins the constraint form with the solver (via: arXiv:2312.09067 Table 1, read by the harvest agent, 2026-11-21)
- [verified] Nielsen's response-time limits are 0.1 s, 1 s and 10 s (via: Nielsen Norman Group, read by the harvest agent, 2026-11-21)
- [unverified] CVE-2025-6514 is an OS command injection in mcp-remote through `authorization_endpoint`, CVSS 9.6, CWE-78, fixed in 0.1.16. A search-result summary citing the GitHub advisory agreed; the NVD page itself returned nothing
- [verified] Epic documents an "Unreal MCP in Unreal Editor" feature, in UE 5.9 docs, described as experimental and embedding an MCP server in the editor process. The page does not mention undo or transactions (via: Epic docs, read by the harvest agent, 2026-11-21)
- [verified] GameDevBench has 333 Godot tasks, and Qwen3.5-397B-A17B scored 5.4% without multimodal feedback (via: arXiv:2602.11103, first 100,000 of 114,736 characters, read by the harvest agent, 2026-11-21)
- [verified] Code4Scene reports that 34.2% of edits that fully recovered the target still caused unintended changes elsewhere in the scene. Narrowed: the page gives 170 cases, not the report's 190 (via: arXiv:2609.36777 abstract, read by the harvest agent, 2026-11-21)
- [verified] Upwelling describes layers as semi-private drafts merged onto a stack. Narrowed: that editing the draft beats cherry-picking is the authors' stated belief, and per-change rejection was designed but not implemented (via: Ink & Switch, read by the harvest agent, 2026-11-21)
- [verified] Google's code review case study covers 9 million reviewed changes (via: ICSE-SEIP 2018 abstract, read by the harvest agent, 2026-11-21)
- [verified] SimpleTool reports 61.2 ms median latency and up to 9.6 times faster function calling. Narrowed: the abstract says consumer-grade GPU and a 4B-scale model, not an RTX 4090 (via: arXiv:2603.00030 abstract, read by the harvest agent, 2026-11-21)
- [verified] SceneAgent (13 Nov 2026) is a portable multi-backend scene generation framework evaluated on 69 prompts, with human preference of 78.2 to 89.4% against five baselines (via: arXiv:2611.17821 abstract, read by the harvest agent, 2026-11-21)
- [unverified] Godot plugins reach the undo manager through `EditorInterface.get_editor_undo_redo()` with paired do and undo calls; the page showed the route only in an example and no full paired example
- [unverified] GameDevBench's best score is 70.6% with category scores 51.4, 38.4, 33.0 and 32.0. Not found: the page shows 53.8% for the best result, the four values match but the category labels differ
- [unverified] SceneAgent scored 83.3% overall human preference; not on the abstract
- [unverified] Google code review has a median change of 24 lines and turnaround under 4 hours; only the abstract was read, which does not give these
- [unverified] Unreal's undo buffer cannot persist across restarts, with FTransaction and FScopedTransaction behaviour. Not found: the page fetched came back empty
- [unverified] Kleppmann et al. 2021 on a verified acyclic replicated tree move (PDF unreadable), and the Loro API claims (the page returned 403); not checked
- [unverified] NarrativeSteward's inspection-ease result, the CHI 2026 co-creation study (N 486), Maloyan and Namiot's attack rates, the cross-framework tool-poisoning measurement, the quantisation papers, RAG-MCP's 43.13% against 13.62%, CaMeL's 77% against 84%, the 39% inference-engine variance, and the VRAM and decode-speed table; none was checked, and the report labels most of the hardware figures as estimates

## Sources

- [aggregator] https://gemini.google.com/ — Gemini Deep Research (Gemini 4 Carbon), 2026-11-21: report "Architecting a Multi-Agent RPG World Authoring Tool Over MCP on Local Hardware" (seed 50, prompt sha256 prefix 189fb4bd)
- [primary] https://modelcontextprotocol.io/specification/2026-07-28 — Model Context Protocol maintainers, Specification (2026-07-28)
- [primary] https://blog.modelcontextprotocol.io/posts/2026-03-16-tool-annotations/ — MCP project blog, Tool annotations (2026)
- [primary] https://arxiv.org/abs/2508.14925 — Wang et al., MCPTox: A Benchmark for Tool Poisoning Attack on Real-World MCP Servers (2025)
- [primary] https://arxiv.org/abs/2602.11103 — Chi et al., GameDevBench: Evaluating Agentic Capabilities Through Game Development (2026)
- [primary] https://arxiv.org/abs/2609.36777 — Ye et al., Code4Scene: Benchmarking Coding Agents for Constructing and Editing 3D Scenes (2026)
- [primary] https://arxiv.org/abs/2312.09067 — Yang et al., Holodeck: Language Guided Generation of 3D Embodied AI Environments (CVPR 2024)
- [primary] https://arxiv.org/abs/2611.17821 — Li et al., SceneAgent: A Multi-Agent Framework for Portable Game Scene Generation (2026)
- [primary] https://arxiv.org/abs/2603.00030 — Shi et al., SimpleTool: Parallel Decoding for Real-Time LLM Function Calling (2026)
- [primary] https://www.inkandswitch.com/upwelling/ — McKelvey et al. (Ink & Switch), Upwelling: Combining real-time collaboration with version control for writers (2023)
- [primary] https://research.google/pubs/modern-code-review-a-case-study-at-google/ — Sadowski et al., Modern Code Review: A Case Study at Google (ICSE-SEIP 2018; abstract read)
- [primary] https://dev.epicgames.com/documentation/unreal-engine/unreal-mcp-in-unreal-editor — Epic Games, Unreal MCP in Unreal Editor (UE 5.9 docs)
- [primary] https://docs.godotengine.org/en/stable/classes/class_editorundoredomanager.html — Godot docs, EditorUndoRedoManager
- [primary] https://github.com/jp10b/godot-mcp-plugin — jp10b, godot-mcp-plugin README
- [primary] https://www.nngroup.com/articles/response-times-3-important-limits/ — Nielsen Norman Group, Response Time Limits
- [primary] https://github.com/mcp-tool-shop-org/world-forge — World Forge, the code checked (commit 023ff9a)
