---
title: Which local model can check claims for offrig?
description: Six local models calibrated as claim verifiers on 2026-10-09. gemma4:31b with thinking on is the default for reasoning claims; with thinking off it passed grounded claims on tune, pending a held-out check.
date: 2026-10-09
status: confirmed (reasoning) · interim (grounded, think off passed tune)
shelf: pending (readouts-internal model-knowledge)
---

## The question

offrig's `verify` step asks a local model whether a claim about code is supported by the evidence. We needed a
default model that is rarely fooled, rarely abstains and is accurate when it does decide. The rule was fixed
before any run:

- the upper end of the 95% interval for false accepts is under 0.10;
- it abstains on at most 20% of claims;
- its balanced accuracy on the claims it decides is at least 0.80;
- no claim is left missing (truncated or unusable).

Two kinds of claim are checked separately: **grounded** (is this sentence about the code true?) and
**reasoning** (does this conclusion follow from the change?). The gold set was built for this: every label was
assigned blind, and a cross-family check found and fixed 2 wrong labels in 120.

## What we found

- **No model passed in the first six-model run.** The models without thinking (llama3.1:8b, mistral-small:24b,
  granite4.1:30b) were fooled most. The thinking qwen3 models were fooled less but abstained too often.
- **gemma4:31b was fooled almost never,** but missed on four replies cut off at the 4,096-token reply limit
  while it was still thinking.
- **Rerun with a bigger reply budget (12,288) and offrig's quote rule 2:** reasoning passed on the tune split,
  then passed on the held-out split. That makes gemma4:31b offrig's default verifier **for reasoning claims
  only**, at exactly the calibrated settings.
- **Grounded still has no default.** One claim sent gemma into a thinking loop: it couldn't choose which of two
  separate passages to quote, because the contract allowed only one quote. It repeated two lines 307 times.
  offrig's next contract allows up to four quotes and adds a loop detector.

- **With thinking off, the same tune claims, post hoc:** the qwen3 models accepted 3–6× more false claims, so
  thinking is doing real work for them. gemma4:31b lost little: it was 3.3× faster, with 4 false accepts of 128
  instead of 0 on grounded claims. With thinking off, it **passed the rule on grounded claims**, the first
  grounded pass of any model. Because we chose to look at it after seeing the results, it names nothing until a
  held-out run confirms it (pre-registered, separate grant). On reasoning claims it narrowly failed with
  thinking off.

![Thinking on vs off, same claims](/rnd/charts/thinking-off-vs-on.svg)

![Calibration, grounded claims](/rnd/charts/calibration-grounded.svg)

![Calibration, reasoning claims](/rnd/charts/calibration-reasoning.svg)

![The reasoning default, tune vs held-out](/rnd/charts/reasoning-default.svg)

![Repeated 8-word runs per reply: clean replies vs the loop](/rnd/charts/loop-repeats.svg)

## Caveats

- The two calibrations used different offrig builds, quote rules and reply budgets. They are separate
  results, never one run that improved.
- The held-out split for reasoning under this contract has now been used. A default under the next contract
  needs a fresh sealed split.
- All four held-out false accepts were on claims whose right answer is "cannot tell" (4 of 21). None of 108
  false claims was accepted.
- gemma4:31b is the default verifier, not the teacher for a distilled verifier. It narrowly misses the stricter
  teacher bar.
- The loop detector's threshold (40 repeats) was derived from this one model's replies.

## Receipts

`mcp-tool-shop-org/rnd`, `experiments/verifier-gold/calibration/`: the README's pre-registrations and results
(rnd 1.1.4.3.28–1.1.4.3.37 and the thinking-off result), and `results/2026-10-09-chain/`, `results/2026-10-09-gemma-r2/` and
`results/2026-10-09-thinking-off/` (each run's
manifest, metrics and verdicts). Chart inputs and their sha256 are in `experiments/charts/manifest.json`.
