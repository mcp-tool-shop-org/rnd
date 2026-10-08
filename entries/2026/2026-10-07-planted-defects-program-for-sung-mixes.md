---
id: 2026-10-07-planted-defects-program-for-sung-mixes
title: Planted defects for sung mixes — an automated planter-versus-detector loop, anchored by the listener's measured threshold
date: 2026-10-07
kind: concept
relevance: act
fields: [audio, evaluation, psychoacoustics, machine-learning, research-method]
tags: [planted-defects, self-play, curriculum, regret, verifiable-reward, catch-trials, psychometric-function, conformal-risk-control, partial-spoof, splice-detection, mert, qwen3-omni, ai-jam-sessions, sense-si]
---

## Summary

The labels are the bottleneck for detecting defects in ai-jam-sessions' sung
mixes.
- Every decision model sits at the base rate on 124 marked phrases.
- About 400 more marks would be needed to confirm a small gain.

The Director's direction is to automate: two models working against each other at
rising difficulty, until the detector exceeds any human. Human listening becomes a
small calibration step instead of the label source.

The design that the evidence supports:

1. **A planter proposes defects as parameters.** Kind, position at a real join,
   severity and disguise are emitted as JSON, and code executes them. The ground
   truth is exact and costs nothing.
2. **A trained detector finds them.** It is a music self-supervised encoder (MERT)
   with a frame-level head. An audio-language model cannot time-localise defects
   well enough to be the detector.
3. **The planter is rewarded for regret, not failure.** Its score is what the
   current detector misses *minus* what an independent reference detector, from a
   different encoder family, misses. Impossible or inaudible plants earn nothing.
4. **Difficulty is held at the frontier.** Severity is mutated so the detector's
   hit rate stays in a learnable band (30–70%). A replay buffer and a league of
   past models prevent collapse and cycling.
5. **The Director's ear sets the audibility line.** Blind catch trials in every
   session, under whatever conditions he is listening in, give his threshold. A
   conformal rule turns about 40 of his heard/not-heard judgements into a flag
   cutoff with a guaranteed false-flag rate. The detector may become far more
   sensitive than he is; it only *fails* a mix above the line.

## Key points

### The loop's prior art: what climbs, and what collapses

- **Plain adversaries make impossible tasks.**
  - Alice/Bob asymmetric self-play builds a curriculum, but Alice can win with
    tasks Bob cannot do (Sukhbaatar et al. 2017).
  - A minimax environment generator rewards unsolvable levels.
  - **PAIRED** rewards the generator with *regret*: an antagonist's return minus
    the protagonist's. An impossible level gives the antagonist no edge, so it
    earns nothing (Dennis et al. 2020).
- **Stable variants:**
  - replaying a buffer ranked by learning potential (PLR, Jiang et al. 2021);
  - small mutations of high-regret levels, so difficulty grows step by step
    (ACCEL, Parker-Holder et al. 2022);
  - a minimal criterion of "neither too easy nor too hard" (POET, Wang et al. 2019);
  - choosing tasks by learning progress, not raw difficulty (Matiisen et al. 2017;
    Graves et al. 2017).
- **Verifiable-reward self-play in LLMs works the same way:**
  - Absolute Zero gives the proposer a learnability reward that is zero for tasks
    always or never solved (Zhao et al. 2025).
  - R-Zero rewards the challenger near the solver's uncertainty edge, for +6.49 on
    maths for Qwen3-4B-Base, and its gains level off over rounds (Huang et al.
    2025).
  - STP rewards "barely provable" conjectures and proved 28.5% of LeanWorkbook
    against 13.2% before (Dong & Ma 2025).
- **Collapse and cycling:**
  - Naive self-play cycles on non-transitive skills. The fix is a league of frozen
    past agents and exploiters (Vinyals et al. 2019; Balduzzi et al. 2019).
  - SPIN improves only while a fixed human anchor stays in the loop (Chen et al.
    2024).
  - Loss-maximising augmentation policies destroy the label unless strength is
    capped (Adversarial AutoAugment, Zhang et al. 2020; AugMax, Wang et al. 2021).
- **No audio precedent was found** for a planter trained against a defect detector
  with a regret objective. The nearest is one-shot boundary-targeted augmentation
  for deepfake detection (Astrid et al. 2024).

### Which models do what (local, one 5090, ≤ 26–28 GB)

- **Audio LLMs cannot localise in time.**
  - On a 21-model temporal-grounding benchmark the best scored 31.2 mIoU, and none
    exceeded 13.2% on counting repeated events, which is the replay/stutter case
    (TAG-Bench 2026).
  - Music temporal grounding needs encoder adaptation plus fine-tuning (MusTBench,
    Sony 2026).
  - Zero-shot quality judging collapses to mid-range scores (Chen et al. 2024).
  - So an audio LLM is a coarse "something is wrong here" judge, not the detector.
- **Detector:** MERT-v1-330M, a music-trained encoder with pitch and CQT teachers
  (MARBLE 87.1 in the constrained probe setting). Use a frozen encoder plus a
  frame-level head at 50–75 Hz, the PartialSpoof recipe. An SSL front-end with
  multi-resolution segment labels reached 0.77% utterance EER (Zhang et al. 2022);
  a boundary-aware head improved localisation (Zhong et al. 2024).
- **Reference detector, for the regret term:** the same head on a *different*
  encoder lineage (Dasheng-0.6B or WavLM-large), so the two do not share blind
  spots. This, not two LLMs, is the "right two models" pairing the evidence
  supports.
- **Rival listener:** Qwen3-Omni-30B-A3B, AWQ 4-bit, thinker only with the talker
  off. That is about 17–22 GB (estimated), prompt-only, with clip-level flags and
  both orders. A second-family listener (MiDashengLM-7B, Apache-2.0, or Kimi-Audio)
  is optional. Audio Flamingo 3 is non-commercial. Fine-tuning Qwen3-Omni does not
  fit in 32 GB.
- **Planter:** it does not need to hear audio. A search over a parameter archive
  (ACCEL-style mutation, with a bandit over defect kinds) is enough; a small text
  LLM adds only variety in disguises.

### Shortcuts, and why our case is different

- **Detectors learn the edit, not the defect.**
  - Silence alone gave 15.1% EER on ASVspoof (Müller et al. 2021).
  - Splice artefacts alone gave 6–7% EER on PartialSpoof and HAD (Negroni et al.
    2024).
  - PartialSpoof detectors degraded when the fake had no join (Zhang et al. 2022/23).
  - Seamless edits that fool listeners are still caught by SSL detectors, which use
    cues people cannot hear (Huang et al. 2025, authors unconfirmed).
- **Our real defects also sit at joins** (an ai-jam-sessions observation):
  - finding the join is partly the true signal;
  - the warped mixes hold many clean joins (take switches, segment starts after the
    lead pad);
  - `phrase_evidence.py` measures every join against 60 non-join controls.
- **So the task is "a defective join versus a clean join", never "join versus no
  join".**
  - Plants go at real join positions.
  - Sham edits at clean joins (roughly one per plant) go through the identical edit
    code.
  - Every clip, clean or planted, passes through the same randomised processing
    chain (RawBoost-style gain, EQ, codec, noise; 27% relative gain in Tak et al.
    2022).
  - A splice-only probe must score at chance, or the run is void.

### Sim-to-real

- **Expect a large drop from planted to natural.** Deepfake detectors lost up to
  about 10× relative EER in the wild (Müller et al. 2022). Synthetic-trained
  denoisers "degrade significantly" on real recordings (Reddy et al. 2020).
- **What helps:**
  - randomise severity and nuisance (Tobin et al. 2017; RawBoost);
  - render through the real pipeline;
  - keep real negatives and all real marks in training;
  - calibrate only on real data (Afchar et al. 2024).
- DCASE already trains on synthetic soundscapes and tests on real labelled audio
  (Turpault et al. 2019).

### The human anchor under real-world listening

- **Measuring his ear:**
  - The task is yes/no with no trial feedback, so use fixed levels in round 1 and
    Psi placement afterwards (Kontsevich & Tyler 1999). Up-down staircases converge
    on the criterion here (Levitt 1971; Kaernbach 1990).
  - Fit the lapse rate (Wichmann & Hill 2001), use the Hautus correction, and report
    d′ and criterion.
  - Prevalence shifts the criterion, not sensitivity (Wolfe et al. 2005).
  - A 30-item adaptive pitch test takes about 10 minutes, with test-retest r = .70
    (Larrouy-Maestri et al. 2019).
- **Listening conditions** (an ai-jam-sessions constraint; they can't be held
  fixed):
  - catch trials in every session make conditions a measured covariate;
  - the review page logs device (headphones or speakers) and a quick level check
    per session;
  - playback is loudness-normalised;
  - the audibility line is defined at the listener's own ordinary playback, not at
    lab thresholds.
  - Fit a threshold per kind with a session-level random offset and a device
    effect.
- **Setting the line (conformal risk control,** Angelopoulos et al. 2022/2024**):**
  - From n heard/not-heard judgements on detector flags near the line, pick the
    lowest score cutoff whose corrected false-flag rate is within α.
  - With n = 40 and α = 0.10, at most 3 of 40 flags may be "not heard"
    ((0.10·41 − 1)/40 = 7.75%). 40 trials cannot reach α below about 2.5%.
- **Masking models cap the planter, but don't settle audibility.** Masking models
  are what adversaries use to hide perturbations: up to 98% attack success, barely
  audible (Schönherr et al. 2019; Qin et al. 2019). So a masking check is a
  necessary floor, not proof of audibility. Objective metrics track glitches only
  coarsely: PEMO-Q, HAAQI and PEAQ Basic did; PEAQ Advanced and ViSQOL did not
  (DAFx 2025).

### Planting method by defect kind

| defect | planted by | verify present |
|---|---|---|
| replay / skip at a join | code, at real joins, production crossfade | the span matches the clean render; lyric alignment |
| voiced noise at a segment start | render (SoulX), driven by parameters | onset energy and harmonicity against a clean render; drop renders that come out clean |
| click | code (Wolff et al. 2022; Godsill & Rayner 1998) | difference signal above the masking floor |
| octave / semitone slip | code (formant-preserving WORLD/PSOLA), plus render via an f0-target perturbation | pitch tracker shows at least 50 cents median error over the note |
| stutter | code, syllable repeat with crossfades | repeated span correlates with its source |
| timbre jump at a take switch | code, from real alternate takes | spectral distance and f0 gap across the join (Vepa et al. 2002) |

The planter always emits parameters. A generated plant (model-made audio) is worth
the loss of certainty only for the voiced onset noise, which is the synthesiser's
own artefact. Even then it is driven by parameters and verified by measurement.

## Studio relevance

**Status (2026-10-07):** adopted by ai-jam-sessions as written.
- The calibrated review is a cockpit feature in ai-jam-sessions #89: catch trials,
  sham edits, the device and level log, loudness-normalised playback, and the
  40-judgement audibility pass.
- **Step A, the planter engine:** ai-jam-sessions #91, `scripts/planter.py`,
  rebased on the placer overrides (#90: per-cut `xfade_s` and `break_before`).
  - It mutates `plan.json` and renders through the production placers.
  - Replay and skip are measured from where the take had reached before the join,
    so the severity is exactly the span heard twice or never.
  - Replay is verified over exactly that span.
  - Tests: 22 pass, 1 skips by design.
  - **Warp trial on the shipped pad16 mixes:** kept 75/100 (Amazing Grace) and
    77/100 (America the Beautiful).
    - Replay and skip survive at every severity; the drops are mostly 20 ms
      replays.
    - Shams: 20 of 20 in each mix.
    - Clicks: 0. In warp mode, a zero crossfade at a non-overlapping run seam falls
      back to 15 ms fades: a dip, not a click. A placer decision for ai-jam-sessions.
  - **Finding: the pad16 warp mixes have no mid-phrase splices.**
    - Every run boundary sits at a score rest, so every candidate join is inside a
      continuous WSOLA run, and every warp-mode seam is a forced break.
    - Defects marked in those mixes cannot be splice replays.
    - A forced break alone silently skipped the source gap before the cut. So a
      warp sham now continues the take exactly, and is refused when that would move
      the vowel more than 30 ms. About 20% of joins qualify.
  - **Timing confound in warp (found in review):** a replay or skip moves the cut's
    vowel.
    - On Amazing Grace pad16, 0.1 s replays moved their vowel by 0.18–0.21 s.
    - Some 0.02 s skips moved it *later* by 0.08–0.11 s.
    - The cause: severity is measured from where the previous run ended, which is
      often well before the cut's own start.
    - The planted run then absorbs it as a stretch of 0.70–1.14.
    - Labels now record `vowel_moved_s` and the run's stretch range, so the study
      can tell a heard replay from a heard late vowel.
  - **Compound filters and reach:**
    - A replay or skip is kept only if it moves its vowel no more than 30 ms beyond
      its own shift, and leaves no more than 30 ms of pause before the seam. A
      forced warp break where the previous run already ended inserts a pause of up
      to ~0.14 s.
    - Only **14 of 96** (Amazing Grace) and **27 of 204** (America the Beautiful)
      warp joins can take a clean replay or skip, at every severity. Eligibility
      comes from join geometry, not from severity.
    - With pools drawn from those joins, replays verify 17–18 of 20 (including
      20 ms) and skips 20 of 20.
    - Step B needs more warp picks, or compound plants as their own labelled kinds,
      so a detector does not learn a dozen positions.
  - Warp renders refuse a missing score clock: without it the baseline is not the
    shipped audio.
  - Pitch slip and a plan-native **stretch** kind (warp ratio outside 0.67–1.5)
    follow in PR 2.
  - Warp clicks wait on ai-jam-sessions #93 (an explicit crossfade honoured at
    non-overlapping run seams).
- Step B results will be filed here as rig entries.
- A native app that can read the system volume and output device is noted for
  later.

### The recommended loop

1. **Archive.** Parameterised defect specs, each a (kind, join, severity,
   disguise) tuple. Seed it with random specs across all kinds, at real joins, plus
   sham edits.
2. **Render.** Execute every spec through the production crossfade, take switch and
   SoulX path. Apply the shared random processing chain to every clip, clean,
   sham and planted. Drop specs that fail their presence check.
3. **Floor.** Drop plants below a masking-model floor, and below the Director's
   current threshold minus a margin. Sub-threshold plants become *labelled
   negatives*.
4. **Train the detector** (MERT + frame head) on a replay buffer: archive levels,
   sham edits, real negatives and every real mark. Never train on only the newest
   batch.
5. **Score the planter.** Regret = detector miss rate − reference miss rate, from
   the Dasheng/WavLM head. The score is zero when the reference also misses.
   - Mutate high-regret specs (ACCEL).
   - Keep the detector's hit rate in the 30–70% band.
   - Hold a minimum quota per defect kind, plus a novelty bonus.
6. **League.** Score each new detector against frozen past planters, and each new
   planter against past detectors. Losing to an old opponent means it is cycling.
7. **External anchors**, never trained on and scored every round:
   - the real marked set, grouped by mix;
   - a frozen early planted set;
   - the Director's catch-trial curves.
   Select checkpoints on these only.
8. **Stop or reset** on any of these:
   - the hit rate pinned at 0 or 100%;
   - planter reward rising while external recall stays flat;
   - losses to old opponents;
   - shrinking kind entropy;
   - near-zero learning progress over a window.
9. **Ship.** The detector flags only above the conformal cutoff set from the
   Director's judgements. Below the line it reports "present, likely inaudible" as
   advisory. The review tool's reviewer levels become measured thresholds per
   listener and kind.

### What training means here, in order

1. **Frozen-encoder head** on cached MERT features: about 1–3 GPU-hours per run.
2. **LoRA, rank 16, on MERT's top layers**, only if frozen recall falls short:
   about 8–15 GPU-hours.
3. **Prompting only** for Qwen3-Omni and any second listener. Fine-tuning it locally
   does not fit.

Prompt-level adaptation is for the planter's disguise variety, not for the
detector.

### Known vs new

- **Known:**
  - regret-based curricula, replay and league training (games and RL);
  - verifiable-reward self-play (code and maths);
  - planting splices and clicks to train detectors;
  - SSL front-ends for partial-spoof localisation;
  - psychometric fitting; conformal thresholds.
- **New (no precedent found by seven research agents):**
  - a regret-rewarded planter against an audio defect detector, with exact
    code-executed ground truth;
  - "defective join versus clean join" as the training task, turning the splice
    shortcut into the design;
  - an audibility line set by one listener's blind catch trials, under his own
    varying conditions, and enforced by conformal risk control;
  - one psychometric scale shared by the listener, the detector and any audio LLM.

### First experiment

**Step A, code only (ai-jam-sessions, no GPU, no listening).**
- The planter engine: JSON spec, then render at real joins.
- Sham edits, the shared processing chain, and presence checks.
- Kinds: replay/skip at a join and semitone/octave slip.

**Step B, on the GPU, about 4–6 hours, watchdog first.**
- Plant about 5,000 ten-second clips from the existing mixes: half defective joins
  at 4 severities, half sham or clean joins.
- Extract MERT and Dasheng features (about 0.5 h).
- Train both frozen heads (about 1–2 h each).
- Qwen3-Omni AWQ, clip-level, both orders, on a 500-clip subset (about 1–2 h,
  never co-loaded with training).

**Step B pass criteria:**
- on held-out mixes, defective-versus-clean-join AUC ≥ 0.9 above the top two
  severities, per kind;
- false-alarm rate on sham edits no higher than on clean joins;
- a splice-only probe at chance.

Also report the out-of-mix AUC on the 124 real marks. It isn't expected to pass yet;
it is the baseline the loop must move.

**Step C, the Director, about 45 minutes over 3 sessions of ≤ 15 minutes.**
- Each session: about 45 phrases.
  - About 10 planted: 2 kinds at graded severities, at most 6 per kind.
  - About 4 sham-edit clean controls.
  - About 30 normal-review phrases, which he would mark anyway.
- Catch share about 22%.
- Device logged, and a level check, per session.
- **Extra cost beyond normal review: about 15 minutes** (about 42 planted and sham
  phrases at about 20 s).
- **Yield:**
  - a first threshold per kind, with session spread;
  - his false-alarm rate on sham edits;
  - the first comparison of detector and listener curves.

**After Step C,** the loop runs unattended.
- Expect about 10–25 GPU-hours for the first full program, including MERT LoRA if
  needed.
- **The Director's ongoing cost:** catch trials in normal sessions (about 4 extra
  minutes a session). Plus one 40-judgement audibility pass, about 15 minutes, when
  the detector first exceeds his threshold and the line has to be set.

### Cost if run on RunPod instead of the 5090

Live RunPod secure-cloud prices via offrig, 2026-10-07, per GPU-hour:
- RTX 4090 24 GB: $0.74 (stock high)
- A40 48 GB: $0.49 (stock low)
- RTX PRO 4500 32 GB: $0.72
- A100 80 GB: $1.59
- RTX PRO 6000 96 GB: $2.09

Every option adds about 0.5 h for setup and downloads.

| scope | option | hours | cost |
|---|---|---|---|
| Step B | A40 for everything (Qwen3-Omni in 4-bit) | 5–7 | $2.50–3.50 |
| Step B | 4090 for MERT/heads, plus A100 for Qwen3-Omni in bf16 | 4–5 + 1.5–2.5 | $5–7.50 |
| Step B | RTX PRO 6000 for everything (bf16) | 5–7 | $10.50–14.50 |
| First full program | A40/4090 class | 10–25 | $5–18.50 |
| First full program | plus bf16 Qwen3-Omni phases on an A100 | — | add about $5–10, so $10–30 in total |
| Locally on the 5090 | electricity only | 10–25 | about $2–3 (575 W, ~$0.17/kWh, estimated) |

Pod risks from [[2026-10-07-pod-host-checks-driver-and-download]] apply: gate each
host on its driver and download speed before downloading. The only thing RunPod
buys here is bf16 Qwen3-Omni (about 70–79 GB) or parallel runs. The detector work
fits the 5090.

## Claims

- [unverified] PAIRED's regret objective (antagonist return minus protagonist return) gives zero reward for unsolvable levels, unlike a minimax adversary (Dennis et al. 2020).
- [unverified] On a 21-model audio temporal-grounding benchmark the best audio LLM reached 31.2 mIoU and none exceeded 13.2% on counting repeated events (TAG-Bench, arXiv 2609.01542; models not identified by the research agent).
- [unverified] R-Zero's challenger–solver loop gave +6.49 on maths benchmarks for Qwen3-4B-Base, with gains levelling off over iterations (Huang et al. 2025).
- [unverified] A leading-silence-only model reached 15.1% EER on ASVspoof (Müller et al. 2021), and splice artefacts alone gave 6–7% EER on partially fake speech (Negroni et al. 2024).
- [unverified] Masking-threshold-constrained adversarial perturbations reached up to 98% attack success while staying barely audible (Schönherr et al. 2019).
- [unverified] With conformal risk control at α = 0.10 and n = 40 calibration judgements, a cutoff is valid if at most 3 of 40 flags are "not heard" (our arithmetic from Angelopoulos et al.'s bound).
- [unverified] Qwen3-Omni-30B-A3B in BF16 needs 78.9 GB or more per its model card; a community AWQ 4-bit checkpoint exists, and its VRAM (about 17–22 GB, talker off) is an estimate.
- [unverified] MERT-v1-330M scores 87.1 on MARBLE's constrained probe setting (Yuan et al. 2023).
- [unverified] No published work was found for a regret-rewarded defect planter in audio, nor for listener catch-trial thresholds used to set a detector's flag line (absence from seven research agents' searches, 2026-10-07).

## Sources

- [primary] https://arxiv.org/abs/1703.05407 — Sukhbaatar et al. 2017, asymmetric self-play
- [primary] https://arxiv.org/abs/1707.00183 — Matiisen et al. 2017, teacher-student curriculum learning
- [primary] https://arxiv.org/abs/1704.03003 — Graves et al. 2017, automated curriculum learning
- [primary] https://arxiv.org/abs/2012.02096 — Dennis et al. 2020, PAIRED
- [primary] https://arxiv.org/abs/2010.03934 — Jiang et al. 2021, Prioritized Level Replay
- [primary] https://arxiv.org/abs/2203.01302 — Parker-Holder et al. 2022, ACCEL
- [primary] https://arxiv.org/abs/1901.01753 — Wang et al. 2019, POET
- [primary] https://doi.org/10.1038/s41586-019-1724-z — Vinyals et al. 2019, AlphaStar league
- [primary] https://arxiv.org/abs/1901.08106 — Balduzzi et al. 2019, open-ended learning in symmetric zero-sum games
- [primary] https://arxiv.org/abs/2401.01335 — Chen et al. 2024, SPIN
- [primary] https://arxiv.org/abs/2505.03335 — Zhao et al. 2025, Absolute Zero
- [primary] https://arxiv.org/abs/2508.05004 — Huang et al. 2025, R-Zero
- [primary] https://arxiv.org/abs/2502.00212 — Dong & Ma 2025, STP
- [primary] https://arxiv.org/abs/1912.11188 — Zhang et al. 2020, Adversarial AutoAugment
- [primary] https://arxiv.org/abs/2110.13771 — Wang et al. 2021, AugMax
- [primary] https://arxiv.org/abs/2407.07598 — Astrid et al. 2024, targeted augmented data for deepfake detection
- [primary] https://huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Instruct — Qwen3-Omni model card
- [primary] https://huggingface.co/mispeech/midashenglm-7b — MiDashengLM-7B
- [primary] https://huggingface.co/nvidia/audio-flamingo-3 — Audio Flamingo 3
- [primary] https://arxiv.org/abs/2609.01542 — TAG-Bench, audio temporal grounding (2026)
- [primary] https://arxiv.org/abs/2605.29300 — MusTBench, music temporal grounding (Sony, 2026)
- [primary] https://arxiv.org/abs/2409.16644 — Chen et al. 2024, auditory LLMs for speech quality evaluation
- [primary] https://arxiv.org/abs/2306.10548 — Yuan et al. 2023, MARBLE
- [primary] https://arxiv.org/abs/2505.16369 — X-ARES encoder benchmark (2025)
- [primary] https://arxiv.org/abs/2407.21611 — Zhong et al. 2024, boundary-aware partial-spoof localisation
- [primary] https://arxiv.org/abs/2204.05177 — Zhang et al. 2022/23, PartialSpoof database and countermeasures
- [primary] https://arxiv.org/abs/2408.13784 — Negroni et al. 2024, splicing artefacts in partially fake speech
- [primary] https://arxiv.org/abs/2106.12914 — Müller et al. 2021, Speech is Silver, Silence is Golden
- [primary] https://arxiv.org/abs/2004.07780 — Geirhos et al. 2020, shortcut learning
- [primary] https://arxiv.org/abs/2203.16263 — Müller et al. 2022, Does Audio Deepfake Detection Generalize?
- [primary] https://arxiv.org/abs/2501.03805 — Detecting the Undetectable (2025; authors unconfirmed)
- [primary] https://arxiv.org/abs/2111.04433 — Tak et al. 2022, RawBoost
- [primary] https://arxiv.org/abs/1808.05665 — Schönherr et al. 2019, psychoacoustic hiding
- [primary] https://arxiv.org/abs/1903.10346 — Qin et al. 2019, imperceptible adversarial examples
- [primary] https://arxiv.org/abs/2208.02814 — Angelopoulos et al. 2022/2024, Conformal Risk Control
- [primary] https://arxiv.org/abs/2005.13981 — Reddy et al. 2020, DNS challenge
- [primary] https://arxiv.org/abs/2405.04181 — Afchar et al. 2024, music deepfake detection
- [primary] https://arxiv.org/abs/1703.06907 — Tobin et al. 2017, domain randomization
- [primary] https://hal.science/hal-02160855 — Turpault et al. 2019, DCASE soundscape synthesis
- [primary] https://arxiv.org/abs/2202.05718 — Wolff et al. 2022, audio defect detection in music
- [primary] https://arxiv.org/abs/2110.05033 — Liu et al. 2021, pitch preservation in singing voice synthesis
- [primary] https://era.ed.ac.uk/items/24f0c592-8523-447a-a4f0-381c1ea03981 — Vepa et al. 2002, spectral discontinuity measures
- [primary] https://doi.org/10.1121/1.1912375 — Levitt 1971, transformed up-down methods
- [primary] https://doi.org/10.1016/S0042-6989(98)00285-5 — Kontsevich & Tyler 1999, Psi method
- [primary] https://doi.org/10.3758/BF03194544 — Wichmann & Hill 2001, the psychometric function
- [primary] https://doi.org/10.1038/435439a — Wolfe et al. 2005, rare targets are often missed
- [primary] https://doi.org/10.3758/s13428-019-01225-1 — Larrouy-Maestri et al. 2019, mistuning perception test
- [primary] https://arxiv.org/abs/2202.02794 — Hacohen et al. 2022, active learning on a budget
- [primary] https://doi.org/10.1111/ecog.02881 — Roberts et al. 2017, cross-validation for structured data
- [primary] https://arxiv.org/abs/2103.03098 — Bouthillier et al. 2021, variance in ML benchmarks
- [user] ai-jam-sessions request, the Director's amendment (automate; listener as calibration), and constraints on joins and listening conditions, 2026-10-07
