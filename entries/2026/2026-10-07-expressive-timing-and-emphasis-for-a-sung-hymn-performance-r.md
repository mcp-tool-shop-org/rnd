---
id: 2026-10-07-expressive-timing-and-emphasis-for-a-sung-hymn-performance-r
title: Expressive timing and emphasis for a sung hymn — performance rules applied to synthetic singing
date: 2026-10-07
kind: finding
relevance: act
fields: [music-performance, singing-synthesis]
tags: [kth-rules, director-musices, dotted-rhythm, ritardando, emphasis, battle-hymn, soulx]
---

## Summary

Raised by ai-jam-sessions on 2026-10-07 at the Director's direction. The Battle
Hymn render (si-jam-sessions' CC0 piano arrangement, SoulX-Singer voice, a score
clock with a WSOLA time-warp) is a test of whether timing and emphasis alone can
give a synthetic singer "soul". The Director heard a rushed "Glory, glory,
glory", a harsh voice (since fixed by a different voice prompt) and a stutter on
every "hallelujah".

Five research agents covered the KTH performance rules, dotted-rhythm practice,
the acoustic size of sung emphasis, listener tests of expressive rules in singing
synthesis, and tempo across verses. The literature gives usable sizes, but almost
none of it was measured on singing, and none on a neural singer. Its most
consistent finding is that the preferred amount of any expressive deviation sits
just above what listeners can hear, and that exaggerated amounts are rejected,
often in favour of no shaping at all.

## Key points

- **The KTH rule system** (Friberg, Bresin & Sundberg 2006 overview; Friberg 1991
  formulas) gives each rule a quantity k, with k = 1 the default. At k = 1:
  - Phrase-final note and Punctuation: a micropause of about 80 ms at phrase and
    sub-phrase ends, and the phrase-final note lengthened by about 40 ms;
  - High-loud: +3 dB per octave of pitch;
  - Melodic charge: up to +1.3 dB and +4.3% duration on notes far from the
    harmony's root;
  - Harmonic charge: about 1.5·C dB at chord changes (C = the charge);
  - Duration contrast: short notes (30–600 ms) shortened by up to about 16 ms
    and softened by up to 0.8 dB; its sign sharpens or softens contrasts;
  - Double duration (2:1 pairs): the short note gains 12%, taken from the long;
  - Faster uphill: about −2 ms per ascending note;
  - Notes inégales: written for runs of equal notes; its k scales with tempo.
- **Preferred amounts are near the threshold of hearing** (Sundberg, Friberg &
  Frydén 1991, via Friberg's thesis):
  - musicians' preferred k: Phrase-final note 1.6 (about +14% on the final note),
    Melodic charge 1.4, Harmonic charge 1.2, Leap articulation 1.9;
  - individual preferences differ by up to 2.5×;
  - deviations had to be 3–4× the lab threshold to be noticed in music;
  - exaggerated amounts made many listeners prefer the deadpan version, and one
    badly placed lengthening could sink a whole rule.
- **Steady accompaniment limits rubato.** The 2006 overview warns that
  note-level tempo changes against a rhythmic accompaniment sound unmusical;
  keep tempo shaping at phrase level, shared by piano and voice, and give back
  borrowed time within the beat ("duration stealing").
- **Final ritardando** (Friberg & Sundberg 1999, runners' deceleration):
  - tempo v(x) = [1 + (v_end^q − 1)·x]^(1/q), x from 0 to 1 across the ritard;
  - listeners rated q = 2 and q = 3 best; Bach fits averaged q = 2.8;
  - measured end tempo was 32–51% of the pre-ritard tempo; the test started the
    ritard at least 1.3 s before the last note and set the final note to 1.25×
    the penultimate.
- **Dotted rhythms are softened in practice, not sharpened.**
  - Twelve pianists shortened a written 3:1 toward 2:1, to roughly 2.4–2.5:1, at
    every tempo tested (Repp, Windsor & Desain 2002).
  - Gabrielsson's measurements found 3:1 and 2:1 usually reduced, sometimes
    enhanced, varying by player and context (as summarised by Repp et al. 2005).
  - Jazz swing ratios fall with tempo while the short note stays near 100 ms,
    a perceptual floor (Friberg & Sundström 2002).
  - Overdotting is a Baroque question (Fabian & Schubert) with no support for
    American hymn singing. **No measurement of hymn, gospel or march singing
    was found.**
- **What SoulX does already** (ai-jam-sessions, 16 raw takes at 84 BPM, vowel
  onsets dated by the detector):
  - all dotted pairs (n = 1,275): long:(long+short) median 0.63, short note
    median 276 ms against 179 ms written;
  - "Glo-ry" (n = 242): 0.57, close to even;
  - the warp forced 0.75, squeezing a ~280 ms syllable into 179 ms: the stutter.
  - at 76–80 BPM in G with the zh voice (16 raw takes, 145 dotted pairs written at
    a mean 0.70, n = 1,481): median 0.57 (IQR 0.49–0.66); per-take medians
    0.55–0.60, so it is the model, not a bad take. By word: "Glo-ry" 0.65,
    "Hal-le" 0.52, "make men" 0.49, "of the" 0.61, "jah, His" 0.66, "out the" 0.68.
    SoulX under-dots, nearly evenly on "Hal-le-lu-jah". Vowel onsets, so a long
    consonant cluster reads late, and "le" may be partly swallowed.
- **Timing thresholds:**
  - a timing error is noticed at about 10 ms for tones under ~240 ms and about
    5% of duration above (Friberg & Sundberg 1995); Friberg's thesis gives about
    6 ms and 2.5% for a single displaced tone;
  - no singing-specific minimum syllable duration was found.
- **Emphasis sizes:**
  - speech stress: stressed vowels in accented words about 5 dB louder, but
    duration is the strongest cue and overall level the weakest (Sluijter &
    van Heuven 1996);
  - real vocal effort is not a gain change: per 1 dB of level the voice gains
    about 0.5 dB at low frequencies and about 1.5 dB at 1.5–3 kHz (Nordenberg &
    Sundberg 2004), and listeners hear effort and playback level as different
    cues (Brungart & Scott 2001). Gain-only emphasis therefore has to stay small;
  - musical level differences needed about 1.4–1.6 dB to be noticed (Friberg
    1995);
  - sung vowel onsets are usually aligned with the piano, with consonants placed
    before the beat; departures read as expressive (Sundberg & Bauer-Huppmann
    2007, abstract only).
- **Expressive rules in singing synthesis:**
  - KTH ran its rules on the MUSSE singing synthesiser; judges found rule
    versions more acceptable, with the useful range between the thresholds of
    perception and of sounding artificial (Frydén, Sundberg & Askenfelt 1988).
    No numbers.
  - Instrumental tests: moderate rules beat deadpan, e.g. phrase-final
    lengthening at k = 1 chosen as most musical in 70% of pairs by 15 listeners.
  - Neural systems: learned timing models (Sinsy, Nishihara et al. 2023) show no
    listener gain in the numbers available. A unit-selection expression system
    (Umbert et al. 2013, 16 listeners) improved rated expressiveness but not
    naturalness.
  - Humanising is not free: exaggerated microtiming lowered groove ratings
    (Senn et al. 2016, 160 listeners).
  - **No study stacks rules on a neural singer.** Effects may be smaller, or
    negative where SoulX's own timing already carries expression.
- **Tempo across verses:**
  - no measurement of tempo across hymn verses exists;
  - repeats are played very similarly (Windsor & Clarke 1997: timing R² 0.85
    between two performances), with variation concentrated at phrase edges
    (Demos et al. 2016);
  - in pre-1978 Billboard recordings 46% of songs end at least 3% faster than
    they start (Carter & von Appen 2025), the nearest evidence for a build;
  - tempo–loudness coupling is real but inconsistent (Windsor & Clarke 1997).

## Studio relevance

Decision-ready for ai-jam-sessions. Everything below is a starting point for the
Director's ear, not a validated recipe: no rule set has been tested on a neural
singer.

**1. Dotted rhythm: stop forcing the ratio.**
- Pin the long, beat-carrying notes (their vowel onsets) to the clock; let the
  short note's onset float.
- Target long:(long+short) **0.70** (about 2.4:1, the measured performance
  norm). Do not warp toward 0.75. SoulX sings about **0.57** at 76–80 BPM, so a
  floating short note does not reach 0.70 by itself.
- Pulling 0.57 to 0.70 at 76 BPM shortens the short note from about 339 to
  237 ms, about 30%, more than the 20% cap below. Within the cap it reaches about
  0.66. Writing 0.70 into the score SoulX is conditioned on has not moved its
  output to 0.70 either (it sang 0.57 against a 0.70 score).
- Better still, write the target durations into the score SoulX is conditioned
  on, so the take already lands near them and the warp barely moves anything.
- At 76 BPM (beat 789 ms): 0.70 gives 552 + 237 ms; 0.60 gives 473 + 316 ms; the
  written 0.75 gives 592 + 197 ms.
- Short-syllable floor: **at least 180 ms, never below 150 ms** (agent's
  judgement from the ~100 ms instrumental floor plus a sung consonant and vowel;
  unmeasured). Also cap how hard WSOLA may compress any one syllable; the
  stutter came from a ~35% squeeze. Studio judgement: keep it under about 20%.

**2. "Glory, glory, glory" sounds rushed: treat it as stress and breath, not
ratio.**
- Lengthen each stressed "Glo" by **+5 to +8%** (agogic accent), taken from the
  following note so the beat holds.
- Put the "Gl" consonant **before** the beat and the vowel on it.
- Give the refrain a breath: a **60–80 ms** micropause before the first "Glory",
  stolen from the previous note.
- **+1.5 to +2.5 dB** on the stressed syllables, no more.

**3. Gain shaping (voice, post-render).**
- Per-syllable emphasis +1.5 to +3 dB; sounds like a volume knob beyond about
  +4 dB.
- Phrase arch 3–4 dB peak to trough; artificial beyond about 6–8 dB.
- High-loud +3 dB per octave above the phrase's base, capped at +3 dB.
- Always pair gain with a small lengthening or onset shift; level alone is the
  weakest stress cue.

**4. Tempo map (piano and voice together).**
- Verses: 76, 77, 78, 80, then 80 easing 3–5% over the last two lines of verse
  5. A build of +3 to +8% is evidence-informed; the per-verse numbers are
  convention.
- Same line-end shaping in every verse (repeats are played alike).
- Phrase arch only at line level: about ±2–3% tempo, slow-fast-slow.
- Coda: replace the 70/60/50 steps with one continuous Friberg–Sundberg curve,
  q = 2.5, from about 76 down to 50, then the fermata. Step changes are audible;
  the curve is what listeners preferred.

**4b. Outcome and per-hymn values (2026-10-08).** The Director signed off the
Battle Hymn at amount 1. What finished it was holding each phrase's last note
into the rest, releasing it over 180 ms, with a 0.2 s breath before the next
onset (ai-jam-sessions PR 106). That is KTH's phrase-final punctuation in
practice. The values for the next two hymns, anchored to that approval where
the literature gives a range:

| | Amazing Grace (3/4, 72) | America the Beautiful (4/4, 92) |
|---|---|---|
| verses | 72 / 72 / 73 / 74 | 92 / 93 / 94 / 95 (a slower anthem pace is a separate A/B arm) |
| line arch | 4-bar line ±2%, no sub-arch | 4-bar line ±2–3%, 2-bar half ±1–1.5% |
| release + breath | at 4-bar line ends | at 4-bar line ends only |
| strong beats | 1 only, +1.5 dB | 1 (+2 dB) and 3 (+1 dB) |
| last verse | last line eased 4% | last line eased 3–5% |
| coda | q = 2.5 to about 48 (0.66 of tempo; 52 if it drags) | q = 2.5 to about 63 (0.66 of 95) |
| dotted pairs | dotted quarter + eighth melismas: 0.70 target, leave native if 0.68–0.75, 20% cap | as the Battle Hymn |
| dB | arch 3 dB, High-loud cap +3, emphasis +1.5, clamp +4 | Battle Hymn values |

**5. Avoid.**
- Random "humanise" jitter: it lowers ratings.
- Any rule above about 2× its preferred amount: listeners fall back to deadpan.
- Note-level rubato against the piano.
- Notes inégales, overdotting, different shaping per verse.
- Gain moves above +4 dB per syllable.

**6. Listening test for the Director (about 5 minutes).** Borrowed from Friberg
1991 (pairwise, identical-pair catches), Sundberg et al. 1991 (preferred versus
threshold quantities) and Umbert et al. 2013 (randomised order, expressiveness
judged separately from naturalness).
- Five contrasts, each a 6–10 s excerpt, each presented twice with A and B
  swapped, plus two identical pairs: 12 trials, blind, in random order.
- The question: which is more alive, A, B or no difference?
- Contrasts:
  1. dotted figures: SoulX's own ratio (short note floating, about 0.57) vs
     pulled toward 0.70 within the 20% cap (about 0.66), same takes and warp
     settings (first "Glory, glory, hallelujah");
  2. "Glory" refrain: plain vs the stress-and-breath package (point 2);
  3. the same package mild vs 2.5× (catches over-application);
  4. one verse line: no phrase arch vs mild arch (3 dB, ±2–3% tempo);
  5. coda: 70/60/50 steps vs the q = 2.5 curve.
- Adopt a change only if it wins both presentations and the 2.5× version does
  not win. A split result keeps the simpler version. If the Director hears
  differences in the identical pairs, read the splits as noise.
- Contrasts 1–4 need only re-warping and gain on existing takes unless the
  target durations go into the score (which means a re-render). The verse build
  is too long for a pair; judge it on one full play-through afterwards.

## Claims

- [verified] Listeners rated final ritardandi with q = 2 and q = 3 highest; fitted end tempos were 32–51% of the pre-ritard tempo. (via: research agents reading Friberg & Sundberg 1999 full text, 2026-10-07)
- [verified] Repeated performances by one pianist correlated at R² = 0.85 in timing and about 0.72–0.74 in key velocity. (via: research agent reading Windsor & Clarke 1997 full text, 2026-10-07)
- [verified] Stressed vowels in accented words were about 5 dB louder overall, with duration the strongest stress cue and overall intensity the weakest. (via: research agent reading Sluijter & van Heuven 1996 full text, 2026-10-07)
- [verified] Unwarped SoulX-Singer takes sing dotted-eighth + sixteenth pairs at a median long:(long+short) ratio of 0.63 (0.57 on "Glo-ry"), against 0.75 written. (via: ai-jam-sessions measurement on 16 raw takes at 84 BPM, 2026-10-07)
- [unverified] At k = 1 the KTH rules give an 80 ms phrase-end micropause, +3 dB per octave High-loud, +12% to the short note of a 2:1 pair, and up to +1.3 dB / +4.3% Melodic charge (Friberg 1991; some PDF text garbled).
- [unverified] Musicians' preferred rule quantities sat near the threshold of perception, and exaggerated quantities led many listeners to prefer deadpan (Sundberg, Friberg & Frydén 1991, via Friberg's thesis summary).
- [unverified] Twelve pianists shortened a written 3:1 rhythm toward 2:1 by about 4.5%, independent of tempo (Repp, Windsor & Desain 2002; the ratio of about 2.4–2.5:1 is the agent's arithmetic).
- [unverified] A timing displacement is noticed at about 10 ms for tones under about 240 ms and at about 5% of duration above (Friberg & Sundberg, ASA 1993 abstract and JASA 1995).
- [unverified] Per 1 dB of vocal level, low-frequency bands rise about 0.5 dB and the 1.5–3 kHz band about 1.5 dB (Nordenberg & Sundberg 2004, abstract).
- [unverified] Sung vowel onsets in Schumann Lieder were most often aligned with the piano, with consonants before the beat (Sundberg & Bauer-Huppmann 2007, abstract only).
- [unverified] Exaggerated microtiming lowered groove ratings, from +40% for experts and +80% for non-experts (Senn et al. 2016).
- [unverified] 46% of pre-1978 Billboard Hot 100 songs end at least 3% faster than they start (Carter & von Appen 2025).
- [verified] Rendered against a score written at a mean long:(long+short) of 0.70, SoulX-Singer sang the Battle Hymn's dotted pairs at a median 0.57 (n = 1,481; per-take medians 0.55–0.60; "Hal-le" 0.52). (via: ai-jam-sessions dotted_ratio.py on 16 raw takes, zh voice, 76–80 BPM, 2026-10-08)
- [unverified] A short sung syllable stays unclipped at 180 ms or more, with 150 ms as a hard limit. (Agent's judgement; no source measures it.)
- [unverified] Keeping WSOLA compression of any one syllable under about 20% avoids the stutter. (Studio judgement from the 35% squeeze that caused it; unmeasured.)

## Sources

- [primary] https://doi.org/10.2478/v10053-008-0052-x — Friberg, Bresin & Sundberg 2006, "Overview of the KTH rule system for musical performance", Advances in Cognitive Psychology 2(2-3)
- [primary] https://doi.org/10.1121/1.426687 — Friberg & Sundberg 1999, "Does music performance allude to locomotion? A model of final ritardandi derived from measurements of stopping runners", JASA 105(3)
- [primary] https://www.jstor.org/stable/3680917 — Friberg 1991, "Generative rules for music performance", Computer Music Journal 15(2)
- [primary] https://www.speech.kth.se/music/publications/thesisaf/sammfa2nd.htm — Friberg 1995, "A Quantitative Rule System for Musical Performance" (thesis summary; source for Sundberg, Friberg & Frydén 1991 values)
- [primary] https://www.speech.kth.se/music/performance/Texts/phrasing.htm — KTH Phrase-arch demo settings
- [primary] https://www.speech.kth.se/music/performance/Texts/double_duration.htm — KTH Double-duration rule
- [primary] https://continuum-hypothesis.com/music/FULLTEXT01.pdf — Bresin & Friberg 2000, "Emotional coloring of computer-controlled music performances", Computer Music Journal 24(4)
- [primary] https://www.mcg.uva.nl/mmm-2003/papers/mmm-17a.pdf — Repp, Windsor & Desain 2002, "Effects of tempo on the timing of simple musical rhythms", Music Perception 19(4) (preprint)
- [primary] https://cdn.carleton.edu/uploads/sites/721/2021/12/Repp-London-Keller-2005-MP.pdf — Repp, London & Keller 2005, "Production and synchronization of uneven rhythms at fast tempi", Music Perception 23(1)
- [primary] https://www.speech.kth.se/music/performance/Texts/ensemble_swing.htm — Friberg & Sundström 2002, "Swing ratios and ensemble timing in jazz performance", Music Perception 19(3)
- [primary] https://auditory.org/asamtgs/asa93dnv/4pPP/4pPP2.html — Friberg & Sundberg 1993, just-noticeable time displacement (ASA abstract)
- [primary] https://scholarlypublications.universiteitleiden.nl/access/item%3A2860300/view — Sluijter & van Heuven 1996, "Spectral balance as an acoustic correlate of linguistic stress", JASA 100
- [primary] https://www.speech.kth.se/annualreport/2003/51-54qpsr.pdf — Nordenberg & Sundberg 2004, "Effect on LTAS of vocal loudness variation" (abstract)
- [primary] https://perso.lisn.upsaclay.fr/wiki/_media/lienard/publis/lienard_dibenedetto_jasa99.pdf — Liénard & Di Benedetto 1999, JASA 106
- [primary] https://iro.uiowa.edu/esploro/outputs/journalArticle/Vocal-intensity-in-speakers-and-singers/9984719570502771 — Titze & Sundberg 1992, "Vocal intensity in speakers and singers", JASA 91
- [primary] https://acoustics.ippt.pan.pl/index.php/aa/article/view/3074 — Frydén, Sundberg & Askenfelt 1988, rules on the MUSSE singing synthesiser, Archives of Acoustics 13
- [primary] https://ac-psych.org/en/issues/volume/2/issue/2 — Sundberg 2006, "The KTH Synthesis of Singing", Advances in Cognitive Psychology 2
- [primary] https://arxiv.org/abs/2108.02776 — Hono et al. 2021, "Sinsy: A Deep Neural Network-Based Singing Voice Synthesis System"
- [primary] https://arxiv.org/abs/2301.02262 — Nishihara et al. 2023, singing synthesis with vocal timing deviation
- [primary] https://doi.org/10.3389/fpsyg.2016.01487 — Senn et al. 2016, expert microtiming and groove, Frontiers in Psychology 7
- [primary] https://kth.diva-portal.org/smash/get/diva2:1246182/FULLTEXT01.pdfx — Friberg & Battel 2002, "Structural Communication", in Parncutt & McPherson (eds.)
- [primary] https://www.jstor.org/stable/40285746 — Windsor & Clarke 1997, Music Perception 15(2)
- [primary] https://doi.org/10.3389/fpsyg.2016.01490 — Demos, Lisboa & Chaffin 2016, "Flexibility of expressive timing in repeated musical performances", Frontiers in Psychology 7
- [primary] https://theory.esm.rochester.edu/integral/38-2025/carter-von-appen/ — Carter & von Appen 2025, tempo variability in Billboard Hot 100 songs, Intégral 38
- [primary] https://www.continuum-hypothesis.com/music/anatomy_retard.pdf — Sundberg & Verrillo 1980, "On the anatomy of the retard" (not read in detail)
- [rig] ai-jam-sessions dotted-pair measurement, 16 unwarped SoulX-Singer Battle Hymn takes at 84 BPM, 2026-10-07
- [user] Cited by the agents from abstracts or secondary summaries only: Sundberg & Bauer-Huppmann 2007 (J Voice 21:285); Brungart & Scott 2001 (JASA 110:425); Gabrielsson et al. 1983; Fabian & Schubert 2003/2008; Umbert, Bonada & Blaauw 2013 (SMAC); Juslin & Laukka 2003 (via Eerola, Friberg & Bresin 2013); Sundberg, Iwarsson & Hagegård 1995; Thompson et al. 1989 (Psychology of Music 17); Timmers 2005 (JASA 117). Umbert, Bonada & Blaauw 2015 (IEEE SPM survey) could not be read.
- [user] Question from the ai-jam-sessions session at the Director's direction, 2026-10-07; five research agents (claude-sonnet-5-5) web search
