# Escape the Valley: "says what happened" arms and weak-card latency, session 4 (2026-11-13)

**Result in one line.** With the truth rules, the outcome lead and the repetition rules on (the shipping shape), 82.9% of lines pass every rule and say what happened, against 78.1% for session 3's combination arm scored the same way (paired by turn: +4.9 points, 95% interval +2.5 to +7.2); no accepted line states a false supply fact, copies the event text or repeats the previous opening; and with part of the model off the GPU a turn takes 5 to 22 times longer.

## What was run

- **Granted** by the Publisher (relayed by R&D) on the merge of #90, 2026-11-13: three full arms and three latency arms, 3-hour wall.
- **Start** 2026-11-13 16:48:38 EST. **End of calls** 19:15:51 EST. **Wall used** 8,834 s (2 h 27 min) of 10,800 s. The deadline (19:48:38 EST) was enforced by `timeout` and was not reached.
- **Code** rust-2.0 at `a3fb14ef848843838c6eb4f327d3708973e5f58b` (the merge of #90), clean worktree, release build with `narrator-ollama`, harness unmodified.
- **Turn set** v2, 360 turns, sha256 `59a3e4f8870474d01b775a52071fae9a12629cec0f225606271e9d77f5f8ca46`, verified before the first call and by the harness on every cell.
- **Model** `qwen3:4b-instruct-2507-q4_K_M` (digest 0edcdef34593), local Ollama only (`http://127.0.0.1:11434`). One process per cell, rows flushed per turn.
- **Full arms:** the plain schema's 9 cells (3 voices x 3 lengths), 6,480 lines each.
- **Latency arms:** the shipping shape on Fireside at each length, with `num_gpu` set so that fewer of the model's 36 blocks sit on the GPU; 120 turns per length (40 for CPU only), per-call timeout raised to 60 s (120 s for CPU only) so a slow call is timed and not cut off. The model was unloaded before each latency arm so the setting took effect on a fresh load.
- **Baseline for every comparison:** session 3's combination arm (`2026-11-13-s3-arms/combo`), same 360 turns. Its rows were re-scored with this session's rules (`rescore_rows.rs`, the harness's own `recompute_row_details`, no model call; written beside the originals as `*.rows.rescored.jsonl`).

| order | arm | flags beyond the combination (`--arm rulings-prompt --arm model-card-sampling --candidates 3 --arm trim-to-cap`) | calls | minutes | card at end, MiB |
|---|---|---|---|---|---|
| 1 | lead | `--arm outcome-lead` | 8,976 | 25 | 5,564 |
| 2 | swh | `--arm says-what-happened --arm outcome-lead --arm no-repeat-opening --arm no-event-copy` | 10,176 | 27 | 5,686 |
| 3 | ship | swh + `--arm brief-by-stop` | 10,038 | 24 | 5,490 |
| 4 | lat-half | ship + `--num-gpu 18 --max-turns 120` | 1,224 | 22 | 4,259 |
| 5 | lat-quarter | ship + `--num-gpu 9 --max-turns 120` | 1,209 | 29 | 4,271 |
| 6 | lat-cpu | ship + `--num-gpu 0 --max-turns 40` | 380 | 17 | 2,750 |

Calls in all: 32,003.

## Results, full arms

Full tables: `ARM-tables.md` (made by `analyse_s4.py`).

| run | pass the rules | good lines (pass and say what happened) | paired difference in good lines vs combo, points (95% interval) | paired difference in pass rate | calls per line | turn latency p50 / p95, ms |
|---|---|---|---|---|---|---|
| combo (session 3, re-scored) | 91.9% | 78.1% | | | 1.39 | 344 / 912 |
| lead | 91.5% | 86.7% | +8.6 (+6.7 to +10.5) | -0.3 (-1.4 to +0.7) | 1.39 | 383 / 911 |
| swh | 83.2% | 83.2% | +5.1 (+2.9 to +7.3) | -8.7 (-10.3 to -7.1) | 1.57 | 433 / 972 |
| ship | 82.9% | 82.9% | +4.9 (+2.5 to +7.2) | -8.9 (-10.6 to -7.3) | 1.55 | 359 / 959 |

**Does the outcome line carry the turn's main fact?** Accepted outcome lines that carry it, then the share of all outcome lines asked for on those turns (fallbacks included):

| run | the journey ended | a traveller died | the party arrived |
|---|---|---|---|
| combo (re-scored) | 54 of 124; 42.9% of 126 | 26 of 221; 11.6% of 225 | 9 of 360; 2.3% of 387 |
| lead | 112 of 126; 88.9% of 126 | 223 of 223; 99.1% of 225 | 294 of 332; 76.0% of 387 |
| swh | 110 of 110; 87.3% of 126 | 181 of 181; 80.4% of 225 | 277 of 277; 71.6% of 387 |
| ship | 114 of 114; 90.5% of 126 | 192 of 192; 85.3% of 225 | 278 of 278; 71.8% of 387 |

**What accepted lines still do:**

| run | accepted lines | false "gone" or "lost" supply | open with the event's text | outcome repeats the previous two-word opening | mention the oxen | Fireside oxen share, brief / standard / rich | unique three-word openings |
|---|---|---|---|---|---|---|---|
| combo (re-scored) | 5,953 | 344 | 526 | 1,327 | 26.1% | 52.6 / 81.4 / 92.5% | 0.134 |
| lead | 5,931 | 262 | 264 | 154 | 17.3% | 30.5 / 55.1 / 70.6% | 0.156 |
| swh | 5,390 | 0 | 0 | 0 | 16.7% | 32.1 / 54.9 / 69.5% | 0.160 |
| ship | 5,374 | 0 | 0 | 0 | 15.4% | 20.0 / 54.4 / 69.3% | 0.140 |

The lead arm's accepted lines also include 38 arrivals and 14 endings not conveyed and 4 actions with no one left alive (318 accepted lines breaking a truth rule in all).

**Good lines per cell (brief / standard / rich):**

| run | Chronicler | Fireside | Lantern-Bearer |
|---|---|---|---|
| lead | 77.8 / 78.3 / 79.9 | 90.4 / 89.7 / 87.1 | 94.6 / 94.0 / 88.1 |
| swh | 81.4 / 80.1 / 79.9 | 81.8 / 81.4 / 77.9 | 93.3 / 90.3 / 82.5 |
| ship | 87.4 / 80.1 / 79.9 | 80.6 / 81.9 / 77.9 | 85.6 / 90.3 / 82.8 |

**Why lines fell back in the ship arm** (the first rule a rejected line broke): resource noun the turn never mentioned 386; event text copied 224; repeated opening 142; numbers or units 72; choice parroting 68; supply contradiction 61; personal pronoun 53; band vocabulary 36; mid-sentence capital 19; arrival not conveyed 13; death words 12; quantifier 9; ending not conveyed 8; punctuation 3.

## Results, latency with fewer layers on the GPU

Fireside, shipping shape. The server's own report of how much of the model sat on the GPU is in the last column, so the setting is known to have been honoured. No call timed out in any latency cell.

| placement | turns per length | per turn p50 / p95 ms, Brief | Standard | Rich | per line p50 / p95 ms, Brief | Standard | Rich | server: on GPU |
|---|---|---|---|---|---|---|---|---|
| whole model on the GPU (ship arm) | 360 | 174 / 317 | 429 / 745 | 761 / 1,322 | 72 / 201 | 172 / 436 | 295 / 720 | 100% |
| half (18 of 36 blocks) | 120 | 870 / 1,930 | 3,557 / 5,971 | 6,311 / 10,344 | 364 / 1,178 | 1,293 / 3,665 | 2,905 / 5,613 | 49% (1.59 of 3.23 GB) |
| quarter (9 blocks) | 120 | 1,299 / 2,435 | 4,416 / 7,319 | 8,843 / 14,038 | 459 / 1,504 | 1,658 / 4,694 | 3,456 / 8,224 | 30% (0.98 of 3.23 GB) |
| CPU only | 40 | 3,873 / 6,051 | 8,277 / 10,610 | 13,370 / 19,201 | 1,867 / 3,261 | 3,276 / 7,135 | 5,067 / 11,841 | 0% |

A turn is two lines, each up to three calls. These figures are from this machine's CPU with the rest on an RTX 5090; a weaker card with the whole model on it was not measured, and a slower CPU would be slower than this.

## Things to know about how it was run

- **The log's first line says "START session 3".** The script was adapted from session 3's and that label was not changed. It is session 4; the folder, the code sha and the arm names are right.
- **Other work overlapped this session, by time:**
  - 17:36 to 17:47 EST (arms swh and ship): builds and unit tests of the Claude API transport on a separate worktree, limited to two build jobs. One more build of a few seconds at 18:02 (ship arm, last cell).
  - 17:44 to 18:02 (ship arm): the Claude API pilot, 611 network calls from one process at a time.
  - 18:03 to about 18:08 (end of the ship arm and the first two minutes of lat-half's Brief cell): a file scan of a worktree folder (disk reads), stopped when noticed.
  - 18:09:35 to 18:55:49 (lat-half Standard and Rich, all of lat-quarter): nine Claude API cells running side by side. They wait on the network and use little CPU, but they were running, and with part of the model on the CPU the machine's CPU was already near full.
  - Nothing else of ours ran during lat-cpu (18:58:26 to 19:15:51).
  The full arms' latency figures (ship arm) and the lat-cpu figures are therefore the clean ones; lat-half and lat-quarter carry the overlap above.
- **Latency cells run fewer turns** (the first 120, or the first 40, in set order), so their acceptance counts are not comparable with the full arms'.
- **The good-line rate for session 3's combination arm is a re-score**, not a re-run: the same answers, checked with rules that did not exist when it ran.

## Andon

None fired. No timeouts and no transport or HTTP errors in any arm; every full cell made its calls and wrote 360 rows.

## VRAM and the card

- Baseline before the run 2,333 MiB. The model held 5.4 to 6.0 GB in the full arms; peak 5,997 MiB at 17:38:57. With 18, 9 and 0 blocks on the GPU the card read about 4.3 to 4.5 GB, 3.7 to 4.3 GB and 2.5 to 2.7 GB.
- The model was unloaded, and Ollama listed no model, before each latency arm (18:06:20, card 2,237 MiB; 18:28:40, card 2,230 MiB; and before lat-cpu).
- Final unload with `keep_alive: 0` at 19:15:52. At 19:16:13 the card read 2,567 MiB with no model loaded. **The card is free.**

## Reading sample

`READING-SAMPLE-ship-29.md`: 30 outcome lines from the ship arm, 10 per voice, chosen by the same rule as session 3's sample (`build_reading_sample.py`), each with the facts the model was given. The builder adds no reading; the notes at the top of that file are R&D's.

## What this does not show

- Whether the lines read well. The rates count rules; the reading sample is for that.
- Latency on a real weaker card or a slower CPU.
- Replays: the arms use the model card's sampling with derived seeds, as session 3's combination arm did; the request and seed are in every row.

## Files

- `run_s4.sh` (the run), `run.log`, `vram.csv`, `unload.json`
- `lead/`, `swh/`, `ship/`, `lat-half/`, `lat-quarter/`, `lat-cpu/`: per cell a report, the rows (everything the model wrote, with the request and seed), stdout and stderr
- `ARM-tables.md`, `analyse_s4.py`, `cell_check.py`, `lat_cell.py`, `ps_brief.py`, `arm_calls.py`, `arm_rate.py`
- `rescore_rows.rs` (re-scores session 3's rows; not part of the repository)
- `build_reading_sample.py`, `READING-SAMPLE-ship-29.md`
