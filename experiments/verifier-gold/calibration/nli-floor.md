# The no-LLM verifier floor: the NLI cross-encoder, scored like the LLM candidates

Pre-registered 2026-10-09, before any NLI claim runs. This measures the floor under offrig's default-verifier
rule (offrig#44): how far a stock cross-encoder is from the LLM candidates, with no prompt engineering and no
thresholds. It is **not** a bid for the default; it prices the fine-tune step on the roadmap.

## What runs, pinned

- **Model:** `cross-encoder/nli-deberta-v3-base` @ `6c749ce3425cd33b46d187e45b92bbf96ee12ec7`, through
  OpenVINO (optimum-intel, `OVModelForSequenceClassification`), reshaped static at (batch 1, 512).
- **Device: the Intel iGPU** (found by name, as `npu_serve.py` does). Not the NPU: the probe's batch-8 NLI
  hung it with `DEVICE_LOST` (`experiments/npu-probe/results/2026-10-09-probe.json`), and batch 1 on the NPU
  was no faster than the CPU. Not the 5090: this lane never touches it.
- **Batch 1, plain softmax argmax. No score thresholds, no abstain gate, no prompt wrapper.** Introducing a
  threshold would be a second knob; the floor is the raw model.

## Claim → NLI pair

- **Premise:** the claim's `context` texts, joined with `"\n\n"` in the order the gold record lists them.
- **Hypothesis:** the claim text. Nothing else is added — no prefixes, no template.
- **Label map:** entailment → `supported`, contradiction → `unsupported`, neutral → `cannot_tell`. The map is
  the model's own `id2label` lowercased, asserted to be exactly these three.
- **Truncation:** the tokenizer's default pair truncation (`longest_first`) at 512, which cuts the premise's
  tail. The count of truncated claims is reported per split (computed by tokenizing untruncated first).

## Scoring — offrig's own metrics, reproduced

The scorer is a pure-Python reproduction of `calibrate::metrics` in offrig @ `0f8b1c4`
(`crates/offrig-core/src/calibrate.rs`), at `experiments/verifier-gold/calibration/calibrate_metrics.py`:

- Wilson 95% intervals, z = 1.959963984540054, `(0, 1)` when n = 0;
- primary false-accept rate: (gold unsupported + gold cannot_tell) judged supported, over all of them;
- the unsupported-only rate, the near-miss (`subtle`) rate, and the cannot_tell gold row;
- abstain: answered `cannot_tell` over gold supported + unsupported only (gold cannot_tell claims are out);
- decided balanced accuracy: mean of (supported right / supported decided) and (not-supported right /
  not-supported decided), where gold cannot_tell decided means judged `supported` (wrong) or `unsupported`
  (right);
- the default rule: missing == 0, unsupported_n ≥ 100, primary FA upper bound < 0.10, abstain ≤ 0.20,
  decided balanced accuracy ≥ 0.80.

The scorer carries a unit test against calibrate.rs's hand-computed case (240 claims: 6/140 primary FA,
2/100 unsupported-only, 1/10 subtle, cannot_tell row 4/10/26, abstain 7/200, balanced (95/96 + 105/111)/2,
rule passes), plus its two edge cases (10/40 cannot_tell accepts fail the rule; `cannot_tell` everywhere
gives abstain (200, 200) and no balanced score). Where the offrig binary supports it, the same outcome file
is also scored by `offrig verify calibrate --report-only` and the rows are diffed. No bootstrap anywhere in
this phase: the rule reads Wilson intervals on the rates, and the NLI answers every claim (unusable = 0 by
construction).

## Sets, splits, and the headline

Read-only gold (`experiments/verifier-gold/`), same sets the LLM candidates run:

| check type | split | supported | unsupported | cannot_tell | n |
|---|---|---|---|---|---|
| grounded (`grounded.jsonl` + `prs/grounded-prs.jsonl`) | tune | 127 | 128 | 15 | 270 |
| grounded | held-out | 112 | 113 | 5 | 230 |
| reasoning (`diffs/reasoning-diffs.jsonl`) | tune | 102 | 102 | 19 | 223 |
| reasoning | held-out | 107 | 108 | 21 | 236 |

Both splits run for both check types. **The held-out numbers are the headline,** matching the calibration
protocol (`README.md`): the floor is reported where it wasn't settled. Every metric row is reported,
including the cannot_tell row and the unsupported-only rate; strata `has_doc_comment`, `self_referential`
and `origin`; seconds per claim; truncated counts.

## The decision attached

The measurement prices roadmap step 3 (fine-tune the cross-encoder on the grounded tune split).

- If the NLI **passes the default rule on grounded tune**, it runs grounded held-out as confirmation — the
  same protocol as an LLM candidate — and earns the fine-tune PR.
- If it doesn't pass, the fork is on the gap to the cheapest LLM that passes grounded tune:
  **gap = (that LLM's grounded tune decided balanced accuracy) − (the NLI's).** A gap ≤ 0.10 earns the
  fine-tune PR; a wider gap reports the floor as a floor and closes the NLI line without one. If no LLM
  passes grounded tune, the gap is taken from the best grounded tune score among the LLM candidates, and the
  report says so.
- Reasoning runs and is reported in full, but is not part of the fork: whether an NLI's entailment semantics
  fit behaviour-diff claims is itself a question this measurement answers.
- Whatever the result, the NLI can answer only `supported` / `unsupported` / `cannot_tell` by construction,
  so its `unusable` count is 0 and `missing` is 0 unless the device fails.

## When it runs

After the overnight 5090 calibration chain, so its timings stay honest; the iGPU is otherwise free, and the
tokenizer's CPU load is minutes, not hours. The NLI legs need an iGPU window only — the NPU ledger is not
touched. Estimated runtime per leg from the probe's rate; the receipt records the wall clock.

## Amendments

(none yet — any change after the first claim runs lands here with its date and reason)
