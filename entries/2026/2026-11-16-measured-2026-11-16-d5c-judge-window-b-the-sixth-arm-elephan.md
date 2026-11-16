---
id: 2026-11-16-measured-2026-11-16-d5c-judge-window-b-the-sixth-arm-elephan
title: Measured 2026-11-16: D5c judge window B, the sixth arm (elephant-1) fails the three-way bars
date: 2026-11-16
kind: finding
relevance: act
fields: [training]
tags: [judge-bakeoff, d5c]
---

## Summary

On 16 November 2026 a second paid Colab window (one G4 card, 749 s, 2.09 compute units) ran the sixth pre-registered judge arm over the D5c temporal set: elephant-1, asked to choose between "supported", "contradicted" and "can't tell". It answered 720 calls (360 items in two material orders) and was scored on the rig against sealed keys on the same held-out test split as window A (264 items, 88 per class). It fails the pre-registered three-way bars under both the strict rule and the order-averaged rule. With window A's five arms, all six arms of the comparison have now failed. These are counts only; no item text, prompt or key is published.

## Key points

Strict three-way accuracy on the 264 held-out items, with per-class recall (out of 88):

| Arm | Judge and prompt | Strict 3-way | Binary-collapsed | Supported | Contradicted | Can't tell | Order flips |
|---|---|---|---|---|---|---|---|
| 4 | elephant-1, choice, "contradicted" wording | 103 (0.390) | 0.723 | 16 | 1 | 86 | 33 |

- **The bars**, pre-registered and the same as window A's: PASS needs strict ≥ 225/264, binary-collapsed ≥ 0.90 and every class ≥ 71/88.
- **Under the order-averaged rule** the arm scores 123/264 (0.466) three-way and 0.777 binary-collapsed. That fails too.
- **It answers "can't tell" almost everywhere:**
  - of the 176 calls on gold-contradicted items, 163 came back "can't tell";
  - of the 176 calls on gold-supported items, 121 came back "can't tell";
  - it found 1 of 88 contradicted items, the lowest of the six arms (window A's generative arms found 4, 6, 9 and 12).
- **Plumbing was clean:**
  - 0 unparseable calls and 0 length stops in either order;
  - 0 invalid calls out of 528 scored, and 0 answers using a key outside the shown set;
  - the rows file's sha256 matched its completion record, and the rig's and the result archive's copies of the run records were byte-identical.
- **Much of this judge's probability sits outside the three offered answers.** The mean probability mass not on any of the three choice words was 0.548 per call (largest 0.792), and about the same whichever answer it gave. This is reported as measured; its cause has not been examined.
- **Item family:** as with window A's generative arms, "at most" items score better (strict 61/132) than "at least" items (42/132). Contradicted recall was 1/44 and 0/44.
- **Timing, for anyone planning a similar window:** building the judge's CUDA extension from source took 424 s, against an estimate of 90 to 240 s; the 720 calls took 77 s after a 15 s load, at a peak of 21,695 MiB of GPU memory.

## Studio relevance

- No judge and no wording in this six-arm set separates "contradicted" from "can't tell" on temporal claims. Adding another three-way choice arm is not the next step.
- The lead is unchanged from window A: the two-question format's ranking signal, with a cut-off fitted on a fresh calibration set and tested on a fresh held-out set under its own pre-registration, and a 27B-class judge scored on that same held-out set.
- `act`: these results gate which judge, if any, can check three-way claims in the studio's data pipelines. None can yet.

## Claims

- [unverified] elephant-1 fails the pre-registered D5c Task 2 bars on test_88 under both the strict and order-averaged rules: strict 103/264, order-averaged 123/264 (step-7 score report sha256 8fd5c450d42557b711b2ba73de754f6c5aeee3e1631c617394b27d6b61c238d4).
- [unverified] Its per-class recall is 16/88 supported, 1/88 contradicted and 86/88 can't tell, with 33 order flips.
- [unverified] The mean probability mass outside the three choice words is 0.548 per call (maximum 0.792).
- [unverified] The window cost 2.0910 Colab units over 749 s on one G4 card.

## Sources

- [primary] https://github.com/mcp-tool-shop-org/reasoning-dataset-lab — reasoning-dataset-lab; the judge kit the window ran (commit ed8b4e73, PRs #93, #99, #102, #103, #105)
- [rig] R&D run receipts (kept local): step-7 score report 8fd5c450…; rows file cba20d3e…; the window's pre-registration (five-arm window ce8e6b97…, with its arm-4 scoring and model-strings addenda), filed before the run; the scorer pins in force (addendum f83a31d0…)
- [rig] The window A finding in this library: `2026-11-15-measured-2026-11-15-d5c-judge-window-a-five-arms-all-fail-th`
