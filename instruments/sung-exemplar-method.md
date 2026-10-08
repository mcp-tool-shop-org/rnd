---
id: sung-exemplar-method
title: Sung-exemplar method — a hymn to a published sung recording
date: 2026-10-08
kind: instrument
relevance: reference
fields: [audio, music]
tags: [instrument, singing-synthesis, ai-jam-sessions]
instrument_status: shipped
invoke: "Follow docs/sung-exemplar-method.md in ai-jam-sessions: arrange-hymn.ts, build-score-clock, takes on offrig, sing_clock.py, mix"
when: "A piece needs a sung exemplar: an arranged piano bed, a synthetic singer placed on the score clock, and the gates to pass before the Director listens."
where: "E:/AI/ai-jam-sessions · github.com/mcp-tool-shop-org/ai-jam-sessions/blob/main/docs/sung-exemplar-method.md"
---

## Summary

The runbook behind the three published hymns, in order:
- the hymn data;
- an LLM piano arrangement ([[2026-10-08-llm-piano-arrangement-from-a-generated-brief]]);
- R&D's interpretation shape;
- takes rendered on a rented GPU;
- phrase picking with the onset-outlier rule ([[2026-10-08-aligner-misdates-cause-sung-dropouts]]);
- placement with the phrase-end hold ([[2026-10-08-phrase-end-hold-removes-the-stutter]]);
- the timing, pitch and one-voice gates ([[2026-10-08-voice-gate-pyannote-segmentation-on-sung-vocals]]).

## Studio relevance

It costs money in two places: the OpenRouter arrangement (estimate first) and the offrig
pod. Local GPU scoring goes through the Publisher's grant.
