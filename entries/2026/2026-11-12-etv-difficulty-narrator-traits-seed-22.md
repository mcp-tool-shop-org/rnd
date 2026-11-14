---
id: 2026-11-12-etv-difficulty-narrator-traits-seed-22
title: Escape the Valley: difficulty target, narrator model shortlist and party traits (seed 22)
date: 2026-11-12
kind: finding
relevance: act
fields: [game-design, narrator]
tags: [escape-the-valley, difficulty, local-models, licences, traits, seed-22, harvest]
---

## Summary

The Escape the Valley (ETV) team had three open questions: how hard the game should be, which small open model should
narrate by default, and whether the party traits matter. A Gemini Deep Research run, given a facts file about the
game's balance table, traits and narrator, wrote a report; it is `[aggregator]` throughout and was written without
the game's code, so its "inference" tags are guesses. R&D checked proportionally: licences and Ollama library names
at source, and the load-bearing numbers by recomputation. The model licences and names held; much of the difficulty
and speed evidence is the report's inference or mixed-source estimate.

Found through a Gemini Deep Research report (2026-11-12); claims checked as marked.

## Key points

- **Licences read at source (2026-11-12):** Qwen3-4B-Instruct-2507, Qwen3-1.7B, Gemma 4 E4B (and its family),
  Ministral-3-3B-Instruct-2512, Granite 4.0 micro and SmolLM3-3B are Apache-2.0; Phi-4-mini-instruct is MIT;
  Llama-3.2-3B-Instruct is the custom Llama 3.2 Community License (attribution, naming, an acceptable-use policy,
  a licence request above 700M monthly users). For a game that only talks to the player's own Ollama and ships no
  weights, none of these bite; Llama is kept as a baseline only.
- **Ollama names and sizes confirmed:** `qwen3:4b-instruct` (2.5 GB), `qwen3:1.7b`, `qwen3:8b`, `phi4-mini`,
  `gemma4:e2b`, `gemma4:e4b`, `ministral-3:3b` and `:8b`, `granite4:3b`, `llama3.2:3b`. `smollm3` has no official
  Ollama tag (404); Hub GGUF only.
- **Json validity by model:** an arXiv paper's abstract gives a range of 78.6% to 100% native schema validity across
  small models; which model owns which number was not confirmed, so "Llama 3.2 is weakest" rests on the report.
- **Priming:** naming banned words in a prompt primes the model to emit them (87.5% of violations, single 7B model,
  single-word task; weak evidence for our setting). Thinking models blow a ten-second budget; use `think:false` or
  an `-instruct` tag.
- **Difficulty evidence is thin and mostly lifetime completion, not per-run rates.** Confirmed: Slay the Spire 2's
  human win rate of about 16% at the lowest difficulty; FTL Easy 26.4% lifetime completion; Death Road to Canada
  lifetime completions of 20.3%, 12.3%, 8.0%, 6.1% and 5.8% across its modes. Not confirmed: FTL Normal tuned for
  about 10% wins and 9.8% completion, and the exact Oregon Trail design wording (the gist, most players fail the
  first time and keep trying, is on the cited page).
- **Scripted bots against humans:** cautious bots do well on short-horizon survival and badly on long planning, so
  the cautious script's 9% is a floor for skilled humans but not necessarily for novices. No source pairs a
  scripted rate and a human rate for a game like ours; the report's human bands (first run 2-8%, returning 12-20%,
  experienced 60-85%) are inference.
- **Binomial noise is not the issue:** 90 wins in 1,000 runs has a 95% interval of 7.38% to 10.93%; 0 and 34 in
  1,000 give 0 to 0.38% and 2.44% to 4.71%. A paired fixed-seed trait test shrinks the detectable effect from
  about 3.6 points to 1.25-2.17 points (R&D recomputed).
- **Trait design:** lasting trait systems combine different axes and unlock choices, not just small percentages; a
  dominated trait is wasted (Sharp Eye's +10% hunting is dominated by Tracker's +15%); pure-penalty anxiety is
  disliked while mixed designs are liked. Practitioner evidence, low strength.
- **Hardware:** a ten-second per-call limit with two calls per turn is fine on a GPU or Apple silicon and fails on a
  DDR4 laptop CPU for 4B models (the report's own latency model; 1.60, 2.47, 7.22 and 16.93 s per call recomputed).
  Published CPU speeds are thin; measure our own.

## Studio relevance

### What it contradicts in our design (read first)

| # | Finding | Our design today | Decision needed |
|---|---|---|---|
| 1 | The default `llama3.2` is the weakest JSON follower of its class (partly confirmed) and has the heaviest licence terms | Default `llama3.2`, carried from the Python version, never measured | Measure the shortlist first on the fallback harness, then change the default |
| 2 | A JSON Schema in Ollama's `format` makes output structurally valid by grammar masking; `"format":"json"` alone does not | "Strict JSON output"; unclear which form the client sends | Check what the client sends; send a full schema (sentence array, 1-3 items) |
| 3 | Thinking models invent details and blow the budget | Not stated; bare `qwen3` tags think | Pin `think:false`; default to the instruct tag, never bare `qwen3:4b` |
| 4 | Naming banned words in the prompt primes them | The checker bans pronouns, invented names and eerie words; unknown whether the prompt lists them | Read the prompt; move banned lists to the checker only and rerun (cheap A/B) |
| 5 | A fixed ten-second limit fails on weak CPUs | No hardware tier or fallback | Add a warm-up speed probe and a tier; needs measured CPU numbers |
| 6 | Starvation as top killer under every policy reads as a food-clock spiral | Starvation leads all five policies | A difficulty-target call, then one lever at a time; first candidate a zero-food emergency phase |
| 7 | Four graded endings make a binary win rate ambiguous | The harness reports win rate | Print all four grades and deaths by cause per policy |
| 8 | Sharp Eye is dominated by Tracker | Both exist unchanged | Give Sharp Eye another axis or merge it |
| 9 | Auto-spending medicine removes a triage decision | Healer auto-treats | A taste call: player-triggered or keep |
| 10 | Small percentage traits are not felt; the best-liked also unlock choices | No trait gates a choice among 464 | Decide whether to add option-unlock tags to some events (an authoring cost) |
| 11 | Mixed traits are liked | The Anxious trait is already mixed | None; tune the numbers |
| 12 | Party names such as "You" would fail the checker on every line | Unclear whether player-chosen names are exempt | Check the checker; whitelist literal party names |
| 13 | Seed replay: prose differs unless the seed is fixed | Engine deterministic; narrator prose not stated reproducible | Decide if prose reproducibility matters; pass a derived seed at low temperature |
| 14 | Starvation is a global killer, so a morale trait may not touch measured deaths | Steady reduces morale loss | Measure morale's share of deaths before building |

### Decisions taken and recommendations sent

- **Narrator model:** the sessions that followed ran `qwen3:4b-instruct-2507` through the local Ollama daemon with
  `think:false`, a full schema and a derived seed (see `experiments/etv-narrator`); the licence is Apache-2.0 and is
  now in the registry. The rest of the shortlist (Phi-4-mini, Gemma 4 E2B, Ministral 3B, Granite 3B, Qwen3 1.7B,
  Llama 3.2 as baseline, and Gemma 4 E4B or Qwen3 8B as a high tier) was recommended for measurement, each with and
  without the prompt change and with a full schema, reporting per-rule rejection and median latency per hardware
  class. Whether every candidate was measured is not recorded here.
- **Recommended to the ETV lead, not rulings:** narrator client fixes then measure; ease difficulty in the next
  ruleset toward a cautious-script win rate of 20-30% so a novice lands in single digits (R&D's reasoning, not a
  published relation); make traits open options. Levers one at a time: food burn rate and hunt yield, a zero-food
  emergency phase, a starting buffer with a score multiplier, risk of bold choices, optional stacked modifiers
  later, and all four grades reported before any tuning.

relevance: `act`.

## Claims

- [verified] Qwen3-4B-Instruct-2507, Qwen3-1.7B, Gemma 4 E4B, Ministral-3-3B-Instruct-2512, Granite 4.0 micro and SmolLM3-3B are Apache-2.0 on their model pages; Phi-4-mini-instruct is MIT (via: the Hugging Face model pages and LICENSE files read at source, R&D, 2026-11-12)
- [verified] Llama-3.2-3B-Instruct is under the Llama 3.2 Community License with attribution, naming, an acceptable-use policy and a 700M-user clause (via: the model page read at source, R&D, 2026-11-12)
- [verified] The Ollama library has `qwen3:4b-instruct` (2.5 GB), `qwen3:1.7b`, `qwen3:8b`, `phi4-mini`, `gemma4:e2b`, `gemma4:e4b`, `ministral-3:3b` and `:8b`, `granite4:3b` and `llama3.2:3b`; `smollm3` is a 404 (via: the library pages read at source, R&D, 2026-11-12)
- [verified] Wilson 95% intervals for 0, 34 and 90 wins in 1,000 are 0-0.38%, 2.44-4.71% and 7.38-10.93%, and the paired-seed detectable effect is about 1.25-2.17 points against 3.59 unpaired (via: recomputation, R&D, 2026-11-12)
- [verified] Naming banned words primes them (87.5% of violations, n = 40,000 samples; arXiv:2601.08070) (via: the abstract read at source, R&D, 2026-11-12; the model and the report's variance figure are not on it)
- [verified] Slay the Spire 2's human win rate is 16% at the lowest difficulty (arXiv:2607.02255); the "240 million runs" is not on the abstract (via: the abstract read at source, R&D, 2026-11-12)
- [verified] Steam lifetime completion: FTL Easy 26.4%; Death Road to Canada 20.3, 12.3, 8.0, 6.1 and 5.8% across modes (via: the Steam achievement-statistics pages read, R&D, 2026-11-12)
- [unverified] Llama 3.2 scored 78.6% and Qwen3-4B 100% native JSON validity (the abstract of arXiv:2609.23742 gives the range without naming models)
- [unverified] FTL Normal was tuned for about 10% wins and has 9.8% lifetime completion; the human win-rate bands for ETV; per-model CPU and GPU speeds; the Vectara hallucination figures; SpireBench numbers; qwen3:8b and ministral-3:8b licences (not opened)

## Sources

- [primary] https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507 — Alibaba Qwen (Apache-2.0)
- [primary] https://huggingface.co/microsoft/Phi-4-mini-instruct — Microsoft (MIT)
- [primary] https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct — Meta (Llama 3.2 Community License)
- [primary] https://ollama.com/library/qwen3/tags — Ollama (library names and sizes)
- [primary] https://arxiv.org/abs/2601.08070 — Rana, priming by banned words
- [primary] https://arxiv.org/abs/2609.23742 — Chavan, native schema validity of small models
- [primary] https://arxiv.org/abs/2607.02255 — Slay the Spire 2 human win rates
- [primary] https://steamcommunity.com/stats/212680/achievements — Steam (FTL achievement statistics)
