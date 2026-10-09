# Calibrating offrig's default verifier

Which local model becomes offrig's default verifier, chosen by `offrig verify calibrate` (offrig#44, oracle
mode: each claim's own context is the evidence) against the gold sets in `..`. This file fixes the protocol
before any candidate runs.

## Fixed before the runs (2026-10-08)

**Gold** (cross-family check passed, `../crossfamily/`):
- grounded: `grounded.jsonl` + `prs/grounded-prs.jsonl`;
- reasoning: `diffs/reasoning-diffs.jsonl`.

**Rule:** offrig's default rule, as merged in #44.
- Per check type: the false-accept upper bound below 0.10 (the primary rate counts gold unsupported and gold
  cannot_tell together), abstain at most 0.20, decided balanced accuracy at least 0.80, and at least 100
  unsupported claims.
- Any model-caused unusable outcome fails the rule.
- The default is **the cheapest model that passes both grounded and reasoning.**

**Selection and confirmation:**
1. **Smoke** (`smoke.sh`): 4 tune claims per check type per model, to settle `--think` (a model without
   thinking refuses `think`) and `--structured`, and to measure seconds per claim. Smoke results choose
   settings only, never a model.
2. **Selection on `--split tune`,** smallest model first, every model with its smoke-settled settings.
3. **Confirmation:** the chosen model runs once on `--split heldout`. **The held-out numbers are the
   headline,** so the choice isn't scored on the data it was picked on. If it fails on held-out, no default is
   named: that is reported, and the next model is not quietly promoted.

**Amendment, 2026-10-08, before any candidate ran:** the reasoning set can't be split. The rule needs at
least 100 unsupported claims per run, and reasoning has 50 in tune and 61 in held-out (grounded has 128 and
113). Split, no model could pass on reasoning, so the protocol as first written could never name a default.
- **grounded:** unchanged. Select on tune; held-out confirms and is the headline.
- **reasoning:** runs on `--split all` (246 claims, 111 unsupported), for selection and for the rule.
- **The cost:** reasoning has no held-out check, so the chosen model's reasoning numbers are in-sample.
  Selection bias stays small, because the rule takes the cheapest model that passes, not the best score. The
  report says so next to the numbers.
- **The fix:** about 90 more reasoning behaviours, so each split reaches 100 unsupported; then reasoning gets
  a held-out confirmation too. That's asked of the Publisher, who owns the reasoning set.
- R&D missed this when the protocol was first committed; it was caught while writing the run script, before
  any model ran.
- **Superseded the same night, still before any candidate ran:** the Publisher's batch 2 (blind pass 208/213,
  adjudicated) takes reasoning to **102 unsupported in tune and 108 in held-out**. So reasoning runs as first
  planned: select on tune, and held-out confirms and is the headline. Both check types now follow the same
  protocol, and `run_model.sh` takes one split for both.

**Candidates** (local, on disk, families other than the generator's): qwen3:8b, llama3.1:8b, qwen3:14b,
mistral-small:24b, granite4.1:30b, gemma4:31b.
- **gemma4:31b has seen the 120 cross-family sample claims.** Its report also shows its result without them.

**Where:** the local 5090 on the CUDA 13.4 system Ollama, overnight, in blocks the Publisher grants. Not the
cloud: a stock RunPod Ollama runs CUDA 13.0, against the 13.4 rule. Runs use a scratch `--project`, so the
schema-v6 store never meets an older offrig MCP server.
- **Rest (Director's standing rule, 2026-10-08):** the card rests 15 minutes with nothing loaded between runs.
  `chain_step.sh` rests before it loads each model after the first, and refuses to load if anything is
  still on the card. Six models add about 75 minutes of rest.
- **Pauses:** a health monitor may pause the chain mid-model. A step whose runs are incomplete exits 3 and
  the chain stops there. Rerunning the same step resumes it, and no completed claim is asked again.

**Reported per model:**
- every metric row, including the cannot_tell row and the false-accept rate on unsupported only;
- the strata `has_doc_comment`, `self_referential` and `origin`;
- unusable counts and seconds per claim.

## Difficulty curve (added 2026-10-09 at 02:15, before any chain run; Director's ask)

Every model runs every tune claim anyway. The question this adds is **where each model's accuracy falls off**
as claims get harder. Tiers come from the gold's own metadata (`difficulty.py`, fixed into `tiers.json`), never
from model results:
- **T1 surface:** a false claim that differs by a value or name, plus supported claims not tagged hard.
- **T2 logic:** negation, conditions, bounds, behaviour, order, defaults, scope.
- **T3 hard:** the reasoning set's hard patterns and change-specific traps. Grounded has none.
- **T4 unknown:** gold cannot_tell.

A second axis is evidence length in quartiles.

| tune claims | T1 | T2 | T3 | T4 |
|---|---|---|---|---|
| grounded | 168 | 87 | — | 15 |
| reasoning | 90 | 53 | 61 | 19 |

**Reported** per model, check type and tier: accuracy (gold cannot_tell answered unsupported or cannot_tell
counts as right), false accepts on not-supported gold, and abstains.

**Falloff** is the first tier where accuracy drops below 0.80 or the false-accept rate exceeds 0.10. Every
cell shows n and a Wilson 95% interval, and cells under 30 claims are marked tentative (the Publisher's ask).

**Descriptive only:** the default rule above is unchanged, and all six models run all tiers whatever the
first one scores.

## Next round: a generated math ladder (Director's idea, 2026-10-09)

Tonight's tiers are set by judgment from the gold's notes. A generated ladder gives a controllable difficulty
dial with exact answers, unlimited items, no labelling cost, and no chance a model has seen them.

- **Format, so it stays a verifier test:** the evidence is a small generated function or formula; the claim
  is "`f(7)` returns 52". The near-misses are wrong results.
- **Knobs, each a level up:**
  - number of steps (1 → 8);
  - precedence (parenthesised → bare);
  - integer traps (division, modulo, rounding, overflow);
  - control flow (none → branch → loop → loop with early exit);
  - unit conversions inside the computation;
  - near-miss distance (far off → off by one or one rounding step).
- **Studio fit:** offrig's budget and price arithmetic (per-GPU price × count, caps, rounding) is exactly
  this, and an error there costs money.
- **Before it runs:** pre-register the generator (seeded), the levels, and n per level sized for a
  falloff call. At least 30 per cell, per the Publisher's rule.

## Post-hoc candidates (added 2026-10-09, after tonight's results were seen)

These joined the pool **after** the overnight chain's results were visible, so they're marked post-hoc
wherever they're reported. A post-hoc pass is a lead to confirm, not the same evidence as a model chosen before
any results.

| model | licence (verify on its card before running) | note |
|---|---|---|
| Qwen3.8-27B | Apache-2.0 per its HF card (August 2026) | dense, `reasoning_effort` thinking; ~17 GB at Q4; download after the ladder |
| Muse Glimmer 30B | Apache-2.0 per Ollama's 2026-08-10 post | trace the base model's licence too; already on disk |
| Nemotron 3.5 Lightning 30B-A3B | NVIDIA licence (unverified; not Apache) | a default-verifier speed candidate only, never a teacher |

Each gets its own smoke run (think and structured settled the same way), its own tune run under its own grant,
and held-out only if it is chosen, under the same rule. The default rule and the falloff tiers are unchanged.
