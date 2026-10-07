---
id: 2026-10-07-single-rater-labels-and-ai-listener
title: Label quality with one expert listener, time marks, and an AI second rater
date: 2026-10-07
kind: finding
relevance: act
fields: [evaluation, statistics, audio, machine-learning]
tags: [intra-rater, kappa, gwet-ac1, sound-event-detection, audio-llm-judge, qwen3-omni, dawid-skene, prediction-powered-inference, listening-test, sense-si]
---

## Summary

Raised by ai-jam-sessions / sense-si on 2026-10-07. The labels behind the Jev
calibration come from one expert: 124 phrases, defects marked at about
1-second resolution while listening to whole takes. Four things decide whether
those labels can carry a model:

- how consistent the listener is with themselves;
- how time marks map onto phrases;
- whether a local audio-language model (Qwen3-Omni) can serve as a second
  rater;
- how to structure review so detecting a defect stays separate from diagnosing
  its cause.

## Key points

- **Intra-rater reliability.** Report kappa with an interval, plus raw
  agreement, prevalence and bias indices (Sim & Wright 2005). Kappa alone
  misleads when defects are rare (the kappa paradox). Gwet's AC1 stays stable
  where kappa swings (Wongpakaran et al. 2013). Clinical voice raters reach
  intra-rater ICC of about .91 overall, with strain-type attributes less
  reliable. Disagreement mostly comes from task design, and comparison stimuli
  roughly doubled exact agreement (Kreiman & Gerratt).
- **Time marks to phrases.**
  - Sound-event-detection scoring uses 200 ms onset collars or 1 s segments
    (DCASE; Mesaros et al. 2016). A 1 s mark is closer to segment scoring.
  - Human marks lag the signal, and the lag is non-stationary (Khorram et
    al. 2019).
  - Continuous quality judgments lag about 1 s and carry a recency effect.
  - Intersection-based scoring is more robust to labelling subjectivity
    (Ferroni et al. 2020).
  - No published rule assigns a mark that lands near a phrase boundary.
- **Audio-language models as judges.**
  - Qwen-Audio, Qwen2-Audio and SALMONN prompted for MOS were competitive with
    small task-specific predictors (Wang et al. 2025).
  - On pairwise naturalness, Gemini-2.5-Flash agreed with humans under 70%,
    and a fine-tuned Qwen2.5-Omni-7B reached 77% (SpeechJudge).
  - Judges show verbosity and position bias (AudioJudge).
  - Timestamps from audio LLMs drift with audio length (Not in Sync).
  - Event omission and quantity errors are named hallucination types (AHA).
  - A snippet reported Qwen3-Omni at 0.25 accuracy for fine temporal
    grounding; not confirmed.
  - So: ask the model yes/no per phrase, and never use its timestamps.
- **Rater models.** Dawid–Skene (1979) and MACE estimate each rater's error
  matrix without ground truth. Prediction-powered inference combines a small
  labelled set with machine predictions and still gives valid intervals.
- **Review tooling.** webMUSHRA (BS.1534 / BS.1116 / forced choice, open
  source); BeaqleJS (ABX/MUSHRA); the Label Studio sound-event-detection
  template (time regions plus labels, i.e. detection plus diagnosis).
- **No direct source** separates detection from diagnosis, or weights expert
  against novice listeners. Per-stage Dawid–Skene is the nearest tool.

## Studio relevance

The protocol to run next, for the Director's marks:

1. **Blind re-mark.** Re-present 40–60 of the 124 phrases (every defective one
   plus a clean sample), shuffled, at least two weeks after the first pass,
   using the same marking procedure. This also measures mark-time jitter.
2. **Report agreement properly:** kappa with a bootstrap interval, raw
   agreement, prevalence and bias indices, and AC1, at phrase level and on
   1 s segments. This intra-rater ceiling bounds every model in
   [[2026-10-07-small-label-decision-learning]].
3. **Derive phrase labels twice.** Use a strict window and a window extended by
   about 1 s of lag, set from the measured jitter. Tag phrases as certain,
   edge or mid-phrase, and report how much the edge cases move the result.
4. **Test Qwen3-Omni as a second rater.**
   - Ask a yes/no glitch question per phrase, with order and wording
     randomised.
   - Run it three times to measure its own consistency.
   - Score it against the expert: sensitivity, specificity, MCC and AC1 with
     intervals.
   - Add a few synthetic injected-glitch controls.
   - Use prediction-powered inference only if it passes. Otherwise it is a
     triage flag, not a label.
5. **Two-stage review.** Stage one is blind detection (yes/no plus a time
   region, in Label Studio); stage two is diagnosis on detected items only.
   Fit Dawid–Skene per stage once there are more raters, with the expert as
   reference.

Listener-screening background: readouts' vocology KB holds ITU-R BS.1534
MUSHRA post-screening (`rnd readouts mushra`).

## Claims

- [unverified] Gwet's AC1 stayed between .752 and 1.0 where Cohen's kappa ranged from 0 to 1.0.
- [unverified] Gemini-2.5-Flash agreed with human pairwise naturalness judgments under 70%; a fine-tuned Qwen2.5-Omni-7B reached 77.2%.
- [unverified] Qwen3-Omni scored 0.253 on minimal-span grounding at 0.5 s tolerance (search snippet only).
- [unverified] Continuous speech-quality judgments lag about 1 s (snippet; Acta Acustica 2001, authors not confirmed).
- [unverified] Kreiman & Gerratt title, year and venue are not fully confirmed.

## Sources

- [primary] https://research.manchester.ac.uk/en/publications/guidelines-for-reporting-reliability-and-agreement-studies-grras-/ — Kottner et al., "GRRAS", 2011 (search only)
- [primary] https://research.birmingham.ac.uk/en/publications/the-kappa-statistic-in-reliability-studies-use-interpretation-and/ — Sim & Wright, "The Kappa Statistic in Reliability Studies", Physical Therapy 2005
- [secondary] https://pmc.ncbi.nlm.nih.gov/articles/PMC4236536 — secondary summary of the kappa paradox (Feinstein & Cicchetti 1990) and PABAK
- [primary] https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3643869/ — Wongpakaran et al., Cohen's kappa vs Gwet's AC1, BMC Med Res Methodol 2013
- [secondary] https://auditory.org/postings/2003/255.html — de Bruijn, intrarater reliability posting (weak source)
- [secondary] https://voicefoundation.org/health-science/videos-education/pvqd/ — Perceptual Voice Qualities Database (CAPE-V reliability)
- [primary] https://www.uclahealth.org/sites/default/files/documents/2007%20Kreiman%20When%20and%20why%20listeners%20disagree%20in%20voice%20quality%20assessment.pdf — Kreiman & Gerratt, listener disagreement in voice quality
- [primary] https://www.doi.org/10.3390/APP6060162 — Mesaros, Heittola, Virtanen, "Metrics for Polyphonic Sound Event Detection", 2016
- [primary] https://dcase.community/challenge2017/metrics — DCASE 2017 metrics
- [primary] https://arxiv.org/abs/2010.13648 — Ferroni et al., "Improving Sound Event Detection Metrics", 2020
- [primary] https://arxiv.org/abs/1907.03050 — Khorram, McInnis, Mower Provost, annotation lag, 2019
- [primary] https://www.ingentaconnect.com/contentone/dav/aaua/2001/00000087/00000003/art00009 — "Instantaneous and Overall Judgements for Time-Varying Speech Quality", Acta Acustica 2001 (snippet only)
- [primary] https://arxiv.org/abs/2104.04214 — Martin-Morato & Mesaros, multi-annotator audio tagging reliability, EUSIPCO 2021
- [primary] https://arxiv.org/abs/2409.16644 — Wang et al., auditory LLMs for speech quality evaluation, ICASSP 2025
- [primary] https://arxiv.org/abs/2511.07931 — Zhang et al., "SpeechJudge", 2025
- [primary] https://arxiv.org/abs/2506.05984 — Chiang et al., audio-aware LLMs as judges for speaking styles, 2025
- [primary] https://arxiv.org/abs/2507.12705 — Manakul et al., "AudioJudge", 2025
- [primary] https://arxiv.org/abs/2510.12185 — Yao et al., "Not in Sync: temporal bias in audio chat models", 2025
- [primary] https://arxiv.org/abs/2512.24052 — Chen et al., "AHA", audio-LLM hallucination, 2025
- [primary] https://arxiv.org/abs/2609.15215 — Shi, Song et al., frame-level grounding for audio LLMs, 2026
- [primary] https://ideas.repec.org/a/bla/jorssc/v28y1979i1p20-28.html — Dawid & Skene 1979
- [primary] https://github.com/dirkhovy/MACE — Hovy et al., MACE, NAACL 2013
- [primary] https://arxiv.org/abs/2301.09633 — Angelopoulos et al., "Prediction-Powered Inference"
- [primary] https://aclanthology.org/2026.acl-long.1797.pdf — HalluAudio, ACL 2026 (not read)
- [primary] https://cris.fau.de/publications/227085502 — Schöffler et al., "webMUSHRA", JORS 2018
- [primary] https://labelstud.io/templates/sound_event_detection — Label Studio sound event detection template
- [primary] https://arxiv.org/abs/1907.10588 — worker expertise for crowdsourcing audio quality (search only)
- [user] Question from the ai-jam-sessions session, 2026-10-07; research agent (claude-sonnet-5-5) web search
