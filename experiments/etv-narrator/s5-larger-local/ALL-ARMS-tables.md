## Both rates, paired by turn against the baseline

| run | lines | calls per line | pass the rules | good lines (pass and say what happened) | paired difference, pass (points) | 95% interval | paired difference, good (points) | 95% interval | turn latency p50 / p95 ms |
|---|---|---|---|---|---|---|---|---|---|
| ship | 6480 | 1.55 | 82.9% | 82.9% |  |  |  |  | 359 / 959 |
| qwen3-8b | 6480 | 1.58 | 82.2% | 82.2% | -0.7 | -2.8 to +1.3 | -0.7 | -2.8 to +1.3 | 507 / 1288 |
| qwen3-14b | 6480 | 1.81 | 70.9% | 70.9% | -12.1 | -14.5 to -9.7 | -12.1 | -14.5 to -9.7 | 1226 / 2835 |
| qwen3-5-4b | 6480 | 1.71 | 80.5% | 80.5% | -2.5 | -4.3 to -0.6 | -2.5 | -4.3 to -0.6 | 855 / 2127 |
| qwen3-5-9b | 6480 | 1.86 | 73.1% | 73.1% | -9.8 | -11.7 to -7.9 | -9.8 | -11.7 to -7.9 | 1315 / 2762 |

## Does the outcome line carry the turn's main fact?

Of the accepted outcome lines on turns where a main fact is required (an ending before a death before an arrival). The second figure in each cell is out of all outcome lines asked for on those turns, fallbacks included.

| run | the journey ended | a traveller died | the party arrived |
|---|---|---|---|
| ship | 114 of 114 (100.0%); 90.5% of 126 asked | 192 of 192 (100.0%); 85.3% of 225 asked | 278 of 278 (100.0%); 71.8% of 387 asked |
| qwen3-8b | 111 of 111 (100.0%); 88.1% of 126 asked | 184 of 184 (100.0%); 81.8% of 225 asked | 279 of 279 (100.0%); 72.1% of 387 asked |
| qwen3-14b | 104 of 104 (100.0%); 82.5% of 126 asked | 151 of 151 (100.0%); 67.1% of 225 asked | 221 of 221 (100.0%); 57.1% of 387 asked |
| qwen3-5-4b | 119 of 119 (100.0%); 94.4% of 126 asked | 86 of 86 (100.0%); 38.2% of 225 asked | 294 of 294 (100.0%); 76.0% of 387 asked |
| qwen3-5-9b | 111 of 111 (100.0%); 88.1% of 126 asked | 166 of 166 (100.0%); 73.8% of 225 asked | 287 of 287 (100.0%); 74.2% of 387 asked |

## What the accepted lines still do

| run | accepted lines | say a supply is gone that is not, or lost that was gained | open with the event's text | outcome repeats the previous opening (two words) | mention the oxen | unique-opening share (three words) |
|---|---|---|---|---|---|---|
| ship | 5374 | 0 | 0 | 0 | 15.4% | 0.140 |
| qwen3-8b | 5328 | 0 | 0 | 0 | 18.1% | 0.122 |
| qwen3-14b | 4592 | 0 | 0 | 0 | 10.6% | 0.175 |
| qwen3-5-4b | 5215 | 0 | 0 | 0 | 24.9% | 0.231 |
| qwen3-5-9b | 4739 | 0 | 0 | 0 | 17.9% | 0.254 |

## Oxen share of accepted Fireside lines, by length

| run | brief | standard | rich |
|---|---|---|---|
| ship | 20.0% | 54.4% | 69.3% |
| qwen3-8b | 37.3% | 56.1% | 70.2% |
| qwen3-14b | 8.8% | 32.0% | 56.8% |
| qwen3-5-4b | 68.1% | 82.3% | 78.4% |
| qwen3-5-9b | 29.2% | 61.7% | 68.2% |

## Why lines fell back (the first rule a rejected line broke)

| reason | ship | qwen3-8b | qwen3-14b | qwen3-5-4b | qwen3-5-9b |
|---|---|---|---|---|---|
| unauthorised_resource_noun | 386 | 185 | 374 | 333 | 713 |
| event_text_copied | 224 | 194 | 658 | 51 | 146 |
| repeated_opening | 142 | 204 | 258 | 96 | 43 |
| choice_parroting | 68 | 87 | 9 | 219 | 176 |
| personal_pronoun | 53 | 45 | 54 | 98 | 297 |
| band_banned_vocabulary | 36 | 45 | 258 | 96 | 75 |
| numbers_digits_or_units | 72 | 70 | 83 | 158 | 119 |
| invalid_punctuation | 3 | 247 | 27 | 24 | 1 |
| death_not_conveyed | 0 | 13 | 19 | 110 | 41 |
| death_words | 12 | 38 | 60 | 29 | 34 |
| supply_state_contradiction | 61 | 11 | 15 | 11 | 19 |
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
| ship | 87.4% / 87.4% | 80.1% / 80.1% | 79.9% / 79.9% | 80.6% / 80.6% | 81.9% / 81.9% | 77.9% / 77.9% | 85.6% / 85.6% | 90.3% / 90.3% | 82.8% / 82.8% |
| qwen3-8b | 87.1% / 87.1% | 82.1% / 82.1% | 74.9% / 74.9% | 86.4% / 86.4% | 79.7% / 79.7% | 81.0% / 81.0% | 88.3% / 88.3% | 84.0% / 84.0% | 76.5% / 76.5% |
| qwen3-14b | 76.1% / 76.1% | 68.1% / 68.1% | 61.3% / 61.3% | 80.3% / 80.3% | 71.7% / 71.7% | 66.0% / 66.0% | 79.6% / 79.6% | 68.6% / 68.6% | 66.2% / 66.2% |
| qwen3-5-4b | 86.2% / 86.2% | 83.9% / 83.9% | 77.6% / 77.6% | 86.2% / 86.2% | 81.5% / 81.5% | 70.0% / 70.0% | 85.7% / 85.7% | 81.8% / 81.8% | 71.2% / 71.2% |
| qwen3-5-9b | 87.9% / 87.9% | 66.1% / 66.1% | 56.2% / 56.2% | 88.1% / 88.1% | 73.9% / 73.9% | 68.6% / 68.6% | 84.7% / 84.7% | 68.8% / 68.8% | 63.9% / 63.9% |
