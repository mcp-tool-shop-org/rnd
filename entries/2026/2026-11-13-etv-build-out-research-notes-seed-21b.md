---
id: 2026-11-13-etv-build-out-research-notes-seed-21b
title: Escape the Valley build-out: what a Deep Research run's notes said, and what held (seed 21b)
date: 2026-11-13
kind: finding
relevance: act
fields: [game-design, narrator]
tags: [escape-the-valley, replayability, ai-narration, accessibility, seed-21b, harvest]
---

## Summary

A Gemini Deep Research run on the Escape the Valley (ETV) build-out (replayability, event structure, AI narration,
balance testing, terminal-game expectations, risks) never produced a final report; R&D salvaged its research notes,
about 6,000 words of unreferenced paragraphs between source lists. Everything is `[aggregator]`. The notes were
strong on repetition maths, AI disclosure, accessibility and random-number design, and said nothing useful on run
length, save systems or onboarding. R&D checked three items at source and one number by recomputation; the rest is
Gemini's assertion, tagged by how well it is supported.

## Key points

- **Decoupling format from content may help prose.** Strict schema decoding in one step is reported to cost quality,
  and a free-prose-then-validator pipeline is suggested. The named paper's abstract confirms a decline in reasoning
  under format restrictions, larger when stricter; the notes' "up to 27%" is not on the abstract.
- **Disclosure of generative AI is penalised when it looks like a cost-cutting shortcut** and tolerated when it is
  part of gameplay. A Steam review analysis (508,192 reviews) confirms lower recommendation rates for disclosing
  games than for procedurally generated ones; the notes' "18-19 points" is not on the abstract.
- **Full-screen grid interfaces that redraw the screen are hostile to screen readers.** An accessibility write-up
  confirms this for redraw-the-grid terminal apps against a sequential line mode, though it says some single-column
  interfaces work.
- **The fallback line table repeats fast.** The notes claim an effective pool of about 22.6 of 88 lines and a near
  certain repeat in a 25-event run with the narrator off. R&D's uniform check gives 97.7% for any repeat, so the
  100% depends on weights it could not reproduce.
- **Plausible but unchecked design claims:** per-subsystem random-number streams so adding an event does not shift
  unrelated draws; avoiding raw floating point in simulation; events whose choices share one outcome shape make
  decisions trivial; under standard caravan formulas a slower pace is dominated; death-spiral valves that keep
  defeat from killing the run; a four-turn category cooldown brings in-biome repetition under 16%.
- **Not answered:** the research plan's own "unasked questions" (pre-generating narration, branching route graph,
  relationships between party members, modding, provenance hygiene).

## Studio relevance

### What it contradicts in our design (read first)

| # | Finding | Our design or plan today | Decision needed |
|---|---|---|---|
| 1 | Decouple generation from format (strength: source named; magnitude not confirmed) | The narrator sends a full schema | Not a reversal (our lines are short prose). Add one harness arm, schema against plain-text-plus-checker; keep the schema only if the fallback rate is no worse |
| 2 | The fallback table repeats quickly (notes only; 97.7% reproduced for uniform draws) | A fixed 88-line approved table is the fallback | Measure repeats on the real per-choice mapping; decide on an anti-repeat buffer and whether more lines are needed |
| 3 | Disclosed generative AI costs recommendations unless integrated into gameplay | Up-front disclosure on title and credits, wording approved | None. Keep disclosure; do not quote the 18-19 figure |
| 4 | Redraw-the-grid interfaces hurt screen readers (confirmed in part) | The terminal UI is a gate for 2.0; a line mode exists | Keep the line mode as a supported, tested accessible mode after the TUI lands; honour NO_COLOR; no colour-only meaning |
| 5 | Isolated RNG streams per subsystem (notes only) | The next ruleset changes event draws; per-subsystem streams not stated | Check the engine; if there is one stream, decide whether that switch is the moment to introduce keyed streams |
| 6 | Avoid raw floating point in simulation (notes only) | New traits use fractions and percentages | Confirm integer arithmetic with stated rounding (cheap audit) |
| 7 | Isomorphic choices make decisions trivial (notes only) | A content lint covers hint match, near duplicates and reachability | A possible lint on shared choice-effect shape; define it before building |
| 8 | A slower pace is dominated (Gemini's modelling, formulas not shown) | Pace mechanics not in the plan | Check in the simulator that no pace setting is dominated |
| 9 | Death-spiral valves that last (notes only) | A zero-food emergency phase is queued after the food clock; one Lucky save per run | Agrees with the plan; adds "defeat that does not kill" as a candidate event type |
| 10 | A four-turn category cooldown (Gemini's simulation) | A four-event cooldown already exists | No change |

These notes say nothing on difficulty targets, the model shortlist or trait design, so they neither confirm nor
contradict the seed 22 harvest.

### Decisions taken

None as rulings: the harvest ends in an actionable list for the build plan, to be taken up item by item:
the plain-text-versus-schema arm; the fallback repeat measurement and anti-repeat decision; line mode kept as a
permanent accessible mode with NO_COLOR; an engine audit for RNG streams and integer arithmetic before the ruleset
switch merges; a pace-dominance check. Optional: the choice-topology lint, after it is defined.

### Do not use

The "18-19 point" and "27%" figures, the "100% repeat" and "22.6 effective lines" as measured facts, and any model,
version or crate number from the notes' source titles (they are stale next to the seed 22 harvest).

relevance: `act` (five small build items). Later measurements of the narrator are in `experiments/etv-narrator`.

## Claims

- [verified] The Steam review analysis (arXiv:2608.11539, 508,192 reviews) reports lower recommendation rates for disclosing games than for procedurally generated ones; the notes' "18-19 points" is not on the abstract page (via: the abstract read at source, R&D, 2026-11-13)
- [verified] Tam et al. (arXiv:2408.02442) report a significant decline in reasoning under format restrictions, larger when stricter, with no percentage on the abstract, so "up to 27%" is not confirmed (via: the abstract read at source, R&D, 2026-11-13)
- [verified] An accessibility article (xogium.me, 2026-01-05) says full-screen redraw terminal apps break screen readers and a sequential mode is better, while noting some single-column interfaces work (via: the article read at source, R&D, 2026-11-13)
- [verified] Uniform draws of 88 lines over 25 draws give a 97.7% chance of at least one repeat (via: recomputation, R&D, 2026-11-13)
- [unverified] The fallback table's effective pool is about 22.6 of 88 lines and a 25-event narrator-off run repeats a line with about 100% probability (Gemini's own simulation; the code and weights were not shown)
- [unverified] Per-subsystem RNG streams, avoiding floating point, isomorphic-choice triviality, pace dominance, death-spiral valves and a four-turn cooldown below 16% repetition (the notes; the cited design write-ups and crate pages were not opened)
- [unverified] Constrained decoding causes repetitive phrasing in small models and a two-stage pipeline keeps prose natural (partly source-named; the repetition claim is the notes' own)

## Sources

- [aggregator] https://gemini.google.com/app/eb83be42e151f56f — Gemini Deep Research notes, "Escape the Valley build-out" (seed 21b, read 2026-11-13; no final report was produced; account-private chat)
- [primary] https://arxiv.org/abs/2608.11539 — Bazzaz and Cooper, player perceptions of generative AI in games, a Steam review analysis
- [primary] https://arxiv.org/abs/2408.02442 — Tam et al., "Let Me Speak Freely?"
- [secondary] https://xogium.me/the-text-mode-lie-why-modern-tuis-are-a-nightmare-for-accessibility — xogium.me, 2026-01-05
