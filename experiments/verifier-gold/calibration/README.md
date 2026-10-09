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

## Amendment, 2026-10-09 ~04:20, before gemma4:31b loads: thinking level (the Director's direction)

The Director: thinking level is a variable to **weigh and test per task**, not a blanket default. Long
thinking can overrun the context and run long, so off or reduced should be considered; some tasks need it,
and the trade-off should shrink as models learn to think less wastefully. So:
- ~~gemma4:31b runs at `--think low`~~ **Withdrawn before gemma loaded (04:58):** R&D's own notes from earlier
  that day record that **gemma4's thinking is on or off only**; its levels aren't graded. ("low" isn't a level it
  has, and Ollama would treat it as on or reject it.) So gemma4 runs at **`on`**, the setting candidates.txt
  pre-registered. Its off/on comparison moves to the post-hoc thinking-level runs.
- **Thinking levels by model** (R&D's 2026-10-08 notes, Ollama 0.35.1). **Check a candidate's setting
  against this table before any amendment**, and add a row (from notes or the model card, not a live call)
  before a new model runs:

  | model | `--think` levels it has | note |
  |---|---|---|
  | gemma4:31b | off, on | not graded |
  | qwen3:8b / qwen3:14b | off, on | likely boolean; graded levels unverified, so no "low" arm unless shown real |
  | mistral-small:24b | none | Ollama errors if asked |
  | granite4.1:30b | none | Ollama errors if asked |
  | llama3.1:8b | none | no thinking capability |
  | Nemotron 3.5 Lightning | off, true, medium | |
  | Muse Glimmer 30B | off, low, medium, high, max | default high |
  | Qwen3.8-27B | off, on, plus `reasoning_effort` low / medium / xhigh | from its HF card; verify under Ollama before use |
- **Wherever a graded level is used, check it's real first** (the Publisher's point). Ollama 0.35.1 documents graded levels for
  gpt-oss; for other models it may treat any string as "think on". So gemma's first claims are compared with
  the smoke's `on` claims on thinking length (eval tokens). If low thinks just as long as on, the README and
  report record **"low = on for gemma4 in this Ollama"**. It is never silently relabelled.
- **Post-hoc thinking-level runs** (a separate grant, marked post-hoc): qwen3:8b and qwen3:14b at `off` (and
  `low` only if the check shows it differs from on), and **gemma4:31b at `off`**, on the same tune claims, so
  each has a curve across its real levels on identical claims. The report gets a
  thinking-level axis: accuracy, false accepts, false rejects, abstains, seconds per claim and unusable rate.
- **Future candidates** get an `off` / `low` arm alongside `on` where thinking could matter, rather than one
  setting by habit.

## Finding, 2026-10-09: a deterministic Ollama 500 leaves a run incomplete

mistral-small:24b, grounded tune: claim `prs-aspire-si-64-10s` gets **HTTP 500 from Ollama on every attempt**,
after about 227 generated tokens. At temperature 0 it's deterministic, probably the structured-output grammar
breaking. offrig#44 treats every 5xx as a transport failure: never recorded, always retried. So the run stays
incomplete at 269/270. mistral fails the rule regardless (FA upper bound 0.253 grounded, 0.269 reasoning). A fix
is proposed to the Publisher: a 5xx on the same claim twice is recorded as `unusable:server_error`.

The run scripts' `--resume` path also had a bug: it didn't repeat the model and gold, which offrig's `--resume`
requires. It surfaced on this one claim and is fixed.

## Result, 2026-10-09: no default named

The chain ran all six candidates on `--split tune`, smallest first, with 15-minute rests (06:48 end). **None
passes the default rule, so no default is named and held-out was not run.** Receipts: `results/2026-10-09-chain/`
(each run's `manifest.json`, `metrics.json`, `verdicts.jsonl`, the chain logs, and `difficulty-report.txt`).

| model (think) | type | FA upper (< 0.10) | abstain (≤ 0.20) | decided BA (≥ 0.80) | missing (0) |
|---|---|---|---|---|---|
| llama3.1:8b (off) | grounded | 0.557 | 73/255 0.286 | 0.630 | 0 |
| | reasoning | 0.225 | 59/202 0.292 | 0.604 | 2 |
| qwen3:8b (on) | grounded | 0.125 | 91/253 0.360 | 0.929 | 2 |
| | reasoning | 0.147 | 52/203 0.256 | 0.940 | 2 |
| qwen3:14b (on) | grounded | **0.089** | 66/255 0.259 | 0.967 | 0 |
| | reasoning | 0.204 | **35/204 0.172** | 0.893 | 0 |
| mistral-small:24b (off) | grounded | 0.253 | 62/254 0.244 | 0.832 | 1 (stuck, Ollama 500) |
| | reasoning | 0.269 | 44/204 0.216 | 0.788 | 0 |
| granite4.1:30b (off) | grounded | 0.261 | 101/254 0.398 | 0.850 | 1 |
| | reasoning | 0.367 | 48/204 0.235 | 0.761 | 0 |
| gemma4:31b (on) | grounded | **0.026** | 52/254 0.205 | **0.989** | 2 (truncated) |
| | reasoning | **0.059** | **13/202 0.064** | **0.990** | 2 (truncated) |

**Reading it:**
- **gemma4:31b is the only model fooled almost never:** 0 false accepts on grounded at every tier, 1/34 on
  reasoning T3 (the others: 0.23–0.29). It misses the rule on four truncated answers and on grounded abstain by
  one claim's worth (0.2047). Its abstentions grow with evidence length (grounded Q1 4/58, Q4 21/72).
- **All four gemma misses are truncations** at offrig calibrate's fixed reply budget, `num_predict` 4096, with
  the model still thinking (`docs-boost-t`, `prs-offrig-39-15s`, `diff-role-os-23-11s`,
  `diffhard-rnd-7fba56f-1u`). Truncations count as missing only, never as abstentions.
- qwen3:14b passes grounded on false accepts and accuracy but abstains too often; on reasoning it is fooled on T3.
- The models without thinking (llama, mistral, granite) are fooled most. The thinking qwens are fooled less but
  abstain more. Model and setting are confounded across families; the post-hoc thinking-off runs below isolate it.
- Per the protocol, the next model is not promoted and no rule is relaxed after the fact.

## Pre-registration, 2026-10-09 ~07:00, before any run: gemma4:31b at a larger reply budget (post-hoc)

Labelled **post-hoc**: it exists because of the result above. Agreed with the Publisher in principle; it runs
on its own card grant. `verify calibrate --num-predict` already exists (recorded in the manifest and in the
resume identity), so no offrig change is needed.

- **The one change:** `num_predict` 4096 → **12288**. Everything else as the chain: think on, structured on,
  temperature 0, seed 0, `num_ctx` 16384, same gold, `--split tune`, both check types.
- **Why 12288:** the chain's answered gemma replies peaked at 3,636 tokens (grounded) and 2,473 (reasoning), and
  the four truncations ran past 4,096; 12288 is three times the old cap. The longest prompt was 4,056 tokens, so
  12288 + 4,056 still fits the unchanged 16384 context; `num_ctx` is not a second variable.
- **What it can and can't fix, said before the result:**
  - **reasoning** passes if the 2 truncated claims answer: every other condition already passes, and the
    false-accept upper bound has room even if both answers are false accepts.
  - **grounded:** the truncations alone can't fix abstain. Of the two, only `docs-boost-t` (gold supported) enters
    the abstain denominator (`prs-offrig-39-15s` is gold cannot_tell). Answered, it gives 52/255 = 0.204; abstained,
    53/255. Grounded passes only if the larger budget also turns at least one existing abstention into an answer.
  - Exactly 51/255 = 0.200 passes **on the line**; the report calls it a **boundary pass**, and the held-out
    confirmation carries the weight.
- **A split result** (one check type passes, the other doesn't): offrig's rule is per check type, so a default
  may be named **for the type that passes only**, after its held-out confirmation; the other type has no default
  and the report says so. The protocol's "cheapest model that passes both" applies when both pass.
- **If it passes on tune:** one held-out run per passing type, same settings, which is the headline. A held-out
  fail names no default.
- **Served as calibrated:** a default chosen at 12288 must be served at 12288 (`offrig verify` carries the
  setting); the calibration report records it per model.
- Every number from this run is reported beside the chain's, never in place of it.

## Post-hoc finding, 2026-10-09: the quote check, not the model, drives most of gemma's grounded abstain

Asked by the Publisher after the ladder exposed offrig's 12-character quote floor. **The chain's result stands as
scored:** the quote rule was part of the contract. This sizes a possible offrig change. Script
`quote_match_posthoc.py`, output `results/2026-10-09-chain/quote-match-posthoc.txt`. Mode 0 reproduces offrig's
scored abstain and false-accept counts exactly for all 12 runs.

**Where a final cannot_tell comes from,** when the model itself said supported or unsupported and offrig
downgraded it (`quote_not_found`):
- **The 12-character floor is almost never the cause on the chain:** 0–3 per run. Diff hunks have short lines,
  but models quote longer spans.
- **Comment markers are the main cause for gemma:** the evidence wraps prose across `///` lines, and the model
  quotes the prose without the markers ("Lane ports are two apart: … for the handoff runner's second tunnel"),
  which isn't a verbatim substring.
- **Elisions** (`...`) and paraphrase make up the rest. The qwens' downgrades are mostly these.

**Rescored under looser matching (descriptive):**

| run | as scored: abstain, FA ub | mode 1 (whole-line short quotes, markers stripped) | mode 2 (+ elision segments) |
|---|---|---|---|
| gemma4:31b grounded | 0.205 ✗, 0.026 | **0.075**, 0.026 | 0.059, 0.026 |
| gemma4:31b reasoning | 0.064, 0.059 | 0.059, 0.059 | 0.045, 0.059 |
| qwen3:14b grounded | 0.259 ✗, 0.089 | 0.247 ✗, 0.089 | 0.224 ✗, 0.098 |
| mistral-small:24b grounded | 0.244 ✗, 0.253 ✗ | 0.165, 0.276 ✗ | 0.161, 0.276 ✗ |
| the other 8 runs | | no rule outcome changes | no rule outcome changes |

- **gemma4:31b grounded:** 33 of its 52 abstentions are marker-stripped quotes that really are in the evidence. Its
  false accepts stay at 0/142. Under mode 1 its only remaining miss would be the 2 truncations.
- Rescues can add false accepts (mistral, granite, llama), so a looser match is not free. That's why it's a
  verdict-contract change with its own pre-registration, never a rescore.
- **For the gemma post-hoc run:** at num_predict 12288 under today's quote rule, grounded is expected to stay
  near 0.20 abstain. The bigger budget fixes the truncations, not this.
