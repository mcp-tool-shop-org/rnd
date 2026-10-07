---
id: 2026-10-07-join-artefact-detection
title: Detecting audible glitches at segment joins in synthesised singing
date: 2026-10-07
kind: finding
relevance: act
fields: [audio, signal-processing, psychoacoustics, evaluation]
tags: [join-cost, splice, concatenation, click, repeat-skip, gap-detection, singing-synthesis, sense-si]
---

## Summary

Raised by ai-jam-sessions / sense-si on 2026-10-07. The defects the Director
heard in SoulX-Singer takes were mostly audio replayed or skipped at segment
joins and noise at segment boundaries. Timing and pitch instruments cannot see
either.

The literature validates only one thing against listeners: spectral mismatch
across concatenative-TTS joins, and only modestly. It has nothing validated for
repeated or skipped fragments, boundary noise bursts, or singing. Join detection
here has to be built from known join positions and calibrated on the studio's
own marks.

## Key points

- **Join cost vs listeners (speech TTS):**
  - spectral join distances correlate with listener scores only by phone,
    about 0.5–0.78 for some vowels and about 0 for others (Vepa, King &
    Taylor 2002);
  - they were significant in 6–7 of 10 test cases (Vepa & King 2005).
- **Best detection numbers:**
  - MFCC Euclidean distance over one pitch period either side of the join
    reached AUC 0.76; complex-Morlet wavelet features reached 0.79
    (Kirkpatrick et al. 2006);
  - at 5% false alarms, symmetric KL on LPC spectra caught 30.9% of audible
    joins, and combined harmonic + AM/FM features 56% (Pantazis et al. 2005);
  - so even the best spectral features miss about half.
- **Skip/repeat errors in seq2seq TTS** were detected from the attention matrix
  with F up to 0.89/0.96 (Valentini-Botinhao & King 2021). The transferable idea
  is to compare the output against what it should contain, e.g. forced-alignment
  deletions or unaligned stretches per join.
- **Clicks:** a hearing-model detector found 78% of audible clicks at 4% false
  alarms on vinyl (Rund et al. 2016).
- **Audibility:**
  - gap-in-noise thresholds average about 4.8 ms (Musiek et al. 2005), and
    speech gaps are higher;
  - silent dropouts are detected and localised, while noise bursts over speech
    often are not (phonemic restoration);
  - F0 jumps matter only above about 1 semitone, and only in sonorants
    (Bořil & Skarnitzl 2019).
- **No validated threshold exists** for a minimum audible repeated or skipped
  fragment, or for crossfade length. Practitioner advice: a few ms to stop a
  click, about 10 ms for speech edits.
- **Tools:**
  - librosa (ISC): RMS, spectral flux, MFCC, onsets;
  - ruptures (BSD-2): change points;
  - praat-parselmouth: HNR, jitter, shimmer, but it is GPLv3, so check before
    bundling;
  - VERSA (Apache-2.0): quality metrics.
  Nothing pip-installable does join cost or repeat detection.

## Studio relevance

Compute at each known join, in this order. Fit every threshold on the 51 marked
phrases, and compare each feature at the join with the same feature at non-join
positions in the same take.

1. **Window-matched spectral jump.** MFCC or log-mel KL over one pitch period
   (about 5–15 ms) either side, normalised by the take's typical frame-to-frame
   distance. It is the only listener-validated measure; expect it to catch a
   third to a half of bad joins.
2. **Repeat/skip test.** A cross-similarity matrix between the 0.5–2 s before
   and after the join, built on **delta** log-mel (frame-to-frame change), not
   the spectra themselves; held vowels make plain log-mel self-similar (see the
   measured note below). An off-diagonal ridge means a repeat, a displaced
   diagonal means a skip. Back it with forced-alignment deletions per join.
   This targets the main defect, but it is unvalidated.
3. **Boundary click/noise.** Within ±10 ms of the join, find the peak energy
   jump and the high-pass first-difference energy, each as a z-score against
   the surrounding 200 ms. Add the waveform step and a spectral-flatness or HNR
   rise.
4. **F0/voicing across the join.** Flag a jump over 1 semitone, an octave ratio,
   or a voiced/unvoiced flip within ±20 ms. This is cheap and reuses the FCPE
   track ([[2026-10-07-singing-pitch-trackers]]).

**Measured on the studio's own takes** (ai-jam-sessions PR #88,
`scripts/phrase_evidence.py`, 2026-10-07; 124 phrases from 7 reviewed mixes, 51
marked, labels from mark windows [t − 1.0, t + 0.2]):

- **Correction to feature 2.** Log-mel cross-similarity on the spectra themselves
  fails on singing. A held vowel is self-similar, so plain synthetic singing
  scored 0.90 against 0.98 with a planted repeat. Correlating frame-to-frame
  spectral *change* (delta log-mel) separates them, and the planted-repeat test
  passes. Use delta log-mel.
- **Univariate AUC, pooled vs mean within a mix:**

  | feature | pooled | within a mix |
  |---|---|---|
  | switches between takes | 0.54 | 0.63 |
  | spectral jump | 0.36 | 0.65 (sign flips) |
  | join count | 0.65 | 0.58 |
  | F0 step at joins | 0.69 | 0.37 (reverses) |
  | click z | 0.61 | 0.53 |
  | repeat similarity (delta) | 0.60 | 0.46 |
  | segment-boundary distance | 0.51 | 0.46 |

- **Confound.** The cut-placement mix carries both the most joins and the most
  marks, so pooled AUCs mostly measure which mix a phrase came from. Within a
  mix, only "how two takes meet" features hold up (take switches, spectral
  jump). Per-mix n is 16–20, so these are leads, not results.

These features become the missing evidence family in
[[2026-10-07-small-label-decision-learning]]'s ablation. readouts' vocology KB
adds glitch causes (VISinger 2: removing the DSP pitch path gives spectral
discontinuities) and a breath-sound perception finding; run
`rnd readouts glitch discontinuity --any`.

## Claims

- [verified] On synthetic singing, log-mel cross-similarity of the spectra cannot separate a held vowel (0.90) from a planted repeat (0.98); delta log-mel correlation can. (via: ai-jam-sessions scripts/phrase_evidence.py, PR #88, 2026-10-07)
- [verified] On the 124 marked phrases, pooled feature AUCs are dominated by which mix a phrase came from; within a mix only take-switch and spectral-jump features exceed 0.6. (via: ai-jam-sessions PR #88 measurement, 2026-10-07)

- [unverified] MFCC Euclidean join distance reached AUC 0.76 against 12 listeners' continuity judgments (Kirkpatrick et al. 2006).
- [unverified] At 5% false alarms the best spectral features detected about 31–56% of audible joins (Pantazis et al. 2005).
- [unverified] Mean gap-in-noise threshold is about 4.8 ms in normal-hearing adults.
- [unverified] No listener-validated detector for repeated or skipped fragments exists (the agent's search found none).
- [unverified] Vepa & King 2005 figures come from a draft; the final version may differ.

## Sources

- [rig] ai-jam-sessions PR #88, scripts/phrase_evidence.py: join-evidence receipt on 124 marked phrases, 2026-10-07

- [primary] https://doi.org/10.21437/ICSLP.2002-663 — Vepa, King, Taylor, "Objective distance measures for spectral discontinuities in concatenative speech synthesis", ICSLP 2002
- [primary] https://doi.org/10.21437/Interspeech.2006-483 — Kirkpatrick, O'Brien, Scaife, "Feature extraction for spectral continuity measures in concatenative speech synthesis", Interspeech 2006
- [primary] https://doi.org/10.21437/Interspeech.2005-621 — Pantazis, Stylianou, Klabbers, "Discontinuity detection in concatenated speech synthesis based on nonlinear speech analysis", Interspeech 2005
- [primary] https://arxiv.org/abs/2202.05718 — Wolff, Mignot, Roebel, "Audio defect detection in music with deep networks", ISMIR 2021
- [primary] https://arxiv.org/abs/2302.07584 — Yang et al. 2023, audio copy-move forgery detection (abstract only)
- [user] Also cited by the agent without a fetched URL: Vepa & King 2005 (IEEE TSAP, draft read); Stylianou & Syrdal 2001 (ICASSP); Klabbers & Veldhuis 2001 (IEEE TSAP 9:39–51); Valentini-Botinhao & King 2021 (Interspeech, abstract only); Rund, Vencovský, Bouše 2016 (DAFx-16); Musiek et al. 2005 (Ear & Hearing 26(6):608–618); Bořil & Skarnitzl 2019 (Akustické listy 25)
- [user] Question from the ai-jam-sessions session, 2026-10-07; research agent (claude-sonnet-5-5) web search
