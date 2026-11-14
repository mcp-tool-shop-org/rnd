## Both rates, paired by turn against the baseline

| run | lines | calls per line | pass the rules | good lines (pass and say what happened) | paired difference, pass (points) | 95% interval | paired difference, good (points) | 95% interval | turn latency p50 / p95 ms |
|---|---|---|---|---|---|---|---|---|---|
| ship | 720 | 1.52 | 80.6% | 80.6% |  |  |  |  | 174 / 317 |
| haiku | 720 | 1.61 | 81.8% | 81.8% | +1.2 | -2.7 to +5.2 | +1.2 | -2.7 to +5.2 | 3076 / 6984 |
| sonnet | 720 | 1.60 | 81.5% | 81.5% | +1.0 | -3.3 to +5.2 | +1.0 | -3.3 to +5.2 | 5546 / 14067 |

## Does the outcome line carry the turn's main fact?

Of the accepted outcome lines on turns where a main fact is required (an ending before a death before an arrival). The second figure in each cell is out of all outcome lines asked for on those turns, fallbacks included.

| run | the journey ended | a traveller died | the party arrived |
|---|---|---|---|
| ship | 14 of 14 (100.0%); 100.0% of 14 asked | 24 of 24 (100.0%); 96.0% of 25 asked | 28 of 28 (100.0%); 65.1% of 43 asked |
| haiku | 9 of 9 (100.0%); 64.3% of 14 asked | 23 of 23 (100.0%); 92.0% of 25 asked | 33 of 33 (100.0%); 76.7% of 43 asked |
| sonnet | 12 of 12 (100.0%); 85.7% of 14 asked | 25 of 25 (100.0%); 100.0% of 25 asked | 37 of 37 (100.0%); 86.0% of 43 asked |

## What the accepted lines still do

| run | accepted lines | say a supply is gone that is not, or lost that was gained | open with the event's text | outcome repeats the previous opening (two words) | mention the oxen | unique-opening share (three words) |
|---|---|---|---|---|---|---|
| ship | 580 | 0 | 0 | 0 | 20.0% | 0.138 |
| haiku | 589 | 0 | 0 | 0 | 38.5% | 0.280 |
| sonnet | 587 | 0 | 0 | 0 | 6.0% | 0.179 |

## Oxen share of accepted Fireside lines, by length

| run | brief | standard | rich |
|---|---|---|---|
| ship | 20.0% |  |  |
| haiku | 38.5% |  |  |
| sonnet | 6.0% |  |  |

## Why lines fell back (the first rule a rejected line broke)

| reason | ship | haiku | sonnet |
|---|---|---|---|
| choice_parroting | 23 | 55 | 50 |
| length_cap_exceeded | 0 | 25 | 33 |
| unauthorised_resource_noun | 23 | 11 | 19 |
| repeated_opening | 21 | 14 | 16 |
| event_text_copied | 47 | 3 | 0 |
| numbers_digits_or_units | 8 | 11 | 10 |
| personal_pronoun | 13 | 2 | 0 |
| mid_sentence_capital | 1 | 7 | 4 |
| band_banned_vocabulary | 2 | 1 | 1 |
| death_words | 2 | 0 | 0 |
| death_not_conveyed | 0 | 1 | 0 |
| ending_not_conveyed | 0 | 1 | 0 |

## Accepted lines that break a says-what-happened rule

| rule | ship | haiku | sonnet |
|---|---|---|---|

## Rule-pass and good-line rate per cell

| run | Chronicler brief | Chronicler standard | Chronicler rich | Fireside brief | Fireside standard | Fireside rich | Lantern-Bearer brief | Lantern-Bearer standard | Lantern-Bearer rich |
|---|---|---|---|---|---|---|---|---|---|
| ship | not run | not run | not run | 80.6% / 80.6% | not run | not run | not run | not run | not run |
| haiku | not run | not run | not run | 81.8% / 81.8% | not run | not run | not run | not run | not run |
| sonnet | not run | not run | not run | 81.5% / 81.5% | not run | not run | not run | not run | not run |
