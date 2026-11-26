---
id: 2026-11-26-what-to-build-around-alpamayo-2-edge-and-the-dataset-licence
title: What to build around Alpamayo 2 Edge, and the dataset licence that gates it
date: 2026-11-26
kind: finding
relevance: watch
fields: [robotics, evaluation]
tags: [alpamayo, licence, deep-research]
---

## Summary

A Deep Research run surveyed what an open project with Alpamayo 2 Edge at its centre could be, and where it should
live. Its strongest idea is an audit tool that checks whether the model's written explanation matches the path it
actually drives, using simple kinematic checks with closed-form tests. That idea needs no training. Its weakest point
is the data. The report did not mention the terms of NVIDIA's own driving dataset, and those terms are narrow:
- internal development of autonomous vehicles only;
- no derivative works, hosting or redistribution;
- the licence expires a year after download, and every copy must then be destroyed.

**Parked (the maintainer's decision, 2026-11-26):** the licence rows are recorded and nothing else is done. There is no
project and no audit repo, and nothing touches the dataset.

## Key points

- **Dataset terms** (the NVIDIA Autonomous Vehicle Dataset License Agreement, read 2026-11-26; the exact clauses are in
  `licences/registry.json` under `nvidia-physicalai-av-dataset`):
  - use solely for internal development of autonomous vehicles and driver-assistance systems using NVIDIA technology;
  - no derivative works, and no hosting, distributing or otherwise making it available;
  - the agreement expires 12 months after first download, and copies are destroyed on termination;
  - the dataset is confidential, including benchmarking results relating to it;
  - access is gated.
- **The model itself** is open: OpenMDW-1.1 weights, Apache-2.0 code, and its backbone Cosmos 3 Edge also under
  OpenMDW-1.1 (registry rows added).
- **Not ready yet.** NVIDIA's simulator post-training recipe supports only the larger Alpamayo 1.5. The Edge recipe is
  listed as coming. The reference-free judge checkpoint reads only two front cameras.
- **Where it would live, if reopened.** A new standalone repository, not the teacher-critic training project: an explanation audit
  is outside that project's stated purpose. Critic-guided training on Alpamayo stays parked until that project's critic
  measurably moves its student and NVIDIA ships the Edge recipe.

## Studio relevance

`watch`, parked 2026-11-26 (the maintainer's decision). Only the licence registry rows are kept. There is no project,
no audit repo, and no download of or work on the NVIDIA dataset. If the idea is reopened, the first question is still
whether an open faithfulness audit with no vehicle counts as "internal development of autonomous vehicles". Either way,
nothing derived from the NVIDIA dataset would ever ship in a public repo.

## Claims

- [verified] The PhysicalAI-AV dataset licence limits use to internal AV/ADAS development with NVIDIA technology, bars
  derivative works and hosting, and expires 12 months after download. (via: the agreement text on the Hugging Face
  dataset card, read 2026-11-26; clauses quoted in the licence registry)
- [verified] Alpamayo 2 Edge weights are under OpenMDW-1.1, and its base nvidia/Cosmos3-Edge is under OpenMDW-1.1 and
  "ready for commercial and non-commercial use". (via: both model cards' raw READMEs, read 2026-11-26)
- [unverified] The report's camera-rig figures, attributed to a crash-anticipation paper, and a 14.3% "silent failure"
  rate were not on the cited abstract pages.

## Sources

- [primary] https://huggingface.co/datasets/nvidia/PhysicalAI-Autonomous-Vehicles — NVIDIA, dataset card and licence
  agreement.
- [primary] https://huggingface.co/nvidia/Alpamayo2-Edge — NVIDIA, model card.
- [primary] https://huggingface.co/nvidia/Cosmos3-Edge — NVIDIA, model card.
- [aggregator] https://gemini.google.com/ — Gemini Deep Research (Gemini 4 Carbon), seed 67, 2026-11-26: report on a project built around an open driving reasoning model (kept
  verbatim in the lab's private notes, with a harvest).
