---
id: 2026-11-13-answer-key-trust-research-seed-24
title: How far can an answer key be trusted? Evidence for rdlab's claims (seed 24)
date: 2026-11-13
kind: finding
relevance: act
fields: [evaluation, benchmarks]
tags: [rdlab, answer-keys, llm-judges, pre-registration, automation-bias, seed-24, harvest]
---

## Summary

The studio's item-generation tool, rdlab, builds test items whose answer keys come from code, and certifies them
with a pre-registered coverage map and blind readers from different model families. To write honestly about that,
R&D asked a Gemini Deep Research run what the literature says about answer-key errors, judge panels, pre-registration
and human review. The report is `[aggregator]` AI output; it tags its own claims as documented, practitioner-reported
or author inference. Found through a Gemini Deep Research report (2026-11-13); claims checked as marked. Only three
citations were spot-checked on the web and all held; everything else is `[unverified]`.

The practical result is a short list of wording limits for rdlab's claims and two measurement gaps.

## Key points

- **Solvers prove a key only inside the formal model.** Specification bugs survive formal methods (Rozier 2016). rdlab's
  own third run showed the same shape: 6 of 11 failed pairs were real value-set faults the blind key had missed.
- **Benchmark keys are wrong more often than assumed.** About 6.5% of MMLU questions were flawed (57% in Virology) in a
  stratified-sample estimate, not a full re-annotation (Gema et al. 2025, confirmed). At least 9.1% of GSM8K's test
  split was flawed, and after cleaning, two models tied at 45 errors split to 2 against 17 (Vendrow et al. 2025;
  not checked).
- **A jury of models shares blind spots.** Nine judges from seven families gave about 2.18 effective votes (Kohli 2026,
  confirmed). By the report's own arithmetic from an NLI correlation, a two-family gate is about 1.4 independent
  votes. That is the report's inference, not a measurement.
- **Rendering drift is real but unmeasured for rdlab.** Open models made a semantic error in 76-86% of zero-shot
  data-to-text outputs (Kasner and Dusek 2024), a different task with longer outputs. It is not rdlab's rate.
- **Human final checks suffer automation bias:** a risk ratio of about 1.26 when the tool is 80-90% accurate
  (Goddard, Roudsari and Wyatt 2012).
- **Pre-registration is associated with fewer positive results.** Large NHLBI trials went from 17 of 30 positive to 2
  of 25 after registration (Kaplan and Irvin 2015, confirmed, with the authors cautious about causation);
  psychology Registered Reports were 96% against 44% positive (Scheel et al. 2021, not checked). These compare eras
  or tracks, so say "associated with".
- **Older fields faced this:** nursing exams with 47.3% flawed items that helped weak students (Tarrant and Ware 2008).
- **Practitioners favour real production traces** over synthetic suites, and an open deterministic generator invites
  gaming (Goodhart).

## Studio relevance

### What it contradicts in our design (read first)

| Finding | rdlab today | Decision |
|---|---|---|
| A solver proves a key only against the model its author wrote; specification bugs survive | "The answer key comes from code" | Do not write "keys are proven correct". Write "proven against the world model the author wrote", and lead with value-set certification |
| Open LLMs drift semantically when they verbalise data (76-86% in a different task) | A local model verbalises the item and a person hand-reads before training use; no measured drift rate | A gap. Measure key against wording on a sample (about 100 items) and print the number, or say "not measured". Never quote 76-86% as rdlab's rate |
| Cross-family agreement is correlated (9 judges, about 2.18 effective votes) | Judged items need several families; value sets use two blind readers from different families | By the report's arithmetic a two-family gate is about 1.4 independent votes. Keep "evidence, not proof" around it; consider a hand-read on every judged item |
| Human final checks have automation bias | Nothing counts as training data until a person checks it | The hand-read is only as good as its design: show the reviewer the item before the key, or sample blind. Worth a card |
| No difficulty or discrimination calibration | Counts per cell; variety bounds | Not a contradiction but a visible hole; frame it as the next step |
| Practitioners say to start from real traces; the strongest critic of a pre-registered map | The map is pre-registered before any item exists | Answer only if the code allows it: the map amended under a new fingerprint |
| An open generator invites gaming | A fingerprint over the map and canon; MIT licence | Private canon and seeds and fresh splits per model release; check that rdlab supports reseeding before claiming it |

### Decisions and actionables

1. Measure rendered-item drift on about 100 items; it is the report's biggest "not found" and rdlab's biggest honest gap.
2. Adopt a blind-first hand-read protocol against automation bias.
3. Keep "evidence, not proof" around two-family certification.
4. The report found no prior machine-learning use of a capacity-zero pre-registered map. Print "we found no prior
   use", not "first".
5. Optional: a calibration pass to prune a large set to a small CI set.

### Cautions (check before anything is printed)

- The GPQA per-item cost figure is community hearsay, and the judge flip rates quoted from a vendor blog are not a study.
- Several 2026 papers the report names are post-knowledge and unchecked; they are left out of the sources here.
- MMLU 6.49% and 57% are sample estimates. The quadrant-chart coordinates in the report are the model's invention.
- Search snippets quote Kohli's accuracy gap two different ways; use the paper's figure.

relevance: `act`. This entry carries findings and wording limits only; diagrams and any story framing belong to the
newsletter.

## Claims

- [verified] Kohli 2026, "Nine Judges, Two Effective Votes", arXiv 2605.29800, reports about 2.18 effective votes for 9 judges from 7 families (via: web check, 2026-11-13)
- [verified] Kaplan and Irvin 2015 (PLOS ONE 10(8) e0132382) report 17 of 30 positive large NHLBI trials before registration against 2 of 25 after, chi-square 12.2, p = 0.0005, and the authors are cautious about causation (via: web check, 2026-11-13)
- [verified] Gema et al. 2025, "Are We Done with MMLU?" (NAACL 2025), estimate 6.49% flawed MMLU questions and 57% in Virology; the final MMLU-Redux is 5,700 questions (via: web check, 2026-11-13)
- [unverified] A two-family judge gate gives about 1.4 independent votes (the report's own arithmetic from an NLI correlation; inference)
- [unverified] At least 9.1% of GSM8K's test split is flawed and two models tied at 45 errors split to 2 against 17 after cleaning (Vendrow et al. 2025, via the report; not checked)
- [unverified] Open LLMs make a semantic error in 76-86% of zero-shot data-to-text outputs (Kasner and Dusek 2024, via the report; not checked)
- [unverified] Automation bias carries a risk ratio of about 1.26 when the tool is 80-90% accurate (Goddard et al. 2012, via the report; not checked)
- [unverified] Psychology Registered Reports were 96% positive against 44% in the standard literature (Scheel et al. 2021, via the report; not checked)
- [unverified] 47.3% of nursing exam items were flawed, and the flaws helped weak students (Tarrant and Ware 2008, via the report; not checked)
- [unverified] Specification bugs survive formal verification (Rozier 2016, via the report; not checked)
- [unverified] rdlab's third run found 6 of 11 failed pairs were real value-set faults the blind key missed (rdlab's own record as supplied with the seed; not re-checked here)

## Sources

- [primary] https://arxiv.org/abs/2406.04127 — Gema et al. 2025, Are We Done with MMLU?
- [primary] https://arxiv.org/abs/2605.29800 — Kohli 2026, Nine Judges, Two Effective Votes
- [primary] https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0132382 — Kaplan and Irvin 2015, PLOS ONE
- [primary] https://gradientscience.org/gsm8k-platinum/ — Vendrow et al. 2025, GSM8K-Platinum
- [primary] https://aclanthology.org/2024.acl-long.651/ — Kasner and Dusek 2024, Beyond Traditional Benchmarks
- [primary] https://arxiv.org/abs/2404.18796 — Verga et al. 2024, Replacing Judges with Juries
- [primary] https://arxiv.org/abs/2306.05685 — Zheng et al. 2023, Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena
- [primary] https://www.psychologicalscience.org/journals/ampps/25152459211007467/ — Scheel, Schijen and Lakens 2021, An Excess of Positive Results
- [primary] https://pubmed.ncbi.nlm.nih.gov/18230093/ — Tarrant and Ware 2008, item-writing flaws in nursing multiple-choice questions
- [primary] https://aclanthology.org/2024.acl-long.555/ — Balepur et al. 2024, Artifacts or Abduction
- [primary] https://arxiv.org/abs/2410.13341 — Dorner, Nastl and Hardt 2025, Limits to scalable evaluation at the frontier
- [aggregator] https://www.researchgate.net/publication/309744189_Specification_The_Biggest_Bottleneck_in_Formal_Methods_and_Autonomy — Rozier 2016 (a repository copy)
- [aggregator] https://www.researchgate.net/publication/51230614_Automation_bias_a_systematic_review_of_frequency_effect_mediators_and_mitigators — Goddard, Roudsari and Wyatt 2012 (a repository copy)
