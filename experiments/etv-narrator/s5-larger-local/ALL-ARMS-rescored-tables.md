## Both rates, paired by turn against the baseline

| run | lines | calls per line | pass the rules | good lines (pass and say what happened) | paired difference, pass (points) | 95% interval | paired difference, good (points) | 95% interval | turn latency p50 / p95 ms |
|---|---|---|---|---|---|---|---|---|---|
| ship | 6480 | 1.55 | 85.7% | 85.7% |  |  |  |  | 359 / 959 |
| qwen3-8b | 6480 | 1.58 | 86.1% | 86.1% | +0.4 | -1.4 to +2.1 | +0.4 | -1.4 to +2.1 | 507 / 1288 |
| qwen3-14b | 6480 | 1.81 | 74.0% | 74.0% | -11.8 | -13.9 to -9.7 | -11.8 | -13.9 to -9.7 | 1226 / 2835 |
| qwen3-5-4b | 6480 | 1.71 | 83.9% | 83.9% | -1.8 | -3.4 to -0.2 | -1.8 | -3.4 to -0.2 | 855 / 2127 |
| qwen3-5-9b | 6480 | 1.86 | 75.5% | 75.5% | -10.3 | -11.9 to -8.6 | -10.3 | -11.9 to -8.6 | 1315 / 2762 |

## Does the outcome line carry the turn's main fact?

Of the accepted outcome lines on turns where a main fact is required (an ending before a death before an arrival). The second figure in each cell is out of all outcome lines asked for on those turns, fallbacks included.

| run | the journey ended | a traveller died | the party arrived |
|---|---|---|---|
| ship | 114 of 114 (100.0%); 90.5% of 126 asked | 211 of 211 (100.0%); 93.8% of 225 asked | 309 of 309 (100.0%); 79.8% of 387 asked |
| qwen3-8b | 113 of 113 (100.0%); 89.7% of 126 asked | 202 of 202 (100.0%); 89.8% of 225 asked | 300 of 300 (100.0%); 77.5% of 387 asked |
| qwen3-14b | 112 of 112 (100.0%); 88.9% of 126 asked | 190 of 190 (100.0%); 84.4% of 225 asked | 239 of 239 (100.0%); 61.8% of 387 asked |
| qwen3-5-4b | 123 of 123 (100.0%); 97.6% of 126 asked | 86 of 86 (100.0%); 38.2% of 225 asked | 313 of 313 (100.0%); 80.9% of 387 asked |
| qwen3-5-9b | 112 of 112 (100.0%); 88.9% of 126 asked | 170 of 170 (100.0%); 75.6% of 225 asked | 290 of 290 (100.0%); 74.9% of 387 asked |

## What the accepted lines still do

| run | accepted lines | say a supply is gone that is not, or lost that was gained | open with the event's text | outcome repeats the previous opening (two words) | mention the oxen | unique-opening share (three words) |
|---|---|---|---|---|---|---|
| ship | 5555 | 0 | 0 | 152 | 15.4% | 0.139 |
| qwen3-8b | 5579 | 0 | 0 | 186 | 17.9% | 0.122 |
| qwen3-14b | 4792 | 0 | 0 | 197 | 10.9% | 0.171 |
| qwen3-5-4b | 5439 | 0 | 0 | 106 | 25.6% | 0.226 |
| qwen3-5-9b | 4890 | 0 | 0 | 44 | 18.1% | 0.255 |

## Oxen share of accepted Fireside lines, by length

| run | brief | standard | rich |
|---|---|---|---|
| ship | 18.9% | 54.5% | 69.9% |
| qwen3-8b | 36.5% | 57.2% | 70.2% |
| qwen3-14b | 8.6% | 32.9% | 57.0% |
| qwen3-5-4b | 70.1% | 82.0% | 78.1% |
| qwen3-5-9b | 28.7% | 62.2% | 67.9% |

## Why lines fell back (the first rule a rejected line broke)

| reason | ship | qwen3-8b | qwen3-14b | qwen3-5-4b | qwen3-5-9b |
|---|---|---|---|---|---|
| unauthorised_resource_noun | 386 | 185 | 374 | 333 | 713 |
| event_text_copied | 226 | 196 | 659 | 51 | 150 |
| personal_pronoun | 53 | 45 | 54 | 98 | 297 |
| band_banned_vocabulary | 36 | 45 | 258 | 96 | 75 |
| numbers_digits_or_units | 72 | 70 | 83 | 158 | 119 |
| invalid_punctuation | 3 | 247 | 27 | 24 | 1 |
| death_not_conveyed | 0 | 13 | 19 | 110 | 41 |
| death_words | 12 | 38 | 60 | 29 | 34 |
| choice_parroting | 16 | 16 | 2 | 82 | 57 |
| supply_state_contradiction | 64 | 11 | 15 | 12 | 21 |
| repeated_opening | 8 | 22 | 64 | 8 | 5 |
| mid_sentence_capital | 19 | 4 | 3 | 29 | 37 |
| arrival_not_conveyed | 13 | 0 | 59 | 1 | 10 |
| quantifier_before_resource_or_half | 9 | 2 | 7 | 7 | 28 |
| action_with_no_one_left | 0 | 7 | 0 | 2 | 2 |
| ending_not_conveyed | 8 | 0 | 2 | 0 | 0 |
| draft_animal_species | 0 | 0 | 1 | 1 | 0 |
| length_cap_exceeded | 0 | 0 | 1 | 0 | 0 |

## Accepted lines that break a says-what-happened rule

| rule | ship | qwen3-8b | qwen3-14b | qwen3-5-4b | qwen3-5-9b |
|---|---|---|---|---|---|

## Rule-pass and good-line rate per cell

| run | Chronicler brief | Chronicler standard | Chronicler rich | Fireside brief | Fireside standard | Fireside rich | Lantern-Bearer brief | Lantern-Bearer standard | Lantern-Bearer rich |
|---|---|---|---|---|---|---|---|---|---|
| ship | 89.0% / 89.0% | 81.7% / 81.7% | 81.5% / 81.5% | 85.1% / 85.1% | 84.9% / 84.9% | 81.2% / 81.2% | 90.1% / 90.1% | 91.7% / 91.7% | 86.2% / 86.2% |
| qwen3-8b | 92.2% / 92.2% | 85.3% / 85.3% | 79.3% / 79.3% | 91.0% / 91.0% | 82.4% / 82.4% | 83.3% / 83.3% | 92.5% / 92.5% | 88.1% / 88.1% | 80.8% / 80.8% |
| qwen3-14b | 79.9% / 79.9% | 71.2% / 71.2% | 63.5% / 63.5% | 82.8% / 82.8% | 76.0% / 76.0% | 70.4% / 70.4% | 82.6% / 82.6% | 70.3% / 70.3% | 68.9% / 68.9% |
| qwen3-5-4b | 89.0% / 89.0% | 87.4% / 87.4% | 80.0% / 80.0% | 92.8% / 92.8% | 85.6% / 85.6% | 75.0% / 75.0% | 88.2% / 88.2% | 84.0% / 84.0% | 73.5% / 73.5% |
| qwen3-5-9b | 89.3% / 89.3% | 68.5% / 68.5% | 60.4% / 60.4% | 90.1% / 90.1% | 77.5% / 77.5% | 71.8% / 71.8% | 86.7% / 86.7% | 70.6% / 70.6% | 64.3% / 64.3% |
