# Escape the Valley: the shipping shape on larger local models, session 5 (2026-11-13)

**Result in one line.** No larger or newer local model beats the shipping 4B model: qwen3:8b is level with it (82.2% good lines against 82.9%; paired -0.7 points, 95% -2.8 to +1.3) at 1.4 times the turn time, qwen3.5:4b is a little worse (80.5%; -2.5, -4.3 to -0.6) and drops most deaths, and the two largest are clearly worse (qwen3:14b 70.9%, qwen3.5:9b 73.1%); no arm's accepted lines state a false supply fact, copy the event text or repeat an opening.

## What was run

- **Granted** by the Publisher (relayed by R&D), 2026-11-13: four arms on the RTX 5090, local Ollama only, 4 h 30 min wall (`SESSION-5-GRANT-REQUEST-2026-11-13.md`).
- **Start** 2026-11-13 19:39:13 EST. **Wall** 16,200 s, deadline 00:09:13 EST, enforced by `timeout`. **All four arms finished**; the run ended 23:38:53 EST (`END`), wall used 14,359 s of 16,200. 45,109 calls in all (10,250 + 11,746 + 11,053 + 12,060).
- **Code** rust-2.0 at `a3fb14ef848843838c6eb4f327d3708973e5f58b`, worktree `etv-run-s4`, clean, the same release build as session 4 (`narrator-ollama`); harness unmodified. The model is the only change: the `--model` flag.
- **Turn set** v2, 360 turns, sha256 `59a3e4f8870474d01b775a52071fae9a12629cec0f225606271e9d77f5f8ca46`, verified at the start and by the harness on every cell.
- **Shape** session 4's ship arm, unchanged: `--arm rulings-prompt --arm model-card-sampling --candidates 3 --arm trim-to-cap --arm says-what-happened --arm outcome-lead --arm no-repeat-opening --arm no-event-copy --arm brief-by-stop`; the plain schema's 9 cells (3 voices x 3 lengths), 6,480 lines per arm.
- **Baseline** `fallback-runs/2026-11-13-s4-says-what-happened/ship` (`qwen3:4b-instruct-2507-q4_K_M`), paired by turn.
- **Sampling** the harness sends temperature 0.7, top_p 0.8, top_k 20 on every call, which overrides each package's own (logged per arm below) and matches both model cards' advice for non-thinking text. It sends no min_p (server default 0, as the cards advise) and no presence penalty: the qwen3.5 packages carry 1.5, which is also the Qwen3.5 card's advice, so it stayed in force. Qwen3's card gives no presence penalty for this use.
- **Baseline VRAM** 2,393 MiB at the start (the idle desktop), no model loaded.

### Thinking check, per arm

Before each arm: three direct calls (`think_probe.py`) and a 20-turn Fireside Standard check cell (`check_cell_think.py`) had to show no thinking, no empty answer and a median line time under a limit; an arm that failed would have been dropped. **Deviation to state:** the limit is three times the 4B model's median line time (172 ms) **scaled by model file size** (8b 1,079 ms; 14b 1,915; 3.5:4b 685; 3.5:9b 1,352), because an unscaled 3x would have dropped the 14B for its size alone. Every arm passed.

| arm | model, digest, quant | packaged defaults (overridden by the harness) | direct calls | check cell: accepted of 40, median line (limit) | VRAM after load | on GPU |
|---|---|---|---|---|---|---|
| qwen3-8b | `qwen3:8b` 500a1f067a9f Q4_K_M 5.23 GB | temperature 0.6, top_k 20, top_p 0.95, repeat_penalty 1 | 3, no thinking | 31, 302 ms (1,079) | 7,992 MiB | 100% |
| qwen3-14b | `qwen3:14b` bdbd181c33f2 Q4_K_M 9.28 GB | temperature 0.6, top_k 20, top_p 0.95, repeat_penalty 1 | 3, no thinking | 27, 681 ms (1,915) | 11,989 MiB | 100% |
| qwen3-5-4b | `qwen3.5:4b` d8b0f5e9760c Q4_K_M 3.32 GB | presence_penalty 1.5 (kept), temperature 1, top_k 20, top_p 0.95 | 3, no thinking | 34, 449 ms (685) | 6,653 MiB | 100% |
| qwen3-5-9b | `qwen3.5:9b` 56671c2ab938 Q4_K_M 6.55 GB | presence_penalty 1.5 (kept), temperature 1, ... | 3, no thinking | 29, 778 ms (1,352) | 9,214 MiB | 100% |

## Results

Tables per arm: `<arm>/ARM-tables.md` (made by `analyse_s4.py`, ship first). One line per arm: `s5_arm_line.py`.

| | s4 ship (4B) | qwen3:8b | qwen3:14b | qwen3.5:4b | qwen3.5:9b |
|---|---|---|---|---|---|
| arm times (EST) | | 19:39:15 to 20:12:48 | 20:12:50 to 21:26:02 | 21:26:03 to 22:22:31 | 22:22:32 to 23:38:32 |
| minutes; calls | 24; 10,038 | 33; 10,250 | 73; 11,746 | 56; 11,053 | 76; 12,060 |
| good lines (pass every rule and say what happened) | 82.9% | 82.2% | 70.9% | 80.5% | 73.1% |
| paired vs ship, points (95%) | | -0.7 (-2.8 to +1.3) | -12.1 (-14.5 to -9.7) | -2.5 (-4.3 to -0.6) | -9.8 (-11.7 to -7.9) |
| re-scored under the two checker changes | 85.7% | 86.1% | 74.0% | 83.9% | 75.5% |
| re-scored, paired vs ship re-scored (95%) | | +0.4 (-1.4 to +2.1) | -11.8 (-13.9 to -9.7) | -1.8 (-3.4 to -0.2) | -10.3 (-11.9 to -8.6) |
| carried, of all asked: ending (126) / death (225) / arrival (387) | 90.5 / 85.3 / 71.8% | 88.1 / 81.8 / 72.1% | 82.5 / 67.1 / 57.1% | 94.4 / 38.2 / 76.0% | 88.1 / 73.8 / 74.2% |
| accepted lines with a false supply fact / event-text opening / repeated opening | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| unique three-word openings | 0.140 | 0.122 | 0.175 | 0.231 | 0.254 |
| oxen share of accepted lines | 15.4% | 18.1% | 10.6% | 24.9% | 17.9% |
| calls per line | 1.55 | 1.58 | 1.81 | 1.71 | 1.86 |
| turn latency p50 / p95 | 359 / 959 ms | 507 / 1,288 ms | 1,226 / 2,835 ms | 855 / 2,127 ms | 1,315 / 2,762 ms |
| peak VRAM (whole card) | 5,490 MiB at end | 8,224 MiB | 12,691 MiB | 7,085 MiB | 9,505 MiB |

All five models sat wholly on the GPU (the server's own report at each warm-up).

Why lines fell back (first rule broken), largest counts: ship / 8b / 14b / 3.5:4b / 3.5:9b:
- resource noun the turn never mentioned 386 / 185 / 374 / 333 / 713;
- event text copied 224 / 194 / 658 / 51 / 146;
- repeated opening 142 / 204 / 258 / 96 / 43;
- choice parroting 68 / 87 / 9 / 219 / 176;
- personal pronoun 53 / 45 / 54 / 98 / 297;
- band vocabulary 36 / 45 / 258 / 96 / 75;
- numbers or units 72 / 70 / 83 / 158 / 119;
- invalid punctuation 3 / 247 / 27 / 24 / 1;
- death not conveyed 0 / 13 / 19 / 110 / 41.

All arms side by side: `ALL-ARMS-tables.md`; re-scored: `ALL-ARMS-rescored-tables.md`.

## Things to know about how it was run

- **Load on the rig during the arms.**
  - One `cargo test -j 1` build at low priority, **19:52:58 to 19:56:46 EST**, for the offline re-score (R&D was told; no build after it). It overlapped qwen3:8b's **Fireside Standard cell** (19:52:01 to 19:56:05) entirely and the first 41 s of its **Fireside Rich cell**. **Those two cells' latency was taken under that load and is not comparable;** their fallback rates are.
  - The Claude API cells (network-only; the cloud harness is a separate process) ran 19:47:53 to 20:55:39 EST: all of qwen3:8b's arm and qwen3:14b's arm up to 20:55. The cloud record states the same overlap.
  - Short single-threaded re-score runs (about 6 s each) and Python analyses ran between and during cells: about 19:57 to 19:58, 20:11, 20:13, 20:25, 20:56, 21:26 and 22:23 EST.
- Ship's turn latency (359 / 959 ms) was itself taken with other work on the rig (session 4 record); the paired latency comparison is indicative only.
- One process per cell, rows flushed per turn; models unloaded between arms and the server's model list confirmed empty each time.

## Andon

VRAM andon at 30,000 MiB and an Ollama-liveness andon, checked every minute (`vram.csv`). Neither fired. The highest reading was 12,691 MiB (qwen3:14b).

## Card free

**Card free 23:38:53 EST.** The run unloaded qwen3.5:9b (`keep_alive 0`) and logged VRAM 2,314 MiB with the server's model list empty (`{"models":[]}`); read again at 23:38:58: 2,314 MiB, no model loaded, no `narrator_measure.exe` running. Baseline at the start was 2,393 MiB. Between arms each model was unloaded and the empty list confirmed (20:12:50, 21:26:03, 22:22:32).

## Reading sample

`READING-SAMPLE-8b-beside-ship.md`: the best arm by good lines (qwen3:8b), 30 slots, 10 per voice, chosen by the same rule as session 4's ship sample (`build_reading_sample.py`), beside that ship sample (R&D's reading of it left out). 29 lines each. No reading is added.

## Files

- `run_s5.sh`, `run.log`, `script.out`, `vram.csv`
- `<arm>/plain-<voice>-<length>.{rows.jsonl,report.json,stdout.txt,stderr.txt}`, `<arm>/check/` (direct calls and the check cell)
- `<arm>/ARM-tables.md`; `analyse_s4.py`, `s5_arm_line.py`, `build_reading_sample.py`
- Re-scored rows under the two agreed checker changes: `fallback-runs/rescore-checker2/s5-<arm>/`
