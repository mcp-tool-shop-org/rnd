## Per arm

| arm | cells done | calls made | accepted | fallback | fallback rate (slots) | turns with a fallback | rule rejects | bad JSON | timeouts | transport/http |
|---|---|---|---|---|---|---|---|---|---|---|
| plain | 9 of 9 | 6480 | 2496 | 3984 | 61.5% | 2399 of 3240 (74.0%) | 3814 | 170 | 0 | 0 |
| cited | 9 of 9 | 6480 | 2655 | 3825 | 59.0% | 2340 of 3240 (72.2%) | 3759 | 66 | 0 | 0 |
| text | 9 of 9 | 6480 | 2457 | 4023 | 62.1% | 2541 of 3240 (78.4%) | 4023 | 0 | 0 | 0 |

Calls made in all: 19440.

## Reason codes per arm (rule rejects; the checker stops at the first rule a line breaks)

| reason code | plain | cited | text |
|---|---|---|---|
| length_cap_exceeded | 2001 | 1617 | 1016 |
| numbers_digits_or_units | 774 | 980 | 910 |
| unauthorised_resource_noun | 449 | 504 | 647 |
| invalid_punctuation | 215 | 142 | 897 |
| quantifier_before_resource_or_half | 174 | 266 | 329 |
| band_banned_vocabulary | 137 | 143 | 126 |
| personal_pronoun | 24 | 33 | 40 |
| mid_sentence_capital | 12 | 37 | 19 |
| death_words | 16 | 19 | 18 |
| choice_parroting | 7 | 17 | 15 |
| draft_animal_species | 5 | 1 | 6 |

## Per cell: fallback rate by slot (accepted of 720), p50 / p95 latency in ms

| arm | profile | brief | standard | rich |
|---|---|---|---|---|
| plain | chronicler | 91.1% (64), 141 / 212 | 31.1% (496), 121 / 176 | 98.8% (9), 268 / 415 |
| plain | fireside | 37.8% (448), 138 / 208 | 44.7% (398), 188 / 248 | 73.9% (188), 279 / 423 |
| plain | lantern-bearer | 42.5% (414), 136 / 197 | 48.8% (369), 176 / 238 | 84.7% (110), 310 / 434 |
| cited | chronicler | 73.6% (190), 290 / 414 | 44.9% (397), 299 / 395 | 94.0% (43), 412 / 537 |
| cited | fireside | 40.0% (432), 281 / 374 | 51.7% (348), 351 / 447 | 64.4% (256), 418 / 525 |
| cited | lantern-bearer | 30.0% (504), 306 / 415 | 56.0% (317), 370 / 463 | 76.7% (168), 462 / 582 |
| text | chronicler | 98.6% (10), 169 / 405 | 46.1% (388), 111 / 172 | 63.3% (264), 138 / 200 |
| text | fireside | 57.6% (305), 135 / 350 | 53.6% (334), 163 / 220 | 66.4% (242), 224 / 296 |
| text | lantern-bearer | 43.6% (406), 115 / 390 | 56.5% (313), 165 / 227 | 72.9% (195), 237 / 305 |

## Scene call against outcome call (fallback rate)

| arm | scene | outcome |
|---|---|---|
| plain | 60.0% | 63.0% |
| cited | 56.0% | 62.1% |
| text | 59.0% | 65.1% |

## The two things the run record must say, measured

Level-1 turns have no weirdness allowance of their own (by ruling), and the Uncanny Bearer's voice asks for weirdness while no-allowance turns carry a band-0 ceiling. Rejections for weirdness words on those turns are that collision, not a model fault.

| arm | profile | allowance | slots | weirdness-word rejects | all rule rejects |
|---|---|---|---|---|---|
| plain | chronicler | hint | 294 | 0 | 214 |
| plain | chronicler | none | 1524 | 4 | 1108 |
| plain | chronicler | strong | 342 | 0 | 246 |
| plain | fireside | hint | 294 | 0 | 123 |
| plain | fireside | none | 1524 | 82 | 815 |
| plain | fireside | strong | 342 | 0 | 138 |
| plain | lantern-bearer | hint | 294 | 0 | 167 |
| plain | lantern-bearer | none | 1524 | 51 | 820 |
| plain | lantern-bearer | strong | 342 | 0 | 183 |
| cited | chronicler | hint | 294 | 0 | 197 |
| cited | chronicler | none | 1524 | 5 | 1117 |
| cited | chronicler | strong | 342 | 0 | 202 |
| cited | fireside | hint | 294 | 0 | 122 |
| cited | fireside | none | 1524 | 92 | 858 |
| cited | fireside | strong | 342 | 0 | 133 |
| cited | lantern-bearer | hint | 294 | 0 | 157 |
| cited | lantern-bearer | none | 1524 | 46 | 824 |
| cited | lantern-bearer | strong | 342 | 0 | 149 |
| text | chronicler | hint | 294 | 0 | 218 |
| text | chronicler | none | 1524 | 6 | 1028 |
| text | chronicler | strong | 342 | 0 | 252 |
| text | fireside | hint | 294 | 0 | 159 |
| text | fireside | none | 1524 | 80 | 962 |
| text | fireside | strong | 342 | 0 | 158 |
| text | lantern-bearer | hint | 294 | 0 | 170 |
| text | lantern-bearer | none | 1524 | 40 | 890 |
| text | lantern-bearer | strong | 342 | 0 | 186 |

## Fallback rate by weirdness level of the run (all profiles and lengths)

| arm | level 0 | level 1 | level 2 | level 3 |
|---|---|---|---|---|
| plain | 63.6% | 63.3% | 58.8% | 60.2% |
| cited | 64.3% | 63.1% | 56.0% | 52.7% |
| text | 63.1% | 64.5% | 60.4% | 60.3% |

## Death turns (where a death may be stated) against the rest

| arm | death-allowed turns: fallback | death-word rejects there | other turns: fallback | death-word rejects there |
|---|---|---|---|---|
| plain | 61.1% of 630 | 2 | 61.5% of 5850 | 14 |
| cited | 62.5% of 630 | 0 | 58.6% of 5850 | 19 |
| text | 62.4% of 630 | 0 | 62.1% of 5850 | 18 |

## VRAM

83 readings, one a minute. First 2065 MiB at 2026-11-13 05:15:20; peak 10144 MiB at 2026-11-13 05:17:20; last 5333 MiB at 2026-11-13 06:37:46.
