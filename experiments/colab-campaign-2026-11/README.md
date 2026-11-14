# Colab campaign, 2026-11-12 to 2026-11-13: ledgers and the LoRA lane

**Status: ledgers filed; the LoRA lane's outcomes filed; no results from the private art lanes.**
Template: none. Source: Antigravity's two Colab unit ledgers (the 2026-11-12 one covers
windows opened on the evening of 2026-11-12 ET, listed in UTC as 2026-11-13; the 2026-11-13
one covers windows from 09:07 ET on 2026-11-13 to 21:48 ET the same evening). `[unverified]`:
the ledgers are Antigravity's bookings (own rate per hour x elapsed seconds / 3600, from
session open to confirmed stop); nothing here was checked against the Colab console. Totals
below were recomputed from the ledger rows.

## What this page holds

- [results/ledger-2026-11-12.md](results/ledger-2026-11-12.md): all 34 windows of the first
  ledger, grouped by lane, with units and outcomes. The bake-off and jam windows have their
  own pages ([judge-bakeoff](../judge-bakeoff/), [ai-jam-colab](../ai-jam-colab/)).
- [results/lora-lane-2026-11-13.md](results/lora-lane-2026-11-13.md): the ten windows of the
  second ledger, all LoRA training: outcomes only.

## Totals (recomputed)

| ledger | windows | units | by card |
|---|---:|---:|---|
| 2026-11-12 | 34 | 103.864214 | G4 98.478163; L4 2.572104; A100 2.325589; CPU 0.488358 (high-mem 0.476992 and 0.011366) |
| 2026-11-13 | 10 | 91.862310 | G4 only |
| both | 44 | 195.726524 | |

Rates in the ledgers: G4 10.05 per hour, L4 1.94, A100 6.73 (one window, before the A100 stop
ruling), CPU high-mem 0.26 per hour.

## What stands out

1. **Guard trips were common in the LoRA lane**: of ten windows, six finished `ok` with
   checkpoints, one trained but tripped a setup-stall guard, three ended on a guard before
   training (a dead-harness, a cap and a stall guard); the units burned by windows that did
   not train were 7.280287 + 8.693512 + 1.480600 = 17.454399, and the one that trained after
   tripping a guard cost 7.971534. (Recomputed here.)
2. **Most bring-up windows were tooling fixes** (an input hash pin, a manifest prefix, a
   command-line flag, a context limit): each is cheap on a CPU stub and the ledger notes record
   the fix; the G4 bring-ups of the B-2 matrix cost 7.234303 units before its final window.
3. **Anything private stays private.** The art-style lanes (caption drafting, preview
   rendering, LoRA training) appear here as counts, statuses and units only: no lane names,
   images, captions, prompts, sample files, checkpoints or Hub links.

## Studio relevance

relevance: `reference` (a cost and failure-mode ledger). Promoted: not yet.
