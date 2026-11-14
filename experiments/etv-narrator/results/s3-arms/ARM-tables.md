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
