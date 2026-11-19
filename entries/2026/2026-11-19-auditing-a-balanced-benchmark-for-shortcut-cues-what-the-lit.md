---
id: 2026-11-19-auditing-a-balanced-benchmark-for-shortcut-cues-what-the-lit
title: Auditing a balanced benchmark for shortcut cues: what the literature and a simulation say about the d5c pool audit
date: 2026-11-19
kind: finding
relevance: act
fields: [evaluation, benchmarks]
tags: [d5c, shortcut-audit, permutation-test, selection-bias, study-swarm, seed-36, seed-37]
---

## Summary

d5c is the studio's test for comparing local models as judges on three-way verification (supported, unsupported,
cannot tell). Its items are generated in triads over shared facts, and a selection step balances a list of surface
features across the three classes. Before a test pool is sealed, an audit runs a permutation test on about 600
feature-against-label associations to decide whether a surface cue gives the label away.

R&D asked four research agents what the literature says about that audit, checked the citations that carry weight,
and ran a simulation of the audit's own statistics code on synthetic data. The agents answered from memory, so
their reports are `[aggregator]` output. The result: most of the design holds, one real gap was found in how the
audit treats data that has already been selected, and the audit's detection limit now has a first estimate from
simulation. The pre-registration was amended (Note 13) before any verdict pool existed. An independent review by a
model from another family (Gemini 4 Carbon) corrected several statements before this entry was merged.

Two Gemini Deep Research seeds and two consults were planted on the open questions on 2026-11-19. This entry will be
updated when they are harvested.

## Key points

- **The permutation p-value counts the observed labelling.** The audit reports (b+1)/(B+1) with B = 2,000
  permutations, so a p-value is never zero. Phipson and Smyth's abstract says p-values that leave the observed
  statistic out are understated by about 1/m for m permutations. At p = 0.05 the Monte Carlo error is about ±0.005
  (one standard deviation).
- **Pooling replicates beats requiring every replicate to flag.** An earlier d5c rule flagged a cue only if it was
  flagged on all five seeds at 30 permutations each. That rule had almost no power, and it had already been
  replaced by a pooled test.
- **The chi-square scale held up in simulation, for well-filled tables.** The audit compares tests with very
  different numbers of levels by their chi-square tail. In the simulation half of the 608 tests were single
  features (2 to 12 levels) and half were the same features crossed with an 11-level cell. Over 2,000 permutations
  of one run, single-feature tests were the family's most extreme statistic 0.49 of the time (0.50 would be even).
  Standardising each test by its own permutation mean and standard deviation (a z-score) gave 0.91: the few-level
  tests dominated, as their skew predicts. Sparse tables, where expected counts fall below one, were not simulated
  and are the known weak point of a chi-square scale; real pools have them.
- **A selected dataset breaks the shuffle's assumption.** The selection step balances about 20 features. The audit's
  shuffle holds only four of them fixed. So shuffled labels do not look like data the selection would have
  produced. The main effect is on every test that is correlated with the balanced features, the learned probe
  included: the shuffle gives those tests their full null spread, while selection has removed part of it from the
  real pool. They are expected to be conservative, so the audit can miss cues a selection-aware test would catch.
  The balanced tests also take null maxima the real pool cannot reach, but that moves the family threshold very
  little.
- **One case can go the other way.** The selected-pool shuffle moves labels between triads. For a feature that is
  negatively correlated inside a triad (say exactly one of the three claims carries it), such a shuffle
  underestimates the null spread and can flag too often. This came from an AI Studio consult (Gemini 4 Carbon) and
  the shuffle's behaviour was confirmed in our code; how common such features are in d5c is not yet measured.
- **A first estimate of the detection limit: about +0.03 accuracy lift for a common binary cue.** With a 608-test
  family on 3,168 items, a planted binary cue present on about half the items was flagged 27% of the time at lift
  +0.018, 70% at +0.026, 90% at +0.031 and 100% at +0.041. These are 30 replicates per point on independent noise
  features, so each rate carries a wide interval (70% is 51% to 85%). Cues with many levels need more lift. In this
  simulation the +0.02 effect floor never decided an outcome.
- **The effect floor can block a rare, pure cue.** A feature present on 48 of 3,168 items, all of one class, lifts
  lookup accuracy by only 48/3,168 = +0.015. It would be overwhelmingly significant and still not flagged. The
  independent review raised this; R&D re-did the arithmetic.
- **Balancing a fixed list of features leaves the unlisted ones.** Schwartz and Stanovsky argue that models keep
  finding smaller correlations after balancing. Feng, Wallace and Boyd-Graber show that a clean partial-input
  baseline does not prove a dataset has no artifacts.
- **Six judges on about 1,000 triads will give tiers, not a full order.** One agent estimated this from sample size
  alone. It is not yet checked against d5c's own scoring; seed 37 asks the question properly.

## Studio relevance

### What it contradicts in our design (read first)

| Finding | d5c today | Decision |
|---|---|---|
| After selection, labels are not exchangeable for the features the selection balanced | The shuffle for selected pools holds four exactly balanced features fixed; the selection balances about 20 | No gate change. The limit is stated in the docs (Note 13). Diagnostics approved on a public-seed pool, one CPU process, no verdict use: each feature's within-triad correlation, its correlation with the balanced features, the share of items in blocks that cannot move, and which tests take the family maximum |
| "Significant and observed effect above a floor" is not a test that the true effect exceeds the floor | A flag needs family-wise p < 0.05 and lift of at least +0.02 | Rule kept. A pass is worded "no listed cue was found above the audit's detection limit (about +0.03 lift)", never "the pool is clean". Known hole: a rare cue confined to one class can be significant and sit under the floor |
| A p near 0.05 from 2,000 permutations carries about ±0.005 of noise | One run decides | A family-wise p in 0.03 to 0.07 is re-run once at 10,000 permutations and the re-run decides. Applies only if built and reviewed before the first verdict audit; otherwise it lapses |
| Tests with different numbers of levels need a common scale | Chi-square tail by degrees of freedom | Kept. It beat z-score scaling in simulation on well-filled tables; sparse tables are unmeasured |
| Per-replicate conjunction rules lose power | Pooled gate | Confirmed |
| Balancing against a list leaves cues outside it | Listed features, synthetic conjunction features, and a learned probe on those features | Stated as a limitation. A text-only baseline (claim alone, facts alone) is queued for after the test windows |
| A small number of judges cannot be fully ordered at this size | To be checked against the scorers | Queued; seed 37 planted |

### Decisions and actionables

1. Note 13 to the d5c pre-registration (2026-11-19) carries the pass wording, the selection limit and the re-run
   band. It changes no gate, threshold, feature list or recipe.
2. Run the approved diagnostics on a public-seed pool after the current generator fix passes review, within-triad
   correlations first.
3. Harvest seeds 36 and 37 and the two consults, check their load-bearing claims, and update this entry.
4. After the windows: the text-only partial-input baseline, and tiered ranking with clustered intervals.

### Limits of this study

- The simulation used independent noise features and guessed level counts. Real features are correlated, which
  lowers the family threshold and raises power. A pool's own planted controls give the real detection limit.
- Nothing here was run on a d5c pool. The audit code is not yet public; it is released with the benchmark.
- The agents' own power estimate (+0.05 to +0.06) was a back-of-envelope guess that the simulation did not support.

## Claims

- [verified] Published permutation p-values are often understated by about 1/m, where m is the number of permutations, and permutation should be viewed as generating an exact discrete null distribution (Phipson and Smyth 2010) (via: arXiv abstract 1603.05766, 2026-11-19)
- [unverified] (b+1)/(m+1) is exact when permutations are drawn without replacement and a valid, slightly conservative bound when drawn at random (Phipson and Smyth 2010, sections 5 and 6, as reported by the Gemini 4 Carbon review; the full paper was not read by R&D)
- [verified] The d5c audit computes its p-values as (b+1)/(B+1) with B = 2,000 (via: R&D code read of the audit statistics, 2026-11-19)
- [verified] Gardner et al. argue that for complex language understanding tasks any correlation between a simple feature and the label is spurious, and they formalise such tasks as "competency problems" (via: arXiv abstract 2104.08646, 2026-11-19)
- [verified] Schwartz and Stanovsky 2022 is an opinion paper arguing that balancing single-word features is not enough and that a fully balanced dataset can lose real signal (via: arXiv abstract 2204.12708, 2026-11-19)
- [verified] Failure of a partial-input baseline does not mean a dataset is free of artifacts; a hypothesis-only model plus trivial premise patterns solves 15% of SNLI "hard" examples (Feng, Wallace and Boyd-Graber 2019) (via: arXiv abstract 1905.05778, 2026-11-19)
- [verified] Underpowered experiments are common in NLP, and small test sets leave many comparisons underpowered (Card et al. 2020) (via: arXiv abstract 2010.06595, 2026-11-19)
- [verified] In a simulation of the d5c audit's statistics code (608 tests, 3,168 items, 2,000 permutations, 30 replicates per point), a planted binary cue present on about half the items was flagged at rates 0.27, 0.70, 0.90 and 1.00 for mean lifts 0.018, 0.026, 0.031 and 0.041 (via: R&D simulation on synthetic data, 2026-11-19)
- [verified] In the same simulation, single-feature tests (304 of 608) were the family's most extreme statistic in 0.49 of 2,000 permutations under chi-square scaling and 0.91 under permutation z-score scaling (via: R&D simulation on synthetic data, one run, 2026-11-19)
- [verified] The d5c selection step balances listed features beyond the four that the selected-pool shuffle holds fixed (via: R&D code read of the generator and audit, 2026-11-19)
- [unverified] Single-step max-statistic resampling controls family-wise error under subset pivotality (Westfall and Young 1993; via an agent report, not checked)
- [unverified] Comparable marginal null distributions are needed or the widest-spread test dominates the maximum (Ge, Dudoit and Speed 2003; via an agent report, not checked)
- [verified] The d5c selected-pool shuffle is keyed on part, design cell and four features, and not on the triad (via: R&D code read of the audit, 2026-11-19)
- [unverified] Tests correlated with the selection-balanced features are conservative under the audit's shuffle, by roughly the share of their variance those features explain (the review's and the consult's reasoning from rerandomization theory; not measured on d5c)
- [unverified] A feature negatively correlated within a triad can be flagged too often under a shuffle that ignores triads (an AI Studio consult's derivation; not measured on d5c)
- [unverified] Five or six judges on about 1,000 triads support tiers but not a full ranking (an agent's estimate; not checked against d5c's scoring)

## Sources

- [primary] https://arxiv.org/abs/1603.05766 — Phipson and Smyth 2010, Permutation p-values should never be zero
- [primary] https://arxiv.org/abs/2104.08646 — Gardner et al. 2021, Competency Problems: On Finding and Removing Artifacts in Language Data
- [primary] https://arxiv.org/abs/2204.12708 — Schwartz and Stanovsky 2022, On the Limitations of Dataset Balancing
- [primary] https://arxiv.org/abs/1905.05778 — Feng, Wallace and Boyd-Graber 2019, Misleading Failures of Partial-input Baselines
- [primary] https://arxiv.org/abs/2010.06595 — Card et al. 2020, With Little Power Comes Great Responsibility
