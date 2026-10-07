---
id: 2026-10-07-singing-pitch-trackers
title: Fast pitch trackers for singing voice (pYIN replacements)
date: 2026-10-07
kind: finding
relevance: act
fields: [audio, signal-processing, machine-learning]
tags: [pitch, f0, swiftf0, fcpe, rmvpe, pesto, crepe, pyin, ai-jam-sessions, sense-si]
---

## Summary

The ai-jam-sessions vocal pipeline spends about 3 minutes per 165 s take on librosa
pYIN, its slowest step. Several modern trackers are one to two orders of magnitude
faster and at least as accurate on singing. Two of them are MIT-licensed and
pip-installable today: SwiftF0 (CPU, tiny) and FCPE (GPU, near-RMVPE accuracy).

## Key points

- **SwiftF0** (2025): about 96k parameters, ONNX Runtime on CPU, around 42x faster
  than CREPE. 16 kHz input, 16 ms hop, range 46.9–2093 Hz, with a confidence value.
  At 10 dB SNR it reaches RPA 89.9% versus 87.0% for pYIN. `pip install swift-f0` (MIT).
- **FCPE** (2025): 96.79% RPA on clean MIR-1K, about 1 point below RMVPE and about
  5x faster (RTF 0.0062 on an RTX 4090). Trained on singing resynthesis.
  `pip install torchfcpe` (MIT, CUDA).
- **RMVPE** (Interspeech 2023): the accuracy reference for vocal pitch, even in
  polyphonic music (97.77% RPA on MIR-1K per FCPE's comparison). Licence and
  packaging not confirmed.
- **PESTO** (ISMIR 2023 best paper): under 30k parameters, self-supervised, near
  CREPE accuracy. `pesto-pitch` supports GPU but is LGPL-3.0.
- **PENN / FCNF0++** (2023): fast, with an entropy-based voicing estimate. `penn` on
  pip; licence not confirmed.
- **torchcrepe**: MIT and CUDA, a safe fallback, but weaker than pYIN under noise.
- No published head-to-head on clean sung audio covers all of these.

## Studio relevance

Recommendation:

1. Make SwiftF0 the default pitch pass. It turns minutes into seconds without
   touching the GPU, which the listener model already occupies.
2. Confirm with FCPE on the 5090.
3. Before switching, run a three-way agreement check against pYIN on a handful
   of real takes. Keep pYIN only for takes the trackers disagree on.

Octave-jump and discontinuity flags from the new pitch track are also the
cheapest artefact detector available
([[2026-10-07-singing-quality-assessment]]).

## Claims

- [unverified] SwiftF0 reaches RPA 89.9% at 10 dB SNR versus pYIN 87.0% and CREPE 72.3%.
- [unverified] FCPE reaches 96.79% RPA on MIR-1K at RTF 0.0062 on an RTX 4090.
- [unverified] torchfcpe and swift-f0 are MIT-licensed; pesto-pitch is LGPL-3.0.
- [unverified] RMVPE's licence is unconfirmed; check its repository before depending on it.

## Sources

- [primary] https://arxiv.org/abs/2306.15412 — Wei, Cao, Dan, Chen, "RMVPE: A Robust Model for Vocal Pitch Estimation in Polyphonic Music", Interspeech 2023
- [primary] https://github.com/yxlllc/RMVPE — RMVPE code
- [primary] https://arxiv.org/html/2509.15140v1 — "FCPE: A Fast Context-based Pitch Estimation Model", arXiv 2509.15140
- [primary] https://pypi.org/project/torchfcpe/ — torchfcpe
- [primary] https://arxiv.org/html/2508.18440v1 — "SwiftF0: Fast and Accurate Monophonic Pitch Detection", arXiv 2508.18440
- [primary] https://pypi.org/project/swift-f0/ — swift-f0
- [primary] https://github.com/lars76/pitch-benchmark — pitch-benchmark (19 trackers, 10 corpora)
- [primary] https://arxiv.org/pdf/2309.02265 — Riou, Lattner, Hadjeres, Peeters, "PESTO", ISMIR 2023
- [primary] https://github.com/SonyCSLParis/pesto — PESTO code
- [primary] https://arxiv.org/pdf/2301.12258 — Morrison, Hsieh, Pruyne, Pardo, "Cross-domain Neural Pitch and Periodicity Estimation"
- [primary] https://pypi.org/project/torchcrepe — torchcrepe
- [user] Question from the ai-jam-sessions session, 2026-10-07; research agent (claude-sonnet-5-5) web search
