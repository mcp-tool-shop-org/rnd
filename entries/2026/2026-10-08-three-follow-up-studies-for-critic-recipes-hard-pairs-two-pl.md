---
id: 2026-10-08-three-follow-up-studies-for-critic-recipes-hard-pairs-two-pl
title: Three follow-up studies for critic recipes — hard pairs, two planter families, natural errors
date: 2026-10-08
kind: concept
relevance: act
fields: [machine-learning, evaluation]
tags: [critic, dataset-recipe, planted-errors, hard-examples, domain-generalisation, natural-errors, aspire-si]
---

## Summary

aspire-si's Auditor plan (PR #45) left three follow-up studies for the Director
to choose from ([[2026-10-08-dataset-recipes-for-critic-jury-roles-designing-roles-by-dat]]):
- train only on the hard pairs;
- train on errors planted by two model families and test on a third;
- check every critic against a small set of natural, unplanted errors.

The Director asked R&D to dig into them. Three research agents covered the
evidence, and R&D measured the existing hard pool. Each study is a recipe
parameter (filtering, planter diversity, evaluation), so each result goes onto
the recipe card.

Verdicts:
- **Natural errors:** build first. It is the yardstick for the other two.
- **Two planters:** the cleanest experiment, as long as data size is matched
  and a same-family control is included.
- **Hard pairs:** the raw version is not viable on today's data. Test
  upweighting first, and generate new hard plants only if that shows a gain.

## Key points

- **A fact all three depend on:** aspire-si's pair filters
  (`clean_dataset.py`) check only form: truncation, similarity, length change
  and self-flag markers. Nothing confirms that an edit introduced a real
  error. Frozen Kev-4B, order-averaged, agrees with the labels on 97.6% of the
  judge pairs. A plant that isn't an error would be a coin-flip for it, so at
  most about 5% are duds.
- **The hard pool, measured** (Kev-4B judge fine-tune, 3 seeds, 149
  confirmation pairs):
  - order-averaged misses: 2–3 pairs per seed, 2 missed by all three;
  - single-choice misses: 9–12 per seed, 9 shared by all three. Hardness is a
    stable property of the pairs, not seed noise;
  - scaled to the 603 training pairs, that is about 15–50 hard pairs, too few
    to train on alone;
  - the three hardest are real errors, not duds:
    - "find all reachable nodes" → "unreachable", in a garbage-collection
      answer;
    - "−18 °C (0 °F)" → "(32 °F)", where Kev confidently prefers the flawed
      version: a unit-conversion blind spot;
    - "must be known at compile time" → "is usually known", a subtle softening
      that Kev scores at exactly 0.5.
- **Hard examples (evidence):**
  - when data is scarce, keeping easy examples beats keeping hard ones
    (Sorscher et al. 2022; the abstract was read, the scarce-data rule is from
    memory);
  - models trained on easy data often match oracles trained on hard data
    (Hase et al. 2024);
  - the hardest examples are often mislabelled, and the ambiguous middle helps
    out-of-distribution performance most (Swayamdipta et al. 2020);
  - upweighting the first model's errors (JTT) closed 75% of the worst-group
    gap while keeping all the data (Liu et al. 2021);
  - adversarially filtered training data has mixed evidence for better
    generalisation.
- **Several generators vs one (evidence):**
  - detectors trained on one text generator transfer to similar generators
    and fail on dissimilar ones (M4);
  - which single generator you train on swings cross-generator transfer by
    about 20 points (DetectRL, Table 5);
  - no paper found tests "a second generator at fixed data size". Domain-
    generalisation theory says few training domains give little protection,
    and the claim is contested (Gulrajani & Lopez-Paz 2021 against Wang et
    al. 2024). A null result at two planters is plausible;
  - LLMs recognise their own text, and that links to self-preference
    (Panickssery et al. 2024). The Auditor's features come from a frozen Qwen
    1.5B, so **a Qwen-based critic scored on Qwen plants is the most
    contaminated cell** of the design.
- **Natural errors (evidence):**
  - FELM is the closest public fit: 847 ChatGPT answers with sentence-level
    labels across science, reasoning and world knowledge. It is CC BY-NC-SA,
    so internal evaluation only, never training or redistribution, and its
    labeller agreement is unreported;
  - ExpertQA has expert-rated long answers, but its dataset licence is
    unconfirmed;
  - the others are maths-only (ProcessBench, BIG-Bench Mistake, PRM800K),
    document-grounded and gated with a no-training clause (LLM-AggreFact), or
    made of synthetic hallucinations (HaluEval);
  - on REALMistake's natural errors, GPT-4 and Claude 3 had low recall, far
    below human experts, and majority voting did not help. Natural errors are
    hard, which is why the check matters;
  - SAFE's search-based fact-checking agreed with crowd labels on about 72% of
    facts and was right in 76% of 100 sampled disagreements, so cheap
    automatic screening is credible but noisy.
- **Local planters available at $0** (Ollama on the rig): Qwen, gemma4:31b,
  mistral-small:24b and granite4.1:30b, so there are two non-Qwen families
  beyond Gemma. The list also holds `*-cloud` tags under similar names; pin
  local model IDs, as aspire-si's `second_planter.py` already does.

## Studio relevance

**Recommended order:** natural errors → two planters → hard pairs
(upweighting). Every run is local and $0. Each needs the Director's go, its GPU
booked through the Publisher, and its readout committed before it runs.

**Study A: a natural-error yardstick** (build first; it is the test set for
the other two).
1. **In-domain set, 60–100 items:**
   - write prompts in the aspire-si style and have a weaker non-Qwen local
     model answer them (e.g. llama3.1:8b, to avoid the self-recognition
     problem);
   - a local screen flags suspect sentences: a vote by three judges from
     different families (gemma, mistral, granite). Keep every flagged item
     plus a random 30–40% of unflagged ones, so the set measures what the
     screen misses;
   - the Director reviews each answer, with the flagged sentences
     highlighted and the unflagged ones blind: error yes or no, which
     sentence, and a corrected version, which gives a correct/incorrect pair
     for free. Estimate: about an hour at 30–40 seconds an item, not
     measured;
   - he re-labels about 10 items blind later as a self-consistency check. The
     set is openly single-annotator ground truth.
2. **Public set:** FELM, filtered to science/tech, reasoning and world
   knowledge, for internal evaluation only. Spot-check about 30 of its labels
   first.
3. **Readout:** each critic's recall and precision on natural errors next to
   its planted-pair accuracy. The gap is how much planting flatters the
   critic.

**Study A status (2026-10-08): the set is built and labelled.**
- Human review was replaced by two blind Claude passes plus adjudication. The
  Director's reason: it doesn't scale, and a strong model finds more of an
  8B's mistakes.
- **The set:** 95 llama3.1:8b answers; 59 have an error and 36 are clean.
  Labeller kappa is 0.63.
- **The screen:**
  - the three-judge screen caught every answer with an error, but only 70%
    of the error sentences;
  - gemma4:31b alone: recall 0.97, precision 0.72 at the answer level;
  - mistral-small and granite are precise but miss most errors.
- 31 correction pairs are built as the reversed control for aspire-si's
  Skeptic.
- Details: `experiments/natural-errors/README.md`. Readout 2 (critics) is
  next.

**Study B: two planter families** (follows directly from #45's
second-planter tooling).
- **Arms, all at the same total size N, on the same prompts and strong
  answers:**
  - Q-only;
  - G-only;
  - Q+G (N/2 each), the main comparison;
  - **Q+Q control:** two Qwen planting seeds or temperatures at N/2 each. It
    separates "more planters" from "more varied samples";
  - optional: Q+G+M (Mistral), tested on held-out Granite.
- **Held fixed:** critic architecture (Auditor-mean and Auditor-attn),
  hyperparameters, epochs, three seeds, a fixed model-selection rule, and no
  tuning on the held-out family.
- **Planting:** each planter plants on the same training strong answers, and
  the held-out family plants on the same validation and test answers. Then the
  planter is the only thing that changes.
- **Matching:**
  - report edit statistics (difflib: characters changed, length change,
    position) for each planter, and stratify the results by edit size;
  - a planter-ID probe: can a small classifier tell planters apart from the
    edit alone?
- **Tests:**
  - in-family plants (Qwen, Gemma);
  - the held-out family (Granite, or Mistral if it isn't in training);
  - clean answers alone, as a false-positive control;
  - the Study A natural set.
- **What counts:**
  - Q+G beats both Q-only and G-only on the held-out family, with a paired
    prompt-clustered CI over seeds excluding 0;
  - in-family accuracy is not worse;
  - the Q+Q control does not close the gap;
  - the gap holds on natural errors.
  Otherwise the result is "no evidence of transfer at two planters", not
  "multi-planter is useless".
- **Kev arm:** the same arms on the Kev-4B judge fine-tune, about 22 min per
  seed on the 5090. It tests whether the conclusion depends on critic
  capacity.

**Study C: hard pairs**, reshaped by the evidence and the measurement.
1. **Upweighting (JTT) first, with no new data:**
   - define hardness by K = 5 cross-fitting (each pair scored by critics that
     never trained on it), over three seeds and two pooling forms;
   - arms: all pairs; all pairs with hard pairs weighted ×2, ×5 and ×20; a
     random subset the size of the hard pool; and hard-only, for completeness;
   - adopt a weighting only if it beats all-pairs on validation and on the
     natural set.
2. **Audit the hard pool before using it:** the Director reads the one-
   sentence diffs, which is fast, and duds are dropped. Report the dud rate
   in the pool against the about-5% base rate.
3. **Generated hard pairs, only if step 1 shows a gain:** plant many new
   pairs (with Study B's planters), keep those the cross-fitted critic misses,
   audit, then compare against a size-matched random set of new plants. This
   is CriticGPT's filter, and the only way to get hundreds of hard pairs.

**Roles:**
- aspire-si (session A) owns the critic-head runs, an extension of #45.
- R&D can run the Kev arms and help build the Study A set.
- The Director's time: about an hour for Study A, and about 15 minutes to
  audit the hard pool.

## Claims

- [verified] On the 149 confirmation pairs, the Kev-4B judge fine-tune misses 2–3 pairs per seed order-averaged (2 shared by all three seeds) and 9–12 on single choices (9 shared by all three). (via: experiments/kev-judge-finetune/results per-pair rows, 2026-10-08)
- [verified] The three hardest confirmation pairs are genuine errors: reachable→unreachable nodes, −18 °C (0 °F)→(32 °F), where Kev confidently prefers the flawed answer, and "must be"→"is usually" known at compile time. (via: R&D reading the difflib spans of those pairs, 2026-10-08)
- [verified] aspire-si's pair filters check truncation, similarity, length change and self-flag markers only; no step verifies that a plant is an error. (via: reading examples/sft-experiment/clean_dataset.py and fresh_pairs.py, 2026-10-08)
- [verified] JTT closed 75% of the worst-group gap between ERM and group-DRO averaged over 4 tasks. (via: research agent reading arXiv 2107.09044 abstract, 2026-10-08)
- [verified] Training on easy data often matches oracles trained on hard data across models up to 70B on 4 QA datasets. (via: research agent reading arXiv 2401.06751 abstract, 2026-10-08)
- [verified] FELM has 847 questions and 4,427 segment labels, under CC BY-NC-SA 4.0. (via: research agent reading the FELM repository, 2026-10-08)
- [verified] On REALMistake, LLM detectors including GPT-4 and Claude 3 had low recall on natural errors, far below humans, and majority voting did not help. (via: research agent reading the REALMistake pages, 2026-10-08)
- [verified] On the 95-answer natural set, the three-judge local screen flagged every answer that has an error, but only 59 of the 84 error sentences both labellers marked (70%); gemma4:31b alone had answer-level recall 0.97 and precision 0.72. (via: experiments/natural-errors gold.json against screen.json, labels by claude-opus-5-5 and claude-sonnet-5-5 blind, adjudicated by Opus, 2026-10-08; labels are model-made, not human)
- [verified] Two blind Claude labelling passes on the natural set agree at kappa 0.63 (error vs not); Sonnet marked fewer, mostly skipping minor errors. (via: experiments/natural-errors labels_claude.json vs labels_sonnet.json, 2026-10-08)
- [unverified] With scarce data, keeping easy examples beats keeping hard ones (Sorscher et al. 2022; the abstract was read, this rule is from memory).
- [unverified] Cross-generator transfer of a supervised detector swings by about 20 points with the choice of training generator (DetectRL Table 5, metric unstated).
- [unverified] Two planter families are too few to expect reliable gains on an unseen family (domain-count theory, contested; no direct study).

## Sources

- [primary] https://arxiv.org/abs/2206.14486 — Sorscher et al. 2022, "Beyond neural scaling laws: beating power law scaling via data pruning"
- [primary] https://arxiv.org/abs/2107.09044 — Liu et al. 2021, "Just Train Twice"
- [primary] https://arxiv.org/abs/2009.10795 — Swayamdipta et al. 2020, "Dataset Cartography"
- [primary] https://arxiv.org/abs/2401.06751 — Hase et al. 2024, "The Unreasonable Effectiveness of Easy Training Data for Hard Tasks"
- [primary] https://arxiv.org/abs/2305.14902 — Wang et al. 2024, M4
- [primary] https://arxiv.org/abs/2305.13242 — Li et al. 2023, MAGE
- [primary] https://arxiv.org/abs/2410.23746 — Wu et al. 2024, DetectRL
- [primary] https://arxiv.org/abs/2405.07940 — Dugan et al. 2024, RAID
- [primary] https://arxiv.org/abs/2404.13076 — Panickssery, Bowman & Feng 2024, LLM self-recognition and self-preference
- [primary] https://arxiv.org/abs/2007.01434 — Gulrajani & Lopez-Paz 2021, "In Search of Lost Domain Generalization" (DomainBed)
- [primary] https://github.com/hkust-nlp/felm — FELM (Chen et al. 2023), arXiv 2310.00741
- [primary] https://huggingface.co/datasets/ryokamoi/realmistake — REALMistake (Kamoi et al. 2024)
- [primary] https://arxiv.org/abs/2309.07852 — ExpertQA (Malaviya et al. 2024)
- [primary] https://github.com/google-deepmind/long-form-factuality — LongFact / SAFE (Wei et al. 2024)
- [primary] https://arxiv.org/abs/2412.06559 — ProcessBench (Zheng et al. 2024)
- [primary] https://huggingface.co/datasets/lytang/LLM-AggreFact — LLM-AggreFact (Tang et al. 2024)
- [rig] Kev judge fine-tune per-pair results on the confirmation set (experiments/kev-judge-finetune/results), and aspire-si clean_dataset.py / fresh_pairs.py / second_planter.py, 2026-10-08
- [user] Cited by the agents from memory, not re-read: Shrivastava et al. 2016 OHEM; Lin et al. 2017 focal loss; Bengio et al. 2009; Kumar et al. 2010; Le Bras et al. 2020 AFLite; Kiela et al. 2021 Dynabench; Sun et al. 2024 easy-to-hard; Wang, Wu & Zhang 2024 (AAAI) on the number of training domains; Shumailov et al. 2023; Gerstgrasser et al. 2024; Cui et al. 2023 UltraFeedback; FActScore; HaluEval; WiCE; Factcheck-GPT
- [user] Request from the Director, 2026-10-08; three research agents (claude-sonnet-5-5)
