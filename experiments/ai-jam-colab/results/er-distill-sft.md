# 3B: verifier-checked E-R distillation and two 4B student LoRAs

Source: Antigravity reply, 2026-11-13 11:08 UTC (06:08 ET), final window `jam-er-distill-g4-3`.
`[unverified]`: the replies' own counts; the only check the reply reports is a local parity
test between the Python verifier and the TypeScript one (0 of 22 mismatches on one
reference proposal file, 0 of 336 chord round-trips).

## Setup

- **Teacher:** `Qwen/Qwen2.5-32B-Instruct` (pinned revision), 8 draws per window at
  temperature 0.8, top-p 0.95, over ABC-notation reharmonisation of 415 training melody
  windows: 3,320 candidates.
- **Gate:** each candidate must pass the harmony verifier, a non-triviality score of at
  least 1/3 and a completeness of at least 0.75. Passing candidates are ranked per window by
  (completeness, lower chromatic ratio, stepwise ratio, non-triviality). Chord voicing is
  rendered deterministically afterwards, so chord fidelity is 100% by construction.
- **Students:** `Qwen/Qwen3-4B-Instruct-2507` with a rank-16 LoRA, 3 epochs, on 408 rows,
  in two surfaces: `full_voiced` (the model writes the measures, intended chords and
  voicings in one shot, with no voicing helper at inference) and `abc_decompose` (the model
  writes ABC, and a deterministic voicing helper supplies the chords).
- **Disjointness (the reply's statements):** zero overlap with the 22 frozen gate songs and
  with the sealed holdout song; 80 training songs (415 windows) against 5 held-out songs (47
  windows) with no song in both; the sealed cohort file was never read.
- **Motivation (as the reply cites it):** an earlier design note put single-shot end-to-end
  voiced reharmonisation at 9.1% (2 of 22) on the 7B base, held back by 37% chord-voicing
  fidelity.

## Teacher acceptance

408 of 415 training windows (98.31%) had a verified candidate; 129 of 131 (98.47%) of the
open-licence "publishable" windows (public domain or CC-BY-SA-3.0-DE).

## Held-out validation (47 windows, 5 songs, greedy, single shot)

| Surface and model | pass@1 (75% of bars) | pass@1 (100% of bars) | Publishable subset (n=35) | Mean chord fidelity | Mean chromatic ratio | Mean non-triviality | Eval wall |
|---|---:|---:|---:|---:|---:|---:|---:|
| full_voiced, base 4B | 6.38% (3/47) | 6.38% (3/47) | 5.71% (2/35) | 48.14% | 0.0823 | 0.9628 | 45.66 s |
| full_voiced, distilled LoRA | 87.23% (41/47) | 87.23% (41/47) | 88.57% (31/35) | 98.67% | 0.0688 | 0.9122 | 52.22 s |
| abc_decompose, base 4B + voicing helper | 95.74% (45/47) | 80.85% (38/47) | 97.14% (34/35) | 100.00% | 0.0770 | 0.9287 | 38.20 s |
| abc_decompose, distilled LoRA + voicing helper | 91.49% (43/47) | 91.49% (43/47) | 94.29% (33/35) | 100.00% | 0.0765 | 0.9043 | 18.96 s |

Reply's headline: `full_voiced` pass@1 6.38% to 87.23% (+80.85 points, "13.7x"), all 41
passing outputs fully measure-complete; publishable subset 5.71% to 88.57%; chord fidelity
48.14% to 98.67%. The decomposed surface's 100%-measure-complete pass rate went from 80.85%
to 91.49% (+10.64 points) while generation wall time fell from 38.20 s to 18.96 s.

Note for readers: on the 75%-of-bars criterion the base model with the voicing helper
(95.74%) scores higher than the distilled LoRA with it (91.49%); the LoRA wins on the
100%-complete criterion and on speed. Two of the four rows differ by two windows.

## Windows and units

| Window | Card | Elapsed (s) | Units | Outcome |
|---|---|---:|---:|---|
| `jam-er-distill-cpustub-1` | CPU | 157.374 | 0.011366 | ok; 415 train and 47 validation windows, zero leakage into the gate songs |
| `jam-er-distill-g4-1` | G4 | 1,075.559 | 3.002603 | 68 of 68 teacher windows verified (432 of 544 draws pass); out-of-memory on a dense window, fixed |
| `jam-er-distill-g4-2` | G4 | 4,927.795 | 13.756762 | all 415 teacher windows distilled and saved; a student tokenisation length guard (3,077 tokens over 2,048) fixed by raising the limit |
| `jam-er-distill-g4-3` | G4 | 958.924 | 2.676995 | ok; 417 of 417 complete; four corpora and two LoRAs |

Total 19.447726 units (recomputed; the reply says 19.448).

## Artefacts (kept on the rig; names, rows, bytes, sha256)

| Artefact | Rows / size | Scope | sha256 |
|---|---:|---|---|
| full-voiced corpus (gz) | 408 rows, 95,659 B | internal library (train) | `19b926b3a760faf4b7db7d1e79a52a55130a400382658e3f8ac0e5bdf3ba7f40` |
| abc-decompose corpus (gz) | 408 rows, 80,221 B | internal library (train) | `cf99f6e10ff86fe512c002f426c3c0dc923ddea2d9d8365e798ff8203502ff11` |
| full-voiced publishable corpus (gz) | 129 rows, 25,715 B | publishable (public domain, CC-BY-SA-3.0-DE) | `a80c0055a983a5c520f770e762aa296651418772748a3f8eb1091fc4b56d104b` |
| abc-decompose publishable corpus (gz) | 129 rows, 20,563 B | publishable | `4383e68f4a491b1cde06fe2855696ad060262d1e3902787a5219c76b566fc8af` |
| full-voiced LoRA adapter | 132,187,888 B (loss 3.577 to 0.586) | trained on 408 rows | `9abadae3e9f4b045a6ccd4deb8bb9f241bd4158524d8f6d02c7005749e7e370c` |
| abc-decompose LoRA adapter | 132,187,888 B (loss 5.689 to 1.102) | trained on 408 rows | `bbe03c4de999deb5766e28a543e18c0dc10342277e3e699dfb0ec39ff70cf84a` |

The teacher's output feeds a training corpus; the licence entry for Qwen2.5-32B-Instruct and
the corpus's publishable scope are for the Publisher's check before any release.
