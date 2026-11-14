## Both rates, paired by turn against the baseline

| run | lines | calls per line | pass the rules | good lines (pass and say what happened) | paired difference, pass (points) | 95% interval | paired difference, good (points) | 95% interval | turn latency p50 / p95 ms |
|---|---|---|---|---|---|---|---|---|---|
| ship | 684 | 1.57 | 83.8% | 83.8% |  |  |  |  | 400 / 735 |
| haiku | 684 | 1.65 | 77.9% | 77.9% | -5.8 | -12.2 to +0.5 | -5.8 | -12.2 to +0.5 | 4335 / 9567 |
| opus | 684 | 1.56 | 80.8% | 80.8% | -2.9 | -9.0 to +3.1 | -2.9 | -9.0 to +3.1 | 7261 / 16095 |

## Does the outcome line carry the turn's main fact?

Of the accepted outcome lines on turns where a main fact is required (an ending before a death before an arrival). The second figure in each cell is out of all outcome lines asked for on those turns, fallbacks included.

| run | the journey ended | a traveller died | the party arrived |
|---|---|---|---|
| ship | 20 of 20 (100.0%); 83.3% of 24 asked | 31 of 31 (100.0%); 86.1% of 36 asked | 28 of 28 (100.0%); 71.8% of 39 asked |
| haiku | 20 of 20 (100.0%); 83.3% of 24 asked | 34 of 34 (100.0%); 94.4% of 36 asked | 31 of 31 (100.0%); 79.5% of 39 asked |
| opus | 20 of 20 (100.0%); 83.3% of 24 asked | 35 of 35 (100.0%); 97.2% of 36 asked | 34 of 34 (100.0%); 87.2% of 39 asked |

## What the accepted lines still do

| run | accepted lines | say a supply is gone that is not, or lost that was gained | open with the event's text | outcome repeats the previous opening (two words) | mention the oxen | unique-opening share (three words) |
|---|---|---|---|---|---|---|
| ship | 573 | 0 | 0 | 0 | 15.9% | 0.264 |
| haiku | 533 | 0 | 0 | 0 | 30.4% | 0.242 |
| opus | 553 | 0 | 0 | 0 | 12.3% | 0.291 |

## Oxen share of accepted Fireside lines, by length

| run | brief | standard | rich |
|---|---|---|---|
| ship |  | 51.1% |  |
| haiku |  | 86.2% |  |
| opus |  | 36.6% |  |

## Why lines fell back (the first rule a rejected line broke)

| reason | ship | haiku | opus |
|---|---|---|---|
| unauthorised_resource_noun | 52 | 34 | 32 |
| choice_parroting | 1 | 43 | 55 |
| repeated_opening | 18 | 16 | 8 |
| numbers_digits_or_units | 3 | 13 | 12 |
| event_text_copied | 17 | 5 | 3 |
| band_banned_vocabulary | 2 | 4 | 15 |
| bad_slot_json | 0 | 18 | 0 |
| supply_state_contradiction | 8 | 1 | 2 |
| personal_pronoun | 1 | 9 | 0 |
| mid_sentence_capital | 0 | 7 | 2 |
| arrival_not_conveyed | 5 | 0 | 0 |
| quantifier_before_resource_or_half | 1 | 1 | 1 |
| ending_not_conveyed | 2 | 0 | 0 |
| death_words | 1 | 0 | 1 |

## Accepted lines that break a says-what-happened rule

| rule | ship | haiku | opus |
|---|---|---|---|

## Rule-pass and good-line rate per cell

| run | Chronicler brief | Chronicler standard | Chronicler rich | Fireside brief | Fireside standard | Fireside rich | Lantern-Bearer brief | Lantern-Bearer standard | Lantern-Bearer rich |
|---|---|---|---|---|---|---|---|---|---|
| ship | not run | 80.3% / 80.3% | not run | not run | 78.1% / 78.1% | not run | not run | 93.0% / 93.0% | not run |
| haiku | not run | 72.4% / 72.4% | not run | not run | 82.5% / 82.5% | not run | not run | 78.9% / 78.9% | not run |
| opus | not run | 79.4% / 79.4% | not run | not run | 81.6% / 81.6% | not run | not run | 81.6% / 81.6% | not run |
