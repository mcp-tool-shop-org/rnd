# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
Versions have five segments, `MAJOR.MINOR.PATCH.MICRO.NANO`. The first three
follow [Semantic Versioning](https://semver.org/) for the `rnd` tool. MICRO marks a
structural library change (a new experiment, catalogue or instrument family), and
NANO an ordinary library update (entries filed or revised, results added).
`python -m rnd bump` writes each section; `1.0.0` reads as `1.0.0.0.0`.

## [Unreleased]

## [1.1.4.3.2] - 2026-10-09

- NPU retrieval benchmark pre-registered (nomic vs bge vs nomic-on-NPU)
- Added experiment `data-designer`
- Added experiment `npu-probe`

## [1.1.4.3.1] - 2026-10-09

- intel-npu instrument points at its skill
- Updated `intel-npu`: The Intel side of the rig — NPU embeddings and iGPU cross-encoders (npu-serve)
- Added experiment `data-designer`

## [1.1.4.3.0] - 2026-10-09

- Intel NPU/iGPU probe and the npu-serve instrument
- Added `intel-npu`: The Intel side of the rig — NPU embeddings and iGPU cross-encoders (npu-serve)
- Added experiment `data-designer`
- Added experiment `npu-probe`

## [1.1.4.2.16] - 2026-10-09

- calibration scripts gate on the watchdog heartbeat (mtime only)
- Added experiment `data-designer`
- Updated experiment `verifier-gold`

## [1.1.4.2.15] - 2026-10-09

- calibration: per-model think from Ollama capabilities; smoke driver
- Added experiment `data-designer`
- Added experiment `verifier-gold`

## [1.1.4.2.14] - 2026-10-08

- reasoning batch 2 blind-relabelled 208/213 and merged; reasoning back to tune/heldout
- Added experiment `data-designer`
- Updated experiment `verifier-gold`

## [1.1.4.2.13] - 2026-10-08

- calibration chain: 15-min rest between models, incomplete stops the chain
- Added experiment `data-designer`
- Updated experiment `verifier-gold`

## [1.1.4.2.12] - 2026-10-08

- calibration protocol amended before any run: reasoning runs on all (under 100 unsupported per split)
- Added experiment `data-designer`
- Updated experiment `verifier-gold`

## [1.1.4.2.11] - 2026-10-08

- calibration protocol pre-registered: tune selects, heldout headline, local 13.4
- Added experiment `data-designer`
- Added experiment `verifier-gold`

## [1.1.4.2.10] - 2026-10-08

- cross-family label check PASS (2 gold errors in 120, fixed); calibration files named
- Added experiment `data-designer`
- Updated experiment `verifier-gold`

## [1.1.4.2.9] - 2026-10-08

- cross-family label check pre-registered: 120-claim sample, gemma4:31b, pass at most 3 gold errors
- Added experiment `data-designer`
- Added experiment `verifier-gold`

## [1.1.4.2.8] - 2026-10-08

- Kev env README: bf16 criterion change disclosed in the gate section
- Added experiment `data-designer`
- Updated experiment `kev-judge-finetune`

## [1.1.4.2.7] - 2026-10-08

- Kev cu134 + causal-conv1d passes, 4.80 s median step; Windows torch.compile probe works
- Updated experiment `cuda-graphs`
- Added experiment `data-designer`
- Updated experiment `kev-judge-finetune`

## [1.1.4.2.6] - 2026-10-08

- atlas map regenerated (CI red since 1.1.4.1.5)
- Added experiment `data-designer`
- Added experiment `kev-judge-finetune`

## [1.1.4.2.5] - 2026-10-08

- site: override postcss-selector-parser to 7.1.6 (Dependabot alert 1)
- Added experiment `data-designer`
- Added experiment `kev-judge-finetune`

## [1.1.4.2.4] - 2026-10-08

- verifier gold, hard reasoning batch blind-relabelled, reasoning at 111 unsupported
- Added experiment `data-designer`
- Added experiment `kev-judge-finetune`
- Updated experiment `verifier-gold`

## [1.1.4.2.3] - 2026-10-08

- verifier gold, Publisher diff-based reasoning set blind-relabelled 208/208
- Added experiment `data-designer`
- Added experiment `kev-judge-finetune`
- Updated experiment `verifier-gold`

## [1.1.4.2.2] - 2026-10-08

- verifier gold: PR set adjudicated (373), grounded unsupported 241
- Added experiment `data-designer`
- Added experiment `kev-judge-finetune`
- Updated experiment `verifier-gold`

## [1.1.4.2.1] - 2026-10-08

- verifier gold batch 3: docs vs code
- Added experiment `data-designer`
- Added experiment `kev-judge-finetune`
- Updated experiment `verifier-gold`

## [1.1.4.2.0] - 2026-10-08

- verifier grounded gold set, batches 1-2 (111 claims)
- Updated experiment `cuda-graphs`
- Added experiment `data-designer`
- Added experiment `kev-judge-finetune`
- Added experiment `verifier-gold`

## [1.1.4.1.6] - 2026-10-08

- causal-conv1d built for cu134 via pip nvcc 13.4
- Added experiment `data-designer`
- Updated experiment `kev-judge-finetune`

## [1.1.4.1.5] - 2026-10-08

- CUDA graphs measured: 7.2-25x on aspire critic heads
- Updated `2026-10-07-cuda-graphs`: CUDA Graphs
- Updated experiment `cuda-graphs`
- Added experiment `data-designer`

## [1.1.4.1.4] - 2026-10-08

- kev cu134 passes full band; graphed_heads seeds CUDA RNG
- Updated experiment `cuda-graphs`
- Added experiment `data-designer`
- Updated experiment `kev-judge-finetune`

## [1.1.4.1.3] - 2026-10-08

- kev cu134 rerun prep: fla/fastapi restored, fla #1330 patch, speed gate
- Added experiment `data-designer`
- Updated experiment `kev-judge-finetune`

## [1.1.4.1.2] - 2026-10-08

- B200 probe: CUDA 13.4 under cuda-compat passes 9 of 9; 2 locality domains
- Updated experiment `cloud-cu134`

## [1.1.4.1.1] - 2026-10-08

- cuda-compat-13-4 gives a real 13.4 driver API on RunPod 13.0 hosts
- Updated experiment `cloud-cu134`

## [1.1.4.1.0] - 2026-10-08

- cloud cu134 probe on a RunPod CUDA 13.0 host; kev cu132 fallback env
- Added experiment `cloud-cu134`
- Updated experiment `kev-judge-finetune`

## [1.1.4.0.13] - 2026-10-08

- cuda-graphs probe venv moved to E:/AI/envs/triton-probe (watchdog-guarded)
- Updated experiment `cuda-graphs`

## [1.1.4.0.12] - 2026-10-08

- CUDA graphs build-out for aspire-si critic heads (code, CPU tests, gates; GPU run pending)
- Updated `2026-10-07-cuda-graphs`: CUDA Graphs
- Added experiment `cuda-graphs`

## [1.1.4.0.11] - 2026-10-08

- kev env: fallback is stable cu132 (to be built), not cu128 (Director)
- Updated experiment `kev-judge-finetune`

## [1.1.4.0.10] - 2026-10-08

- kev-judge-finetune: new-env runs write their own output names, never over a reference run
- Updated experiment `kev-judge-finetune`

## [1.1.4.0.9] - 2026-10-08

- kev-judge-finetune: CUDA 13.4 env (torch 2.16 nightly cu134) pinned with a lock file and a fixed pass band; KEV_VENV selects the env
- Updated experiment `kev-judge-finetune`

## [1.1.4.0.8] - 2026-10-08

- nvidia-skills review: training-lane skills read (tao-finetune-huggingface-model, nemo-rl-auto-research, data-designer, nemotron-customize)
- Updated catalog `nvidia-skills`

## [1.1.4.0.7] - 2026-10-08

- natural-errors build.py p2: numbered sentences, one verdict per sentence, tune half only, resumable, run tags for the noise floor and the thinking dial
- Updated experiment `natural-errors`

## [1.1.4.0.6] - 2026-10-08

- hymn-arrangements uploaded (private), round-trip verified 21/21

## [1.1.4.0.5] - 2026-10-08

- natural-errors: pre-registered tuning grid, frozen 53/42 split, P1 baselines on the tune half; R&D pre-run amendments (per-sentence schema, cross-family verifier); full-95 screen plan withdrawn
- Updated experiment `natural-errors`

## [1.1.4.0.4] - 2026-10-08

- natural-errors: screen2 full-run plan and the 40% bar, committed before the run; --sample
- Updated experiment `natural-errors`

## [1.1.4.0.3] - 2026-10-08

- Data pack hymn-arrangements (v1, spec and manifest; not uploaded): three Kimi-K3 piano arrangements of public-domain hymns, CC0, with briefs, prompts, raw answers and generation records. The arrangement entry's CC0 and public-domain claims are verified at source.
- Updated `2026-10-08-llm-piano-arrangement-from-a-generated-brief`: Piano arrangements by an LLM from a brief generated from the score

## [1.1.4.0.2] - 2026-10-08

- natural-errors: context-rich screen pilot (5 judges x 3 answers); capability-aware thinking, reasoning-first replies, --num-predict
- Added experiment `natural-errors`

## [1.1.4.0.1] - 2026-10-08

- Six findings and one instrument from the ai-jam-sessions sung-exemplar work: the pyannote one-voice gate, aligner misdates, the phrase-end hold, LLM piano arrangement from a generated brief, Pages cache stitching of replaced media, TranslateGemma fraction and name slips; instrument sung-exemplar-method.
- Added `2026-10-08-aligner-misdates-cause-sung-dropouts`: Misdated syllable onsets cause dropouts in phrase-picked singing
- Added `2026-10-08-llm-piano-arrangement-from-a-generated-brief`: Piano arrangements by an LLM from a brief generated from the score
- Added `2026-10-08-pages-cache-stitches-replaced-media`: Replacing a media file under the same URL on GitHub Pages can break playback
- Added `2026-10-08-phrase-end-hold-removes-the-stutter`: Holding the phrase-final note removes the "stutter" in placed singing
- Added `2026-10-08-translategemma-failure-modes-on-readme-tables`: TranslateGemma 27B mistranslates fractions and transliterates model names
- Added `2026-10-08-voice-gate-pyannote-segmentation-on-sung-vocals`: A one-voice gate for synthesised singing with pyannote segmentation
- Added `sung-exemplar-method`: Sung-exemplar method — a hymn to a published sung recording
- Updated experiment `natural-errors`

## [1.1.4.0.0] - 2026-10-08

- rnd datapack build|list|verify: data packs hosted outside the clone, with per-file SHA-256, licences and model pins (integrity model from research-packs)
- first pack: natural-errors v1, private on Hugging Face (mcp-tool-shop/rnd-natural-errors)
- natural-errors build.py: screen2, a context-rich re-screen (thinking where supported, reasoning-first otherwise, failure reasons logged)
- Updated experiment `natural-errors`

## [1.1.3.3.2] - 2026-10-08

- muse-glimmer as a natural-error screen judge
- Updated `2026-10-08-three-follow-up-studies-for-critic-recipes-hard-pairs-two-pl`: Three follow-up studies for critic recipes — hard pairs, two planter families, natural errors
- Updated experiment `natural-errors`

## [1.1.3.3.1] - 2026-10-08

- SAM3 and sam-3d-objects access accepted
- Updated `2026-10-08-gated-model-scouting-what-to-request-for-the-critic-audio-an`: Gated model scouting — what to request for the critic, audio and visual research

## [1.1.3.3.0] - 2026-10-08

- Study A natural-error set labelled (two blind Claude passes, adjudicated); screen readout; 31 correction pairs
- Updated `2026-10-08-three-follow-up-studies-for-critic-recipes-hard-pairs-two-pl`: Three follow-up studies for critic recipes — hard pairs, two planter families, natural errors
- Updated experiment `natural-errors`

## [1.1.3.2.7] - 2026-10-08

- Scouting: Llama 4 access accepted
- Updated `2026-10-08-gated-model-scouting-what-to-request-for-the-critic-audio-an`: Gated model scouting — what to request for the critic, audio and visual research

## [1.1.3.2.6] - 2026-10-08

- Gemma licensing checked at the source: Gemma 4 is Apache-2.0, outside the Gemma Terms
- Updated `2026-10-08-gated-model-scouting-what-to-request-for-the-critic-audio-an`: Gated model scouting — what to request for the critic, audio and visual research

## [1.1.3.2.5] - 2026-10-08

- Kev judge fine-tune transfers to gemma-planted errors; scouting gating corrections
- Updated `2026-10-07-open-jev-style-decision-models`: Open Jev-style decision models — the landscape, checked against primary sources
- Updated `2026-10-08-gated-model-scouting-what-to-request-for-the-critic-audio-an`: Gated model scouting — what to request for the critic, audio and visual research
- Updated experiment `kev-judge-finetune`

## [1.1.3.2.4] - 2026-10-08

- Scouting: access status and a reading of the Gemma Terms of Use
- Updated `2026-10-08-gated-model-scouting-what-to-request-for-the-critic-audio-an`: Gated model scouting — what to request for the critic, audio and visual research

## [1.1.3.2.3] - 2026-10-08

- Fix: aggregator source URL in the scouting entry
- Updated `2026-10-08-gated-model-scouting-what-to-request-for-the-critic-audio-an`: Gated model scouting — what to request for the critic, audio and visual research

## [1.1.3.2.2] - 2026-10-08

- Gated model scouting: what to request for the critic, audio and visual research
- Added `2026-10-08-gated-model-scouting-what-to-request-for-the-critic-audio-an`: Gated model scouting — what to request for the critic, audio and visual research
- Added experiment `kev-judge-finetune`

## [1.1.3.2.1] - 2026-10-08

- ASPIRE: the found Auditor holds on fresh pairs (0.678)
- Updated `2026-10-08-more-prompts-raise-the-aspire-critic-s-accuracy-but-not-its-`: More prompts raise the ASPIRE critic's accuracy but not its spread between seeds; critic init and run seed both carry the spread

## [1.1.3.2.0] - 2026-10-08

- Experiment natural-errors: in-domain natural-error yardstick built (95 answers, 3-judge screen, 85 for review)
- Added experiment `natural-errors`

## [1.1.3.1.1] - 2026-10-08

- Three follow-up studies for critic recipes: designs for natural errors, two planter families, hard pairs
- Added `2026-10-08-three-follow-up-studies-for-critic-recipes-hard-pairs-two-pl`: Three follow-up studies for critic recipes — hard pairs, two planter families, natural errors

## [1.1.3.1.0] - 2026-10-08

- Dataset recipes for critic jury roles: evidence, recipe card, controls, panel selection, role-os connection
- Added `2026-10-08-dataset-recipes-for-critic-jury-roles-designing-roles-by-dat`: Dataset recipes for critic jury roles — designing roles by data and choosing the panel

## [1.1.3.0.8] - 2026-10-08

- ASPIRE critic-init: report PR #44; seed-44 composite critic may have been an inverted draw
- Updated `2026-10-07-sft-before-aspire-weakens-critic`: SFT before ASPIRE has no reliable effect on the critic; run-to-run critic variance dominates (3 seeds)
- Updated `2026-10-08-more-prompts-raise-the-aspire-critic-s-accuracy-but-not-its-`: More prompts raise the ASPIRE critic's accuracy but not its spread between seeds; critic init and run seed both carry the spread

## [1.1.3.0.7] - 2026-10-08

- ASPIRE critic-init test: init and run seed both carry the spread; one init inverted the critic
- Updated `2026-10-08-more-prompts-raise-the-aspire-critic-s-accuracy-but-not-its-`: More prompts raise the ASPIRE critic's accuracy but not its spread between seeds; critic init and run seed both carry the spread

## [1.1.3.0.6] - 2026-10-08

- ASPIRE step 2: report PR #42 as primary source
- Updated `2026-10-08-more-prompts-raise-the-aspire-critic-s-accuracy-but-not-its-`: More prompts raise the ASPIRE critic's accuracy but not its spread between seeds

## [1.1.3.0.5] - 2026-10-08

- ASPIRE step 2: more prompts raise the critic's level, not its seed spread
- Updated `2026-10-07-sft-before-aspire-weakens-critic`: SFT before ASPIRE has no reliable effect on the critic; run-to-run critic variance dominates (3 seeds)
- Added `2026-10-08-more-prompts-raise-the-aspire-critic-s-accuracy-but-not-its-`: More prompts raise the ASPIRE critic's accuracy but not its spread between seeds

## [1.1.3.0.4] - 2026-10-08

- America the Beautiful is written at 92 BPM: relative verse build and coda
- Updated `2026-10-07-expressive-timing-and-emphasis-for-a-sung-hymn-performance-r`: Expressive timing and emphasis for a sung hymn — performance rules applied to synthetic singing

## [1.1.3.0.3] - 2026-10-08

- Hymn timing: Battle Hymn outcome; per-hymn values for Amazing Grace and America the Beautiful
- Updated `2026-10-07-expressive-timing-and-emphasis-for-a-sung-hymn-performance-r`: Expressive timing and emphasis for a sung hymn — performance rules applied to synthetic singing

## [1.1.3.0.2] - 2026-10-08

- Battle Hymn: SoulX's measured dotted ratio at 76–80 BPM (0.57) replaces the assumption; A/B contrast 1 reframed
- Updated `2026-10-07-expressive-timing-and-emphasis-for-a-sung-hymn-performance-r`: Expressive timing and emphasis for a sung hymn — performance rules applied to synthetic singing

## [1.1.3.0.1] - 2026-10-08

- Experiment scripts point at E:/AI/rnd, the local folder's new name
- Updated experiment `kev-judge-finetune`
- Updated experiment `openjev-vs-jev`

## [1.1.3.0.0] - 2026-10-08

- Name-clash fix: the code moves to `mcptoolshop_rnd` (the import name that always works); `rnd` stays as a compatibility shim that aliases every submodule, and the `rnd` command runs `mcptoolshop_rnd.cli:main`, so an unrelated PyPI `rnd` replacing the shim breaks neither the command nor `python -m mcptoolshop_rnd`
- tests/test_packaging.py and a CI clash check (a raising rnd/ stub after a clean install) prove it

## [1.1.2.0.0] - 2026-10-08

- Packaged for PyPI as `mcptoolshop-rnd` (pyproject.toml, uv.lock); the `rnd` command finds its library via `--library`, `$RND_ROOT` or the nearest folder with entries/ and instruments/, else stops with NO_LIBRARY
- release.yml: publishes to PyPI by trusted publishing when a GitHub release is published; refuses a tag that differs from the package version
- CI: build, twine check, clean-install smoke and pip-audit; README and handbook document the install

## [1.1.1.2.3] - 2026-10-07

- Battle Hymn expressive timing and emphasis research
- Added `2026-10-07-expressive-timing-and-emphasis-for-a-sung-hymn-performance-r`: Expressive timing and emphasis for a sung hymn — performance rules applied to synthetic singing

## [1.1.1.2.2] - 2026-10-07

- Kev judge: scorer identity with the reference confirmed
- Updated experiment `kev-judge-finetune`

## [1.1.1.2.1] - 2026-10-07

- Kev judge weights in the private HF repo
- Updated `2026-10-07-open-jev-style-decision-models`: Open Jev-style decision models — the landscape, checked against primary sources
- Updated experiment `kev-judge-finetune`

## [1.1.1.2.0] - 2026-10-07

- Kev-4B judge fine-tune: three seeds pass the pre-registered rule; aspire-si confirmation filed
- Updated `2026-10-07-open-jev-style-decision-models`: Open Jev-style decision models — the landscape, checked against primary sources
- Updated `2026-10-07-qwen32b-judge-position-bias`: Qwen2.5-32B as a judge of planted errors — ties, total position bias, and how to plant errors
- Updated experiment `kev-judge-finetune`

## [1.1.1.1.0] - 2026-10-07

- New experiment kev-judge-finetune: Kev-4B LoRA fine-tune as a planted-error judge on aspire-si's fresh pairs (1,086 rows, both orders, 0 leaks), success rule written before the run
- Added experiment `kev-judge-finetune`

## [1.1.1.0.19] - 2026-10-07

- Planted-defects program: event spans merged (#96); detector heads fit their operating point on validation mixes; a third song (Battle Hymn) makes the song split 3-fold
- Updated `2026-10-07-planted-defects-program-for-sung-mixes`: Planted defects for sung mixes — an automated planter-versus-detector loop, anchored by the listener's measured threshold

## [1.1.1.0.18] - 2026-10-07

- Planted-defects program: event spans (#96) and detector heads (#98) as CPU-tested code; the operating point must include shams
- Updated `2026-10-07-planted-defects-program-for-sung-mixes`: Planted defects for sung mixes — an automated planter-versus-detector loop, anchored by the listener's measured threshold

## [1.1.1.0.17] - 2026-10-07

- Planted-defects program: planter PR 2 merged (#95); Step B split between ai-jam-sessions (clips, evidence) and the R&D seat (MERT/Dasheng heads); MERT is CC BY-NC, so a shipped detector needs Dasheng
- Updated `2026-10-07-planted-defects-program-for-sung-mixes`: Planted defects for sung mixes — an automated planter-versus-detector loop, anchored by the listener's measured threshold

## [1.1.1.0.16] - 2026-10-07

- Planted-defects program: planter PR 2 opened as ai-jam-sessions #95; alternate picks (#94) merged
- Updated `2026-10-07-planted-defects-program-for-sung-mixes`: Planted defects for sung mixes — an automated planter-versus-detector loop, anchored by the listener's measured threshold

## [1.1.1.0.15] - 2026-10-07

- Kev as a judge: 9B trails 4B because its order gap is noisier (sd 0.205 vs 0.144; 25 vs 3 pairs on the wrong side), not because it is less biased; the confirmation run is specified
- Updated `2026-10-07-open-jev-style-decision-models`: Open Jev-style decision models — the landscape, checked against primary sources

## [1.1.1.0.14] - 2026-10-07

- Kev as a judge (exploratory): averaging over both answer orders took Kev-4B from 0.547 to 0.976 on aspire-si's 127 planted-error pairs; to be confirmed on fresh pairs. Cross-linked from the Qwen-32B judge entry
- Updated `2026-10-07-open-jev-style-decision-models`: Open Jev-style decision models — the landscape, checked against primary sources
- Updated `2026-10-07-qwen32b-judge-position-bias`: Qwen2.5-32B as a judge of planted errors — ties, total position bias, and how to plant errors

## [1.1.1.0.13] - 2026-10-07

- Kev: training is adapter-only for 0.8B/4B/9B, so a local WSL run on the 5090 is plausible; smoke-test before renting
- Updated `2026-10-07-open-jev-style-decision-models`: Open Jev-style decision models — the landscape, checked against primary sources

## [1.1.1.0.12] - 2026-10-07

- Kev: how to fine-tune it (--init_from, JSONL with labels), its server switches (/permute against option-order bias, KEV_DATE_FACTS), and that kev.train fails on native Windows
- Updated `2026-10-07-open-jev-style-decision-models`: Open Jev-style decision models — the landscape, checked against primary sources

## [1.1.1.0.11] - 2026-10-07

- Planted-defects program: PR 2 built (stretch, pitch slip, vocoded sham, compound kinds); compounds are 3–4× more available than clean replays, and replay+early-vowel has no eligible join in the shipped warp mixes
- Kev as a planted-error judge: 0.547 (4B) and 0.598 (9B) with heavy first-option bias; not a useful judge for that task
- Updated `2026-10-07-open-jev-style-decision-models`: Open Jev-style decision models — the landscape, checked against primary sources
- Updated `2026-10-07-planted-defects-program-for-sung-mixes`: Planted defects for sung mixes — an automated planter-versus-detector loop, anchored by the listener's measured threshold

## [1.1.1.0.10] - 2026-10-07

- Planted-defects program: planter #91 ready; warp clicks verified at either hard edge of a seam and graded by crossfade length; final warp trial kept 83/100 and 86/100
- Updated `2026-10-07-planted-defects-program-for-sung-mixes`: Planted defects for sung mixes — an automated planter-versus-detector loop, anchored by the listener's measured threshold

## [1.1.1.0.9] - 2026-10-07

- Planted-defects program: only 13–15% of shipped warp joins can carry a clean replay/skip once vowel-move and pause compounds are refused; replays now verify 17–18 of 20
- Updated `2026-10-07-planted-defects-program-for-sung-mixes`: Planted defects for sung mixes — an automated planter-versus-detector loop, anchored by the listener's measured threshold

## [1.1.1.0.8] - 2026-10-07

- SFT-before-ASPIRE correction: aspire-si PR #30 and the run 1 report added as primary sources
- Updated `2026-10-07-sft-before-aspire-weakens-critic`: SFT before ASPIRE has no reliable effect on the critic; run-to-run critic variance dominates (3 seeds)

## [1.1.1.0.7] - 2026-10-07

- Correction: SFT before ASPIRE has no reliable effect on the critic (3 seeds, pre-registered rule); the earlier claim is marked wrong. Critic run-to-run variance (0.425–0.866) and a replicating ASPIRE drift direction against SFT are the findings that hold
- Pod host checks: container disk with HF_HOME on it wrote at ~1.3 GB/s; one draw stalled pulling its image
- Updated `2026-10-07-pod-host-checks-driver-and-download`: Rented GPU pods — the driver and download speed vary per host, so check both first
- Updated `2026-10-07-sft-before-aspire-weakens-critic`: SFT before ASPIRE has no reliable effect on the critic; run-to-run critic variance dominates (3 seeds)

## [1.1.1.0.6] - 2026-10-07

- Planted-defects program: #91 review fixes; warp replay/skip plants displace the cut's vowel (0.1 s replays moved it 0.18–0.21 s), now recorded per label
- Updated `2026-10-07-planted-defects-program-for-sung-mixes`: Planted defects for sung mixes — an automated planter-versus-detector loop, anchored by the listener's measured threshold

## [1.1.1.0.5] - 2026-10-07

- New logo (brand repo logos/rnd), teal accent and favicon to match
- Planted-defects program: planter engine rebased on the placer overrides; warp trial on the shipped mixes kept 75/100 and 77/100; finding that the pad16 warp mixes have no mid-phrase splices
- Updated `2026-10-07-planted-defects-program-for-sung-mixes`: Planted defects for sung mixes — an automated planter-versus-detector loop, anchored by the listener's measured threshold

## [1.1.1.0.4] - 2026-10-07

- Planted-defects program: planter engine drafted as ai-jam-sessions #91 (plan mutation, replay/skip measured from where the take had reached; 39/40 plants kept on a real mix)
- Updated `2026-10-07-planted-defects-program-for-sung-mixes`: Planted defects for sung mixes — an automated planter-versus-detector loop, anchored by the listener's measured threshold

## [1.1.1.0.3] - 2026-10-07

- Planted-defects program: RunPod cost estimate from live offrig prices (Step B $2.50–14.50; first full program $5–30) against about $2–3 of electricity on the local 5090
- Updated `2026-10-07-planted-defects-program-for-sung-mixes`: Planted defects for sung mixes — an automated planter-versus-detector loop, anchored by the listener's measured threshold

## [1.1.1.0.2] - 2026-10-07

- Planted-defects program: adopted by ai-jam-sessions; calibrated review tracked as ai-jam-sessions #89
- Updated `2026-10-07-planted-defects-program-for-sung-mixes`: Planted defects for sung mixes — an automated planter-versus-detector loop, anchored by the listener's measured threshold

## [1.1.1.0.1] - 2026-10-07

- Planted-defects program for sung mixes: an automated planter-versus-detector loop with a regret reward, a MERT frame-level detector, and the Director's catch trials setting the audibility line (seven research agents' findings)
- Added `2026-10-07-planted-defects-program-for-sung-mixes`: Planted defects for sung mixes — an automated planter-versus-detector loop, anchored by the listener's measured threshold

## [1.1.1.0.0] - 2026-10-07

- Coverage bar raised to 90%: CI fails under 90% and Codecov's project and patch targets are 90%
- 45 tests (was 25), including end-to-end CLI tests of every command, catalogue sync with gh mocked, and rnd bump in a real git repo; rnd/ coverage 96% (was 63%)

## [1.1.0.0.0] - 2026-10-07

- Added `rnd bump`: five-segment versions (MAJOR.MINOR.PATCH.MICRO.NANO) with a CHANGELOG section written from the files changed since the last tag
- Kev-4B and Kev-9B measured against hosted Jev and OpenJev on sense-si's 124 phrases, 0-shot and with knowledge in context
- Added `2026-10-07-open-jev-style-decision-models`: Open Jev-style decision models — the landscape, checked against primary sources
- Updated `2026-10-07-openjev-and-open-jev-alternatives`: OpenJev and the other open "Jev" models — what each one is
- Updated experiment `openjev-vs-jev`

## [1.0.0] - 2026-10-07

### Added

- `rnd` CLI over a Markdown research library: `build`, `check`, `search`, `show`,
  `list`, `tools`, `stats`, `new`, `catalog`, `readouts`, `sql`, each listing with `--json`.
- Entry format with source tiers (`primary`, `secondary`, `aggregator`, `user`, `rig`)
  and claim confidence (`unverified`, `verified`, `disputed`, `wrong`; `verified`
  needs a `via:` note).
- SQLite FTS5 index (`rnd.db`), rebuilt automatically when files change; the previous
  index is kept when a rebuild meets errors.
- Instrument registry (`instruments/`) of the studio tools research can call.
- NVIDIA skills catalogue mirror (398 skills, 18 lanes) with a studio-fit review.
- `rnd readouts`: read-only federated search across the readouts knowledge bases,
  with prefix matching and `--any`.
- `experiments/` for rig measurements, with pinned inputs and result receipts.
- `--version`, and `--debug` to show a traceback; unexpected errors otherwise print
  a structured `INTERNAL` error and exit 3.
- `verify.sh` (tests, library check, index build, smoke), CI, landing page and handbook.

### Fixed

- The `rnd sql` error hint pointed at a missing `docs/schema.md`; it now shows how
  to list the tables.
