---
id: 2026-11-13-small-model-narrator-seed-23
title: Cutting a small local narrator's fallback rate under hard rules: what the report said and what was ruled (seed 23)
date: 2026-11-13
kind: finding
relevance: act
fields: [narrator, local-models]
tags: [escape-the-valley, narrator, fallback-rate, constrained-output, seed-23, harvest]
---

## Summary

After the first measurement session showed a small local model's lines rejected about six times in ten by the
Escape the Valley rule checker, R&D asked a Gemini Deep Research run how to cut that rate. The question set was nine
questions and the prompt led lightly, with none of the planned fixes named; the game's facts file was attached.
The report is `[aggregator]` throughout. Its citations carry 2026 arXiv numbers R&D could not have known and none
was opened, so any paper must be checked at source before a decision or a public line rests on it. R&D checked its
claims against the game's code (at the commit after the first fix) and against session 1's reports. The useful part
is nine contradictions with the studio's own method, six of which the Publisher agreed as written.

## Key points

- **The arm comparison was inside the noise.** Eighteen calls share each turn, so 360 turns resolve about 2.8 to
  3.6 points paired. Cited against plain differed by 2.45 points and text against plain by 0.6.
- **The checker stops at the first broken rule,** so later rules are undercounted: 42% of lines that pass the length
  rule fail a later one. The first fix's preview showed it (quantifier rejects 174 rose to 417 once length was
  fixed).
- **Negative rules prime the forbidden words in small models.** The shared rules are mostly negatives.
- **A retry at a fixed seed and low temperature returns the same line.** The model card's suggested sampling
  (0.7 / top-p 0.8 / top-k 20) had not been read.
- **Quantisation is not the cause** (one paper: no instruction-following loss at Q4_K_M); model-side repair of a
  failed line does not work at this size, while deterministic trimming of extra sentences in code does.
- **Wrong or filler:** the report explained a gap in the rule table by an unlisted rule; the gap was R&D's own
  omission of the draft-animal rule from the facts file. The report's fallback forecasts (18-25%, then 8-15%, then
  3-7%) are its own estimates. A part-of-speech tagger and a survey of shipped games' fallback rates add nothing.

## Studio relevance

### What it contradicts in our design (read first)

| # | Finding | Our design today (checked) | Decision | Owner |
|---|---|---|---|---|
| 1 | The arm comparison is inside the noise | Per-arm rates, no interval | Do not choose an arm from session 1; report paired per-turn differences with an interval from now on (a one-cell change needs about 300 to 550 turns to show 5 points; the set has 360) | R&D and lead |
| 2 | The checker undercounts later rules | One reason code per line | Add an "all rules" count to the measurement harness; play-time behaviour unchanged | lead |
| 3 | Banning semicolons drove the sentence cap | Both the prompt and the checker ban them; the first fix replaced the sentence cap with word caps | No change now; look again only if the re-check shows the terse voice failing on punctuation | Publisher |
| 4 | `coin` in the unit list rejects legal coin change | True; after the fix it fires only after a number word | Keep; count coin rejects in the re-check | lead |
| 5 | Drop the verbatim choice and event text from the prompt | The narrator is told the event title, text and choice by ruling; choice-parroting rejects were 7 to 17 per arm | Keep the ruling; the measured cost is tiny | settled |
| 6 | Negative rules prime forbidden words | The shared rules are mostly negatives | Test, do not assume: one arm with the rules reworded as positives, same turns, paired | lead, needs a grant |
| 7 | Retry is pointless at a fixed seed | One attempt at temperature 0.15, then the fallback | Read the model card; test two or three candidates per slot with different seeds and a deterministic pick | R&D reads; Publisher rules |
| 8 | Quantisation is not the cause | Q4_K_M ships; an fp16 copy is on the rig | Do not spend a session on quantisation | settled |
| 9 | Deterministic trimming works, repair does not | No repair step | Try trimming in the same test as row 7 | lead |

### Decisions taken (the Publisher's rulings, 2026-11-13)

- Rows 1, 2, 4, 5, 6 and 8 agreed as written; row 3 is decided after the re-check.
- **Row 7 ruled:** several candidates keep "same seed, same telling" if every candidate seed is derived from the turn
  seed (seed, seed + k, a fixed k list), the pick is a pure function of the candidates (first accepted in fixed
  order, ties by index), and trimming is deterministic. A test must show two plays of the same turn give identical
  text. At most three candidates, sequential, stopping at the first accepted; the experiment reports latency.
- **Held until the cheap fixes are measured:** bundling a pinned llama.cpp server in place of the player's Ollama
  (it would allow token bans, grammars and parallel candidates but changes how the game ships), and training a
  small adapter on accepted and rejected lines (only if the cheap fixes stall above roughly 15%).
- **Other actionable items:** brief lines as plain text with a stop at the first full stop; pre-generating the next
  scene line while the player reads the outcome; keeping the model loaded between calls and lowering the ten-second
  timeout; counting repeated openings per voice; checking that fallback lines exist per voice.

### What was measured afterwards

The re-check and the experiment arms are filed in `experiments/etv-narrator`. In those records, copied as written:
the fallback rate fell from 61.5% (session 1, plain) to 55.5% after the first fix, and to 8.1% with the rulings
prompt, up to three candidates and trimming (paired by turn +47.4 points, interval +45.1 to +49.7); the positive
wording arm was worse (63.7%), the unquantised model worse (66.8%), and model-card sampling alone changed nothing.
The report's forecast bands did not match, which is unsurprising for estimates. Those later records also warn that
passing the rules is not the same as saying what happened.

relevance: `act`; the cheap-fix experiments it prompted are done.

## Claims

- [verified] 18 calls share each turn and 360 turns resolve about 2.8 to 3.6 points paired; cited against plain differed by 2.45 and text against plain by 0.6 in session 1 (via: session 1's reports and R&D's arithmetic, 2026-11-13)
- [verified] The checker records one reason code per line and stops at the first broken rule; the first fix's checker-only preview moved quantifier rejects from 174 to 417 once length was fixed (via: the game's code at the commit after the first fix, R&D, 2026-11-13)
- [verified] The report's "missing lines" in the rule table were the draft-animal rule (5, 1 and 6 rejects) left out of R&D's facts file (via: R&D's own file and session 1's reports, 2026-11-13)
- [verified] The first-fix checker-only preview measured 38.7% fallback (via: R&D's preview run, 2026-11-13)
- [unverified] 42% of lines that pass the length rule fail a later rule (the report's figure; consistent in direction with the preview, not recomputed)
- [unverified] Negative rules prime forbidden words in small models (the report's papers; none opened)
- [unverified] The model card suggests temperature 0.7, top-p 0.8, top-k 20 (not checked when the harvest was written; the experiments later used them)
- [unverified] One paper finds no instruction-following loss at Q4_K_M; the report's fallback forecasts of 18-25%, 8-15% and 3-7%; a 2,000-2,700 line adapter set (the report)
- [unverified] Ollama supports schema and stop sequences but not custom grammars or token bans (the report; check at build)

## Sources

- [aggregator] https://gemini.google.com/app/35a5c8bba065d454 — Gemini Deep Research report on small local model narration under hard rules (seed 23, 2026-11-13; account-private chat)
- [rig] experiments/etv-narrator — the measured sessions that followed (session reports and run records, 2026-11-13)
