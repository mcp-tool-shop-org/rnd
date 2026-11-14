## Both rates, paired by turn against the baseline

| run | lines | calls per line | pass the rules | good lines (pass and say what happened) | paired difference, pass (points) | 95% interval | paired difference, good (points) | 95% interval | turn latency p50 / p95 ms |
|---|---|---|---|---|---|---|---|---|---|
| ship | 284 | 1.54 | 81.0% | 81.0% |  |  |  |  | 172 / 317 |
| haiku | 284 | 1.65 | 79.2% | 79.2% | -1.8 | -8.8 to +5.3 | -1.8 | -8.8 to +5.3 | 3100 / 7326 |
| sonnet | 284 | 1.60 | 82.4% | 82.4% | +1.4 | -5.6 to +8.4 | +1.4 | -5.6 to +8.4 | 6090 / 14744 |

## Does the outcome line carry the turn's main fact?

Of the accepted outcome lines on turns where a main fact is required (an ending before a death before an arrival). The second figure in each cell is out of all outcome lines asked for on those turns, fallbacks included.

| run | the journey ended | a traveller died | the party arrived |
|---|---|---|---|
| ship | 9 of 9 (100.0%); 100.0% of 9 asked | 14 of 14 (100.0%); 93.3% of 15 asked | 8 of 8 (100.0%); 57.1% of 14 asked |
| haiku | 7 of 7 (100.0%); 77.8% of 9 asked | 14 of 14 (100.0%); 93.3% of 15 asked | 10 of 10 (100.0%); 71.4% of 14 asked |
| sonnet | 7 of 7 (100.0%); 77.8% of 9 asked | 15 of 15 (100.0%); 100.0% of 15 asked | 12 of 12 (100.0%); 85.7% of 14 asked |

## What the accepted lines still do

| run | accepted lines | say a supply is gone that is not, or lost that was gained | open with the event's text | outcome repeats the previous opening (two words) | mention the oxen | unique-opening share (three words) |
|---|---|---|---|---|---|---|
| ship | 230 | 0 | 0 | 0 | 25.2% | 0.217 |
| haiku | 225 | 0 | 0 | 0 | 31.6% | 0.347 |
| sonnet | 234 | 0 | 0 | 0 | 6.0% | 0.269 |

## Oxen share of accepted Fireside lines, by length

| run | brief | standard | rich |
|---|---|---|---|
| ship | 25.2% |  |  |
| haiku | 31.6% |  |  |
| sonnet | 6.0% |  |  |

## Why lines fell back (the first rule a rejected line broke)

| reason | ship | haiku | sonnet |
|---|---|---|---|
| choice_parroting | 12 | 20 | 13 |
| repeated_opening | 8 | 9 | 9 |
| unauthorised_resource_noun | 9 | 4 | 10 |
| length_cap_exceeded | 0 | 11 | 10 |
| event_text_copied | 18 | 1 | 0 |
| numbers_digits_or_units | 4 | 6 | 6 |
| mid_sentence_capital | 0 | 5 | 1 |
| personal_pronoun | 1 | 2 | 0 |
| band_banned_vocabulary | 1 | 1 | 1 |
| death_words | 1 | 0 | 0 |

## Accepted lines that break a says-what-happened rule

| rule | ship | haiku | sonnet |
|---|---|---|---|

## Rule-pass and good-line rate per cell

| run | Chronicler brief | Chronicler standard | Chronicler rich | Fireside brief | Fireside standard | Fireside rich | Lantern-Bearer brief | Lantern-Bearer standard | Lantern-Bearer rich |
|---|---|---|---|---|---|---|---|---|---|
| ship | not run | not run | not run | 81.0% / 81.0% | not run | not run | not run | not run | not run |
| haiku | not run | not run | not run | 79.2% / 79.2% | not run | not run | not run | not run | not run |
| sonnet | not run | not run | not run | 82.4% / 82.4% | not run | not run | not run | not run | not run |
