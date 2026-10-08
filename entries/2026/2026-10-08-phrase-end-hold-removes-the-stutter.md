---
id: 2026-10-08-phrase-end-hold-removes-the-stutter
title: Holding the phrase-final note removes the "stutter" in placed singing
date: 2026-10-08
kind: finding
relevance: act
fields: [audio, music-performance]
tags: [phrasing, phrase-final-lengthening, kth-rules, placement, singing-synthesis, ai-jam-sessions]
---

## Summary

A vocal placed note by note onto a score clock ends each phrase where the note ends and
cuts to digital silence. Over a piano, the Director heard that as a stutter after
"hallelujah". Holding the last sung note into the following rest, then releasing it over
a short fade with a breath before the next onset, made it read as phrasing. In the KTH
performance rules' terms, this is phrase-final lengthening.

## Key points

- Hold the phrase's last note into the rest, up to **1.6×** its written length.
- Leave **0.2 s** of breath before the next onset.
- Release over **180 ms**.
- Stretch only sung source audio, never the silence after it.

## Studio relevance

Part of ai-jam-sessions placement (`hold_end` and `warp_map` in scripts/vocal_clock.py,
PR #106) and of step 6 of its sung-exemplar runbook. The vocology knowledge base in
readouts covers phrase-final breath and /h/ in synthesis. This entry is the measured
parameter set that worked here. The one-voice gate treats a hold as the note's release
and flags it only past 1.6 s ([[2026-10-08-voice-gate-pyannote-segmentation-on-sung-vocals]]).

## Claims

- [verified] With the hold, the Director judged the Battle Hymn "perfect now"; without it, he said it "reads like a stutter". This is one listener's verdict (user tier). (via: the Director by ear, 2026-10-08)
- [unverified] The same parameters suit Amazing Grace (3/4, 72 bpm) and America the Beautiful (4/4, 92 bpm). Both passed the Director's listen, but the hold was not A/B tested on them separately.

## Sources

- [primary] https://www.speech.kth.se/music/performance/performance_rules.html — KTH rule system for music performance (phrase-final punctuation)
- [rig] ai-jam-sessions scripts/vocal_clock.py HOLD_BREATH_S 0.2, HOLD_MAX_RATIO 1.6, HOLD_FADE_S 0.18; PR #106, 2026-10-08
- [user] The Director's listening verdicts, 2026-10-08
