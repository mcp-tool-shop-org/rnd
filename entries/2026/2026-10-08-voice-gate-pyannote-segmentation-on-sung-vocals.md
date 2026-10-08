---
id: 2026-10-08-voice-gate-pyannote-segmentation-on-sung-vocals
title: A one-voice gate for synthesised singing with pyannote segmentation
date: 2026-10-08
kind: finding
relevance: act
fields: [audio, machine-learning]
tags: [pyannote, segmentation, voice-activity, overlap, singing-synthesis, soulx-singer, artefact-detection, ai-jam-sessions]
---

## Summary

pyannote/segmentation-3.0 is a speech model (voice activity and overlapped speech, up to
three speakers per 10 s window), but on a placed synthetic vocal it separates sung frames
from rests almost perfectly. Read against the score clock, it flags three faults that no
pitch or timing gate sees: a patch of voice in a rest, two voices singing at once, and a
sung note with no voice in it. It is precise, with no false flags on approved vocals.
Its recall on short-gap honks is poor.

## Key points

- Per 17 ms frame, take the strongest speaker's probability as "voice" and the second
  strongest as "overlap". Which speaker slot is which changes between chunks, but the
  strongest and second strongest do not.
- `Inference(step=2.5 s)` returns **per-chunk** frames (chunks × frames × speakers), not a
  stitched timeline. Each frame is seen by four chunks; aggregate by averaging yourself.
- Judge against the score clock with tolerances: 0.15 s consonant lead before an onset,
  0.45 s release after a note, blips under 0.12 s in a rest ignored (breath, reverb).
  Overlap counts only past 0.10 s (crossfades overlap 50 ms by design).
- Voice continuous with a note is that note held into the rest (placement holds phrase
  endings on purpose), so it is flagged only past 1.6 s.
- A sung note counts as silent when its median voice is below 0.2. A median of 0.25 means
  one of the four chunks heard it, which is a soft held ending, not silence.
- Environment: its own venv (torch 2.11.0+cu130, torchaudio 2.11.0+cu130,
  pyannote.audio 4.0.7). Mixing pyannote 4 into an environment with another torchaudio
  build fails on an ABI mismatch. Feed audio as a waveform dict, never through pyannote's
  file decoder. The model is gated on Hugging Face, so HF_TOKEN is required.
- Runs on CPU in about 20 s per 3–4 minute song.

## Studio relevance

The ai-jam-sessions pipeline now runs it on every sung exemplar by default (PRs #111,
#113). It found a near-silent syllable in a published recording that the timing and pitch
gates had passed. The cause was an aligner misdate
([[2026-10-08-aligner-misdates-cause-sung-dropouts]]).

**The limit is honk recall.** A honk in a short gap between phrases is voice to this
model. Telling it from a held vowel needs pitch evidence: the octave-jump and
discontinuity flags in [[2026-10-07-singing-pitch-trackers]], and the join detectors in
[[2026-10-07-join-artefact-detection]]. That is the next step. Broader artefact scoring
is in [[2026-10-07-singing-quality-assessment]].

## Claims

- [verified] On the placed Battle Hymn vocal, mean voice probability is 0.98 in sung frames and 0.08 in rests. (via: ai-jam-sessions voice_gate.py on the RTX 5090 rig, 2026-10-08)
- [verified] It raised no flags on the four vocals the Director had passed by ear. (via: ai-jam-sessions evaluation against the 2026-10-07 listening marks, 2026-10-08)
- [verified] All three of its voice-in-rest flags fell on the Director's honk marks. (via: same evaluation, 2026-10-08)
- [verified] It caught 3 of the 20 marked honks; the 17 it missed sat in short phrase gaps. (via: same evaluation, 2026-10-08)
- [verified] It found a syllable at 0:52 of the published Battle Hymn rendered at −42 dB, which the timing and pitch gates had passed. (via: voice gate on the published vocal, confirmed by listening, 2026-10-08)
- [unverified] Pitch evidence would separate short-gap honks from held vowels.

## Sources

- [primary] https://huggingface.co/pyannote/segmentation-3.0 — model card (MIT, gated)
- [primary] https://github.com/pyannote/pyannote-audio — pyannote.audio
- [rig] ai-jam-sessions scripts/voice_gate.py and test_voice_gate.py (5 synthetic-frame tests); PRs #111, #113, 2026-10-08
- [rig] Batch over 96 raw SoulX-Singer takes on the RTX 5090, under a Publisher GPU grant, 2026-10-08
- [user] The Director's listening marks (honks) on four vocals, 2026-10-07
