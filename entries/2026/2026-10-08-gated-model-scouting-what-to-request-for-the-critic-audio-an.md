---
id: 2026-10-08-gated-model-scouting-what-to-request-for-the-critic-audio-an
title: Gated model scouting — what to request for the critic, audio and visual research
date: 2026-10-08
kind: catalog
relevance: act
fields: [machine-learning, audio, vision]
tags: [gated-models, hugging-face, licences, judges, feature-sources, scouting]
---

## Summary

The Director holds gated Hugging Face access to Meta's Llama 3.2 and 3.1
collections, briaai/RMBG-2.0, DINOv3 and FLUX.1, and asked R&D to scout other
gated repos that fit the studio's research.

Three agents checked repos live against the Hugging Face API on 2026-10-08:
- language, judge and reward models;
- audio;
- vision.
The studio's model notes are partly stale. The biggest change: **Gemma 4 is
Apache-2.0 and not gated**, while Gemma 3 and ShieldGemma are still gated under
Gemma terms.

Gating is rarer than expected among the useful repos. Many of the best
candidates are open. Several are non-commercial (fine for research, not for
shipping). Licences below are the API's licence tags; any marked "check card"
need the card read before relying on them, and **no access was requested and no
terms were accepted**. That is the Director's call.

## Key points

**Gated repos worth requesting** (gating type, licence tag, the thread each
serves):

| repo | gate | licence | serves |
|---|---|---|---|
| google/gemma-3-4b-it, gemma-3-1b-it | manual | Gemma terms (check card) | gated matched-size feature source from a third family |
| google/shieldgemma-2-4b-it | manual | Gemma terms | second-family safety judge (one Gemma approval covers it) |
| CohereLabs/tiny-aya-base-32K | auto | CC-BY-NC-4.0 | fourth family at about 3B, research only |
| swiss-ai/Apertus-v1.5-8B (base, SFT, DPO, RLVR) | auto | Apache-2.0 + acceptable-use policy | fully open data; separate training stages test "same lineage" recognition |
| meta-llama/Llama-Guard-4-12B | manual | Llama 4 Community | judge baseline, fits easily |
| CohereLabs/c4ai-command-r-08-2024 | auto | CC-BY-NC-4.0 | Cohere planter at 32B, 4-bit only |
| pyannote/segmentation-3.0, speaker-diarization-community-1 | auto | MIT; CC-BY-4.0 | where singing starts and stops, to locate joins in sung mixes |
| stabilityai/stable-audio-open-1.0 | auto (form) | Stable Audio Community (check card) | VAE latents as an extra audio feature source |
| facebook/sam3 | manual | Meta SAM licence (check card) | text-prompted segmentation for sprite masks |
| facebook/sam-3d-objects | manual | other (check card) | single image to 3D, a TRELLIS rival |
| black-forest-labs/FLUX.1-Kontext-dev, FLUX.2-dev | auto | FLUX non-commercial | instruction-based editing of sprite views, experiments only |
| google/paligemma2-10b-pt-448 | manual | Gemma terms | base for fine-tuning a visual judge, if wanted |

**Open repos worth trying now** (no request needed):
- **Matched-size feature sources from new families** for the critic
  self-recognition test (aspire-si #46):
  - mistralai/Ministral-3-3B-Instruct-2512 (Apache-2.0);
  - ibm-granite/granite-4.1-3b (Apache-2.0);
  - google/gemma-4-E4B-it (Apache-2.0);
  - allenai OLMo 3 7B (Apache-2.0, fully open data).
- **Judges, reward models and fact-checkers:**
  - Skywork-Reward-V2, in Qwen3-8B and Llama-3.2-3B variants: the same
    reward recipe in two families (Apache-2.0; the Llama variant follows
    Llama terms);
  - granite-guardian-4.1-8b (Apache-2.0);
  - Vectara HHEM (110M, Apache-2.0);
  - MiniCheck-Flan-T5-Large (MIT) and Bespoke-MiniCheck-7B (check card);
  - nvidia/Qwen-3-Nemotron-32B-Reward (NVIDIA Open Model License, check card).
- **Audio:**
  - MuQ-large-msd-iter: the only new music-trained encoder, CC-BY-NC like
    MERT; Dasheng stays the shippable one;
  - facebook/audiobox-aesthetics (CC-BY-4.0, about 0.8 GB, per-clip quality
    scores);
  - SongEval: singing-specific scores including breath and phrasing, weights
    on GitHub, licence unverified;
  - local audio-language judges from different labs: Qwen2.5-Omni-7B,
    Step-Audio-2-mini (both Apache-2.0) and Kimi-Audio-7B (MIT, check card);
  - RMVPE pitch plus RoFormer separators (lj1995/VoiceConversionWebUI, MIT).
- **Vision:**
  - Qwen3-VL-8B and 32B (Apache-2.0; 32B at 4-bit): the strongest open
    visual judges;
  - UnifiedReward-2.0-qwen3vl-8b (MIT): an image quality and preference judge
    to test on the cases where SigLIP2 failed;
  - Gemma 4 31B as a second-family visual judge (vision support to confirm on
    the card);
  - microsoft/TRELLIS.2-4B (MIT): mesh-stage upgrade candidate;
  - SAM 2.1 (Apache-2.0) as the ungated segmentation fallback.

**Skip:**
- too big for one 32 GB card: Llama 4 Scout (108B total), Mistral Medium and
  Large, the Nemotron 70B rewards;
- superseded by ungated equivalents: Gemma 3 27B, Llama Guard 3;
- off-topic: Seamless, AudioSeal, MusicGen;
- weak on sung lyrics: speech ASR (Parakeet, Canary);
- CLIP-era image scorers (ImageReward, PickScore, Q-Align), which share
  SigLIP2's weakness;
- non-commercial depth and pose models (Depth-Anything V2, Sapiens): research
  only, if at all.

## Studio relevance

**Recommendation, in order of research value:**
1. **Request Gemma 3 (4B, 1B) together with ShieldGemma 2**, under one Gemma
   approval. They give the critic self-recognition test a gated third family,
   plus a safety judge.
2. **Request SAM 3 and SAM 3D Objects** (manual). They are the two gated repos
   with direct pipeline value (sprite masks; image to 3D), but read SAM 3D's
   licence first.
3. **Click-through, research-only, any time:** pyannote (both repos),
   tiny-aya-base, Apertus, and Stable Audio Open.
4. **Llama Guard 4** (manual), as a judge baseline.
5. **FLUX Kontext and FLUX.2** if image editing of sprite views is wanted;
   non-commercial.

**No request needed:**
- For the self-recognition test, aspire-si's #46 can add matched-size sources
  from new families today: Ministral 3B, Granite 4.1 3B, Gemma 4 E4B.
- The visual-judge gap can be tested at once with Qwen3-VL-8B and
  UnifiedReward-2.0.

**Stale knowledge:** readouts' `model-knowledge` KB predates Gemma 4's Apache
release and likely other 2026 releases (FLUX.2, SAM 3, TRELLIS.2,
Qwen3-VL). It is due a refresh through the readouts build.

## Access status (2026-10-08, from the Director's gated-repo page)

- **Accepted the same day:**
  - Google's Gemma models family (covers Gemma 3 and ShieldGemma);
  - CohereLabs/tiny-aya-base;
  - pyannote/speaker-diarization-3.1 and pyannote/segmentation-3.0;
  - stabilityai/stable-audio-open-1.0.
- **Pending:**
  - the Llama 4 collection (expected to include Llama Guard 4);
  - facebook/sam-3d-objects.
- **Not yet requested:** facebook/sam3, swiss-ai/Apertus-v1.5-8B, FLUX Kontext /
  FLUX.2, PaliGemma 2.

## Gemma Terms of Use: what they mean here

The Director pasted the Gemma Terms of Use. This is R&D's reading, not legal
advice, and it needs one careful check before anything Gemma-3-based is
published:
- **Outputs are free to use.** Google claims no rights in Outputs, and Outputs
  are not Model Derivatives. Gemma-3-planted pairs, and labels or scores it
  produces, can go into datasets, public ones included.
- **"Model Derivatives"** covers modifications of Gemma, works based on it, and
  models trained on its outputs (distillation, synthetic data) *in order to
  perform similarly to Gemma*.
  - A critic trained on Gemma-planted pairs learns to find errors, not to
    imitate Gemma, so it reads as outside that clause.
  - A critic head that runs on Gemma 3's hidden states is a work based on Gemma:
    it needs Gemma at inference.
- **Distribution, including hosting it as a service, carries obligations:**
  - pass on the Section 3.2 use restrictions;
  - give recipients the terms;
  - mark modified files;
  - ship the required Notice file.
  Internal research use triggers none of these. The Prohibited Use Policy
  always applies.
- **Rule of thumb:** Gemma 3 for research comparisons; **Gemma 4 (Apache-2.0)
  for anything that ships**, since it carries none of these terms.

## Claims

- [verified] google/gemma-4-31B-it and the smaller Gemma 4 instruct models are Apache-2.0 and not gated, while google/gemma-3-27b-it, gemma-3-4b-it and shieldgemma-2-4b-it are gated with manual approval. (via: research agent reading the Hugging Face model API, 2026-10-08)
- [verified] pyannote/segmentation-3.0 (MIT) and pyannote/speaker-diarization-community-1 (CC-BY-4.0) are gated with automatic approval; stabilityai/stable-audio-open-1.0 is gated by an automatic form. (via: research agent reading the Hugging Face model API, 2026-10-08)
- [verified] facebook/sam3 and facebook/sam-3d-objects are gated with manual approval under non-standard ("other") licences. (via: research agent reading the Hugging Face model API, 2026-10-08)
- [verified] Qwen3-VL-8B/32B-Instruct are Apache-2.0 and ungated; UnifiedReward-2.0-qwen3vl-8b and TRELLIS.2-4B are MIT and ungated. (via: research agent reading the Hugging Face model API, 2026-10-08)
- [unverified] Critics trained on Gemma-3-planted data are not Model Derivatives under the Gemma Terms of Use, because they are not trained to perform similarly to Gemma (R&D's reading of the terms the Director pasted, 2026-10-08; not legal advice).
- [unverified] Licence terms beyond the API's licence tags (use restrictions, any clause against training other models) for the Gemma terms, the SAM licence, Stable Audio Community, EXAONE and Bespoke-MiniCheck. Read each card before relying on it.

## Sources

- [primary] https://huggingface.co/api/models — Hugging Face model API records for each repo above, read 2026-10-08
- [primary] https://huggingface.co/google/gemma-4-31B-it — Gemma 4 31B card
- [primary] https://huggingface.co/facebook/sam3 — SAM 3
- [primary] https://huggingface.co/facebook/sam-3d-objects — SAM 3D Objects
- [primary] https://huggingface.co/pyannote/segmentation-3.0 — pyannote segmentation
- [primary] https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct — Qwen3-VL
- [primary] https://huggingface.co/facebook/audiobox-aesthetics — Audiobox Aesthetics
- [primary] https://huggingface.co/OpenMuQ/MuQ-large-msd-iter — MuQ
- [aggregator] https://llmreference.com/ — Nemotron 3 Content Safety details, not cross-checked
- [user] Screenshot of the Director's gated-repo access list, and his request, 2026-10-08; three research agents (claude-sonnet-5-5)
