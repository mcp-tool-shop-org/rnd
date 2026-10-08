---
id: 2026-10-08-dataset-recipes-for-critic-jury-roles-designing-roles-by-dat
title: Dataset recipes for critic jury roles — designing roles by data and choosing the panel
date: 2026-10-08
kind: concept
relevance: act
fields: [machine-learning, evaluation]
tags: [critic, jury, dataset-recipe, role-os, planted-errors, reward-model, llm-as-judge, ensemble-diversity]
---

## Summary

The Director's direction (2026-10-08): the studio's critics should get their jury
positions from data designed for the purpose, not from the luck of a random
seed. The ASPIRE critic-init test had produced an inverted "Auditor" by
accident ([[2026-10-08-more-prompts-raise-the-aspire-critic-s-accuracy-but-not-its-]]).
The studio should be in the business of finding and making **dataset recipes**,
and of knowing which combination of roles best suits each assignment. This
entry gathers the evidence for doing that scientifically and maps it onto
role-os.

Five research agents covered:
- critic training-data recipes;
- shortcut learning and generator artefacts;
- jury and ensemble theory;
- roles by data versus by prompting;
- recipe documentation and role selection.

A sixth surveyed role-os. In brief, the evidence supports the direction:
- prompted personas do not reliably make judges more accurate, and roles that
  work are instilled by training data or enforced by protocol;
- juries of off-the-shelf LLMs add little, because their errors are correlated,
  and designing errors to differ through data is one of the few levers;
- a recipe needs controls that prove it taught the attribute and not the
  data generator's fingerprint;
- role-os already has a trained-specialist layer a critic can plug into. It
  lacks a recipe object, a jury aggregation step and a learned role selector.

## Key points

- **Roles come from data or protocol, not from personas.**
  - 162 system-prompt personas did not raise factual accuracy over no persona,
    and automatic persona choice was no better than random (Zheng et al. 2023).
  - The roles with evidence behind them are all trained:
    - a verifier trained against "sneaky" provers (Kirchner et al. 2024);
    - attribute heads mixed by a gate (ArmoRM, Wang et al. 2024);
    - a critic trained on inserted bugs (CriticGPT, McAleese et al. 2024).
  - Debate helps mainly when the judge lacks information the debaters have
    (Khan et al. 2024; Kenton et al. 2024).
- **Recipe parameters with evidence:**
  - **Negative construction** changes results: modified-instruction negatives
    scored 83.8 on RewardBench against 80.7 for directly prompted bad answers
    (Self-Taught Evaluators, Wang et al. 2024). CriticGPT used human-inserted
    bugs.
  - **Difficulty filtering** is the cheapest lever:
    - CriticGPT kept only bugs an LLM critic missed in at least one of three
      tries;
    - Self-Taught Evaluators kept only pairs a judge could get right.
  - **Pointwise and pairwise data interfere:** training them jointly was worse
    than training separately and merging the weights (Prometheus 2: 0.595 vs
    0.670 Pearson, 75.3% vs 79.2% pairwise accuracy). Give each role its own
    run.
  - **Presentation order and swap augmentation:**
    - always putting the winner first or last shifted Self-Taught Evaluators'
      results (85.5 vs 91.1 against about 88.5 randomised);
    - swap augmentation raised order consistency from 73.5% to 78.9% (JudgeLM,
      Zhu et al. 2023).
  - **Quantity:** JudgeLM's agreement rose from 75.9 to 83.7 (7B) and from 85.4
    to 90.1 (33B) going from 3.5K to 100K examples. Curation can beat volume:
    Skywork-Reward topped RewardBench with 80K curated pairs.
  - **Granularity:** step-level labels beat outcome-only labels in maths
    (PRM800K; Math-Shepherd with automatic step labels). A single planted
    sentence is a coarse step label.
  - **No evidence found for:** edit size, how many error types, or one versus
    several negative generators. These have to be the studio's own experiments.
- **Generators leave fingerprints; recipes need controls.**
  - Classifiers tell five major LLMs' text apart at about 97%, even after
    rewriting (Sun et al. 2025). Detectors do not generalise across generators.
  - Models learn data artefacts: NLI annotation artefacts, hypothesis-only
    baselines, and the HANS heuristics (Gururangan 2018; Poliak 2018; McCoy
    2019).
  - Minimal pairs, cartography-guided subsets and adversarial filtering help
    (Gardner 2020; Swayamdipta 2020; Le Bras 2020), though counterfactual data
    is not a guaranteed fix (Huang 2020).
- **Juries add little unless their errors differ.**
  - Across 350+ LLMs, two models that are both wrong agree on the wrong answer
    about 60% of the time, and more so for larger models and the same
    developer (Kim et al. 2025).
  - LLM judges favour models like themselves, and errors grow more similar with
    capability. CAPA is a chance-adjusted measure of mistake overlap (Goel et
    al. 2025).
  - The PoLL panel's kappa beat the best single judge on two of three QA sets,
    by small margins (Verga et al. 2024).
  - A 2026 preprint found nine judges acting like 2.3–3.1 independent votes,
    with the best single judge matching the panel. Unreplicated.
  - Theory agrees: correlated jurors saturate the benefit (Ladha 1992), and
    training members to decorrelate their errors beats training them
    independently (negative correlation learning, Liu & Yao 1999).
- **Selection:** greedy forward selection with replacement from a library of
  models, with equal weights (Caruana et al. 2004). It overfits small selection
  sets, so bag it and nest it.
- **Recipes as the unit of study:** DataComp held model and compute fixed and
  varied only the data recipe, scored on a fixed suite (Gadre et al. 2023).
  Documentation standards: Datasheets (Gebru), Data Cards (Pushkarna), data
  statements (Bender & Friedman), provenance audits (Longpre). A judge's skill
  does not transfer across task categories (RewardBench, JudgeBench), so each
  assignment needs its own check.
- **role-os today** (survey of E:/AI/role-os, read-only):
  - **Roles:** markdown contracts plus keyword routing. "Confidence" is a count
    of keyword hits.
  - **Specialists layer:** a role can carry a `specialist:` block pointing at a
    trained non-Claude model, with:
    - a registry with versions and rollback;
    - L0–L5 certification from exams with bootstrap CIs and two-seed
      replication;
    - shadow probes against Claude, with an andon halt;
    - drift detection.
    Two specialists already have dataset builders with exam/train splits
    (`tools/conformance-dataset/`, `tools/token-budget-dataset/`).
  - **Missing:**
    - a recipe object tied to a role (builders are one-off scripts);
    - trained critics;
    - any aggregation of several critics' verdicts beyond the conservative
      claim and citation panels;
    - a learned role selector. The outcome ledger (`src/calibration.mjs`,
      which records `rolesUsed`) exists, but it is not wired into routing.

## Studio relevance

**Recommendation: make the recipe the unit of work.** Each critic role is
(recipe card + trained checkpoint + exam), registered as a role-os specialist
and chosen per assignment by measured, not keyword, evidence.

**1. The recipe card.** Every critic dataset ships one; fields justified by the
sources above.

| field | contents |
|---|---|
| role and target | the attribute (e.g. "find the error in one answer"), the failure type, out-of-scope uses |
| sources | prompts and strong answers, licences, provenance |
| negative construction | planter models (family, revision), edit request, error taxonomy, edit-size stats (difflib), seed, code hash |
| filtering | difficulty filter (kept if the current critic misses it), solvability filter, cartography pass |
| format | pointwise or pairwise (one per run), order randomisation, swap augmentation, reference answer (train = test), rationale or not |
| mixture | counts per error type and planter family |
| splits | train, validation, frozen exam, never-tuned final set, held-out planter family, natural-error set |
| controls | the list in point 2, with each result |
| results | per category, against chance, the best single critic and the reference judges, with prompt-clustered CIs |
| pins | every model, prompt and tool version (PIN_PER_STEP) |

**2. Controls every recipe ships with** (cheapest first):
1. Positive control: a learnable marker must be learned.
2. Graded marker: one rare token at the edit position. This tells "the features
   can't see it" apart from "the error is hard".
3. Shuffled labels must sit at chance.
4. Partial-input baseline: the edit span alone, or one side alone.
5. Generator-identity probe: can the features tell the planters apart?
6. Same-planter edits with no error must read as clean.
7. A fully held-out planter family as the headline transfer number.
8. A small set of natural, non-planted errors (CriticGPT's lesson: plant
   recovery overstates quality).

**3. Recipe defaults until the studio's own experiments say otherwise.**
- Planters from 2–3 model families for training plus one family held out. This
  is a judgement call; no study fixes the number.
- Difficulty-filtered negatives.
- One format per role, trained separately; merge weights if a combined critic
  is needed.
- Randomised order plus swap augmentation.
- Error types tagged so results can be sliced.

**4. Choosing the panel for an assignment.**
- Build 100–300 checkable validation items for the assignment.
- Score each candidate role, and drop any not clearly above chance.
- Compute pairwise error overlap (CAPA, double-fault) and effective votes.
- Greedy forward selection with replacement and equal weights, adding a member
  only if it brings error diversity. Aim for 3–5 members.
- Keep the best single critic as the bar the panel must beat.
- Validate the selection itself with nested resampling. At about 150 items,
  differences under 5–8 points are noise.

**5. The role-os connection** (proposals for role-os, not changes made here):
- **Recipe link:** add a `recipe_card` hash beside `exam_hash` in the
  specialist registry version, so every certified critic points at the
  recipe that made it.
- **Jury step:** a panel aggregation next to `gateClaims` (equal-weight,
  sign-normalised, error-diverse members), placed before the Critic Reviewer.
- **Learned selector:** wire the outcome ledger and extend it per role
  combination and assignment type (it already records `rolesUsed`), so
  selection learns from measured outcomes instead of keyword counts.

**6. First recipes to card.**
- The planted-error text pairs behind the Kev judge fine-tune and aspire-si's
  Auditor/Advocate (PR #45).
- ai-jam-sessions' planted defects for sung mixes
  ([[2026-10-07-planted-defects-program-for-sung-mixes]]). It is the same
  planter-versus-detector pattern, in audio.

A natural first comparison, DataComp-style: the Auditor recipe with one planter
family against two, with the critic architecture fixed. That is local and $0
once A's second-planter tooling exists.

## Claims

- [verified] Adding any of 162 personas to the system prompt did not improve factual accuracy over a no-persona control across 4 model families, and automatic persona selection was often no better than random. (via: research agent reading Zheng et al. 2023 abstract, 2026-10-08)
- [verified] Self-Taught Evaluators lifted Llama-3-70B-Instruct from 75.4 to 88.3 on RewardBench; modified-instruction negatives scored 83.8 against 80.7 for directly prompted bad responses. (via: research agent reading arXiv 2408.02666 HTML, 2026-10-08)
- [verified] Prometheus 2: separately trained pointwise and pairwise judges merged by weight reached 0.670 Pearson and 79.15% pairwise accuracy, against 0.595 and 75.29% for joint training. (via: research agent reading arXiv 2405.01535 HTML, 2026-10-08)
- [verified] JudgeLM: swap augmentation raised order consistency from 73.45% to 78.89% (7B); going from 3.5K to 100K training examples raised agreement 75.9→83.7 (7B) and 85.4→90.1 (33B). (via: research agent reading arXiv 2310.17631 HTML, 2026-10-08)
- [verified] Across 350+ LLMs, when two models both err they choose the same wrong answer on about 60% of items, more so for larger models and the same developer. (via: research agent web-checking Kim et al. 2025, arXiv 2506.07962, 2026-10-08)
- [verified] LLM judges favour models similar to themselves, and model mistakes grow more similar with capability; CAPA measures chance-adjusted mistake overlap. (via: research agent web-checking Goel et al. 2025, arXiv 2502.04313, 2026-10-08)
- [verified] PoLL reached Cohen's kappa 0.763 / 0.906 / 0.867 on NQ / TriviaQA / HotpotQA, against best single judges at 0.749 / 0.894 / 0.873. (via: research agent web-checking Verga et al. 2024, arXiv 2404.18796, 2026-10-08)
- [verified] role-os has a specialists layer (registry, L0–L5 certification, shadow probes with andon halt, drift detection) that lets a role point at a trained non-Claude model; its outcome-ledger calibration (src/calibration.mjs) is not called from routing. (via: survey agent reading E:/AI/role-os source at c0f8614, 2026-10-08)
- [unverified] Nine LLM judges from 7 families behaved like 2.3–3.1 independent votes, and the best single judge matched or beat the panel (arXiv 2605.29800; single preprint, search summary only).
- [unverified] A classifier distinguishes text from five major LLMs at about 97%, and the signal survives rewriting (Sun et al. 2025, arXiv 2502.12150; from memory).
- [unverified] CriticGPT's critiques were preferred over human critiques 63% of the time on naturally occurring bugs, and human+critic teams hallucinated fewer bugs than the critic alone (McAleese et al. 2024; abstract and snippets).
- [unverified] Training on 2–3 planter families with one more held out is enough to expose generator fingerprints. (Judgement from indirect evidence; no study fixes the number.)

## Sources

- [primary] https://arxiv.org/abs/2311.10054 — Zheng et al. 2023, "Is 'A Helpful Assistant' the Best Role for Large Language Models?"
- [primary] https://arxiv.org/abs/2407.00215 — McAleese et al. 2024, "LLM Critics Help Catch LLM Bugs" (CriticGPT)
- [primary] https://arxiv.org/abs/2408.02666 — Wang et al. 2024, "Self-Taught Evaluators"
- [primary] https://arxiv.org/abs/2405.01535 — Kim et al. 2024, "Prometheus 2"
- [primary] https://arxiv.org/abs/2310.17631 — Zhu et al. 2023, "JudgeLM"
- [primary] https://arxiv.org/abs/2305.20050 — Lightman et al. 2023, "Let's Verify Step by Step"
- [primary] https://arxiv.org/abs/2312.08935 — Wang et al. 2024, "Math-Shepherd"
- [primary] https://arxiv.org/abs/2408.15240 — Zhang et al. 2024, "Generative Verifiers"
- [primary] https://arxiv.org/abs/2410.18451 — Liu et al. 2024, "Skywork-Reward"
- [primary] https://arxiv.org/abs/2506.01937 — RewardBench 2
- [primary] https://arxiv.org/abs/2407.13692 — Kirchner et al. 2024, "Prover-Verifier Games improve legibility of LLM outputs"
- [primary] https://arxiv.org/abs/2407.04622 — Kenton et al. 2024, "On scalable oversight with weak LLMs judging strong LLMs"
- [primary] https://arxiv.org/abs/2402.06782 — Khan et al. 2024, "Debating with More Persuasive LLMs Leads to More Truthful Answers"
- [primary] https://arxiv.org/abs/2506.07962 — Kim et al. 2025, "Correlated Errors in Large Language Models"
- [primary] https://arxiv.org/abs/2502.04313 — Goel et al. 2025, "Great Models Think Alike and this Undermines AI Oversight"
- [primary] https://arxiv.org/abs/2404.18796 — Verga et al. 2024, "Replacing Judges with Juries"
- [primary] https://arxiv.org/abs/2605.29800 — "Nine Judges, Two Effective Votes" (2026 preprint, not read)
- [primary] https://arxiv.org/abs/2304.14108 — Gadre et al. 2023, "DataComp"
- [primary] https://arxiv.org/abs/2410.12784 — Tan et al. 2024, "JudgeBench"
- [rig] role-os survey, E:/AI/role-os @ c0f8614 (src/specialist/, src/calibration.mjs, src/route.mjs, tools/conformance-dataset/), 2026-10-08
- [user] Cited by the agents from memory, not re-read this session: Gururangan et al. 2018 (arXiv 1803.02324); Poliak et al. 2018; McCoy et al. 2019 HANS (1902.01007); Geirhos et al. 2020 (2004.07780); Gardner et al. 2020 (2004.02709); Kaushik et al. 2020; Huang et al. 2020; Swayamdipta et al. 2020 (2009.10795); Le Bras et al. 2020 AFLite (2002.04108); Sun et al. 2025 (2502.12150); Li et al. 2023 MAGE; Panickssery et al. 2024 (2404.13076); Krogh & Vedelsby 1995; Brown et al. 2005; Liu & Yao 1999; Kuncheva & Whitaker 2003; Ladha 1992; Caruana et al. 2004; Wolpert 1992; Dawid & Skene 1979; Chan et al. 2023 ChatEval; Irving et al. 2018; Michael et al. 2023; Wang et al. 2024 ArmoRM and HelpSteer2; Xu et al. 2024 CGPO; Huang et al. 2023 self-correction; Gebru et al. Datasheets; Pushkarna et al. 2022 Data Cards; Bender & Friedman 2018; Longpre et al. 2023; Xie et al. 2023 DoReMi; Ye et al. 2024 Data Mixing Laws; Thakur et al. 2024; Polo et al. 2024 tinyBenchmarks; Kiela et al. 2021 Dynabench; Hu et al. 2024 RouterBench; Ong et al. 2024 RouteLLM
- [user] Direction from the Director, 2026-10-08; six research and survey agents (claude-sonnet-5-5)
