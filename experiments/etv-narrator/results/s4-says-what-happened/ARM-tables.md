## Both rates, paired by turn against the baseline

| run | lines | calls per line | pass the rules | good lines (pass and say what happened) | paired difference, pass (points) | 95% interval | paired difference, good (points) | 95% interval | turn latency p50 / p95 ms |
|---|---|---|---|---|---|---|---|---|---|
| combo | 6480 | 1.39 | 91.9% | 78.1% |  |  |  |  | 344 / 912 |
| lead | 6480 | 1.39 | 91.5% | 86.7% | -0.3 | -1.4 to +0.7 | +8.6 | +6.7 to +10.5 | 383 / 911 |
| swh | 6480 | 1.57 | 83.2% | 83.2% | -8.7 | -10.3 to -7.1 | +5.1 | +2.9 to +7.3 | 433 / 972 |
| ship | 6480 | 1.55 | 82.9% | 82.9% | -8.9 | -10.6 to -7.3 | +4.9 | +2.5 to +7.2 | 359 / 959 |

## Does the outcome line carry the turn's main fact?

Of the accepted outcome lines on turns where a main fact is required (an ending before a death before an arrival). The second figure in each cell is out of all outcome lines asked for on those turns, fallbacks included.

| run | the journey ended | a traveller died | the party arrived |
|---|---|---|---|
| combo | 54 of 124 (43.5%); 42.9% of 126 asked | 26 of 221 (11.8%); 11.6% of 225 asked | 9 of 360 (2.5%); 2.3% of 387 asked |
| lead | 112 of 126 (88.9%); 88.9% of 126 asked | 223 of 223 (100.0%); 99.1% of 225 asked | 294 of 332 (88.6%); 76.0% of 387 asked |
| swh | 110 of 110 (100.0%); 87.3% of 126 asked | 181 of 181 (100.0%); 80.4% of 225 asked | 277 of 277 (100.0%); 71.6% of 387 asked |
| ship | 114 of 114 (100.0%); 90.5% of 126 asked | 192 of 192 (100.0%); 85.3% of 225 asked | 278 of 278 (100.0%); 71.8% of 387 asked |

## What the accepted lines still do

| run | accepted lines | say a supply is gone that is not, or lost that was gained | open with the event's text | outcome repeats the previous opening (two words) | mention the oxen | unique-opening share (three words) |
|---|---|---|---|---|---|---|
| combo | 5953 | 344 | 526 | 1327 | 26.1% | 0.134 |
| lead | 5931 | 262 | 264 | 154 | 17.3% | 0.156 |
| swh | 5390 | 0 | 0 | 0 | 16.7% | 0.160 |
| ship | 5374 | 0 | 0 | 0 | 15.4% | 0.140 |

## Oxen share of accepted Fireside lines, by length

| run | brief | standard | rich |
|---|---|---|---|
| combo | 52.6% | 81.4% | 92.5% |
| lead | 30.5% | 55.1% | 70.6% |
| swh | 32.1% | 54.9% | 69.5% |
| ship | 20.0% | 54.4% | 69.3% |

## Why lines fell back (the first rule a rejected line broke)

| reason | combo | lead | swh | ship |
|---|---|---|---|---|
| unauthorised_resource_noun | 336 | 351 | 415 | 386 |
| event_text_copied | 0 | 0 | 199 | 224 |
| repeated_opening | 0 | 0 | 125 | 142 |
| numbers_digits_or_units | 37 | 66 | 71 | 72 |
| personal_pronoun | 76 | 42 | 42 | 53 |
| supply_state_contradiction | 0 | 0 | 96 | 61 |
| band_banned_vocabulary | 35 | 29 | 38 | 36 |
| choice_parroting | 10 | 25 | 30 | 68 |
| mid_sentence_capital | 3 | 14 | 15 | 19 |
| death_words | 17 | 8 | 10 | 12 |
| quantifier_before_resource_or_half | 12 | 10 | 12 | 9 |
| arrival_not_conveyed | 0 | 0 | 22 | 13 |
| ending_not_conveyed | 0 | 0 | 10 | 8 |
| invalid_punctuation | 1 | 4 | 5 | 3 |

## Accepted lines that break a says-what-happened rule

| rule | combo | lead | swh | ship |
|---|---|---|---|---|
| supply_state_contradiction | 344 | 262 | 0 | 0 |
| arrival_not_conveyed | 351 | 38 | 0 | 0 |
| death_not_conveyed | 195 | 0 | 0 | 0 |
| ending_not_conveyed | 70 | 14 | 0 | 0 |
| action_with_no_one_left | 32 | 4 | 0 | 0 |

## Rule-pass and good-line rate per cell

| run | Chronicler brief | Chronicler standard | Chronicler rich | Fireside brief | Fireside standard | Fireside rich | Lantern-Bearer brief | Lantern-Bearer standard | Lantern-Bearer rich |
|---|---|---|---|---|---|---|---|---|---|
| combo | 89.6% / 70.6% | 87.6% / 66.9% | 84.0% / 67.4% | 97.1% / 85.8% | 97.2% / 85.8% | 92.1% / 79.7% | 96.8% / 85.8% | 94.3% / 83.8% | 88.1% / 76.8% |
| lead | 89.6% / 77.8% | 88.8% / 78.3% | 89.6% / 79.9% | 92.4% / 90.4% | 93.5% / 89.7% | 89.3% / 87.1% | 96.9% / 94.6% | 94.7% / 94.0% | 89.0% / 88.1% |
| swh | 81.4% / 81.4% | 80.1% / 80.1% | 79.9% / 79.9% | 81.8% / 81.8% | 81.4% / 81.4% | 77.9% / 77.9% | 93.3% / 93.3% | 90.3% / 90.3% | 82.5% / 82.5% |
| ship | 87.4% / 87.4% | 80.1% / 80.1% | 79.9% / 79.9% | 80.6% / 80.6% | 81.9% / 81.9% | 77.9% / 77.9% | 85.6% / 85.6% | 90.3% / 90.3% | 82.8% / 82.8% |
