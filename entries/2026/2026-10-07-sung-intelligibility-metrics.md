---
id: 2026-10-07-sung-intelligibility-metrics
title: Measuring intelligibility of sung audio
date: 2026-10-07
kind: finding
relevance: act
fields: [audio, speech, evaluation]
tags: [intelligibility, whisper, wer, stoi, lyrics-transcription, singing, sense-si]
---

## Summary

The field's working proxy for sung intelligibility is ASR error rate: Whisper
large-v3 WER/CER for English, the metric SoulX-Singer itself reports. But ASR
degrades sharply on singing for reasons that are not synthesis faults, so the
number is useful only relative to itself.

## Key points

- Whisper on Schubert's Winterreise scored WER 0.56 sung against 0.14 for the
  same text recited. Singing style hurts more than accompaniment.
- Jam-ALT (ISMIR 2024) benchmarks Whisper large-v2/v3 on full songs, with and
  without source separation. Full-mix WER of roughly 28–36% is reported second-hand.
- Plain STOI is a speech metric and needs a clean reference, which a generated
  take lacks. A singing-adapted STOI plus vocal features reached r = 0.81 against
  human intelligibility ratings (Sharma & Wang).
- Perception: high pitch (soprano range) and melisma are the main reasons sung
  words are hard to understand, for humans as well as for ASR.
- SoulX-Singer scores intelligibility with Whisper large-v3 (English) and
  Paraformer (Mandarin, Cantonese).

## Studio relevance

Add Whisper large-v3 WER/CER per isolated take, scored against the lyrics already
aligned by HubertFA. Track it across versions of the same song rather than
against a pass line, and expect high or melismatic passages to score worse for
reasons that are not faults. A per-word view (which aligned words Whisper
missed) is more actionable than a single WER.

## Claims

- [unverified] Unmodified Whisper had WER 0.56 on sung Winterreise versus 0.14 recited.
- [unverified] A singing-adapted STOI regression reached r = 0.81 with human intelligibility ratings.
- [unverified] Full-mix Whisper WER on Jam-ALT is about 28–36% (secondary figure, not checked in the paper).

## Sources

- [primary] https://aclanthology.org/2024.nlp4musa-1.3 — Berendes, Schwär, Müller, "Lyrics Transcription in Western Classical Music with Whisper", NLP4MusA 2024
- [primary] https://arxiv.org/pdf/2507.01349 — Suda et al., "IdolSongsJp Corpus"
- [primary] https://arxiv.org/pdf/2311.13987 — Cífka, Schreiber, Miner, Stöter, "Jam-ALT", ISMIR 2024
- [primary] https://smcnus.comp.nus.edu.sg/archive/pdf/2019-2021/2019_SingingIntelligibility.pdf — Sharma & Wang, "Automatic Evaluation of Song Intelligibility using Singing Adapted STOI and Vocal-specific Features"
- [primary] https://pmc.ncbi.nlm.nih.gov/articles/PMC4155173/ — Fine & Ginsborg, "Making myself understood", Frontiers in Psychology 2014
- [primary] https://arxiv.org/html/2602.07803v2 — SoulX-Singer, arXiv 2602.07803
- [user] Question from the ai-jam-sessions session, 2026-10-07; research agent (claude-sonnet-5-5) web search
