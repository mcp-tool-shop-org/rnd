# Escape the Valley: the narrator on the Claude API (2026-11-13)

**State: COMPLETE at 20:55:39 EST, $66.31 spent of the $75 cap.** Halted at 19:38:14 EST by the account's own spend limit ($10.52 spent); resumed 19:47 EST after the Director raised the Console limit to $100 and gave R&D the go. Complete: the pilot, the full Haiku 5.5 arm and its 300-token supplement, the Sonnet 5.5 Fireside Brief cell (360 turns, joined), Opus 5.5 on the three Standard cells (360 turns each, joined), Fable 5.2 on the three Standard cells (one run, not joined).

**The key was deleted after the run, 2026-11-13, by the Director** (the local key file is gone too, checked 21:14 EST). The Claude API test is closed; any future live run needs a new key and a new go.

**Result in one line.** On the three Standard cells (2,160 lines, the same 360 turns), every Claude model writes fewer lines that pass the rules as they stand than the local 4B model (ship 84.1%; Fable 5.2 80.7%, paired -3.4, 95% -6.3 to -0.4; Opus 5.5 78.8%, -5.3, -8.6 to -2.1; Haiku 5.5 76.2%, -7.9, -11.4 to -4.4), mostly by the choice-parroting rule; under the two agreed checker changes the order turns over (ship 86.1%; Fable 91.5%, +5.4, +3.3 to +7.5; Opus 89.3%, +3.2, +0.9 to +5.5; Haiku 85.6%, -0.5, -3.0 to +2.0), at 9 to 19 times the local latency per turn. On Fireside Brief, Sonnet 5.5 is level with the local model (81.5% against 80.6%; +1.0, -3.3 to +5.2).

## What was asked and granted

- The Director's go for the spend, relayed by R&D, on a key file he placed. The cap was raised in steps to **$75 total** for everything here. The harness enforced $75 throughout the paid stages after the first pilot cell.
- Plan, in order: pilot; full Haiku arm; one Sonnet Brief cell (Fireside); Opus 5.5 on the three Standard cells; Fable 5.2 on the three Standard cells. Each estimated from a probe before its run.
- **Replay exemption (Publisher's ruling):** these arms cannot be replayed byte for byte, because the API takes no seed and no sampling settings. Instead every raw response is kept, with the API's request-id, in the call logs.

## Shape

- The shipping shape of session 4, unchanged: rulings prompt, up to 3 candidates (here: up to 3 independent calls), trim, says-what-happened, outcome lead, no repeated opening, no event copy, Brief by stop. Turn set v2, 360 turns, sha256 `59a3e4f8870474d01b775a52071fae9a12629cec0f225606271e9d77f5f8ca46`, verified before every stage.
- Compared against `fallback-runs/2026-11-13-s4-says-what-happened/ship` (the local `qwen3:4b-instruct-2507-q4_K_M`), paired by turn.
- Code: branch `feat/narrator-claude-transport` (local, from rust-2.0 `a3fb14ef`), debug build with the `narrator-claude` feature. Commits used: pilot `d479a9907d2736f27d7d2a0fc24a6a14b3a22aa5`; Haiku arm `b2fe670f340b4b396ef22d02a1e52385cc641c7d`; supplement, probes, Sonnet and Opus `99dea76bff2e3bec23f5b3e67b6f8118d0249e40`. The commit is logged at the start of every stage.

### What the transport sends, and what differs from the local arm

- `POST https://api.anthropic.com/v1/messages`, headers `x-api-key`, `anthropic-version: 2026-10-21`, `content-type`.
- The system prompt as one text block; the turn prompt as the one user message; no assistant turn, so nothing is prefilled.
- The plain schema as `output_config.format` (JSON schema, with the item-count limits removed because the API does not accept them; the checker enforces them). Brief by stop sends `stop_sequences: ["."]` and no schema, as the local arm does.
- **Dropped, because the API refuses or has no such thing:** temperature, top_p, top_k, seed, context size, GPU options, `think`. So the "model-card sampling" part of the shape does not exist here: every model runs at the API's defaults. Each call log line names the options dropped and the seed that was ignored.
- **Thinking:** Haiku 5.5 `thinking: disabled`. Sonnet 5.5 `thinking: between_tools` (its way of switching it off). Opus 5.5 and Fable 5.2 cannot switch it off: no `thinking` field, `output_config.effort: "low"`. Their thinking is billed as output and is in the cost.
- **No `fallbacks` field is ever sent**, so no call is rerouted to another model. A refusal would be logged with its `stop_details` and count as a fallback line. There were none.
- **Answer limit (`max_tokens`):** the pilot and the Haiku arm used the local model's limit (110 tokens; 150 for Rich). That limit was sized for the local tokenizer and cut Haiku's answers (see below). From the supplement on, every cloud call has a 300-token answer limit; Opus, Fable and Sonnet also get 2,000 tokens of headroom on top, so thinking cannot eat the answer.
- **Cache marker:** on the system block for Haiku and Sonnet; not for Opus and Fable. The system prompt differs from turn to turn, so the marker is read only when a candidate repeats the same prompt (a write costs 1.25 times the input price).

### TLS

Certificate verification was on for every call and was never switched off. `rust/etv-core/src/cloud_claude.rs`, `UreqHttpsPost::default`: `.https_only(true)`, `TlsProvider::NativeTls` (Windows system TLS), `RootCerts::PlatformVerifier` (the Windows certificate store decides trust). ureq's one off-switch, `disable_verification`, is never called. The first build used ureq's bundled root list, which Windows' TLS refused for every connection: 125 requests that never left the machine, $0 (folders `pilot-attempt1-network-failed`, `pilot-attempt2-tls-roots`). That was verification failing closed; the fix changed which roots are trusted, not whether they are checked.

### Money and the halt

- **Prices** (https://platform.claude.com/docs/en/about-claude/pricing, read 2026-11-13; per million tokens, input / 5-minute cache write / cache read / output): Haiku 5.5 $0.10 / $0.125 / $0.01 / $0.50 (prompts up to 100,000 tokens); Sonnet 5.5 $2 / $2.50 / $0.10 / $10; Opus 5.5 $4 / $5 / $0.20 / $20; Fable 5.2 $8 / $10 / $0.20 / $40.
- **Cost is counted from each response's usage fields**, in a ledger file per process (`ledger-*.json`). Before every call the transport adds up every ledger in this folder and stops if the total plus the worst case for the next call would pass the cap. A model with no listed price cannot start.
- **Halt file:** on HTTP 400, 401, 402, 403 or any other unexpected status, on five attempts at one call answered 429/5xx/529, on eight such answers in a row, on five network failures in a row, on a response with no usage, or at the cap, the process writes `<its ledger>.HALT`. Every process checks for any `*.HALT` in this folder before each call and at start.
- **What happened:** at 19:38:14 EST one Opus call got HTTP 400 `invalid_request_error`, "You have reached your specified API usage limits. You will regain access on 2026-12-01 at 00:00 UTC." (request-id `req_011Ch1tPZRGNQUpVbS1okz4F`). That is a spend limit set on the account, at about $10; it is not the harness cap. The cell wrote `ledger-opus-fireside-standard.json.HALT`; the other two Opus cells, the Sonnet cell and the last supplement cell (already finished its turns) stopped at their next check.
- After a halt the harness finishes its cell without calling: the rest of each rows file holds not-sent lines. **Only the clean turns before the halt are analysed.**

| stage | model | what | calls answered | dollars |
|---|---|---|---|---|
| pilot (two failed starts) | Haiku 5.5 | 125 requests never sent (TLS trust store) | 0 | 0 |
| pilot | Haiku 5.5 | 9 cells x first 20 turns | 611 | 0.0719 |
| haiku | Haiku 5.5 | 9 cells x 360 turns | 11,037 | 1.2491 |
| haiku-supplement-300 | Haiku 5.5 | the 556 turns with a cut line, 6 cells | 1,907 | 0.2582 |
| opus-probe | Opus 5.5 | Fireside Standard, 10 turns | 28 | 0.2102 |
| fable-probe | Fable 5.2 | Fireside Standard, 10 turns | 29 | 0.3905 |
| sonnet-probe | Sonnet 5.5 | Fireside Brief, 10 turns | 36 | 0.0614 |
| sonnet (partial) | Sonnet 5.5 | Fireside Brief, 142 of 360 turns | 454 | 0.7866 |
| opus (partial) | Opus 5.5 | 3 Standard cells, 120 / 114 / 115 of 360 turns | 1,097 | 7.4898 |
| resume-probe | Opus 5.5 | one call | 1 | 0.0061 |
| opus-rest | Opus 5.5 | the missing 240 / 246 / 245 turns | 2,345 | 15.6995 |
| sonnet-rest | Sonnet 5.5 | the missing 218 turns of Fireside Brief | 701 | 1.2048 |
| fable | Fable 5.2 | 3 Standard cells x 360 turns | 3,218 | 38.8838 |
| **total** | | | **21,464** | **66.3119** |

**Estimates made before each run:** Haiku full arm about $1.30 (actual $1.25). One Sonnet Brief cell about $2.2. Opus three cells about $23 (range $19 to $26); at the halt it had spent $7.49 for 32% of its turns, on course for about $23. Fable three cells about $42 (range $35 to $47).

**To finish the plan** the account's limit would have to allow about $62 more: the rest of Opus about $16, Fable about $42, the rest of Sonnet about $1.5, and margin.

### The key

- Read once per process from a file outside any repository (the transport refuses a key file inside a git work tree), sent only as the `x-api-key` header, never read from the environment, never printed. The transport strips the key from anything it writes; a unit test proves that with an error body that echoes the key.
- **Key check after the halt (19:41 EST):** `key_check.py` read the key from its file inside the script and searched every file in this folder for the whole key and for its characters 20 to 40 (the first 12 characters are a prefix all keys share and would prove nothing): **209 files read, 0 matches.** The header name appears in no output file. The same check on an archive of the branch at `b2fe670f`: 846 files, 0 matches.
- Every answered call, error rows included, carries the API's `request-id` in the call log (15,199 answered plus the one refused: all have one).
- **Key check after the resumed run (20:56 EST):** `key_check.py` on this folder: **334 files read, 0 matches** (whole key, characters 20 to 40); `x-api-key` in no output file. On the re-score folder `fallback-runs/rescore-checker2/`: 214 files, 0 matches. All 6,265 resumed calls carry a request-id.

## Results

### The resumed run (19:47:53 to 20:55:39 EST)

- **Probe:** with the halt file moved to `halt-cleared/` (kept), one Opus call through the harness at 99dea76b (`resume-probe/`, request cap set to one request) returned HTTP 200 at 19:47:56 EST (`req_011Ch1u8J5yfKTTN5PMUF59B`, $0.0061). Hitting the one-request cap wrote a second halt file by design; it is in `halt-cleared/` too.
- **Same commit as the halted arms:** every resumed stage logs code `99dea76bff2e3bec23f5b3e67b6f8118d0249e40`, tree clean, the same debug binary.
- **Opus rest** (`opus-rest/`): the missing turns of each Standard cell (240 / 246 / 245, from the first unclean turn on, listed by `missing_turns.py` in `only-turns-*.txt`), `--cloud-answer-tokens 300 --cloud-no-cache-marker`, 19:48:21 to 20:24:45. 2,345 calls, all HTTP 200, $15.70.
- **Sonnet rest** (`sonnet-rest/`): the missing 218 turns of Fireside Brief, `--cloud-answer-tokens 300` (cache marker on), 19:48:45 to 20:11:18. 701 calls, all HTTP 200, $1.20.
- **Joined** by `join_rest.py` (`opus-joined/`, `sonnet-joined/`): the clean prefix of the first run, then the re-run's rows, every turn once, no unclean row. **Joining caveat:** in the re-run the "previous opening" memory starts empty at its first turn and follows the re-run's own turns.
- **Fable gate** (agreed with R&D): re-estimated from Opus's actual $23.19 for its three cells times Fable's probe cost relative to Opus's probe: $41.6 by the per-call ratio (1.79), $43.1 by the dollar ratio (1.86). Left under the cap: $47.57. It fitted; Fable started 20:25:28. **Actual: $38.88.**
- **Fable** (`fable/`): three Standard cells side by side, `--cloud-answer-tokens 300 --cloud-no-cache-marker`, 20:25:28 to 20:55:39. 3,218 calls, all HTTP 200 (`end_turn`), no answer cut, no refusal, every one with a request-id.

### All four models on the three Standard cells, 360 turns each (2,160 lines)

Tables: `STANDARD-360-tables.md` (views cut by `make_views.py` into `views-standard-360/`). Haiku as run at the local answer limit; the others at 300.

| | local ship | Haiku 5.5 | Opus 5.5 | Fable 5.2 |
|---|---|---|---|---|
| good lines | 84.1% | 76.2% | 78.8% | 80.7% |
| paired difference vs ship, points (95%) | | -7.9 (-11.4 to -4.4) | -5.3 (-8.6 to -2.1) | -3.4 (-6.3 to -0.4) |
| good lines re-scored under the two checker changes | 86.1% | 85.6% | 89.3% | 91.5% |
| re-scored, paired vs ship re-scored (95%) | | -0.5 (-3.0 to +2.0) | +3.2 (+0.9 to +5.5) | +5.4 (+3.3 to +7.5) |
| calls per line | 1.54 | 1.70 | 1.59 | 1.49 |
| carried, of all asked: ending (42) / death (75) / arrival (129) | 85.7 / 84.0 / 67.4% | 90.5 / 86.7 / 76.0% | 78.6 / 93.3 / 78.3% | 57.1 / 90.7 / 67.4% |
| accepted lines with a false supply fact, event-text opening, repeated opening | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| oxen share of accepted lines; Fireside Standard | 17.7%; 54.4% | 30.5%; 86.3% | 13.0%; 38.7% | 12.6%; 37.0% |
| unique three-word openings | 0.171 | 0.158 | 0.222 | 0.220 |
| largest reject: choice parroting | 7 | 182 | 219 | 197 |
| turn latency p50 / p95 | 391 / 728 ms | 4,632 / 9,827 ms | 7,550 / 16,032 ms | 3,469 / 9,444 ms |
| per call incl. network p50 / p95 | | 1,395 / 2,403 ms | about 2,450 / 5,050 ms | 1,328 to 1,571 / 1,881 to 2,340 ms (by cell) |
| dollars for the three cells; per line | | $0.45 (Haiku's share); $0.0002 | $23.19; $0.0107 | $38.88; $0.0180 |

Opus per call $0.0067 (3,442 calls in all, the halted part included); Fable per call $0.0121.

### Sonnet 5.5, Fireside Brief, all 360 turns (720 lines)

Tables: `SONNET-tables.md` (`views-fireside-brief-360/`).

| | local ship | Haiku 5.5 | Sonnet 5.5 |
|---|---|---|---|
| good lines | 80.6% | 81.8% | 81.5% |
| paired vs ship (95%) | | +1.2 (-2.7 to +5.2) | +1.0 (-3.3 to +5.2) |
| re-scored under the two checker changes; paired vs ship re-scored | 85.1% | 88.9%; +3.8 (+0.7 to +6.8) | 89.3%; +4.2 (+0.9 to +7.4) |
| calls per line | 1.52 | 1.61 | 1.60 |
| carried, of all asked: ending (14) / death (25) / arrival (43) | 100 / 96.0 / 65.1% | 64.3 / 92.0 / 76.7% | 85.7 / 100 / 86.0% |
| false supply, event copy, repeated opening | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| oxen share | 20.0% | 38.5% | 6.0% |
| unique three-word openings | 0.138 | 0.280 | 0.179 |
| turn latency p50 / p95 | 174 / 317 ms | 3,076 / 6,984 ms | 5,546 / 14,067 ms |

Sonnet per call $0.0017, $1.99 for the cell; per call incl. network p50 1,533, p95 4,739 ms (the re-run).

### Pilot (Haiku 5.5, 9 cells x the first 20 turns, 17:46 to 18:02 EST)

611 calls, all HTTP 200. Per call: about 1,010 prompt tokens (65 uncached, 555 cache-written, 391 cache-read) and 76 output; $0.000118. Latency per call with the network: p50 1,415 ms, p95 2,443 ms. 43 answers stopped at `max_tokens`.

### Haiku 5.5, full arm (18:09:35 to 18:55:49 EST; local answer limit)

Tables: `HAIKU-tables.md`, `cap_analysis.py`, `supplement_analysis.py`.

| | local ship arm | Haiku 5.5 as run | Haiku with cut lines re-run at 300 tokens |
|---|---|---|---|
| lines | 6,480 | 6,480 | 6,480 |
| good lines (pass every rule and say what happened) | 82.9% | 76.7% | 78.7% |
| fell back | 17.1% | 23.3% (1,511) | 21.3% (1,379) |
| paired difference vs ship, points (95% interval) | | -6.3 (-8.9 to -3.6) | not computed |
| calls per line | 1.55 | 1.70 | |
| main fact carried, of all lines asked: ending / death / arrival | 90.5% / 85.3% / 71.8% | 87.3% / 86.7% / 73.6% | |
| accepted lines with a false supply fact, an event-text opening or a repeated opening | 0 / 0 / 0 | 0 / 0 / 0 | |
| oxen share of accepted lines | 15.4% | 24.3% | |
| Fireside oxen share, brief / standard / rich | 20.0 / 54.4 / 69.3% | 38.5 / 86.3 / 94.8% | |
| unique three-word openings | 0.140 | 0.208 | |
| turn latency p50 / p95 | 359 / 959 ms | 4,267 / 10,701 ms | |

- **Good lines per cell, Haiku against ship (brief / standard / rich):** Chronicler 86.0 / 71.1 / 67.6 against 87.4 / 80.1 / 79.9; Fireside 81.8 / 81.0 / 69.7 against 80.6 / 81.9 / 77.9; Lantern-Bearer 86.7 / 76.7 / 69.6 against 85.6 / 90.3 / 82.8.
- **Why Haiku's lines fell back** (first rule broken; ship's count in brackets): choice parroting 482 (68); resource noun the turn never mentioned 317 (386); unreadable answer 176 (0), mostly answers cut by the token limit; repeated opening 140 (142); numbers or units 112 (72); personal pronoun 88 (53); mid-sentence capital 51 (19); event text copied 46 (224); over the word cap 34 (0); draft animal species 15 (0); band vocabulary 15 (36); supply contradiction 3 (61).
- **Our own token limit:** 832 of 11,037 calls stopped at `max_tokens`; 626 lines had a call cut, and 321 of those fell back. The supplement re-ran the 556 turns holding such a line with a 300-token answer limit (1,907 calls, none cut): 189 of the 321 still fell back. So the limit accounts for 132 lines, about 2 of the 6.3 points; the rest is the rules themselves, mostly choice parroting.
- **How the supplement was joined:** only the cut lines take the re-run's result; lines that were not cut keep their original result, though the supplement re-ran the whole turn. In a re-run the "previous opening" memory is the previous re-run turn of the same run, not the true previous turn. The paired interval was not recomputed on the joined figure.
- Tokens per call (mean): 66 uncached + 501 cache-written + 446 cache-read input, 79 output; $0.000113. The cache was read on 5,202 of 11,037 calls. Per call p50 1,395 ms, p95 2,403 ms.

### Opus 5.5, partial: the first 114 turns of each voice at Standard (19:21:42 to 19:38:14 EST)

Like for like: the same 114 turns of the ship arm and of Haiku, 684 lines each (`views-standard-114`, `OPUS-partial-tables.md`). Haiku's figures here are as run at the local answer limit; Opus had 300 answer tokens.

| | local ship | Haiku 5.5 | Opus 5.5 |
|---|---|---|---|
| good lines | 83.8% | 77.9% | 80.8% |
| paired difference vs ship, points (95% interval) | | -5.8 (-12.2 to +0.5) | -2.9 (-9.0 to +3.1) |
| calls per line | 1.57 | 1.65 | 1.56 |
| main fact carried, of all asked: ending (24) / death (36) / arrival (39) | 83.3% / 86.1% / 71.8% | 83.3% / 94.4% / 79.5% | 83.3% / 97.2% / 87.2% |
| accepted lines with a false supply fact, event-text opening, repeated opening | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| oxen share of accepted lines; Fireside Standard | 15.9%; 51.1% | 30.4%; 86.2% | 12.3%; 36.6% |
| unique three-word openings | 0.264 | 0.242 | 0.291 |
| good lines per voice: Chronicler / Fireside / Lantern-Bearer | 80.3 / 78.1 / 93.0% | 72.4 / 82.5 / 78.9% | 79.4 / 81.6 / 81.6% |
| turn latency p50 / p95 | 400 / 735 ms | 4,335 / 9,567 ms | 7,261 / 16,095 ms |

- Why Opus's lines fell back (first rule broken): choice parroting 55; resource noun 32; band vocabulary 15; numbers or units 12; repeated opening 8; event text copied 3; supply contradiction 2; mid-sentence capital 2.
- Opus per call: 1,086 input and 124 output tokens (thinking included), $0.00683; p50 2,407 ms, p95 5,094 ms. No refusal, no answer cut.
- With 114 turns per voice the intervals are wide; neither cloud model is shown to differ from the local one here.

### Sonnet 5.5, partial: the first 142 turns of Fireside Brief

Like for like on those 142 turns, 284 lines each (`views-fireside-brief-142`, `SONNET-partial-tables.md`).

| | local ship | Haiku 5.5 | Sonnet 5.5 |
|---|---|---|---|
| good lines | 81.0% | 79.2% | 82.4% |
| paired difference vs ship, points (95% interval) | | -1.8 (-8.8 to +5.3) | +1.4 (-5.6 to +8.4) |
| calls per line | 1.54 | 1.65 | 1.60 |
| main fact carried, of all asked: ending (9) / death (15) / arrival (14) | 100% / 93.3% / 57.1% | 77.8% / 93.3% / 71.4% | 77.8% / 100% / 85.7% |
| oxen share of accepted lines | 25.2% | 31.6% | 6.0% |
| unique three-word openings | 0.217 | 0.347 | 0.269 |
| turn latency p50 / p95 | 172 / 317 ms | 3,100 / 7,326 ms | 6,090 / 14,744 ms |

Sonnet per call: about 867 prompt tokens and 41 output, $0.00173; p50 1,740 ms, p95 5,144 ms.

### Probes (10 turns each, 19:19:36 to 19:21:02 EST)

All three models answered HTTP 200 on the first call, so the request shape is accepted and Fable 5.2 is allowed on this account.

| model | cell | calls for 20 lines | input + output tokens per call | dollars per call | per call p50 / p95 | lines accepted |
|---|---|---|---|---|---|---|
| Opus 5.5 | Fireside Standard | 28 | 1,123 + 151 | 0.0075 | 2,592 / 5,497 ms | 18 of 20 |
| Fable 5.2 | Fireside Standard | 29 | 1,127 + 111 | 0.0135 | 1,650 / 5,619 ms | 16 of 20 |
| Sonnet 5.5 | Fireside Brief | 36 | 876 + 41 | 0.0017 | 1,659 / 4,859 ms | 16 of 20 |

### Re-scored under the two agreed checker changes (offline, about 19:57 EST)

Full method and tables: `fallback-runs/2026-11-13-s4-says-what-happened/RESCORE-checker2-2026-11-13.md`. The changes: choice parroting rejects only a verbatim copy of the whole label (two words or more) or 5+ of its words in a row (a one-word label is never a parrot); the repeated opening compares three words, with the lead's subjects (the party, a traveller, the last, the turn, the wagon) exempt.

Method: each arm's rows walked in set order, every kept line re-checked with the arm's own checker plus the change, the opening memory carried forward from lines the re-score accepts. A fallen-back slot can be rescued only by the last candidate its row kept, so "after" is a lower bound. The same walk without the change reproduces every recorded status on every unspliced arm (0 mismatches).

| arm | lines | good, recorded | good, after | after, paired vs ship after (95%) |
|---|---|---|---|---|
| local ship | 6,480 | 82.9% | 85.7% | |
| Haiku as run | 6,480 | 76.7% | 85.4% | -0.3 (-2.3 to +1.6) |
| Haiku, cut lines re-run at 300 | 6,480 | 78.9% | 87.7% | +2.0 (+0.1 to +3.9) |
| ship / Haiku / Opus, Standard, 114 turns | 684 each | 83.8 / 77.9 / 80.8% | 86.3 / 86.1 / 89.8% | Haiku -0.1 (-4.9 to +4.6); Opus +3.5 (-0.7 to +7.7) |
| ship / Haiku / Sonnet, Fireside Brief, 142 turns | 284 each | 81.0 / 79.2 / 82.4% | 85.9 / 87.3 / 88.7% | Haiku +1.4 (-4.0 to +6.8); Sonnet +2.8 (-2.3 to +7.9) |

Choice-parroting rejects after the change: ship 16 (was 68), Haiku 50 (was 482).

**Correction:** the Haiku figure with cut lines re-run at 300 tokens was 78.7% above; 26 of those re-runs (Fireside Rich) were never sent because of the 19:38:14 halt and had been counted as fallbacks. Kept as run: **78.9%**. (`join_supplement.py`.)

## Things to know about how it was run

- **Latency is under our own load.** Cells ran side by side (nine for Haiku, six for the supplement, four for Opus and Sonnet), each with a ledger of its own. Per-call figures include the network; per-turn figures add up a turn's calls, which run one after another.
- **Overlap with session 5 (resumed run):** every resumed cloud call (19:47:53 to 20:55:39) ran while session 5's qwen3:8b and qwen3:14b arms were on the card. The cloud calls are network-only; the cloud harness is a separate process on the CPU. Session 5's record states the same overlap.
- **Overlap with the local sessions:** the pilot and the transport's builds ran during session 4's swh and ship arms; the nine Haiku cells ran during session 4's half-GPU and quarter-GPU latency arms (18:09:35 to 18:55:49); the last minute of the Opus and Sonnet cells and all later analysis overlap session 5 (started 19:39:13).
- **One build difference inside the Haiku comparison:** the cloud harness is a debug build; the local arms used a release build. The harness's own work per call is a few milliseconds either way.
- **The sample is the same turns, not the same conditions:** the local arm samples at the model card's settings with derived seeds; the cloud arms run at the API's defaults with no seed.

## Reading sample

**All 360 turns, Fable added:** `READING-SAMPLE-side-by-side-standard-360.md`, 10 turns per voice (30), each with the ship, Haiku, Opus and Fable Standard outcome lines and the turn facts, chosen by the same rule (`build_cloud_reading_sample.py`). No reading is added.

The first sample, on the 114 common turns:

`READING-SAMPLE-side-by-side-standard.md`: for each voice, 8 turns from the common 114, each with the local ship line, the Haiku line and the Opus line for that turn at Standard length, and the turn facts all three were given. Chosen by rule (`build_cloud_reading_sample.py`): per category, the first unused turn in set order whose line was accepted by all three; if none, by the most. The first 114 turns hold no triumphant and no pyrrhic ending, so those two categories are empty: 24 turns in all, not 30. No reading is added.

## What this does not show

- Fable 5.2 beyond 20 lines; Opus and Sonnet beyond the first third of the turns (no late-run turns, no victories).
- Whether the cloud lines read better. The rates count rules written for a small model's failures; choice parroting is the cloud models' largest reject and may be the rule being strict about a line that reads well. The reading sample is for that.
- Cloud latency as a player would see it (one call at a time, their network).

## Files

- `run_cloud.sh`, `run.log` (every stage with its commit, model and flags)
- `pilot/`, `haiku/`, `haiku-supplement-300/`, `opus-probe/`, `fable-probe/`, `sonnet-probe/`, `opus/`, `sonnet/`: per cell the rows and report, and `calls-<cell>.jsonl` (one line per HTTP attempt: request-id, status, stop reason, usage, cost, latency, the raw response)
- `ledger*.json`, `ledger-opus-fireside-standard.json.HALT`
- `views-standard-114/`, `views-fireside-brief-142/` (rows cut to common turns by `make_views.py`)
- `HAIKU-tables.md`, `OPUS-partial-tables.md`, `SONNET-partial-tables.md`
- `calls_summary.py`, `cap_analysis.py`, `capped_turns.py`, `supplement_analysis.py`, `key_check.py`
- `build_cloud_reading_sample.py`, `READING-SAMPLE-side-by-side-standard.md`
