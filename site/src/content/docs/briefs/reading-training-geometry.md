---
title: What ScalarScope's training-geometry views can and can't tell you
description: Two caveats for reading ASPIRE's training runs in ScalarScope. Step-by-step comparisons fire on seed noise alone, and drift comparisons measure the scoring teacher rather than the run.
date: 2026-10-08
status: measured
shelf: pending (readouts-internal training-knowledge)
---

## The question

ScalarScope draws how a training run's evaluator geometry changes, and flags when two runs differ. Before using
those flags to compare ASPIRE's training setups, we checked what actually makes them fire.

## What we found

- **Step-by-step comparisons fire on noise.** Two seeds of the *same* training setup trip the "runs differ"
  flags. In one setup the stretch flag stays on for 28 steps, from seed alone. So a step-by-step difference
  between two setups means nothing without repeat seeds.
- **Checkpoint ("drift") comparisons agree across seeds,** so they don't have that problem. But with each
  item's score held fixed, two training setups scored by the same teacher give identical spectra: the
  difference is 0.000 at every checkpoint. Two different teachers differ by about 0.16–0.18. **A drift
  difference tells you which teacher scored, not how the run trained.**
- **Two defects fixed:**
  - Opening an older saved bundle showed a verdict recomputed under today's rules instead of the one saved in
    it.
  - A bundle's manifest said it held no raw data when it stored both runs in full.

## Caveats

- These are properties of the views, pinned by tests on a small set of ASPIRE exports (seeds 43 and 44).
- A further claim (that mean-centred PCA hides the fine-tune's drift offset) is only in a pull-request
  description, with no committed receipt, so it isn't included.

## Receipts

`mcp-tool-shop-org/scalarscope`:

- `rust/tests/aspire_export_tests.rs` and the fixtures under `rust/tests/fixtures/aspire-si/` (commits 599a5d5,
  a01dd88, acaf17f);
- `rust/tests/bundle_tests.rs` with a real 3.1.0-saved bundle (0b37f92, 1969680).
