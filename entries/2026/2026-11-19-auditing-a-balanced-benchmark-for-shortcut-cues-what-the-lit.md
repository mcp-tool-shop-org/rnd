---
id: 2026-11-19-auditing-a-balanced-benchmark-for-shortcut-cues-what-the-lit
title: Auditing a balanced benchmark for shortcut cues: what the literature and a simulation say about the d5c pool audit
date: 2026-11-19
kind: finding
relevance: act
fields: [evaluation, benchmarks]
tags: [d5c, shortcut-audit, permutation-test, selection-bias, study-swarm, seed-34, seed-36, seed-37, harvest]
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
model from another family (Gemini 4 Carbon) first failed this entry on five overstated or mis-sourced statements,
then passed the corrected text with follow-ups; its review of this harvest also passed with follow-ups, applied here.

Two Gemini Deep Research seeds and two consults were planted on the open questions on 2026-11-19 and harvested the
same night, with an earlier seed on shortcut-free test items. Their findings are in "Harvest" below. All five are
`[aggregator]` AI output and their citations are unchecked unless a claim says otherwise.

## Key points

- **The permutation p-value counts the observed labelling.** The audit reports (b+1)/(B+1) with B = 2,000
  permutations, so a p-value is never zero. Phipson and Smyth's abstract says permutation p-values computed as
  tail-probability estimates are understated by about 1/m for m permutations. At p = 0.05 the Monte Carlo error is about ±0.005
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
| "Significant and observed effect above a floor" is not a test that the true effect exceeds the floor | A flag needs family-wise p < 0.05 and lift of at least +0.02 | Rule kept. A pass is worded "no listed cue was found above the audit's detection limit (about +0.03 lift)", never "the pool is clean". The +0.03 is for a common binary cue; cues with many levels need more. Known hole: a rare cue confined to one class can be significant and sit under the floor |
| A p near 0.05 from 2,000 permutations carries about ±0.005 of noise | One run decides | A family-wise p in 0.03 to 0.07 is re-run once at 10,000 permutations and the re-run decides. Applies only if built and reviewed before the first verdict audit; otherwise it lapses |
| Tests with different numbers of levels need a common scale | Chi-square tail by degrees of freedom | Kept. It beat z-score scaling in simulation on well-filled tables; sparse tables are unmeasured |
| Per-replicate conjunction rules lose power | Pooled gate | Confirmed |
| Balancing against a list leaves cues outside it | Listed features, synthetic conjunction features, and a learned probe on those features | Stated as a limitation. A text-only baseline (claim alone, facts alone) is queued for after the test windows |
| A small number of judges cannot be fully ordered at this size | The scorers judge each arm against pre-registered bars; they hold no pairwise ranking test | No scorer change. After the windows the write-up reports arms in tiers with triad-clustered intervals, labelled post hoc |

### Decisions and actionables

1. Note 13 to the d5c pre-registration (2026-11-19) carries the pass wording, the selection limit and the re-run
   band. It changes no gate, threshold, feature list or recipe.
2. Run the approved diagnostics on a public-seed pool after the current generator fix passes review, within-triad
   correlations first.
3. Done 2026-11-19: seeds 36 and 37 and the two consults are harvested below. Still open: checking their citations at source.
4. After the windows: the text-only partial-input baseline, and tiered ranking with clustered intervals.

### Limits of this study

- The simulation used independent noise features and guessed level counts. Real features are correlated, which
  lowers the family threshold and raises power. A pool's own planted controls give the real detection limit.
- Nothing here was run on a d5c pool. The audit code is not yet public; it is released with the benchmark.
- The agents' own power estimate (+0.05 to +0.06) was a back-of-envelope guess that the simulation did not support.

## Harvest (2026-11-19): two consults and three Deep Research reports

Five outside reads, all from Gemini models, all `[aggregator]`. Where they agree with each other and with our code,
that is noted; none of their numbers has been reproduced on a d5c pool.

- **All three reads of the selection gap agree on its main direction.** After a selection step that balances
  features, a shuffle that does not respect the selection is conservative for every feature correlated with the
  balanced ones. This is the rerandomization result from experimental design (Morgan and Rubin 2012; Li, Ding and
  Rubin 2018, as cited by the reads). One report puts numbers on it: where half a feature's variance is explained
  by the balanced features, family-wise power at 3,000 items falls from 80% to about 17%, for a cue that a selection-aware test would catch at 80% power.
- **Three reads raise the same risk in the other direction.** Our selected-pool shuffle moves labels between triads.
  For a feature that is negatively correlated inside a triad, that underestimates the null variance of each class
  count (and so the scale of the chi-square statistic), by up to a factor of 1.5 when exactly one claim per triad
  carries the feature. The independent reviewer re-derived this. It can
  cause a false flag, never a false pass. It matters only where within-triad correlation is clearly negative, which
  the approved diagnostics measure.
- **A cheap selection-aware test exists on paper.** Two reads propose the same shape: remove the balanced features'
  influence from each tested feature once, then shuffle within triads. One claims seconds of CPU; one proposes a
  Markov chain over balance-respecting within-triad shuffles, with exact Monte Carlo p-values in the manner of Besag
  and Clifford 1989 (the chain is the consult's proposal; the paper is about exact significance tests from such
  chains). Either would be a
  change to a pre-registered gate, so it waits until after the test windows.
- **The detection limit agrees across three sources.** Our simulation gives about +0.03 lift for a common binary
  cue. One Deep Research report computes +0.032 to +0.033 at 80% power for 600 tests on 3,000 items. The earlier
  seed computes +0.021 for a single feature and +0.031 with 17 features controlled, at 3,000 items or more.
- **One consult's recipe for publishing a detection limit.** Plant cues into the real feature matrix of a public-seed pool, not
  into synthetic noise; use at least 500 replicates per point; cover six cue shapes (common, rare and pure,
  one-class, many weak cues together, a conjunction, a nonlinear single feature); run both the per-feature scan and
  the learned probe; publish the lift detected at 50, 80 and 90% power with Monte Carlo errors.
- **The rule "significant and effect above a floor" has a named weakness.** It tests "no effect" and then filters on
  a noisy estimate. A label shuffle cannot produce a null of "lift at most 0.02". The reads suggest confidence
  bounds with three outcomes per feature: flagged, bounded below the tolerance, or inconclusive.
- **A long feature list has a cost.** Every extra test raises the family threshold for all of them. One report
  suggests a short first tier of 20 to 30 high-risk features with its own error budget.
- **Balancing can create joint cues.** A feature can become predictive only together with a balanced one. A
  per-feature scan cannot see that; a probe that learns interactions can.
- **Ranking five or six judges on about 1,000 triads supports tiers, not ranks.** One report's planning figure is a
  detectable gap of about 3.3 points between two judges at 80% power with family-wise control (2.4 to 5.0 across
  its assumptions). Ignoring the triad structure and the multiple comparisons would suggest 1.6 points. It
  recommends the triad as the unit, paired triad differences, a step-down bootstrap over whole triads, and tier
  reports (simultaneous rank sets or a model confidence set). Its inputs are assumed correlations, not our data.
- **Scoring choices change power.** By that report's own simulation, counting a triad only when all three items are
  right loses a large share of power (75% to 54% at one setting). A second presentation order trims the detectable
  gap by only about 8%; its value is measuring position bias.
- **The earlier seed (shortcut-free test items) already shaped the audit.** Its recommendations are the ones d5c
  adopted: permutation nulls instead of fixed bars, folds grouped by triad only, corruption probes, synthesised
  relational features with a family-wise maximum test, and fixing a cue by construction, not by filtering.

### What the harvest contradicts in our design

| Finding | d5c today | Decision |
|---|---|---|
| A shuffle that crosses triads can flag too often on within-triad-negative features | The selected-pool shuffle is keyed on part, cell and four features | No gate change. The diagnostics report within-triad correlations first; any strongly negative feature's tests are named before a verdict is read |
| The audit is less sensitive for features correlated with the balanced ones | Not corrected for | Stated as a limitation. A selection-aware test (project out the balanced features, shuffle within triads) is the candidate fix after the windows |
| A detection limit should be measured on real features across cue shapes | One simulated estimate on synthetic features | Queued for after the windows: the six-shape table on a public-seed pool, scan and probe |
| "No effect" plus an effect filter is not a magnitude test | Flag = significant and lift at least +0.02 | Rule kept for this benchmark. Three-outcome bounds are a candidate for the next one |
| Judges should be compared by triad, in tiers | Checked: the scorers judge each arm against pre-registered bars and hold no pairwise test | Wording only, after the windows: tiers with triad-clustered intervals, labelled post hoc |
| Strict scoring costs power | The primary rule is strict across both presentation orders, and pre-registered | Kept as pre-registered |

## Claims

- [verified] Published permutation p-values are often understated by about 1/m, where m is the number of permutations, and permutation should be viewed as generating an exact discrete null distribution (Phipson and Smyth 2010) (via: arXiv abstract 1603.05766, 2026-11-19)
- [unverified] (b+1)/(m+1) is exact when permutations are drawn without replacement and a valid, slightly conservative bound when drawn with replacement (Phipson and Smyth 2010, sections 5 and 6, as reported by the Gemini 4 Carbon review; the full paper was not read by R&D)
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
- [unverified] Five or six judges on about 1,000 triads support tiers but not a full ranking when judges sit within a few percentage points of each other; the detectable gap between two judges is about 3.3 percentage points at 80% power with family-wise control (a Gemini Deep Research report's calculation from assumed correlations; not checked against d5c's scoring)
- [verified] For one feature present on exactly one claim of every triad, the null variance of a class's count of that feature under a label shuffle across triads is 2K/(3K-1) of its variance under a within-triad shuffle, about two thirds (0.6669 at K = 1,056 triads): binomial K, 1/3 against hypergeometric 3K, K, K (via: R&D algebraic check, 2026-11-19; first derived in an AI Studio consult)
- [unverified] After rerandomization-style selection, the null variance of a linear contrast correlated with the balanced covariates (and the scale of its chi-square statistic) shrinks by up to the squared correlation, down to one minus the squared correlation in the exact-balance limit (Morgan and Rubin 2012; Li, Ding and Rubin 2018; as cited by two consults and a Deep Research report and described by the Gemini 4 Carbon review; papers not read by R&D)
- [unverified] At 3,000 items and 600 tests, the smallest three-way accuracy lift detectable at 80% power for a common binary cue is about +0.032 to +0.033 (a Gemini Deep Research report's calculation; consistent with R&D's simulation)
- [unverified] Scoring a triad only when all three items are correct lowers pairwise power from about 75% to about 54% at a 75% baseline (a Gemini Deep Research report's own simulation, code not shown)
- [unverified] A detection limit should be estimated by planting cues into the real feature matrix with at least 500 replicates per point (a consult's recommendation for d5c; it cites Morris, White and Crowther 2019, a general tutorial on designing simulation studies and sizing them from the Monte Carlo error wanted, which does not itself discuss shortcut audits; paper not read by R&D)

## Sources

- [primary] https://arxiv.org/abs/1603.05766 — Phipson and Smyth 2010, Permutation p-values should never be zero
- [primary] https://arxiv.org/abs/2104.08646 — Gardner et al. 2021, Competency Problems: On Finding and Removing Artifacts in Language Data
- [primary] https://arxiv.org/abs/2204.12708 — Schwartz and Stanovsky 2022, On the Limitations of Dataset Balancing
- [primary] https://arxiv.org/abs/1905.05778 — Feng, Wallace and Boyd-Graber 2019, Misleading Failures of Partial-input Baselines
- [primary] https://arxiv.org/abs/2010.06595 — Card et al. 2020, With Little Power Comes Great Responsibility
- [aggregator] https://aistudio.google.com/ — AI Studio consult, Gemini 4 Carbon, 2026-11-19: the audit's selection gap
- [aggregator] https://gemini.google.com/ — Gemini app consult, Gemini 4 Neon, 2026-11-19: reporting an audit's detection limit
- [aggregator] https://gemini.google.com/ — Gemini Deep Research, seeds 34 (2026-11-17), 36 and 37 (2026-11-19)
