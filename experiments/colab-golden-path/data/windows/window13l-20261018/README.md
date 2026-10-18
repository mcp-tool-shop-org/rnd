# Window 13l: W-A, 2026-10-18 (step 6)

W-A resumes four writers at w1: Qwen3.8, Gemma, Granite and Bolt. Muse critiques. The window ran Granite's one
sent-back draft (T02-D-01) through a rewrite and a critique. Then it ran the two T04 twins for every writer, each one
written and then critiqued.

All of it ran at role-set `430285a`, rnd `018b6cf`. Four of the five models came pre-built from the studio's private
GGUF repo at commit `d847f5b8`; Bolt is NVIDIA's own GGUF, fetched as before.

**Read this first.**
- **This is a screen.** Its batches are not releasable.
  - Granite's w3 critique logged the batch-mix rule failing: "T02: 0 of 4 verdict-bearing items (0%) are keyed
    cannot_tell; at least 25% are needed." The two stub rungs logged the same line.
  - The failure comes from the pilot's frozen 8 slots, so it isn't a halt.
  - Any batch we release must pass that rule.
- **Twin counts are 2 slots per writer.** "2 of 2" against "1 of 2" says a twin can work. It doesn't rank writers.

| Writer | Pilot | Twins written (of 2) | Twins accepted | Twin write, s per slot | Against its T02 rate | Muse critique, s per draft | Cut off at the limit (twin write) |
|---|---|---|---|---|---|---|---|
| Qwen3.8-27B | 8 accepted, carried from w1 | 2 | 2 of 2 | 920 | 2.28× (T02 404) | 465 | 1 |
| Gemma-4-31B-it | 7 accepted, carried from w1 | 2 | 2 of 2 | 234 | 1.98× (T02 118) | 280 | 0 |
| Granite-4.2-30B | T02-D-01 rewritten via the chain, then 8 of 8 accepted | 1 (1 dropped at write) | 1 of 1 | 1,128 | 2.01× (T02 560) | 439 | 1 |
| Nemotron-3.5-Bolt-74B (maker QAT) | 7 accepted, carried from w1 | 2 | 1 of 2 (1 dropped at critique) | 446 | 1.15× (T02 388) | 461 | 0 |

**Totals:** 30 pilot rows accepted, 6 twins accepted, 0 model errors, 0 refused calls.

## What it settles

- **Pre-built GGUFs work in a paid window.**
  - The prefetch downloaded the four Q8_0s (122.4 GB) in 684 s, at about 179 MB/s. The projection had allowed 5,145 s
    of setup for conversion.
  - Every file equalled its pin: Qwen3.8 `2ab268e0`, Gemma `e357a450`, Granite `1b5c4783`, Muse `c321320a`.
  - The read token was dropped before any wave. When Bolt was fetched later, huggingface_hub found no token and fell
    back to Colab secrets, and it said so in a warning.
- **The card-pin chain worked again.**
  - Granite's w2 rewrite entry records `card_pins_via: chain`, with prior `0af16945…` (Granite's w0). It's still in
    w3's `waves[]`.
  - Bolt's `card-pins-chain.json` records the chain, with 7 pins and prior `dffd69dc…`.
- **Twin slots cost about 2× a T02 slot.** Bolt is the exception at 1.15×. W-B measured Lightning at 2.33× and Muse at
  2.92×. Use about 2× for twin projections, per writer where measured.
- **The projection was 19% high: 21.8 units projected, 17.55 spent.**
  - Setup came in 4,461 s under projection.
  - The twins came in over it: 5,455 s of twin writes against 2,940 projected, and 2,850 s of twin critique against
    2,368.

## Cost

| Measure | Units |
|---|---|
| Rate × runtime (5.3/hr × 3.312 h, 10:18:57 to 13:37:39Z) | **17.55** (booked) |
| Balance (1158.62 → 1141.14) | 17.48 |
| Cap / projection | 25.1 / 21.8 |

The exec ended by itself at 11,749 s, under the 16,200 s wall. The session list after the stop was empty. The study
stands at 161.12 of 200.

## The VM gate (for the floor recalibration)

The gate passed try 1. Its readings:
- card: A100-SXM4-40GB, with 0 GPU processes and 0 MiB of VRAM in use;
- disk: 207.6 GB;
- RAM: 85.8 GB;
- HF short read: 114.6 MB/s.

The window's real prefetch ran at about 179 MB/s, 1.56× the short read. The A100 prebuild windows (13i, 13j, 13k)
downloaded BF16 snapshots at 302–310 MB/s, against short reads of 88–90: about 3.45×. The ratio depends on the download
path, so the short read is a guard against a broken pipe, not a predictor of speed. The floor stays 60 until R&D rules.

## Sources (this folder)

- `pin-result.json`: arms, waves, seconds, hosted shas, serves.
- `job.log`: the prefetch timeline and the resources lines.
- `pilot-out.tar`: drafts, the chain headers, the sidecar, accepted.jsonl.
- `gate.jsonl` and `rig.log`: the balance, the session times, the empty list.
- T02 rates come from `docs/drafts/step6-projections-2026-10-18.md`, measured on night one. W-B's twin rates come from
  `window13b-20261018/pin-result.json`.
- Token scan: 0 matches of `hf_[A-Za-z0-9]{30,}` in 151 files, `pilot-out.tar`'s contents included.
