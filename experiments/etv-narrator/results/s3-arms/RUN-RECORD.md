# Escape the Valley: experiment arms, session 3 (2026-11-13)

**Result in one line.** The rulings prompt with up to three candidates and trimming brought the fallback rate from 55.5% to 8.1% of lines (paired by turn: +47.4 points of lines accepted, 95% interval +45.1 to +49.7). The prompt rulings and the candidates each did most of that on their own; model-card sampling alone, the unquantised model and the positive wording did not help. **These are rates of lines that pass the rules, not of lines that say what happened**: a reading of 29 accepted lines from the best arm (`READING-SAMPLE-combo-30.md`) found 7 that contradict their turn's facts.

## What was run

- **Pre-granted** by the Publisher and released on the relayed merge sha and "card free", 2026-11-13. One arm (the combination) was added by the Publisher during the run, inside the same grant and wall.
- **Start** 2026-11-13 10:41:52 EST. **End of calls** 14:13:25 EST. **Wall used** 12,658 s (3 h 31 min) of 14,400 s. The deadline (14:41:52 EST) was enforced by `timeout` and was not reached.
- **Code** rust-2.0 at `b12cbb851e2953f51acef89c7c74aba3b9e0ce69` (the merge of #87), clean worktree, release build with `narrator-ollama`, harness unmodified.
- **Turn set** v2, 360 turns, sha256 `095455fb593311ecdb76b139aa1ad20220807bdf7bcd4d236ec648e276c13769`, verified before the first call and by the harness on every cell.
- **Every arm:** the plain schema's 9 cells (3 voices x 3 lengths), 6,480 lines, one process per cell, rows flushed per turn. Local Ollama only (`http://127.0.0.1:11434`). Per call: timeout 10 s, `think: false`, `num_ctx` 2048, derived seeds.
- **Baseline for every comparison:** session 2 (the re-check), same turn set, same code path with every arm off.

| order | arm | flags | model (quant, digest) | calls | minutes | card at end, MiB |
|---|---|---|---|---|---|---|
| c | rulings | `--arm rulings-prompt` | q4_K_M, 0edcdef34593 | 6,480 | 18 | 5,423 |
| d | modelcard | `--arm model-card-sampling` | q4_K_M, 0edcdef34593 | 6,480 | 26 | 5,385 |
| e2 | cand-modelcard | `--arm model-card-sampling --candidates 3 --arm trim-to-cap` | q4_K_M, 0edcdef34593 | 11,379 | 43 | 5,721 |
| added | combo | `--arm rulings-prompt --arm model-card-sampling --candidates 3 --arm trim-to-cap` | q4_K_M, 0edcdef34593 | 8,992 | 23 | 5,575 |
| b | briefstop | `--arm brief-by-stop` | q4_K_M, 0edcdef34593 | 6,480 | 21 | 5,564 |
| f | fp16 | none (shipped prompt and sampling) | F16, 259cbeb0f33b | 6,480 | 48 | 10,963 |
| a | positive | `--prompt-rules positive` | q4_K_M, 0edcdef34593 | 6,480 | 28 | 5,484 |

Calls in all: 52,771.

## Things to know about how it was run

- **The run was stopped and restarted once, on purpose.** The combination arm was added while arm e2 was running. A running shell script cannot be edited safely, so the script was asked to stop at its own between-cells check the moment e2 ended (12:09:58 EST; no arm b cell had started; the model was unloaded), the combination arm was added, and the script was restarted at 12:10:32 EST with the remaining arms under the original deadline. The note written for that stop is `PLANNED-STOP-note.txt`; it was not an andon.
- **The combination arm's sampling is the model card's (0.7 / 0.8 / 20), not 0.15.** Why: arm e2 runs at 0.7, so it cannot show whether candidates differ at 0.15, and the arm that would have shown it was dropped before the run; at 0.7 candidates clearly matter (in e2, 1,183 lines were accepted on the second call and 537 on the third); arm d shows 0.7 costs nothing in acceptance and widens the openings; and this exact flag set is the one #87's byte-identical replay test covers.
- **A defect in the harness's all-rules count, found by this run.** In the two arms with the rulings prompt, Fireside is allowed to say "oxen". The game-side check honours that, and so do the fallback rates and the first-rule counts below. The all-rules list does not: it re-checks each line with the shipped checker, so it lists the draft-animal rule for 1,372 accepted Fireside lines in the rulings arm and 1,551 in the combination arm. Read the `draft_animal_species` all-rules figures for those two arms (1,609 and 1,608) as that artefact. To be fixed in the next harness change.
- **`stop` is honoured by Ollama with `think: false`:** 0 of 2,160 raw Brief answers in arm b ran past a full stop.

## Andon

None fired. No timeouts and no transport or HTTP errors in any arm; every cell made its calls and wrote 360 rows.

## VRAM and the card

- Baseline before the run 2,236 MiB. The q4_K_M model held 5.4 to 5.7 GB.
- **fp16 held about 11 GB:** 10,963 MiB at the end of its arm, peak 11,447 MiB at 13:24:55. That is the session's peak.
- One q4 reading of 10,008 MiB at 12:49:44, at a cell boundary, as in session 1 (a brief double load at warm-up).
- The model was unloaded and Ollama listed no model before each change of quant (12:56:06, card 2,311 MiB; 13:45:00, card 2,318 MiB).
- Final unload with `keep_alive: 0` at 14:13:26. At 14:13:47 the card read 2,230 MiB with no model loaded. **The card is free.**

## Reading the result

1. **The prompt rulings work: 55.5% to 25.4%** (+30.1 points, interval +27.8 to +32.4). Length rejections fell from 1,086 to 16 and quantifier rejections from 1,001 to 29: a target and a sentence count, and no "allowed quantifiers" line, were the whole of it. Fireside gained most (Brief 72.5% to 8.9%).
2. **Candidates work: 56.2% (one call) to 20.4% (up to three)** at the same sampling, for 1.76 calls per line. Trimming removed every length rejection.
3. **Together: 8.1%** (+47.4 points, interval +45.1 to +49.7), at 1.39 calls per line. 74.1% of lines are accepted on the first call. Turn latency p50 344 ms, p95 912 ms (baseline 491 / 632).
4. **Model-card sampling alone changes nothing in acceptance** (-0.7 points, interval -2.2 to +0.8) and widens the openings (unique-opening share 0.198 against 0.142).
5. **Brief by stop fixes Brief** (Chronicler 1.8%, Fireside 21.5%, Uncanny Bearer 4.6%) and nothing else: the Standard and Rich cells match the baseline, so the schema's sentence-item limit has no effect. The model puts every sentence in one item.
6. **The unquantised model is worse, not better: 66.8%** (-11.2 points, interval -13.0 to -9.4), at twice the latency and twice the memory. Quantisation is not our problem.
7. **Positive wording is worse: 63.7%** (-8.1 points, interval -10.1 to -6.1). Length rejections rose to 1,505 and punctuation to 143.
8. **What is left in the combination arm:** resource nouns the turn never mentioned (336 first-rule, 357 at all), personal pronouns (76), numbers and units (37), band vocabulary (35).
9. **Repetition did not improve.** The combination arm's unique-opening share is 0.134 (baseline 0.142). The oxen ruling made a new habit: 1,551 of Fireside's 2,062 accepted lines in that arm mention the oxen.
10. **Coin under the unit rule:** 0 in the rulings, candidates, combination and Brief-by-stop arms; 3, 1 and 2 in the modelcard, fp16 and positive arms.

## What this does not show

The fallback rate counts lines that pass the rules. The Publisher's rulings after reading the combination arm's lines (a next PR, not built) add rules that a line must say what happened. Until those exist, 8.1% is a ceiling on quality, not a measure of it.

## Per arm, against session 2 (the re-check)

| arm | model, quant, digest | cells | lines | calls made | fallback rate (lines) | mean turn pass rate | paired difference vs s2 (points) | 95% interval | unique-opening share | turn latency p50 / p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| s2 baseline | qwen3:4b-instruct-2507-q4_K_M | 9 | 6480 | 6480 | 55.5% | 44.5% | | | 0.142 | 491 / 632 |
| rulings (rulings-prompt) | qwen3:4b-instruct-2507-q4_K_M, Q4_K_M, 0edcdef34593 | 9 | 6480 | 6480 | 25.4% | 74.6% | +30.1 | +27.8 to +32.4 | 0.103 | 290 / 509 |
| modelcard (model-card-sampling) | qwen3:4b-instruct-2507-q4_K_M, Q4_K_M, 0edcdef34593 | 9 | 6480 | 6480 | 56.2% | 43.8% | -0.7 | -2.2 to +0.8 | 0.198 | 472 / 606 |
| cand-modelcard (model-card-sampling+candidates-3+trim-to-cap) | qwen3:4b-instruct-2507-q4_K_M, Q4_K_M, 0edcdef34593 | 9 | 6480 | 11379 | 20.4% | 79.6% | +35.2 | +33.4 to +36.9 | 0.145 | 707 / 1524 |
| combo (rulings-prompt+model-card-sampling+candidates-3+trim-to-cap) | qwen3:4b-instruct-2507-q4_K_M, Q4_K_M, 0edcdef34593 | 9 | 6480 | 8992 | 8.1% | 91.9% | +47.4 | +45.1 to +49.7 | 0.134 | 344 / 912 |
| briefstop (brief-by-stop) | qwen3:4b-instruct-2507-q4_K_M, Q4_K_M, 0edcdef34593 | 9 | 6480 | 6480 | 40.2% | 59.8% | +15.4 | +14.5 to +16.3 | 0.105 | 467 / 597 |
| fp16 (shipped) | qwen3:4b-instruct-2507-fp16, F16, 259cbeb0f33b | 9 | 6480 | 6480 | 66.8% | 33.2% | -11.2 | -13.0 to -9.4 | 0.174 | 874 / 1197 |
| positive (shipped) | qwen3:4b-instruct-2507-q4_K_M, Q4_K_M, 0edcdef34593 | 9 | 6480 | 6480 | 63.7% | 36.3% | -8.1 | -10.1 to -6.1 | 0.147 | 511 / 665 |

The paired difference is the arm minus session 2, per turn, over the cells the arm finished; positive means more lines accepted. Unique-opening share is the accepted-line-weighted mean of the per-cell shares.

## Fallback rate per cell (lines)

| arm | Chronicler brief | Chronicler rich | Chronicler standard | Fireside brief | Fireside rich | Fireside standard | Lantern-Bearer brief | Lantern-Bearer rich | Lantern-Bearer standard |
|---|---|---|---|---|---|---|---|---|---|
| s2 baseline | 46.8% | 54.7% | 49.6% | 72.5% | 56.2% | 65.0% | 46.8% | 51.1% | 57.1% |
| rulings | 31.4% | 45.0% | 38.3% | 8.9% | 25.3% | 8.9% | 14.6% | 36.8% | 19.7% |
| modelcard | 45.1% | 62.2% | 50.6% | 70.8% | 56.1% | 66.1% | 45.4% | 51.8% | 57.9% |
| cand-modelcard | 9.7% | 28.3% | 19.7% | 21.2% | 29.9% | 26.5% | 6.7% | 23.2% | 18.2% |
| combo | 10.4% | 16.0% | 12.4% | 2.9% | 7.9% | 2.8% | 3.2% | 11.9% | 5.7% |
| briefstop | 1.8% | 54.7% | 49.6% | 21.5% | 56.1% | 65.0% | 4.6% | 51.1% | 57.1% |
| fp16 | 67.4% | 76.7% | 69.0% | 71.5% | 57.6% | 64.2% | 60.7% | 66.9% | 66.8% |
| positive | 62.9% | 74.9% | 67.6% | 71.0% | 53.8% | 61.4% | 59.6% | 60.6% | 61.4% |

## First-rule counts (the rule each rejected line broke first)

| rule | s2 | rulings | modelcard | cand-modelcard | combo | briefstop | fp16 | positive |
|---|---|---|---|---|---|---|---|---|
| unauthorised_resource_noun | 611 | 998 | 612 | 415 | 336 | 620 | 1031 | 1439 |
| quantifier_before_resource_or_half | 1001 | 29 | 1003 | 463 | 12 | 817 | 1248 | 156 |
| length_cap_exceeded | 1086 | 16 | 1084 | 0 | 0 | 394 | 1167 | 1505 |
| numbers_digits_or_units | 446 | 251 | 488 | 202 | 37 | 385 | 419 | 172 |
| personal_pronoun | 180 | 126 | 175 | 117 | 76 | 149 | 149 | 346 |
| band_banned_vocabulary | 77 | 143 | 104 | 39 | 35 | 80 | 127 | 155 |
| draft_animal_species | 103 | 0 | 79 | 41 | 0 | 81 | 49 | 3 |
| choice_parroting | 47 | 28 | 37 | 22 | 10 | 35 | 41 | 47 |
| death_words | 22 | 44 | 21 | 10 | 17 | 21 | 39 | 77 |
| mid_sentence_capital | 3 | 9 | 9 | 4 | 3 | 7 | 11 | 48 |
| invalid_punctuation | 5 | 3 | 9 | 5 | 1 | 6 | 38 | 143 |
| bad JSON | 18 | 1 | 23 | 3 | 0 | 8 | 7 | 35 |
| timeouts | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## All-rules counts (lines that break the rule at all; a line counts once per rule)

| rule | s2 | rulings | modelcard | cand-modelcard | combo | briefstop | fp16 | positive |
|---|---|---|---|---|---|---|---|---|
| unauthorised_resource_noun | 1915 | 1052 | 1935 | 866 | 357 | 1546 | 2695 | 2242 |
| quantifier_before_resource_or_half | 1156 | 30 | 1176 | 464 | 12 | 884 | 1520 | 223 |
| length_cap_exceeded | 1087 | 16 | 1084 | 0 | 0 | 394 | 1172 | 1530 |
| numbers_digits_or_units | 596 | 255 | 657 | 226 | 38 | 459 | 646 | 288 |
| personal_pronoun | 241 | 161 | 243 | 151 | 94 | 198 | 335 | 701 |
| band_banned_vocabulary | 199 | 186 | 232 | 100 | 53 | 177 | 371 | 470 |
| draft_animal_species | 135 | 1609 | 129 | 57 | 1608 | 104 | 103 | 6 |
| choice_parroting | 110 | 36 | 97 | 62 | 13 | 89 | 157 | 225 |
| death_words | 39 | 48 | 32 | 11 | 17 | 34 | 82 | 106 |
| mid_sentence_capital | 7 | 9 | 13 | 5 | 3 | 10 | 18 | 82 |
| invalid_punctuation | 5 | 3 | 9 | 5 | 1 | 6 | 38 | 143 |
| lines checked | 6462 | 6479 | 6457 | 6477 | 6480 | 6472 | 6473 | 6445 |
| lines breaking more than one rule | 1583 | 344 | 1616 | 567 | 98 | 1108 | 2127 | 1522 |
| coin under the unit rule | 0 | 0 | 3 | 0 | 0 | 0 | 1 | 2 |

## Attempts per line, arm cand-modelcard

| calls the line took | lines | of those, accepted |
|---|---|---|
| 1 | 3439 (53.1%) | 3439 |
| 2 | 1183 (18.3%) | 1183 |
| 3 | 1858 (28.7%) | 537 |

Mean calls per line: 1.76.

## Attempts per line, arm combo

| calls the line took | lines | of those, accepted |
|---|---|---|
| 1 | 4800 (74.1%) | 4800 |
| 2 | 848 (13.1%) | 848 |
| 3 | 832 (12.8%) | 305 |

Mean calls per line: 1.39.
