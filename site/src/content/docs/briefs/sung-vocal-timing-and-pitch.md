---
title: How close to the beat and the note do the sung hymns land?
description: Three published hymn renders (SoulX singing voice, local 5090), measured syllable by syllable. Timing medians are under 10 ms; Battle Hymn's misses are mostly short notes the clock skips by design. The aligner that cross-checks timing is not yet validated.
date: 2026-10-08
status: measured · aligner interim
shelf: pending (readouts-internal vocology-knowledge)
---

## The question

ai-jam-sessions renders hymns with a singing-voice model, then checks every syllable: does its vowel land on
the beat (within 40 ms), and is each note in tune (within 25 cents to pass, 50 to fail)? How did the three
published hymns do, and what limits the checks themselves?

## What we found

| hymn | timing: syllables passing | median / p90 onset error | pitch: notes pass or warn | scatter SD |
|---|---|---|---|---|
| Amazing Grace | 107/112 | 7.8 / 20 ms | 135/140 | 16.6 cents |
| America the Beautiful | 217/224 | 9.4 / 18 ms | 218/224 | 51.5 cents |
| Battle Hymn of the Republic | 285/414 | 9.6 / 45 ms | 368/424 | 42.1 cents |

- **Timing is tight where it's measured.** Battle Hymn's misses are mostly short notes (101 of them) that ride the
  time warp by design. There are also 38 disagreements between methods, 6 silent syllables and 2 empty windows.
- **Pitch is centred:** the global offset is −2.1 to −2.7 cents, but individual notes scatter. A pYIN recheck
  rescued 1, 1 and 12 notes.
- **Phrases are picked whole from one take,** ranked by intelligibility first, then pitch, then timing. Ranking
  timing first had made Amazing Grace worse (8 pitch fails became 14).
- **Before the song, a sound check predicts the takes needed.** It rendered one America phrase 3 times and said
  4 takes, which matches what the exemplar needed (7 if both timing instruments must agree). Vowel-first words
  land early (about −62 ms) and stops and fricatives late (+51 and +47 ms), but the spread from render to render
  (29–82 ms) is too wide for a fixed correction. The answer is choosing takes, not shifting them.
- **The one-voice gate catches only 3 of 20 marked "honks"** in its evaluation. Its flags are good; its recall is
  low.

![Onset timing error per syllable](/rnd/charts/vocal-timing.svg)

![Pitch per note](/rnd/charts/vocal-pitch.svg)

## Caveats

- **The forced aligner is not validated.** It is the timing gate's second instrument: it can rescue a syllable
  but never fails one alone. Its validation against a human-annotated corpus hasn't run, pending corpus
  licences (Director, 2026-10-06), so its ±20 ms agreement band is provisional. It has gross errors of its
  own, up to 1.4 s on long phrases.
- **The listening model (Qwen3-Omni, local) is advisory only.** It heard 89% of Amazing Grace's words and 75% of
  America's on the first renders, but it can fill in a famous line from memory, so it ranks takes and never
  gates them. These first-render figures are prose in `docs/vocal-clock.md` @ 99c0216, without committed
  receipts.
- The sound-check figures come from one phrase and one voice, with 3 renders. An earlier detector-only version
  (589538e) is superseded.
- The artefact detector heads are built and tested but have no recorded results yet, so they aren't charted.

## Receipts

`mcp-tool-shop-org/ai-jam-sessions` @ 5aa092c (merging 836641ef9b):

- `scores/receipts/<song>/sung-2026-10-08/` (receipt, pitch, plan, phrase scores, voice gate, mix, piano bed);
- `scores/receipts/voice-gate-eval-2026-10-08/` (the one-voice gate's evaluation);
- `scores/receipts/README-sung-2026-10-08.md` (field guide);
- `scores/receipts/america-the-beautiful/soundcheck.receipt.json` @ 9b92862.

Every published figure reproduces from these files.
