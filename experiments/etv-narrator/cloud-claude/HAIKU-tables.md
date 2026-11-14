## Both rates, paired by turn against the baseline

| run | lines | calls per line | pass the rules | good lines (pass and say what happened) | paired difference, pass (points) | 95% interval | paired difference, good (points) | 95% interval | turn latency p50 / p95 ms |
|---|---|---|---|---|---|---|---|---|---|
| ship | 6480 | 1.55 | 82.9% | 82.9% |  |  |  |  | 359 / 959 |
| haiku | 6480 | 1.70 | 76.7% | 76.7% | -6.3 | -8.9 to -3.6 | -6.3 | -8.9 to -3.6 | 4267 / 10701 |

## Does the outcome line carry the turn's main fact?

Of the accepted outcome lines on turns where a main fact is required (an ending before a death before an arrival). The second figure in each cell is out of all outcome lines asked for on those turns, fallbacks included.

| run | the journey ended | a traveller died | the party arrived |
|---|---|---|---|
| ship | 114 of 114 (100.0%); 90.5% of 126 asked | 192 of 192 (100.0%); 85.3% of 225 asked | 278 of 278 (100.0%); 71.8% of 387 asked |
| haiku | 110 of 110 (100.0%); 87.3% of 126 asked | 195 of 195 (100.0%); 86.7% of 225 asked | 285 of 285 (100.0%); 73.6% of 387 asked |

## What the accepted lines still do

| run | accepted lines | say a supply is gone that is not, or lost that was gained | open with the event's text | outcome repeats the previous opening (two words) | mention the oxen | unique-opening share (three words) |
|---|---|---|---|---|---|---|
| ship | 5374 | 0 | 0 | 0 | 15.4% | 0.140 |
| haiku | 4969 | 0 | 0 | 0 | 24.3% | 0.208 |

## Oxen share of accepted Fireside lines, by length

| run | brief | standard | rich |
|---|---|---|---|
| ship | 20.0% | 54.4% | 69.3% |
| haiku | 38.5% | 86.3% | 94.8% |

## Why lines fell back (the first rule a rejected line broke)

| reason | ship | haiku |
|---|---|---|
| unauthorised_resource_noun | 386 | 317 |
| choice_parroting | 68 | 482 |
| repeated_opening | 142 | 140 |
| event_text_copied | 224 | 46 |
| numbers_digits_or_units | 72 | 112 |
| bad_slot_json | 0 | 176 |
| personal_pronoun | 53 | 88 |
| mid_sentence_capital | 19 | 51 |
| supply_state_contradiction | 61 | 3 |
| band_banned_vocabulary | 36 | 15 |
| length_cap_exceeded | 0 | 34 |
| death_words | 12 | 11 |
| quantifier_before_resource_or_half | 9 | 14 |
| draft_animal_species | 0 | 15 |
| arrival_not_conveyed | 13 | 0 |
| ending_not_conveyed | 8 | 2 |
| death_not_conveyed | 0 | 4 |
| invalid_punctuation | 3 | 0 |
| action_with_no_one_left | 0 | 1 |

## Accepted lines that break a says-what-happened rule

| rule | ship | haiku |
|---|---|---|

## Rule-pass and good-line rate per cell

| run | Chronicler brief | Chronicler standard | Chronicler rich | Fireside brief | Fireside standard | Fireside rich | Lantern-Bearer brief | Lantern-Bearer standard | Lantern-Bearer rich |
|---|---|---|---|---|---|---|---|---|---|
| ship | 87.4% / 87.4% | 80.1% / 80.1% | 79.9% / 79.9% | 80.6% / 80.6% | 81.9% / 81.9% | 77.9% / 77.9% | 85.6% / 85.6% | 90.3% / 90.3% | 82.8% / 82.8% |
| haiku | 86.0% / 86.0% | 71.1% / 71.1% | 67.6% / 67.6% | 81.8% / 81.8% | 81.0% / 81.0% | 69.7% / 69.7% | 86.7% / 86.7% | 76.7% / 76.7% | 69.6% / 69.6% |
