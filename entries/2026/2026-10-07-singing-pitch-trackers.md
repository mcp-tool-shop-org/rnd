---
id: 2026-10-07-singing-pitch-trackers
title: Fast pitch trackers for singing voice (FCPE replaces pYIN)
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

**Settled by measurement (ai-jam-sessions, 2026-10-07, RTX 5090):** FCPE replaces pYIN
for the gate. SwiftF0 is dominated, even for ranking.

Synthetic ±40-cent vibrato at 5.5 Hz on D4 (mean cents; p5..p95 swing):

| tracker | mean | swing |
|---|---|---|
| pYIN | +1.1 | −40.0..+40.0 |
| SwiftF0 | +5.7 | −22.2..+32.9 (clipped) |
| FCPE | +0.3 | −42.7..+42.1 |

Real singing: four SoulX-Singer takes of public-domain hymns, 721 notes, read
through the gate's own note windows. Figures are per-note median cents compared
against pYIN:

| | median diff | median abs | p90 abs | >25 c | pass/warn/fail agreement |
|---|---|---|---|---|---|
| SwiftF0 | −1.0 | 8.0 | 19.5 | 4.0% | 85–87% |
| FCPE | −1.7 | 2.7 | 7.0 | 1.0% | 91–94% |

Time per 165–196 s take:

| tracker | time |
|---|---|
| pYIN | 160–190 s |
| SwiftF0 | 2.2–3.4 s |
| FCPE | 0.2 s (3.7 s on the first call, including the model load) |

That makes FCPE about 800× faster than pYIN.

- SwiftF0 adds false fails, for example 7 against pYIN's 1 on one take; FCPE's fails
  are nearly pYIN's set.
- SwiftF0's vibrato clipping reproduces. Its bias depends on the test tone: +20.6 c
  on the 2026-09-05 tone, +5.7 c here.
- Practical note: normalise input to peak ≤ 1.0 before FCPE, or its mel extractor
  complains.
- The literature's accuracy ranking (RMVPE ≥ FCPE > others on singing) held on our
  own takes, while SwiftF0's published noise robustness did not translate into
  gate-grade accuracy on clean synthesised singing.

Octave-jump and discontinuity flags from the new pitch track are also the
cheapest artefact detector available
([[2026-10-07-singing-quality-assessment]]).

## Claims

- [verified] FCPE agrees with pYIN to a median 2.7 cents (p90 7.0) per note on 721 notes of real synthesised singing, and keeps a ±40-cent vibrato at +0.3 cents bias with full swing. (via: ai-jam-sessions three-way measurement on the RTX 5090, 2026-10-07)
- [verified] FCPE takes about 0.2 s per 165–196 s take after model load, versus 160–190 s for pYIN. (via: ai-jam-sessions three-way measurement on the RTX 5090, 2026-10-07)
- [verified] SwiftF0 clips vibrato excursion (−22.2..+32.9 c on a ±40 c vibrato) and adds false gate fails. (via: ai-jam-sessions measurements 2026-09-05 and 2026-10-07)
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
- [rig] ai-jam-sessions three-way comparison (torchfcpe 0.0.4, swift-f0, librosa pYIN hop 240 @ 48 kHz), RTX 5090, 2026-10-07
- [user] Question from the ai-jam-sessions session, 2026-10-07; research agent (claude-sonnet-5-5) web search
