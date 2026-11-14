## Both rates, paired by turn against the baseline

| run | lines | calls per line | pass the rules | good lines (pass and say what happened) | paired difference, pass (points) | 95% interval | paired difference, good (points) | 95% interval | turn latency p50 / p95 ms |
|---|---|---|---|---|---|---|---|---|---|
| ship | 2160 | 1.54 | 84.1% | 84.1% |  |  |  |  | 391 / 728 |
| haiku | 2160 | 1.70 | 76.2% | 76.2% | -7.9 | -11.4 to -4.4 | -7.9 | -11.4 to -4.4 | 4632 / 9827 |
| opus | 2160 | 1.59 | 78.8% | 78.8% | -5.3 | -8.6 to -2.1 | -5.3 | -8.6 to -2.1 | 7550 / 16032 |
| fable | 2160 | 1.49 | 80.7% | 80.7% | -3.4 | -6.3 to -0.4 | -3.4 | -6.3 to -0.4 | 3469 / 9444 |

## Does the outcome line carry the turn's main fact?

Of the accepted outcome lines on turns where a main fact is required (an ending before a death before an arrival). The second figure in each cell is out of all outcome lines asked for on those turns, fallbacks included.

| run | the journey ended | a traveller died | the party arrived |
|---|---|---|---|
| ship | 36 of 36 (100.0%); 85.7% of 42 asked | 63 of 63 (100.0%); 84.0% of 75 asked | 87 of 87 (100.0%); 67.4% of 129 asked |
| haiku | 38 of 38 (100.0%); 90.5% of 42 asked | 65 of 65 (100.0%); 86.7% of 75 asked | 98 of 98 (100.0%); 76.0% of 129 asked |
| opus | 33 of 33 (100.0%); 78.6% of 42 asked | 70 of 70 (100.0%); 93.3% of 75 asked | 101 of 101 (100.0%); 78.3% of 129 asked |
| fable | 24 of 24 (100.0%); 57.1% of 42 asked | 68 of 68 (100.0%); 90.7% of 75 asked | 87 of 87 (100.0%); 67.4% of 129 asked |

## What the accepted lines still do

| run | accepted lines | say a supply is gone that is not, or lost that was gained | open with the event's text | outcome repeats the previous opening (two words) | mention the oxen | unique-opening share (three words) |
|---|---|---|---|---|---|---|
| ship | 1817 | 0 | 0 | 0 | 17.7% | 0.171 |
| haiku | 1647 | 0 | 0 | 0 | 30.5% | 0.158 |
| opus | 1702 | 0 | 0 | 0 | 13.0% | 0.222 |
| fable | 1744 | 0 | 0 | 0 | 12.6% | 0.220 |

## Oxen share of accepted Fireside lines, by length

| run | brief | standard | rich |
|---|---|---|---|
| ship |  | 54.4% |  |
| haiku |  | 86.3% |  |
| opus |  | 38.7% |  |
| fable |  | 37.0% |  |

## Why lines fell back (the first rule a rejected line broke)

| reason | ship | haiku | opus | fable |
|---|---|---|---|---|
| choice_parroting | 7 | 182 | 219 | 197 |
| unauthorised_resource_noun | 138 | 115 | 116 | 75 |
| repeated_opening | 42 | 35 | 20 | 52 |
| numbers_digits_or_units | 20 | 37 | 36 | 37 |
| event_text_copied | 65 | 20 | 8 | 17 |
| band_banned_vocabulary | 8 | 7 | 30 | 32 |
| personal_pronoun | 13 | 39 | 3 | 0 |
| bad_slot_json | 0 | 52 | 1 | 0 |
| supply_state_contradiction | 28 | 2 | 4 | 1 |
| mid_sentence_capital | 2 | 16 | 3 | 1 |
| draft_animal_species | 0 | 2 | 13 | 2 |
| arrival_not_conveyed | 13 | 0 | 0 | 0 |
| quantifier_before_resource_or_half | 1 | 2 | 4 | 2 |
| death_words | 2 | 3 | 1 | 0 |
| ending_not_conveyed | 4 | 0 | 0 | 0 |
| action_with_no_one_left | 0 | 1 | 0 | 0 |

## Accepted lines that break a says-what-happened rule

| rule | ship | haiku | opus | fable |
|---|---|---|---|---|

## Rule-pass and good-line rate per cell

| run | Chronicler brief | Chronicler standard | Chronicler rich | Fireside brief | Fireside standard | Fireside rich | Lantern-Bearer brief | Lantern-Bearer standard | Lantern-Bearer rich |
|---|---|---|---|---|---|---|---|---|---|
| ship | not run | 80.1% / 80.1% | not run | not run | 81.9% / 81.9% | not run | not run | 90.3% / 90.3% | not run |
| haiku | not run | 71.1% / 71.1% | not run | not run | 81.0% / 81.0% | not run | not run | 76.7% / 76.7% | not run |
| opus | not run | 76.8% / 76.8% | not run | not run | 79.3% / 79.3% | not run | not run | 80.3% / 80.3% | not run |
| fable | not run | 81.0% / 81.0% | not run | not run | 82.2% / 82.2% | not run | not run | 79.0% / 79.0% | not run |
