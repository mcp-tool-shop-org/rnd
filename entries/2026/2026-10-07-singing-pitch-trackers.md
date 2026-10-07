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

**Prior in-house measurement (ai-jam-sessions, 2026-09-05):** its pitch gate
(`scripts/vocal_clock.py`, `track_f0`) chose pYIN over SwiftF0. On a synthetic
±40-cent vibrato:

- pYIN read +2.8 cents mean and kept the full swing;
- SwiftF0 read +20.6 cents mean and clipped the excursion.

The gate fails a note at 50 cents and warns at 25, so a 20-cent bias disqualifies
SwiftF0 *for gating*. It stayed in the code as a cross-check only. That was one
synthetic test.

Revised recommendation:

1. Run a three-way check (pYIN, SwiftF0, FCPE) on real takes. ai-jam-sessions is
   running it on hymn takes, and its numbers belong in this entry.
2. For the gate: FCPE (GPU) is the candidate to replace pYIN, provided it keeps
   vibrato depth and stays near zero bias. Otherwise keep pYIN.
3. SwiftF0 may still suit ranking, where speed matters and a uniform bias
   cancels out.

Octave-jump and discontinuity flags from the new pitch track are also the
cheapest artefact detector available
([[2026-10-07-singing-quality-assessment]]).

## Claims

- [verified] On a synthetic ±40-cent vibrato, SwiftF0 read +20.6 cents mean bias and clipped the excursion, while pYIN read +2.8 cents with the full swing. (via: ai-jam-sessions vocal_clock measurement, 2026-09-05, reported by that session 2026-10-07)
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
- [rig] ai-jam-sessions scripts/vocal_clock.py track_f0 comparison, 2026-09-05
- [user] Question from the ai-jam-sessions session, 2026-10-07; research agent (claude-sonnet-5-5) web search
