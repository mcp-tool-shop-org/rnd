---
id: 2026-10-07-singing-quality-assessment
title: Automatic quality and artefact scoring for synthesised singing
date: 2026-10-07
kind: finding
relevance: act
fields: [audio, evaluation, machine-learning]
tags: [mos, singmos, sheet-ssqa, utmos, audiobox-aesthetics, versa, artefacts, singing-synthesis, sense-si]
---

## Summary

Singing needs singing-trained quality predictors: speech MOS models transfer
badly. SingMOS and Sheet-SSQA are the field-standard automatic scores (SoulX-Singer
reports both), and VERSA wraps many metrics behind one interface. No published
detector targets specific synthesis artefacts such as buzzy or honking vocoder
tone.

## Key points

- SingMOS (2024) and SingMOS-Pro (2025): singing MOS datasets. Pro has 7,981 clips
  from 41 systems, rated for overall quality, lyrics and melody.
- Speech MOS models score poorly on singing: UTMOS has utterance-level SRCC 0.36
  and DNSMOS 0.33. The best singing model reaches 0.51 at utterance level and 0.79
  at system level, so even the best is far better at ranking systems than at
  judging single clips.
- PS-SQA won the 2024 VoiceMOS singing track by adding pitch and spectral inputs
  to an SSL predictor.
- Meta Audiobox Aesthetics scores four axes for any audio (`pip install
  audiobox_aesthetics`, CC-BY 4.0 weights); it has no singing validation.
- NISQA predicts speech quality plus noisiness, colouration, discontinuity and
  loudness. Discontinuity might catch glitches; it is built for speech.
- VERSA: 65 metrics with singing synthesis as a named use case.
- Artefact detectors found in the literature are deepfake detectors, not quality
  tools.

## Studio relevance

Add SingMOS / Sheet-SSQA via VERSA as a ranking signal for deciding which takes a
human hears first, never as a pass line, since utterance-level agreement is
modest. Build artefact flags from signals the pipeline already has: octave jumps
and pitch discontinuities from the new tracker
([[2026-10-07-singing-pitch-trackers]]), plus spectral-flux spikes. Validate any
of these against the Director's review marks before trusting them
([[2026-10-07-calibrating-probabilistic-decision-layers]]).

## Claims

- [unverified] UTMOS reaches utterance-level SRCC 0.36 and DNSMOS 0.33 on SingMOS-Pro.
- [unverified] SoulX-Singer reports SingMOS and Sheet-SSQA as its automatic quality scores.
- [unverified] No published detector targets specific singing-synthesis artefacts (the agent's search found none).

## Sources

- [primary] https://arxiv.org/abs/2406.10911 — Tang, Shi, Wu, Jin, "SingMOS", 2024
- [primary] https://arxiv.org/html/2510.01812v4 — Tang et al., "SingMOS-Pro"
- [primary] https://huggingface.co/datasets/TangRain/SingMOS-Pro — SingMOS-Pro data
- [primary] https://arxiv.org/abs/2411.11123 — Shi, Ai, Lu, Du, Ling, "Pitch-and-Spectrum-Aware Singing Quality Assessment"
- [primary] https://arxiv.org/abs/2204.02152 — Saeki et al., "UTMOS", Interspeech 2022
- [primary] https://arxiv.org/abs/2409.09305 — Baba et al., "UTMOSv2", SLT 2024
- [primary] https://arxiv.org/pdf/2502.05139 — Meta FAIR, "Audiobox Aesthetics", 2025
- [primary] https://arxiv.org/abs/2104.09494 — Mittag et al., "NISQA", Interspeech 2021
- [primary] https://arxiv.org/abs/2412.17667 — Shi et al., "VERSA"
- [primary] https://github.com/wavlab-speech/versa — VERSA code
- [primary] https://arxiv.org/abs/2302.09198 — Sun et al., vocoder-artefact deepfake detection, CVPRW 2023
- [user] Question from the ai-jam-sessions session, 2026-10-07; research agent (claude-sonnet-5-5) web search
