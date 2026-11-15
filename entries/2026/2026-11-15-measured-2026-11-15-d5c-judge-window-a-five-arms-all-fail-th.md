---
id: 2026-11-15-measured-2026-11-15-d5c-judge-window-a-five-arms-all-fail-th
title: Measured 2026-11-15: D5c judge window A, five arms, all fail the three-way bars
date: 2026-11-15
kind: finding
relevance: act
fields: [training]
tags: [judge-bakeoff, d5c]
---

## Summary

On 15 November 2026 a paid Colab window (one G4 card, 539 s, 1.50 compute units) ran five pre-registered judge arms over the D5c temporal set: three d3-mini prompt variants, the larger d3-flash, and one three-class NLI encoder. Each arm answered 720 calls (360 items in two material orders). The arms were scored on the rig against sealed keys on the held-out test split (264 items, 88 per class: supported, contradicted, can't tell). All five fail the pre-registered three-way bars under both the strict rule and the order-averaged rule. These are counts only; no item text, prompt or key is published.

## Key points

Strict three-way accuracy on the 264 held-out items, with per-class recall (out of 88):

| Arm | Judge and prompt | Strict 3-way | Binary-collapsed | Supported | Contradicted | Can't tell | Order flips |
|---|---|---|---|---|---|---|---|
| 1 | d3-mini, choice, "contradicted" wording | 120 (0.455) | 0.769 | 45 | 4 | 71 | 45 |
| 6 | d3-mini, choice, symmetric wording | 123 (0.466) | 0.765 | 46 | 6 | 71 | 44 |
| 2 | d3-mini, two yes/no questions, fixed 0.5 cut-off | 112 (0.424) | 0.682 | 61 | 9 | 42 | 88 |
| 3 | d3-flash, choice, "contradicted" wording | 124 (0.470) | 0.803 | 38 | 12 | 74 | 35 |
| 5 | DeBERTa-v3-large NLI encoder | 87 (0.330) | 0.655 | 7 | 80 | 0 | 24 |

- **The bars**, pre-registered: PASS needs strict ≥ 225/264, binary-collapsed ≥ 0.90 and every class ≥ 71/88. No arm comes close.
- **Plumbing was clean on every arm:**
  - 0 unparseable calls and 0 length stops in either order;
  - 0 answers using a key outside the arm's shown set (read from each row's raw answer);
  - 0 answers carrying an error field;
  - every rows file's sha256 matched its completion record.
- **Wording did not move d3-mini:**
  - An earlier window the same day (kit 2e6423fd, same items) used the label "unsupported" with a yes/no-style instruction, and found 3 of 88 contradicted items.
  - Arm 1 (the plain label "contradicted" and a choice instruction) found 4 of 88, and arm 6 (symmetric "proved true / proved false / undetermined") found 6 of 88.
  - Roughly 80% of gold-contradicted items still go to "can't tell".
- **Size helped a little:** d3-flash (8B) has the best binary-collapsed score (0.803) and finds 12 of 88 contradicted items. It collapses the same way.
- **Two questions carry ranking signal that the fixed cut-off wastes:**
  - The AUROC of the "must the claim be true?" probability is 0.904 (supported against not); for "must the claim be false?" it is 0.832 (contradicted against not).
  - At the pre-registered 0.5 cut-off, though, the second question rarely fires.
- **The NLI encoder fails the other way:** it calls nearly everything a contradiction and never "neutral" (0 of 88). Its pre-registered risk was the opposite, a collapse to neutral.
- **Item family matters:** the generative arms score much better on "at most" items (strict about 0.58–0.64) than on "at least" items (about 0.27–0.31).

## Studio relevance

- The "can't tell" collapse on contradicted claims belongs to these judges and this task, not to our label words. Changing the shown words is not the fix.
- The live lead is the two-question format's ranking signal.
  - A cut-off fitted on fresh data, never on this test split, is approved as the next step.
  - It will be fit on a new calibration set and tested on a new held-out set, under a new pre-registration.
  - A 27B-class judge (vllm-sr/d3) will be scored on the same new held-out set.
- elephant-1 (the sixth arm) runs separately.
- `act`: these results gate which judge, if any, can check three-way claims in the studio's data pipelines. None can yet.

## Claims

- [unverified] All five arms fail the pre-registered D5c Task 2 bars on test_88 under both the strict and order-averaged rules (step-7 score report sha256 03f531e1b90b3f98eb5e0beafb3eea39755eb79cc4ee6e3c08e85435f8ad9cea).
- [unverified] d3-mini's contradicted recall is 4/88 (arm 1), 6/88 (arm 6) and 9/88 (arm 2); d3-flash's is 12/88.
- [unverified] The two-question arm's item-mean AUROC is 0.904 for p(true) and 0.832 for p(false).
- [unverified] The window cost 1.5047 Colab units over 539 s on one G4 card.

## Sources

- [primary] https://github.com/mcp-tool-shop-org/reasoning-dataset-lab — reasoning-dataset-lab; the judge kit the window ran (commit 797ad7eb, PRs #88, #91, #92)
- [rig] R&D run receipts (kept local): step-7 score report 03f531e1…; rows files arm 1 7b5689ac…, arm 2 1bbe9de2…, arm 6 f17c05f2…, arm 5 02bda24f…, arm 3 9f9b80a4…; the window's pre-registrations (five-arm window ce8e6b97…, arm-6 addendum e5e3b550…), filed before the run
