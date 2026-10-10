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

- **Amended 07:27, before any run (the Publisher's sequencing):** this is **a new calibration, not a rescore**,
  on the released offrig binary that carries **quote rule 2** (offrig#47: comment and diff markers stripped per
  line, whole-line short quotes). Two settings change from the chain, both named here: `num_predict` and the
  quote rule. Its result is reported beside the chain's, never as a corrected version of it, and Mike sees the
  rule change stated plainly.
- **The changes:** `num_predict` 4096 → **12288**, and quote rule 1 → **2**. Everything else as the chain: think
  on, structured on, temperature 0, seed 0, `num_ctx` 16384, same gold, `--split tune`, both check types.
- **The binary (fixed 13:17, before any run):** offrig main **751fb1d**, the Publisher's install after the ladder.
  It carries quote rule 2 (#47), `--keep-thinking` (#48), the health-checked 5xx and dropped-reply rule (#46,
  #49), and per-provider caps (#51, budget only; calibrate spends nothing). Installed by the Publisher; R&D
  re-hashed both files before the run (about 14:05) and they match:
  - `offrig.exe` sha256 `6A1622C53B96E828CBA2D28AE2288218B94B19CC5C727368523BCD7E8ED72741`
  - `offrig-mcp.exe` sha256 `E564295A590AF1FFD30E104660593957FABE54FCF2640B6873D6CA5AE55F1617`

  `offrig --version` still prints 1.0.0, so **the sha256 is the pin**, not the version string.
- **Context check (the Publisher's question, answered before the run): `num_ctx` stays 16384.**
  - The longest tune prompt in the chain's gemma verdicts (`prompt_eval_count`) is 4,056 tokens
    (`diffhard-role-os-4342dff-1s`). 4,056 + 12,288 = 16,344 ≤ 16,384, so the reply cap is hit before the
    window fills, on every tune claim.
  - The four truncated claims have short prompts, about 1.6–1.9k tokens, measured on sibling claims.
  - **Held-out** evidence is shorter. Fitting tokens ≈ 1,304 + 0.285 × characters on tune (max residual 330)
    puts held-out's longest prompt at about 3.2k tokens.
  - The report still flags any claim where `prompt_eval_count + eval_count` reaches 16,384, which would mean a
    silent context shift. If one appears, that claim is reported as compromised.
  - Changing `num_ctx` would add a second variable against the chain for no measured need.
- **The run line, fixed before the run:**
  `CAL_EXTRA="--num-predict 12288 --keep-thinking" bash chain_step.sh /e/AI/rnd-calibrate-r2 gemma4:31b on on <rest> tune`
  - It runs in a fresh scratch project (`/e/AI/rnd-calibrate-r2`), so no directory or store is shared with the
    chain.
  - `run_model.sh` passes `CAL_EXTRA` to both a new run and a resume.
  - `thinking.jsonl` stays in the run directory and is not committed to rnd, which is public, unless it's
    scanned first.
- **`--keep-thinking` (added 09:36, before any run; diagnosis only):** the run records gemma's thinking text to
  `thinking.jsonl` in the run directory. It is untrusted model output, never scored, and not part of the verdict
  or the resume identity, so it changes no number. It answers two questions the chain couldn't: what the
  truncated replies were doing at the cap, and whether long-evidence abstentions come from the quote step or
  from the model's own doubt.
- **Expected from the post-hoc rescore** (`quote_match_posthoc.py`, and a line-for-line port of #47's rule that
  reproduces rule 1 with 0 mismatches): grounded abstain about 0.075 with 0/142 false accepts, if the replies are
  the same. A rerun can differ, so this is a prediction, not a result.
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
- **For the gemma post-hoc run:** the budget alone fixes the truncations, not this. So the run's pre-registration
  (above) names quote rule 2 as well, making it a new calibration.

## Post-hoc, 2026-10-09: each model's error lean (for ASPIRE's judge choice)

ASPIRE's control B found mistral-small:24b saying "wrong" regardless of consensus, and asked whether the gold
agrees. Script `error_lean_posthoc.py`, output `results/2026-10-09-chain/error-lean-posthoc.txt`. Final verdict:

| model | false rejects, grounded | false rejects, reasoning | false accepts, grounded | false accepts, reasoning |
|---|---|---|---|---|
| gemma4:31b | 2/126 (0.02) | 0/101 (0.00) | 0/128 (0.00) | 1/101 (0.01) |
| qwen3:14b | 1/127 (0.01) | 4/102 (0.04) | 5/128 (0.04) | 13/102 (0.13) |
| qwen3:8b | 3/126 (0.02) | 1/101 (0.01) | 8/127 (0.06) | 7/102 (0.07) |
| mistral-small:24b | 9/126 (0.07) | 12/102 (0.12) | 25/128 (0.20) | 20/102 (0.20) |
| granite4.1:30b | 0/126 (0.00) | 5/102 (0.05) | 24/128 (0.19) | 25/102 (0.25) |
| llama3.1:8b | 7/127 (0.06) | 41/101 (0.41) | 64/128 (0.50) | 14/101 (0.14) |

**Reading:**
- mistral is noisy in **both** directions, not just "wrong"-leaning. It has 3–10× the false rejects of gemma and
  the qwens, plus a 20% false-accept rate.
- granite is quiet on false rejects here, but abstains on 40% of grounded claims. On the math ladder it called
  14% of true claims false (`../math-ladder/results/2026-10-09-ladder/`).
- None of this measures a rewrite judge's task. ASPIRE ran its own pre-registered control for that (aspire-si
  #77).

## Pre-registration note, 2026-10-09 15:27: before any reasoning result exists

Written after grounded finished (FAIL, 1 missing; diagnosed in the rerun report) and **before** the reasoning
half has a result.

- **If reasoning passes on tune:** the registered next step runs. That's a **reasoning-only held-out** run on
  the same binary (751fb1d) and settings (quote rule 2, num_predict 12288, num_ctx 16384, think on), under its
  own grant. It's skipped only by a recorded decision, never quietly.
- **That run is reasoning's one held-out look under verdict contract v2.** offrig's planned contract v3
  (several quotes per verdict, quote rule 3, and a loop detector, decided 2026-10-09 after this run's grounded
  diagnosis) changes the verdict contract. **A v3 reasoning default can't reuse this held-out:** its
  confirmation needs a fresh sealed split, the same kind planned for the distilled student. That's planned
  here, not discovered later.
- **If reasoning fails on tune:** there's no held-out run. gemma's next calibration is the v3 one,
  pre-registered on tune.

## Result, 2026-10-09: gemma4:31b rerun on tune (contract v2, quote rule 2, num_predict 12288)

A new calibration as pre-registered (rnd d05a11e, 08ca419, 7565465), offrig main 751fb1d (sha256s above), run
14:25–16:12. Receipts: `results/2026-10-09-gemma-r2/`. `thinking.jsonl` stays in the scratch run directory:
it's untrusted model text and isn't committed.

| check | FA upper (< 0.10) | abstain (≤ 0.20) | decided BA (≥ 0.80) | missing (0) | rule |
|---|---|---|---|---|---|
| grounded | 0.026 (0/142) | **0.0745** (19/254) | 0.991 | **1** | **FAIL** |
| reasoning | 0.070 (3/121) | 0.059 (12/204) | 0.980 | 0 | **PASS** |

- **The prediction held.** Grounded abstain is 0.0745 against the 0.075 predicted from the quote-rule-2
  rescore, and false accepts stay at 0/142.
- **The chain's truncations:** three of the four now answer. `diff-role-os-23-11s` needed 8,937 tokens
  (prompt + reply), more than twice the old 4096 cap.
- **No context shift:** the largest prompt + reply was 8,937 of 16,384, and no claim reached the window.
- **Grounded's one miss is a thinking loop, not the budget.** In `prs-offrig-39-15s` (gold cannot_tell: "Record
  search returns only active records, with a default limit of 8 when none is given and a cap of 50"), the
  evidence for "limit" and for "active" is not contiguous. The verdict contract allows one quote, so gemma
  can't settle which span to cite. At 11% of its thinking it falls into a two-line loop, repeated 307 times,
  until num_predict 12288. That's deterministic at temperature 0, so no budget fixes it.
  - **offrig's response (the Publisher, decided):** contract v3, with 1–4 quotes per verdict (quote rule 3) and
    a streaming loop detector at n = 8 words, k = 40.
  - **The k = 40 threshold is gemma-derived from this run** (`loop_repeats_posthoc.py` →
    `results/2026-10-09-gemma-r2/loop-repeats.txt`). Clean replies peak at 12 (grounded) and 13 (reasoning)
    repeats, against 307 for the loop. It's enabled only for models with a false-hit check on record.
- **Under the split-case rule,** reasoning passing on tune triggers the registered **reasoning-only held-out run**
  (same binary and settings, `CAL_TYPES=reasoning`), which is its one held-out look under contract v2.
  Grounded has no held-out under v2; gemma's next grounded calibration is v3.

**The held-out run line, fixed before the run:**
`CAL_TYPES=reasoning CAL_EXTRA="--num-predict 12288 --keep-thinking" bash chain_step.sh /e/AI/rnd-calibrate-r2 gemma4:31b on on <rest> heldout`

(`CAL_TYPES` was added to `run_model.sh` and `chain_step.sh` for this. It changes which check types run, never
a setting.)

## Headline, 2026-10-09: gemma4:31b is offrig's default verifier for reasoning (held-out confirmed)

The registered reasoning-only held-out run (rnd c658ebf line, same binary 751fb1d and settings), run 16:28–17:16.
Receipts: `results/2026-10-09-gemma-r2/cal-gemma4_31b-reasoning-heldout/`.

| split | FA upper (< 0.10) | FA unsupported only | abstain (≤ 0.20) | decided BA (≥ 0.80) | missing | rule |
|---|---|---|---|---|---|---|
| tune | 0.070 (3/121) | 2/102 | 0.059 (12/204) | 0.980 | 0 | PASS |
| **held-out (headline)** | **0.077 (4/129)** | **0/108** | **0.070 (15/215)** | **0.982** | **0** | **PASS** |

- **Named, per the protocol's split-case rule:** gemma4:31b is offrig's default verifier **for reasoning only**.
  - **The setup:** verdict contract v2, think on, structured on, quote rule 2, num_predict 12288, num_ctx 16384,
    temperature 0, seed 0, model digest `6316f0629137…`, offrig 751fb1d.
  - **It must be served at exactly these settings** ("calibrate what is served").
  - Changing offrig's default is the Publisher's design path.
- **No context shift:** the max prompt + reply was 5,702 tokens.
- **Where its errors live:** on gold `cannot_tell` claims it accepted 4/21 (19%). Those make up the whole of the
  primary false-accept count (0/108 on unsupported). It's inside the rule, but the thing to watch in v3.
- **Grounded has no default.** It failed on tune by one deterministic thinking loop (above). Its next look is
  the v3 calibration (several quotes, a loop detector), with a fresh sealed split.
- **This held-out is spent:** a v3 reasoning default can't reuse it (the note of 15:27).

## Pre-registration, 2026-10-09 (evening), before any run: thinking off (post-hoc)

The post-hoc thinking-level runs named in the 04:20 amendment, under their own grant from the Publisher. They're
**post-hoc** (chosen after the chain and rerun results were seen), and the report says so.

- **Arms:** qwen3:8b, qwen3:14b and gemma4:31b, each at **`--think off`**, structured on, temperature 0, seed 0,
  on the **tune** split, both check types. They run smallest first, with a 15-minute rest before each load. No
  `low` arm: none of the three has a graded level that has been shown to be real (table above).
- **The binary (fixed before the run):** the installed offrig, main 9b6527f (#53), as installed by the
  Publisher. R&D hashed it before writing this, and the sha256 is the pin (`--version` still prints 1.0.0):
  - `offrig.exe` sha256 `AD3CED566E4BCB8DCC44B1D07672D7B2E8C173595821BF0F8E667A5E850D0E73`
  - `offrig-mcp.exe` sha256 `FCFDF1344A4F3D3DC206A720FC65D4F945441847AACBDDB0409CCCE6F3CC981B`

  It's re-hashed just before the run. A mismatch stops the run, and it's re-pinned here first.
- **Settings held to each model's think-on run, so thinking is the one variable that moves within a model:**

  | model | its think-on run | num_predict | num_ctx | quote rule (binary) |
  |---|---|---|---|---|
  | qwen3:8b, qwen3:14b | the chain (older binary) | 4096 | 16384 | 2 (rule 1 then) |
  | gemma4:31b | the rerun (751fb1d) | 12288 | 16384 | 2 (rule 2 then too) |

  `num_ctx` is passed as a fixed **16384**, never `auto`, so #53's adaptive window isn't a second variable. The
  quote rule and the binary still differ from the qwens' chain run. That's why the comparison below is on the
  model's own verdict.
- **The comparison (fixed now):**
  - **Primary: the model's own verdict, before the quote check.** Its scoring is the math ladder's
    `report.py --model-verdict` view. It's computed for off and for the matching on run, on identical tune
    claims. For each model, check type and level: accuracy, false accepts (the upper bound, as the default
    rule computes it), false rejects, cannot_tell rate, seconds per claim, and the unusable or missing count.
  - **Secondary: offrig's final verdict and the default rule,** reported beside the primary view. For gemma, on
    vs off on the final verdict is a near-like comparison: same quote rule, same budget, a newer binary. For
    the qwens it isn't like-for-like, and the report says so.
- **Is it really off?** For every off reply, the report gives eval tokens and checks that no thinking text came
  back. If a model still thinks at `off`, its arm is reported as "off not honoured" and isn't compared.
- **If an off arm passes the default rule on tune for a check type:** one held-out run for that type, same
  settings, under its own grant. It's labelled as selected post-hoc. A held-out fail names nothing.
  - gemma4:31b's reasoning default stays as named (think on) unless an off pass is also confirmed on held-out.
  - Even then, switching it is the Publisher's design call. Off would be cheaper per claim, not more accurate
    by definition.
- **What each outcome would mean, said before the result:**
  - Off at about the same accuracy and false accepts, and faster: thinking isn't earning its cost on this task,
    for that model.
  - Off with more false accepts: thinking is doing verifier work. Keep it on, and size the budget instead.
  - Off with fewer abstains but more false accepts: a trade, not a win. The default rule decides.
- **Run lines (fixed before the run;** scratch project `/e/AI/rnd-calibrate-off`, nothing shared with earlier
  stores):
  - `CAL_EXTRA="--num-predict 4096 --num-ctx 16384" bash chain_step.sh /e/AI/rnd-calibrate-off qwen3:8b off on 0 tune`
  - `CAL_EXTRA="--num-predict 4096 --num-ctx 16384" bash chain_step.sh /e/AI/rnd-calibrate-off qwen3:14b off on 900 tune`
  - `CAL_EXTRA="--num-predict 12288 --num-ctx 16384" bash chain_step.sh /e/AI/rnd-calibrate-off gemma4:31b off on 900 tune`

  The exit code of each step is read before the next one starts. Exit 3 stops the chain, and a resume uses the
  same line.
- **Run note, 20:12, after step 1 and before step 2** (a check fix, not a setting): step 1 (qwen3:8b) exited 3,
  "INCOMPLETE", but both runs are complete. Grounded attempted 270/270 and reasoning 223/223, and each
  `metrics.json` says `"status": "complete"`. `chain_step.sh` grepped offrig's report for the word
  "incomplete", and the 9b6527f binary prints a note containing that word in every report. It now reads each
  run's `metrics.json` status instead. That field still says `incomplete` for the known-stuck mistral runs.
  Per the Publisher's terms, the chain stopped and was reported before any change. Completeness is now
  run_model.sh's exit code plus `status == "complete"`, and a missing or unreadable metrics.json fails closed.
  This fixes the check only; no setting changed. Step 1's result stands as recorded and is not re-run.

## Result, 2026-10-09: thinking off (post hoc), tune

Run 20:06–21:41 under the Publisher's grant, offrig 9b6527f (sha256 re-hashed and matching), think off, num_ctx
16384. Receipts: `results/2026-10-09-thinking-off/`, with each run's manifest, metrics and verdicts and the step
logs. Two run notes:

- **Step 1's exit 3 was a false INCOMPLETE** (see the run note above).
- **gemma's grounded run left one claim with no outcome.** `cal-dedupe-t` had no verdict row and no error. It
  was finished under a separate short grant with offrig's resume (the registered path), and it answered
  correctly (supported). The no-outcome didn't recur, so no offrig defect is filed. "The first request raced
  the 31B load" remains a guess.

**offrig's default rule (final verdict):**

| model, think off | type | FA upper (< 0.10) | abstain (≤ 0.20) | decided BA (≥ 0.80) | missing | rule |
|---|---|---|---|---|---|---|
| qwen3:8b | grounded | 0.380 (43/143) | 0.275 | 0.785 | 0 | FAIL |
| | reasoning | 0.393 (37/121) | 0.251 | 0.742 | 1 | FAIL |
| qwen3:14b | grounded | 0.314 (34/143) | 0.141 | 0.859 | 0 | FAIL |
| | reasoning | 0.401 (38/121) | 0.157 | 0.786 | 0 | FAIL |
| gemma4:31b | grounded | **0.0697 (4/143)** | **0.086** | **0.980** | **0** | **PASS (post hoc)** |
| | reasoning | 0.115 (7/121) | 0.044 | 0.967 | 0 | FAIL |

**The pre-registered primary comparison: the model's own verdict, on vs off, on identical tune claims**
(`thinking-off-vs-on.svg`). "on" is the chain for the qwens and the rerun for gemma.

| model | type | FA on → off | FR on → off | median s/claim on → off | median eval tokens on → off |
|---|---|---|---|---|---|
| qwen3:8b | grounded | 12/127 → 56/128 | 3/126 → 3/127 | 1.77 → 0.56 | 356 → 111 |
| | reasoning | 12/102 → 42/102 | 3/101 → 10/101 | 2.42 → 0.73 | 463 → 125 |
| qwen3:14b | grounded | 6/128 → 39/128 | 1/127 → 1/127 | 2.65 → 0.98 | 337 → 124 |
| | reasoning | 16/102 → 37/102 | 5/102 → 8/102 | 3.27 → 1.12 | 394 → 128 |
| gemma4:31b | grounded | 0/128 → 4/128 | 2/127 → 1/127 | 9.70 → 2.91 | 517 → 140 |
| | reasoning | 2/102 → 6/102 | 1/102 → 0/102 | 11.44 → 4.36 | 576 → 174 |

**Reading it (each against the outcomes named before the run):**

- **Off was honoured** for every model: a median of 111–174 eval tokens, and no thinking text came back.
- **The qwens: "off with more false accepts".** Thinking is doing verifier work for them. Off accepts 3–6× more
  false claims, so keep thinking on and size the budget instead.
- **gemma4:31b: "off at about the same accuracy and false accepts, and faster".** It is 3.3× faster per claim,
  with a few more false accepts: 4 of 128 against 0 on grounded, and 6 against 2 on reasoning.
  - On grounded, off **passes** the rule, where on failed only on its one thinking loop.
  - On reasoning, off fails: an FA upper bound of 0.115 against on's 0.070 pass.
- **Model and thinking interact.** The bigger model loses much less without thinking. That's the evidence for a
  cascade (2026-10-09 study-swarm entry): a strong model run cheaply first, escalating only where needed.
- **What this does and doesn't establish:**
  - The grounded pass is selected post hoc. It names nothing until a fresh grounded held-out run confirms it
    (pre-registered below).
  - If confirmed, the defaults split by check type: reasoning = gemma think on (contract v2, its own settings
    line), grounded = gemma think off (its own settings line). Neither implies the other.
  - Neither is a teacher choice. The teacher bar is a separate test; 0.0697 sitting just under 0.07 is not a
    teacher result.

## Pre-registration, 2026-10-09 21:50, before any run: gemma4:31b think off, grounded held-out

- **What:** one run, `CAL_TYPES=grounded`, split `heldout`, gemma4:31b think off, structured on, temperature 0,
  seed 0.
- **Settings:** num_predict 12288, num_ctx 16384 fixed, quote rule 2 (in the binary).
- **Binary:** offrig 9b6527f, re-hashed before the run (sha256 `AD3CED56…0E73`, above).
- **Grounded's held-out split is unspent.** Nothing has passed grounded tune before, so this is its first look.
- **Rule:** offrig's default rule, unchanged. A pass names gemma4:31b think off as offrig's default verifier
  **for grounded only**, at exactly these settings. The Publisher wires defaults.
- **A fail names nothing.** Grounded keeps no default, the tune split stays spent for selection, and no further
  think-off tuning is chosen on it. Grounded's next look is the contract v3 calibration, on a fresh sealed
  split.
- **Incomplete runs:** one offrig resume is allowed for claims with no outcome (the registered path). A second
  no-outcome stops the run, and it's reported as an offrig defect.
- **Report:** the same columns as the reasoning headline (FA upper, FA on unsupported only, cannot_tell FA,
  abstain, BA, missing), plus seconds per claim. Any claim where prompt + reply reaches 16,384 is flagged.
- **Run line (fixed now; a separate grant from the Publisher; after the E1 re-run):**
  `CAL_EXTRA="--num-predict 12288 --num-ctx 16384" CAL_TYPES=grounded bash chain_step.sh /e/AI/rnd-calibrate-off gemma4:31b off on 900 heldout`

Promoted: not yet. The readouts-internal model-knowledge wave waits on the uncommitted 2026-09-29 edits in the readouts clone being settled (asked of the Director, 2026-10-09).

## Pre-registration, 2026-10-10 ~00:30, before any run: nemotron-3.5-lightning on tune (post hoc candidate)

The Director asked why Nemotron was never tried. There was no good reason: it was never on the candidate list.
It is added now, **before** the grounded held-out split is spent, so selection on tune finishes first. **The
gemma think-off grounded held-out run (pre-registered above) is on hold** until this result exists. The held-out
then goes to whichever grounded candidate is best on tune, under its own pre-registration written before it
runs.

- **Candidate:** `nemotron-3.5-lightning:latest`, local only, digest `e7a64ff15fb1`.
  - 32.9B `nemotron_h_moe` (a hybrid Mamba-Transformer MoE), Q4_K_M, 23.7 GiB, Ollama 0.35.1.
  - The `:cloud` Nemotrons are refused under Standing Rule 1.
  - **Licence:** NVIDIA Open Model License, not Apache-2.0. That rules it out as a distillation teacher under the
    Director's rule, but not as a verifier. The Publisher reads the licence terms before anything is named.
- **Arms:** tune split, both check types, at three thinking levels: **off**, **on** and **medium**. offrig's
  `--think` accepts `medium`, and the model lists levels false / true / medium.
  - **Is "medium" really different?** The graded-level check from the 04:20 amendment applies. If medium's
    median eval tokens are within 10% of on's on the same claims, the report says "medium = on for this model in
    this Ollama", and medium is not counted as its own level.
- **Settings, matching the gemma runs:**
  - offrig 9b6527f, re-hashed before the run (sha256 `AD3CED56…0E73`);
  - num_ctx 16384 fixed;
  - num_predict 12288 (thinking needs room; the same budget as gemma's);
  - quote rule 2, structured on, seed 0;
  - **temperature 0**.
- **Temperature:** the model's Ollama default is temperature 1 (top_p 0.95). offrig sends an explicit 0. In 9b6527f
  `ollama.rs` inserts `options.temperature` whenever it is set, and a unit test asserts `options.temperature ==
  0.0` in the request body. The manifest records it, and the report confirms it from each run's manifest.
- **Speculative decoding:** the model's defaults also carry `draft_num_predict 2`, an MTP/speculative draft.
  Under greedy decoding this doesn't change outputs. It's recorded here as a model default, not a setting.
- **Order:** off, then on, then medium, smallest replies first, each a chain step with a 900 s rest.
- **Stop rule:** as tonight. Each step's exit code plus `metrics.json` `status == "complete"`. A missing or
  unreadable status stops the chain and is reported. One offrig resume is allowed for no-outcome claims.
- **What counts:** offrig's default rule, per check type, as before. A pass is post hoc, because the candidate was
  added after seeing other results, and names nothing until a held-out confirmation, which spends a split. It is
  compared with gemma4:31b on the same tune claims, on the model's own verdict and the final verdict, with seconds
  per claim.
- **Run lines (fixed now; a separate grant from the Publisher):**
  - `CAL_EXTRA="--num-predict 12288 --num-ctx 16384" bash chain_step.sh /e/AI/rnd-calibrate-nemo nemotron-3.5-lightning:latest off on 0 tune`
  - `CAL_EXTRA="--num-predict 12288 --num-ctx 16384" bash chain_step.sh /e/AI/rnd-calibrate-nemo nemotron-3.5-lightning:latest on on 900 tune`
  - `CAL_EXTRA="--num-predict 12288 --num-ctx 16384" bash chain_step.sh /e/AI/rnd-calibrate-nemo nemotron-3.5-lightning:latest medium on 900 tune`
- **chain_step's model tag:** the tag contains `:` and `.`. `chain_step.sh` derives a directory tag by replacing
  `:` and `/`, giving `nemotron-3.5-lightning_latest`, which is a valid directory name.
