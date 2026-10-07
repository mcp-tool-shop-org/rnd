---
id: 2026-10-07-small-label-decision-learning
title: Learning a decision from 100–200 labels — LLM presentation, baselines, active learning
date: 2026-10-07
kind: finding
relevance: act
fields: [machine-learning, evaluation, statistics]
tags: [tabular, llm, serialisation, tabpfn, logistic-regression, active-learning, few-shot, cross-validation, sense-si, jev]
---

## Summary

Raised by ai-jam-sessions / sense-si on 2026-10-07. A typed LLM decision model
("is this phrase clean?") read structured hearing records and scored Brier 0.25
after temperature scaling. That is no better than the base rate (about 0.24) on
124 single-listener labels.

At this sample size the literature says:

- run cheap tabular baselines beside the LLM, to tell "the evidence isn't there"
  apart from "the model can't read it";
- treat the LLM's input format as a variable to sweep, not a fixed choice;
- don't trust uncertainty sampling while the model has no signal.

## Key points

- **LLMs vs trees by sample size:** fine-tuned LLMs on serialised rows (TabLLM)
  match or beat XGBoost and logistic regression at about 4–32 labels. Trees and
  TabPFN win from roughly 256–512 labels. 100–200 sits in the crossover.
- **Format sensitivity:** meaning-preserving prompt-format changes moved few-shot
  accuracy by up to 76 points, and neither more shots nor a bigger model removed
  it (Sclar et al. 2024). Several serialisations must be tried and the spread
  reported.
- **LLM as feature engineer:** the LLM writes feature rules once and a linear
  model predicts (FeatLLM). It beat TabLLM by about 10% on average, with no
  per-row LLM call. LLMs can also rank useful features from names alone
  (LLM-Select), which is useful for pruning before serialising.
- **TabPFN** (Nature 2025) beat tuned baselines up to 10,000 rows with default
  settings and no tuning. It is the natural third comparator beside L2/L1
  logistic regression and a shallow GBDT.
- **Small-n evaluation:**
  - at n≈100 cross-validation error bars are about ±10 points, and fold
    standard errors understate them;
  - k-fold is biased at small n, while nested CV is not;
  - naive CV confidence intervals undercover;
  - model comparisons on repeated CV need the Nadeau–Bengio corrected variance.
- **Active learning:**
  - at low budgets uncertainty sampling is poor and random often wins: the
    cold-start problem, so prefer typical and diverse points (Hacohen et
    al. 2022);
  - for logistic regression, uncertainty sampling does fine overall but rarely
    crushes random (Yang & Loog 2018);
  - an actively chosen set may not transfer to a different model (Lowell et
    al. 2019).
- **In-context examples:**
  - choose examples by similarity to the test item, not uncertainty (Margatina
    et al. 2023; Liu et al. 2022);
  - demonstrations mainly teach format and label space (Min et al. 2022);
  - ablate the shot count rather than guessing it.

## Studio relevance

For the Jev / sense-si work:

1. Freeze the 124 labels as a development set. Report base-rate Brier with
   bootstrap and repeated-CV intervals. Differences under about 0.02 Brier are
   not resolvable at this n.
2. Run L2/L1 logistic regression, a depth-limited GBDT and default TabPFN with
   repeated stratified CV (Brier and log loss), compared with the
   Nadeau–Bengio correction.
3. Ablate by evidence family: timing, pitch, transcript, then the new join and
   pitch-artefact flags.
4. Rerun the LLM on the same folds, sweeping serialisation, the feature subset
   and the shot count. Try the FeatLLM pattern (LLM proposes features,
   logistic regression predicts).
5. Label the next 50–80 phrases in rounds of about 20: about 70% typical or
   diverse (cluster, pick representatives, cover under-represented types) and
   about 30% random. Hold out a purely random 20-phrase test set. Switch toward
   margin sampling from the baseline only once it beats the base rate.

**Measured confound (ai-jam-sessions PR #88, 2026-10-07): group by mix.** The 124
phrases come from 7 reviewed mixes. The cut-placement mix carries both the most
joins and the most marks, so pooled feature AUCs largely measure which mix a phrase
came from. Two features reverse sign once you look within a mix: F0 step at joins
(pooled 0.69, within-mix 0.37) and spectral jump (0.36 → 0.65). So:

- cross-validation must be **grouped by mix**: leave-one-mix-out, or stratified
  within mix;
- every AUC or Brier should be reported both pooled and as the within-mix mean;
- a model that only learns "which mix" will look good pooled and fail on a new
  mix.

Per-mix n is 16–20, so within-mix results are leads.

The listener's own consistency sets the ceiling for any model; see
[[2026-10-07-single-rater-labels-and-ai-listener]]. The missing evidence family
is covered in [[2026-10-07-join-artefact-detection]]. Calibration method is in
[[2026-10-07-calibrating-probabilistic-decision-layers]].

## Claims

- [unverified] TabLLM matches or beats XGBoost/LR at about 4–32 labels; trees and TabPFN lead from about 256–512 (numbers from a fetched summary).
- [unverified] Prompt-format changes moved few-shot accuracy by up to 76 points on LLaMA-2-13B.
- [unverified] FeatLLM beat TabLLM by about 10% on average.
- [unverified] At low budgets random sampling often beats uncertainty sampling (image experiments).
- [unverified] Liu et al. 2022 arXiv ID (2101.06804) was recalled, not confirmed.

## Sources

- [primary] https://proceedings.mlr.press/v206/hegselmann23a.html — Hegselmann et al., "TabLLM", AISTATS 2023 (arXiv 2210.10723)
- [primary] https://arxiv.org/html/2310.11324v2 — Sclar, Choi, Tsvetkov, Suhr, "Quantifying Language Models' Sensitivity to Spurious Features in Prompt Design", ICLR 2024
- [primary] https://arxiv.org/abs/2305.13062v5 — Sui et al., "Table Meets LLM", WSDM 2024
- [primary] https://arxiv.org/pdf/2310.10358 — Singha et al. 2023, table serialisation formats
- [primary] https://arxiv.org/pdf/2402.17944 — Fang et al., "Large Language Models on Tabular Data: A Survey", TMLR 2024
- [primary] https://proceedings.mlr.press/v235/han24f.html — Han, Yoon, Arik, Pfister, "FeatLLM", ICML 2024
- [primary] https://arxiv.org/abs/2407.02694 — Jeong et al., "LLM-Select", TMLR 2025
- [primary] https://arxiv.org/abs/2508.17391 — Pavlidis et al. 2025, frontier LLMs as tabular baselines
- [primary] https://arxiv.org/abs/2305.14975v1 — Tian et al., verbalised confidence calibration, EMNLP 2023
- [primary] https://pubmed.ncbi.nlm.nih.gov/39780007/ — Hollmann et al., "Accurate predictions on small data with a tabular foundation model" (TabPFN), Nature 2025
- [primary] https://arxiv.org/html/2506.16791v4 — "TabArena", NeurIPS 2025 D&B
- [primary] https://arxiv.org/abs/2207.08815v1 — Grinsztajn, Oyallon, Varoquaux, tree models on tabular data, NeurIPS 2022
- [primary] https://arxiv.org/pdf/1706.07581 — Varoquaux, "Cross-validation failure: small sample sizes lead to large error bars", NeuroImage 2018
- [primary] https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6837442/ — Vabalas et al., small-sample CV bias, PLoS ONE 2019
- [primary] https://arxiv.org/abs/2104.00673 — Bates, Hastie, Tibshirani, CV confidence intervals, JASA 2024
- [secondary] https://search.r-project.org/CRAN/refmans/MachineShop/html/t.test.html — Nadeau & Bengio corrected variance (secondary page; original Machine Learning 2003)
- [primary] https://ar5iv.labs.arxiv.org/html/2202.02794 — Hacohen, Dekel, Weinshall, "Active Learning on a Budget", ICML 2022
- [primary] https://arxiv.org/pdf/1611.08618 — Yang & Loog, active learning for logistic regression benchmark, Pattern Recognition 2018
- [primary] https://arxiv.org/abs/1807.04801 — Lowell, Lipton, Wallace, actively acquired data transfer, EMNLP 2019
- [primary] https://arxiv.org/abs/2305.14264v1 — Margatina et al., "Active Learning Principles for In-Context Learning", Findings of EMNLP 2023
- [primary] https://aclanthology.org/2022.deelio-1.10/ — Liu et al., "What Makes Good In-Context Examples for GPT-3?", DeeLIO 2022
- [primary] https://arxiv.org/pdf/2202.12837 — Min et al., role of demonstrations, EMNLP 2022
- [user] Question from the ai-jam-sessions session, 2026-10-07; research agent (claude-sonnet-5-5) web search
