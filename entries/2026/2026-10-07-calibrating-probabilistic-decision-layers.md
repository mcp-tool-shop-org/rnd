---
id: 2026-10-07-calibrating-probabilistic-decision-layers
title: Calibrating a probabilistic decision layer against one reviewer's marks
date: 2026-10-07
kind: finding
relevance: act
fields: [machine-learning, statistics, evaluation]
tags: [calibration, ece, brier, conformal-prediction, selective-prediction, abstention, sense-si, jev]
---

## Summary

How to calibrate and evaluate a layer that answers typed questions with
probabilities (never pass/fail) when the labels are a small set of review marks
from one expert, and how to set a "too close to call" band. The short answer:
small-n-safe metrics with bootstrap intervals, a one- or two-parameter
recalibration, and an abstention band chosen by a fixed rule on held-out data.

## Key points

- Binned ECE is biased and needs far more samples than it appears to; with tens
  of items use 3–5 bins or prefer other measures (Kumar et al. 2019).
- Report the Brier score with a bootstrap interval; its reliability/resolution
  decomposition is biased on small samples (Ferro & Fricker 2012).
- Draw reliability diagrams with CORP (isotonic, data-driven bins and resampled
  bands) instead of fixed bins (Dimitriadis, Gneiting & Jordan 2021).
- Recalibration by overfit risk, lowest first: temperature scaling (1 parameter),
  Platt (2), beta calibration (3), isotonic (many). Below about 100 labels, use
  temperature or Platt only (Guo et al. 2017; Kull et al. 2017; Niculescu-Mizil &
  Caruana 2005).
- Abstention band, two principled routes:
  - selective prediction: sweep the band, plot risk against coverage, and take the
    narrowest band whose upper confidence bound meets the target risk (Geifman &
    El-Yaniv 2017);
  - split conformal prediction: for a yes/no question, a prediction set containing
    both labels is a principled "too close to call" (Angelopoulos & Bates 2021).
    The coverage guarantee is on average; at n ≈ 30 realised coverage swings
    widely, at n ≈ 100 it tightens (Hulsman 2022).
- Label noise from one reviewer: random inconsistency makes conformal sets
  conservatively wider; systematic bias shifts them, and nothing here can detect
  bias from a single rater (Einbinder et al. 2022).

## Studio relevance

For sense-si's Jev calibration (budget $0.25):

1. Fix the band rule before looking at test items.
2. Split the marks (or use repeated k-fold).
3. Fit temperature or Platt only.
4. Report Brier with a bootstrap interval and a CORP diagram.
5. Choose the band by risk–coverage, or use conformal sets for the yes/no
   questions.
6. Put bootstrap intervals on the band edges. If they swing, the data does not
   yet support a band.

To get a noise ceiling, the Director re-marks a random 20–30% of items blind,
weeks later, and the layer reports intra-rater kappa. Do not expect the layer to
beat that ceiling. The re-marking and the kappa step are a recommendation, not a
cited finding.

## Claims

- [unverified] The standard binned ECE estimator is biased; a debiased estimator needs O(√B) rather than O(B) samples.
- [unverified] Temperature scaling, one parameter, is effective at recalibrating modern neural networks.
- [unverified] Isotonic recalibration overfits on small datasets; beta calibration stays near identity for already-calibrated models.
- [unverified] Conformal coverage holds under dispersive label noise (it over-covers).
- [unverified] Ferro & Fricker authorship and venue were recalled, not read; the title and abstract were confirmed.

## Sources

- [primary] https://arxiv.org/abs/1909.10155 — Kumar, Liang, Ma, "Verified Uncertainty Calibration", NeurIPS 2019
- [primary] https://ore.exeter.ac.uk/repository/handle/10871/8503 — Ferro & Fricker, "A bias-corrected decomposition of the Brier score", QJRMS 2012
- [primary] https://arxiv.org/abs/2008.03033 — Dimitriadis, Gneiting, Jordan, "Evaluating probabilistic classifiers: Reliability diagrams and score decompositions revisited", PNAS 2021
- [primary] https://arxiv.org/abs/1706.04599 — Guo, Pleiss, Sun, Weinberger, "On Calibration of Modern Neural Networks", ICML 2017
- [primary] https://mlanthology.org/icml/2005/niculescumizil2005icml-predicting — Niculescu-Mizil & Caruana, "Predicting Good Probabilities with Supervised Learning", ICML 2005
- [primary] https://proceedings.mlr.press/v54/kull17a — Kull, Silva Filho, Flach, "Beta calibration", AISTATS 2017
- [primary] https://arxiv.org/abs/1705.08500 — Geifman & El-Yaniv, "Selective Classification for Deep Neural Networks", NeurIPS 2017
- [primary] https://arxiv.org/abs/2107.07511 — Angelopoulos & Bates, "A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification"
- [primary] https://arxiv.org/abs/2210.14735 — Hulsman, "Distribution-Free Finite-Sample Guarantees and Split Conformal Prediction", 2022
- [primary] https://arxiv.org/abs/2209.14295 — Einbinder et al., "Label Noise Robustness of Conformal Prediction", 2022
- [user] Question from the ai-jam-sessions session, 2026-10-07; research agent (claude-sonnet-5-5) web search
