Cells compared: 9 of 9. Slots per run: 6480 and 6480.

## Overall

| | session 1 | re-check |
|---|---|---|
| calls made | 6480 | 6480 |
| accepted | 2496 | 2881 |
| fallback | 3984 | 3599 |
| fallback rate (slots) | 61.5% | 55.5% |
| turns with at least one fallback | 2399 of 3240 (74.0%) | 2388 of 3240 (73.7%) |

## Per cell: fallback rate by slot (accepted of 720)

| profile | length | session 1 | re-check | change in points |
|---|---|---|---|---|
| chronicler | brief | 91.1% (64) | 46.8% (383) | -44.3 |
| chronicler | standard | 31.1% (496) | 49.6% (363) | +18.5 |
| chronicler | rich | 98.8% (9) | 54.7% (326) | -44.0 |
| fireside | brief | 37.8% (448) | 72.5% (198) | +34.7 |
| fireside | standard | 44.7% (398) | 65.0% (252) | +20.3 |
| fireside | rich | 73.9% (188) | 56.2% (315) | -17.6 |
| lantern-bearer | brief | 42.5% (414) | 46.8% (383) | +4.3 |
| lantern-bearer | standard | 48.8% (369) | 57.1% (309) | +8.3 |
| lantern-bearer | rich | 84.7% (110) | 51.1% (352) | -33.6 |

## Reject codes, before and after (first rule a line broke)

| outcome | session 1 | re-check |
|---|---|---|
| accepted | 2496 | 2881 |
| length_cap_exceeded | 2001 | 1086 |
| numbers_digits_or_units | 774 | 446 |
| quantifier_before_resource_or_half | 174 | 1001 |
| unauthorised_resource_noun | 449 | 611 |
| invalid_punctuation | 215 | 5 |
| band_banned_vocabulary | 137 | 77 |
| personal_pronoun | 24 | 180 |
| bad_slot_json | 170 | 18 |
| draft_animal_species | 5 | 103 |
| choice_parroting | 7 | 47 |
| death_words | 16 | 22 |
| mid_sentence_capital | 12 | 3 |

## Paired by turn (the turn is the unit)

Each of the 360 turns was asked 18 times in each run (9 cells x 2 calls). Per turn: the share of its 18 lines accepted. The difference is re-check minus session 1, with a 95% interval from the 360 paired differences (normal approximation).

| scope | turns | mean pass rate, session 1 | mean pass rate, re-check | paired difference | 95% interval |
|---|---|---|---|---|---|
| all cells | 360 | 38.5% | 44.5% | +5.9 points | +3.3 to +8.6 |
| brief (3 profiles) | 360 | 42.9% | 44.6% | +1.8 points | -2.0 to +5.5 |
| standard (3 profiles) | 360 | 58.5% | 42.8% | -15.7 points | -19.4 to -11.9 |
| rich (3 profiles) | 360 | 14.2% | 46.0% | +31.8 points | +29.0 to +34.5 |
| chronicler (3 lengths) | 360 | 26.3% | 49.6% | +23.3 points | +19.9 to +26.6 |
| fireside (3 lengths) | 360 | 47.9% | 35.4% | -12.5 points | -16.0 to -8.9 |
| lantern-bearer (3 lengths) | 360 | 41.3% | 48.3% | +7.0 points | +3.2 to +10.8 |

## Unit-rule rejects in the re-check

`coin` or `coins` rejected under the unit rule: **0**.

| detail | count |
|---|---|
| unit word 'foot' after quantity word 'one' | 141 |
| banned number word 'two' | 96 |
| unit word 'step' after quantity word 'one' | 87 |
| banned number word 'three' | 36 |
| unit word 'feet' after quantity word 'both' | 30 |
| unit word 'steps' after quantity word 'one' | 16 |
| unit word 'turns' after quantity word 'one' | 9 |
| banned number word 'twice' | 8 |
| unit word 'ration' after quantity word 'one' | 5 |
| unit word 'step' after quantity word 'single' | 4 |
| banned number word 'zero' | 3 |
| unit word 'mile' after quantity word 'one' | 3 |
| unit word 'yard' after quantity word 'one' | 3 |
| unit word 'rations' after quantity word 'both' | 1 |
| unit word 'day' after quantity word 'one' | 1 |

## Punctuation rejects by character

| character | session 1 | re-check |
|---|---|---|
| U+2019 | 176 | 0 |
| disallowed punctuation or missing terminal period | 30 | 4 |
| U+2014 | 8 | 1 |
| U+201D | 1 | 0 |

## Bad JSON

| length | session 1 | re-check |
|---|---|---|
| brief | 0 | 10 |
| standard | 0 | 7 |
| rich | 170 | 1 |

## Latency in ms

| | session 1 p50 | session 1 p95 | re-check p50 | re-check p95 |
|---|---|---|---|---|
| per call, all lengths | 179 | 384 | 243 | 335 |
| per turn (both calls), all lengths | 358 | 720 | 491 | 632 |
| per call, brief | 138 | 207 | 172 | 285 |
| per turn (both calls), brief | 281 | 380 | 355 | 528 |
| per call, standard | 165 | 235 | 240 | 308 |
| per turn (both calls), standard | 331 | 444 | 482 | 579 |
| per call, rich | 284 | 430 | 287 | 353 |
| per turn (both calls), rich | 573 | 804 | 578 | 661 |

## Repeated openings in the re-check (first three words of accepted lines)

| profile | accepted lines | distinct openings | most common opening | its count |
|---|---|---|---|---|
| chronicler | 1072 | 132 | mud grips the | 166 |
| fireside | 765 | 172 | smoke curls from | 57 |
| lantern-bearer | 1044 | 212 | mud pools stretch | 201 |

## VRAM

28 readings, one a minute. First 2454 MiB at 2026-11-13 07:50:51; peak 5699 MiB at 2026-11-13 08:04:56; last 5575 MiB at 2026-11-13 08:18:00.
