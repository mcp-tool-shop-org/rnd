---
id: 2026-10-07-audio-text-embedding-models
title: Audio-text embedding models (the CLIP/SigLIP counterpart for ears)
date: 2026-10-07
kind: concept
relevance: watch
fields: [audio, machine-learning, multimodal]
tags: [clap, imagebind, muq, s2cap, embeddings, zero-shot, sense-si]
---

## Summary

The audio counterpart to CLIP/SigLIP image-text scoring is the CLAP family:
contrastive audio-text embeddings that support retrieval and zero-shot
classification. That pairing is what an eyes/ears instrument family would copy.
None is validated as a scorer of singing-specific attributes.

## Key points

- LAION-CLAP (ICASSP 2023): trained on 633k audio-text pairs, public weights.
- Microsoft CLAP (ICASSP 2023): evaluated on 16 tasks including music and speech;
  `pip install msclap`.
- ImageBind (CVPR 2023): one embedding for six modalities, anchored on images.
  Audio reaches text only through images, so it is weaker for fine audio-text
  scoring.
- MuQ-MuLan (2025): strong music-text embedding, but CC-BY-NC-SA, which rules it
  out for a commercial studio.
- S2Cap (CIKM 2025): a singing-style captioning dataset (pitch, volume, tempo,
  mood, singer gender and age, genre). The closest singing-attribute resource,
  but a dataset and baseline, not a scorer.

## Studio relevance

A CLAP model is the natural sibling to sense-si's SigLIP2 eyes. Text prompts for
singing attributes ("breathy", "strained", "on pitch") are untested experiments
until they are checked against review marks. Check licences first: MuQ is
non-commercial.

## Claims

- [unverified] No CLAP-family model has been validated for scoring singing-specific attributes.
- [unverified] MuQ / MuQ-MuLan weights and code are CC-BY-NC-SA 4.0.

## Sources

- [primary] https://arxiv.org/pdf/2211.06687 — Wu et al., "Large-scale Contrastive Language-Audio Pretraining" (LAION-CLAP), ICASSP 2023
- [primary] https://arxiv.org/pdf/2206.04769 — Elizalde et al., "CLAP: Learning Audio Concepts from Natural Language Supervision", ICASSP 2023
- [primary] https://arxiv.org/abs/2305.05665 — Girdhar et al., "ImageBind", CVPR 2023
- [primary] https://arxiv.org/abs/2501.01108 — Zhu et al., "MuQ", 2025
- [primary] https://arxiv.org/abs/2409.09866 — Ok & Lee, "S2Cap", CIKM 2025
- [primary] https://zenodo.org/records/15673764 — S2Cap data
- [user] Question from the ai-jam-sessions session, 2026-10-07; research agent (claude-sonnet-5-5) web search
