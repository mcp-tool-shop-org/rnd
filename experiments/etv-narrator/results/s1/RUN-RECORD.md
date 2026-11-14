# Escape the Valley: fallback-rate run, session 1 (2026-11-13)

**Result in one line.** All three arms ran to the end (19,440 calls, no timeouts, no transport errors). The narrator's line was rejected on about 6 slots in 10 in every arm: plain 61.5%, cited 59.0%, text 62.1%. Most rejections are the rules and the prompt disagreeing with each other, not the model failing.

## What was run

- **Granted by** the Publisher, relayed by R&D, 2026-11-13: session 1, 120-minute wall, RTX 5090, local Ollama only.
- **Start** 2026-11-13 05:15:19 EST. **End of calls** 06:38:04 EST. **Wall used** 4,964 s (82 min 44 s) of 7,200 s. The wall was enforced by `timeout` against one deadline set at the start; it was not reached.
- **Model** `qwen3:4b-instruct-2507-q4_K_M` (Ollama digest 0edcdef34593…), endpoint `http://127.0.0.1:11434`.
- **Code** rust-2.0 at `b45cae47f0bf99d654a9563c72824a1240868fbe`, clean worktree, release build with `narrator-ollama`. The harness was not modified.
- **Turn set** v2, 360 turns, sha256 `518beeccde989abc20b08ada42b2b3d582755bd5c4bd0f39b05f31204323535e`, verified before the first call (by `sha256sum`, by `--check-only`, and by the harness on every cell).
- **Arms, in order:** plain, cited, text; shipped rule wording. 6,480 calls each (360 turns x 3 profiles x 3 lengths x 2 calls). No arm was shortened.
- **Per call:** timeout 10 s, `think: false`, temperature 0.15, `num_ctx` 2048, `num_predict` 110 (160 cited), derived seed.

## How it was run, and two things to know about the files

- **One process per cell.** The harness writes its rows only when it finishes, so a wall or a crash mid-arm would have lost the arm. Each of the 27 cells (arm x profile x length, 720 calls) was run as its own `narrator_measure --profiles P --lengths L` process, in the harness's own order. The calls are the same as one process per arm would make (the harness checks the model and warms up once per cell either way). Script: `run_s1.sh`. After every cell `cell_check.py` confirmed 360 rows, 720 calls made, and no error streak.
- **The request and seed in the rows were rebuilt, not captured.** The harness keeps the raw response, the candidate line, the verdict and the reason code for each slot, but not the request. `enrich_rows.rs` rebuilt each request with the harness's own code at the same commit and a transport that records and calls no model, and wrote `<cell>.rows.full.jsonl` with `request` and `seed` added to each slot. The original `<cell>.rows.jsonl` files are untouched. A later harness change should record the request itself.
- **One reason code per rejected line.** The checker stops at the first rule a line breaks, so the counts say which rule fired first, not every rule a line broke.

## Files (all in this folder, outside the repository)

- `<arm>-<profile>-<length>.report.json`: the harness's summary for the cell (no model text).
- `<arm>-<profile>-<length>.rows.jsonl`: one line per turn, both slots, raw model response in full.
- `<arm>-<profile>-<length>.rows.full.jsonl`: the same with the request and seed added.
- `run.log`, `vram.csv` (one reading a minute), `SUMMARY-tables.md`, `summarise.py`, `run_s1.sh`, `cell_check.py`, `enrich_rows.rs`.

## Andon

None fired. No timeouts, no transport or HTTP errors, no cell short of 720 calls. The harness turns the two-strike breaker off for measurement (every turn is asked for), so there was no breaker to trip.

## VRAM and the card

- Baseline before the run 2,065 MiB. Steady during the run 5.2 to 5.9 GB.
- **Peak 10,144 MiB**, one reading at 05:17:20, three seconds after the second cell started; the readings on either side are 5,562 and 5,790 MiB. Most likely the model briefly loaded twice as the new process warmed up. Far under the 30,000 MiB andon line and the 31,200 MiB ceiling.
- Model unloaded with `keep_alive: 0` at 06:38:04. At 06:38:25 the card read 2,098 MiB and Ollama listed no loaded model. **The card is free.**

## Two notes the record must carry, so rejections are not misread

1. **Level-1 turns have no weirdness allowance of their own.** By ruling, the engine gives `none`, `hint` or `strong`, and a run created at level 1 is `none`. The set's split is none 254, hint 49, strong 57 turns.
2. **The Uncanny Bearer's voice meets a band-0 ceiling on no-allowance turns.** Its voice rules ask it to let the weirdness breathe; on a no-allowance turn the shared rules cap it at band 0 and the checker rejects weird vocabulary. Those `band_banned_vocabulary` rejections are the two instructions colliding. The table below counts them: in the plain arm, 51 for the Uncanny Bearer and 82 for Fireside on no-allowance turns, and none at all on hint or strong turns.

## What the rejections are (plain arm, read from the rows)

- **Length, 2,001.** The cap counts sentences (Brief 1, Standard 1 to 2, Rich 2 to 3). The model writes several short sentences inside one array item, so the schema's item limit does not hold it. The Chronicler is told to write short declarative sentences and is then rejected for it: 91% fallback at Brief, 99% at Rich.
- **Numbers and units, 774.** The largest single word is `step` (264 rejections), then `two` (129), `foot` (48), `years` (42), `turn` (41), `coin` (37), `days`, `yard`, `rations` (34 each). `step`, `foot`, `turn` and `second` are being read as units in lines like "each step sinks"; that is the checker's unit list being too wide, not the model stating a measurement.
- **Resource nouns, 449.** Only 3 of these are a supply the situation text names. 36 are a noun from the event's own text. About 410 are either a noun the turn never mentioned (boots, gold, wool) or a permitted noun used after the first sentence (the "sentence 1 only" rule).
- **Punctuation, 215.** 176 are the typographic apostrophe (U+2019), which the checker does not treat as an apostrophe. 9 are an em dash, 6 a semicolon.
- **Bad JSON, 170, all in Rich cells.** Every one is an answer cut off by `num_predict` 110 after about half a second. None is a timeout; the 10 s limit was never approached (worst p95 was 582 ms).
- **Death words, 16.** Only 2 on the 35 turns where a death may be stated (both the gore word "blood"), 14 elsewhere. The death ruling works as intended.

The cited and text arms show the same pattern. The text arm has more punctuation rejections (897), as expected with no schema.

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
