# Pre-registered tuning grid — judge knobs

**Written 2026-10-08, before any tune-half run.** The configurations, decision
rules and stop rules below are the confirmatory set. Anything run outside
this grid, or any change made after the first tune-half run starts, is
exploratory and is logged in the amendments section at the bottom — its
results do not count for or against these decisions.

This grid covers steps 2–5 of the tuning plan in the 2026-10-08 consult
brief: numbered prompts, logprob confidence, a second-pass verifier, and the
muse thinking-level dial.

## 0. Bench and split

- **Bench:** the 95 answers with adjudicated gold labels (`data/gold.json`:
  59 error / 36 clean answers; 84 error sentences marked by both passes, 63
  of them clear).
- **Split: FROZEN 2026-10-08 in `data/split.json`** (before any tune-half run),
  by `make_split.py create` (seed 20261008). 53 tune / 42 report, stratified by
  - topic area (the 12 aspire-si areas),
  - gold verdict (error / clean),
  - error-sentence count band (0 / 1 / 2+),
  - and so that the 10 blind re-label items sit in the **report** half.
- Each cell assigns ceil(n/2) to tune; the 10 pins occupy report slots, so the
  halves are 53/42 rather than 48/47. Verdict mix: tune 32/21, report 27/15.
- Structural note: verdict and band cannot be balanced jointly — every gold
  clean answer has zero error sentences, so all band-1/2+ items are errors.
- Each answer has its own question, so answer-level splitting does not leak
  questions across halves; topic-area stratification guards the weaker
  topic-level correlation.
- **Fully held out, not touched by any step here:** the report half and the
  31 correction pairs (`data/corrections.json`).
- **Integrity:** `make_split.py check` recomputes the split and fails if
  `split.json`, its self-hash, or any input file has changed. Overwriting the
  split is refused; changing it means deleting the file by agreement and
  logging an amendment below.
- Baselines under the old quoted-sentence prompt (P1) for the original four
  judges are recomputed on the tune-half subset from the existing
  `data/screen.json` / `data/screen_extra.json` — no GPU needed.

## 1. Fixed protocol for every arm

| setting | value |
|---|---|
| temperature | 0, with the fixed seed recorded per run |
| items per call | one |
| prompt | purpose + criteria + worked examples drawn from **outside** the 95 |
| output | JSON schema S1: `reasoning` (string) **before** `flags: [{index, claim}]`; no quotes of answer text |
| sentences | numbered in the prompt; judges return indices |
| `num_predict` | 16,000 floor for thinking models (final after the gemma 16k rerun lands); 4,096 for non-thinking reasoning-first models |
| `num_ctx` | current per-model values, recorded per run |
| `keep_alive` | on between calls within a run |
| GPU | one model at a time, each run granted by the Publisher |
| models | pinned digests; names containing "cloud" refused (as in `build.py`) |

**Abstain rule.** A call ending `finish_reason=length` or with an unparsable
reply is **abstain**, never scored as "no errors". Abstains count against
recall (the answer's errors still exist) and are excluded from the precision
denominator. The abstain rate is reported per judge per arm; a judge with
more than 10% abstains in an arm invalidates that arm, and the budget fix is
logged as an amendment.

**Per-call record:** model + digest, parameter hash, prompt hash, latency,
`finish_reason`, prompt/completion token counts, raw reply.

**Noise-floor check (runs before step 2):** one judge (muse-glimmer, think
high) run twice on the tune half under identical settings. Verdict flips
between the two runs set the noise floor; any decision margin below the
observed flip rate is read as noise, however the numbers look.

## 2. Step 2 — numbered-prompt re-baseline (arms S2)

One arm per judge, on the tune half, prompt P2 (numbered sentences, indices
back) under the fixed protocol:

| arm | model (pinned digest) | think | think level |
|---|---|---|---|
| S2-gemma | gemma4:31b (6316f0629137) | on | — |
| S2-muse | muse-glimmer (de878ce33ad8) | on | high |
| S2-nemotron | nemotron-3.5-lightning (e7a64ff15fb1) | `true` | — |
| S2-mistral | mistral-small:24b (8039dd90c113) | n/a | — |
| S2-granite | granite4.1:30b (3f3e5df8a021) | n/a | — |

Nemotron's `medium` level is exploratory, not scored against the rule.

**Decision rule (per judge):** adopt P2 for judge *j* if tune-half
answer-level recall is non-inferior to the P1 baseline within 3 points
absolute, and precision is no more than 3 points worse. For gemma
additionally require the correct-sentence rate on flagged error answers to
rise by at least 5 points (its known weakness). A judge failing the rule
keeps P1, and steps 3–5 run for it under P1.

## 3. Step 3 — logprob confidence (analysis S3)

- **Feasibility check first:** confirm Ollama 0.35 returns `logprobs` /
  `top_logprobs=5` through the Publisher path, on one call, before relying on
  it.
- **Capture:** piggybacked on the S2 runs (declared here, in advance) for
  every judge that returns them. No extra GPU time.
- **Signal:** probability of the answer-level verdict token; per-flag
  probabilities secondary.
- **Saturation check (per judge):** if ≥ 80% of verdict probabilities are
  ≥ 0.99, logprobs are declared saturated for that judge. Fallback:
  probability of the first reasoning token. If that also saturates,
  confidence for that judge is deferred to self-consistency (not in this
  grid).
- **Threshold selection:** per judge, τ chosen on the tune half to maximise
  answer-level F1, ties broken toward higher recall.

**Decision rule (per judge):** adopt τ only if thresholding lifts
answer-level F1 by at least 5 points over the untuned yes/no on the tune
half. Otherwise report the plain verdict.

## 4. Step 4 — second-pass verifier (arm S4)

- **Verifier:** muse-glimmer, think high — one verifier for flags from **all**
  judges, so verifier quality is uniform and not confounded with judge
  identity.
- **Input:** numbered answer + flagged index + the judge's claim. Schema:
  `reasoning` then `{real_error: bool, correction: string}`. `num_predict`
  4,096. Temperature 0, same seed.
- **Volume:** one call per S2 flag, tune half only.
- **Known risk, declared:** muse verifying its own flags is
  self-corroboration. Mitigation: per-judge breakdown reported; if the pooled
  rule below passes only on muse's own flags, that is an exploratory finding,
  not adoption.

**Decision rule:** a flag survives iff `real_error` is true. Adopt the
verification stage if, pooled over judges on the tune half, answer-level
precision rises ≥ 5 points and recall falls ≤ 3 points (sentence level
reported secondarily). Correction strings are banked, not scored, until the
held-out check.

## 5. Step 5 — muse thinking-level dial (arms S5)

Three arms on the tune half, everything else identical to S2-muse:

| arm | think level |
|---|---|
| S5-low | low |
| S5-medium | medium |
| S5-high | high (already run as S2-muse; reuse) |

`max` is exploratory only.

**Decision rule:** adopt the **lowest** level whose answer-level recall is
within 3 points of high's **and** whose error-sentence recall (both-pass
sentences) is within 5 points of high's. If low fails, test medium against
the same margins. Latency per level is recorded to reprice future sweeps.

## 6. Evaluation and reporting

- **Primary:** answer-level precision and recall against gold verdicts.
- **Secondary:** sentence-level recall on the both-pass error sentences (84
  full-set; tune-half subset per split) and on the clear subset.
- **Intervals:** bootstrap over answers, 95% (same convention as the screen
  readout). With ~47 items per half the intervals will be wide, and the
  report says so.
- **Sequencing:** noise-floor check → S2 → S3 (analysis only) → S4 → S5.
  Adopted settings carry forward into later steps.
- **Final confirmatory run, once, after the grid closes:** the frozen
  configuration on the report half, then the 31 correction pairs as the
  reversed control. No knob moves after the report half is seen.
- **GPU budget:** S2 = 5 runs × ~47 items; S3 = none; S4 = one call per flag;
  S5 = 2 extra muse runs. Priced per judge once the gemma 16k rerun lands.

## Amendments

- **2026-10-08 (pre-run):** the split was frozen the same day via
  `make_split.py` → `data/split.json` (53/42, not the sketched ~47/48: the 10
  pins occupy report slots and small clean cells round against report).
  Added the integrity rule (create refuses overwrite; check verifies inputs
  and self-hash). Nemotron's digest pinned to e7a64ff15fb1 per `build.py`.
  No tuning run had started, so this is a registration edit, not a
  post-hoc change.
- **2026-10-08 (pre-run, R&D, after reading the four reviews: Google, Gemini, Kimi K3, Grok):**
  1. **The output schema for P2 (supersedes S1 in section 1):**
     - one verdict per numbered sentence, `{"sentences": [{"n": int, "verdict": "error"|"ok"}]}`,
       with `claim` required on rows marked error;
     - the code checks one row per sentence and that `n` is a permutation of 1..N; anything else is
       an abstain, retried once;
     - reason: with a flags list, the empty list is the shortest valid reply, which is how
       muse-glimmer collapsed under `format: json`; a per-sentence verdict cannot collapse
       silently.
     - Thinking models (gemma4, muse-glimmer, nemotron) get no `reasoning` field, since their
       reasoning is already in `message.thinking` and would spend the shared `num_predict` twice.
       Non-thinking models (mistral, granite) keep `reasoning` first.
     - muse-glimmer stays on plain text plus a code-side parse of the same shape. Under Ollama's
       grammar it collapsed before, so a 2-item schema pilot on muse runs before it is put under
       `format`.
  2. **Verifier (step 4):** cross-family, not muse-only. muse verifies the flags of gemma,
     nemotron, mistral and granite; gemma4 (thinking) verifies muse's flags. Self-corroboration is
     designed out instead of reported.
  3. **`num_predict` floor:** 16,000 for gemma4 is confirmed by the pilot (6000 truncated 3/3;
     16000 finished 3/3 at about 124 s per answer, 26.0 GB peak at num_ctx 24576).
  4. **README "context-rich re-screen" plan withdrawn:** its full-95 run and its 20-answer sample
     (which includes report-half items) are superseded by this grid. All tuning-stage runs use the
     tune half only. The 3-answer pilot used n000–n002, all tune half.
  5. **Muse family caveat:** muse-glimmer is Meta, as is llama3.1:8b, which wrote the answers.
     Self-preference (Panickssery et al. 2024, arXiv 2404.13076) may make it lenient or sharp on
     its own family. Its results are reported with that caveat and not discounted by formula.
  6. **Performance knobs** (KV-cache quantisation, flash attention, speculative muse) stay out of
     the grid. They change the Ollama server's environment for every session on the rig, so they
     are scheduled with the Publisher after the scoring config is frozen.
