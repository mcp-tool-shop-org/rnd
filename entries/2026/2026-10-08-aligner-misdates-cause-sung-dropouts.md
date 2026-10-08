---
id: 2026-10-08-aligner-misdates-cause-sung-dropouts
title: Misdated syllable onsets cause dropouts in phrase-picked singing
date: 2026-10-08
kind: finding
relevance: act
fields: [audio, signal-processing]
tags: [forced-alignment, onset-detection, outliers, phrase-picking, singing-synthesis, ai-jam-sessions]
---

## Summary

When a sung vocal is assembled phrase by phrase from several synthetic takes, each
syllable is placed by the onset dated for it in its take, so a wrong date places the wrong
audio. In the published Battle Hymn, one syllable ("jah") was dated 0.7 s late, onto its
own fading tail, and placement put near-silence where the word should be. A neighbour
rule catches it: a syllable's onset should agree with where its neighbours put the take.

## Key points

- Rule: undate any onset more than **0.3 s** from the median offset (dated minus score
  time) of up to **4 neighbours on each side**. The syllable is then taken from another
  take.
- Run it **before and after** the aligner fills undated syllables. The first fix covered
  only detector dates and missed this case, because here the forced aligner supplied the
  bad date.
- Timing and pitch gates do not see it. The misplaced audio was in tune, and its onset was
  where the take said it was.
- It also found a misdated "all" in America the Beautiful. Two of that song's 20 phrases
  now come from other takes, with timing and pitch unchanged.

## Studio relevance

Part of the ai-jam-sessions pick (`undate_outliers` in scripts/vocal_clock.py, PR #112) and
of the runbook. The one-voice gate found the symptom
([[2026-10-08-voice-gate-pyannote-segmentation-on-sung-vocals]]); this rule removes the
cause. Re-picking a finished song after a rule change needs no new takes and no GPU.

## Claims

- [verified] The Battle Hymn's silent "jah" at 0:52 came from an aligner date 0.7 s late. With the rule, the re-picked syllable is audible, and the Director called the result "much better". (via: ai-jam-sessions re-pick and listening, 2026-10-08)
- [verified] The rule changed America the Beautiful's pick in two phrases and left Amazing Grace unchanged. (via: ai-jam-sessions re-pick of all three hymns, 2026-10-08)
- [unverified] 0.3 s and 4 neighbours were tuned on three hymns at 72–95 bpm; faster music may need a tighter threshold.

## Sources

- [rig] ai-jam-sessions scripts/vocal_clock.py `undate_outliers` (DATE_OUTLIER_S 0.3, DATE_NEIGHBOURS 4); PR #112, 2026-10-08
- [user] The Director's listening verdict on the corrected Battle Hymn, 2026-10-08
