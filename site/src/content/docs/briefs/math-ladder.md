---
title: Where does each model's arithmetic checking fall off?
description: A generated ladder of code-arithmetic claims, from one step to many. Thinking models hold to level 5; every model stumbles at an off-by-one cliff on big numbers.
date: 2026-10-09
status: measured
shelf: pending (readouts-internal model-knowledge)
---

## The question

The calibration says how often a model is fooled on average. The ladder asks where it starts being fooled. Each
level adds difficulty (more steps, operator precedence, traps, unit conversions, near-miss wrong answers) to
small generated functions whose true result is known by running them.

## What we found

- **Three ways to fail.** llama3.1:8b accepts: from level 5 it calls every false claim true.
  mistral-small:24b abstains. granite4.1:30b rejects true claims. The accuracy is similar, but the risk isn't:
  for a verifier, accepting false claims is the dangerous failure.
- **Thinking flattens the curve.** Both qwen3 models and gemma4:31b are perfect through level 5.
- **Level 6 is a precision cliff.** Converting bytes to MiB makes 7–10 digit answers, and the false claims are
  off by exactly one. The thinking models accept 768937860 for 768937861.
- **A cheap "check the last number" guard doesn't help.** It caught none of the qwen models' 16 false accepts.
  Running the code is the sure check.

![Math ladder: accuracy by level](/rnd/charts/math-ladder.svg)

## Caveats

- This chart scores the model's own verdict, before offrig's quote check. That is a post hoc view: the
  pre-registered table scores the final verdict, which on this ladder mostly measured the quote check (the code
  lines were shorter than its minimum quote length).
- mistral-small:24b's run is INCOMPLETE: one claim stuck on a server error, so it isn't drawn as a score.
- gemma4:31b ran at a 4,096-token reply limit, so its levels 7–8 lost claims to the limit. Those points are
  hollow: fewer than 30 claims, tentative.

## Receipts

`mcp-tool-shop-org/rnd`, `experiments/verifier-gold/math-ladder/`: `ladder.jsonl` (the gold), `report.py`, and
`results/2026-10-09-ladder/` (per-model runs and both report views).
