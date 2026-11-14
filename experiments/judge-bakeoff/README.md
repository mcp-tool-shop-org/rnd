# Judge bake-off: the counted 430-triad run on Colab G4

**Status: run and scored (one counted pass); promotion pending.** Template: none.
Source: Antigravity's reply of 2026-11-12 (ET) and the rig's public score summary, read
2026-11-13. Claims are `[unverified]` unless a line names a check. No verifier pass was
run (Standing Rule 3). Numbers are copied from the records; anything recomputed is marked.

## The question

Which of five small local judge models should be the studio's claim-support judge, under a
preregistered rule? A judge reads a claim and its evidence and says whether the evidence
supports it. Each item is asked in two orders, and items come in three-item "triads" (one
per class: supported, unsupported, cannot tell).

## What ran

- **Where:** Colab, `G4` Standard for every counted window, with local scoring on the rig
  afterwards. The sealed keys were never opened by the Colab side or read into the scoring
  agent's context; this page carries aggregates only.
- **Windows** (see `results/counted430-g4.md`): four lock-check windows (one on an A100
  before the A100 stop ruling, one pre-fix `G4` diagnostic, two successful) and two counted
  shards: 29.058459 units for the four successful `G4` windows and 33.237715 units in all
  (recomputed here from the ledger rows).
- **Counted set:** 420 triads (1,260 items); 10 canary triads excluded; realized split
  dev 387, test 903, total 1,290.
- **Judges:** `d3-mini`, `granite-guardian-4.1-8b`, `nemotron-3-nano-4b`, `mu-judge`,
  `flow-judge-v0.1`.

## Result

The reply's selected winner is **`d3-mini`** (the only judge clearing the floors). Not adopted.
The perfect score was checked on the rig on 2026-11-13: no leak was found, the task is binary and transfer
is untested (see Cautions). The selection rule (from
the score summary): a judge is eligible only if it clears all the floors, namely the
one-sided 95% lower bound of AND-gate precision at least 0.86, of AND-gate recall at least
0.45, per-negative-class precision (unsupported, and cannot-tell) at least 0.85, and
AND-gate recall at least 0.25 in at least 8 of 10 domains. Among eligible judges a
Holm-adjusted paired test picks the candidate set, then precision within 0.015 of the best,
then accuracy, then fewer parameters, then lower median latency. The floors removed
judges as follows (a judge can fail several): lower-bound precision 3, lower-bound recall 2,
unsupported-class precision 3, cannot-tell precision 1, domain coverage 1; none failed to run.

| Judge | Class-balanced strict | 95% CI | All-3-of-triad | Flip rate | AUROC | Yes-precision (LCB) | Yes-recall (LCB) | Length stops | Unparseable |
|---|---:|---|---:|---:|---:|---|---|---:|---:|
| `d3-mini` | 1.0000 | [1.0000, 1.0000] | 1.0000 | 0.0000 | 1.0000 | 1.0000 (1.0000) | 1.0000 (1.0000) | 0 | 0 |
| `granite-guardian-4.1-8b` | 0.7175 | [0.7008, 0.7341] | 0.2286 | 0.1897 | 0.9397 | 0.9906 (0.9722) | 0.2500 (0.2167) | 0 | 0 |
| `nemotron-3-nano-4b` | 0.6008 | [0.5762, 0.6246] | 0.1786 | 0.2968 | 0.8424 | 0.8324 (0.7880) | 0.3548 (0.3167) | 0 | 0 |
| `mu-judge` | 0.5492 | [0.5230, 0.5754] | 0.1571 | 0.3659 | 0.9098 | 0.7615 (0.7328) | 0.7071 (0.6714) | 0 | 0 |
| `flow-judge-v0.1` | 0.4333 | [0.4079, 0.4595] | 0.0786 | 0.3937 | N/A | 0.5659 (0.5369) | 0.5929 (0.5548) | 0 | 0 |

Trivial baselines in the same summary: always-no 0.6667 class-balanced, always-yes 0.3333.

## Determinism and merge checks (the reply's account)

- All five merge gates `ok` (anchor agreement, bijection and input-token hash, colocation,
  row-done hash, session environment with zero uncorrected ECC errors).
- Three independent `G4` sessions agree bit for bit on the 500 anchor calls: 0 verdict
  flips, 0 output-token hash differences and 0 input-token hash differences for every pair.
- 12,900 of 12,900 rows matched the exact assembled prompt hash.
- Combined-outputs hash and schedule hash are in `results/counted430-g4.md`.

## Cautions, read before relying on the selection

1. **A perfect score, checked for leaks on 2026-11-13 (R&D, on the rig, aggregates only).** `d3-mini` scores
   1.0000 on every measure over 1,260 items, with zero flips and an AUROC of 1.0000. The check found:
   - **No judge-visible leak.** Its input is the material and the claim only, the same facts every judge gets, and
     12,900 of 12,900 assembled prompts matched their hashes.
   - **The part passed the surface-feature probe.**
   - **A shuffled-key control falls to chance:** mean agreement 0.555 over 200 permutations, against about 5/9
     expected.
   - **It is the full counted part,** not a subset.

   So the score is real agreement with the keys, but two things stay open before any adoption:
   - **The pass is binary** ("is the claim supported?"). It separates supported from not-supported, and does not test
     unsupported against cannot-tell.
   - **Transfer is untested.** It is not known whether the model was trained on procedurally generated fact tables
     like these; a held-out item family from a different generator would show whether the result transfers.
2. **The summary's own banner reads "shakedown, decision rule not applied".** The selection line comes from the same
   file's selection block, where the reply calls it the selected winner. Whether the rule was formally applied is for
   the Publisher to confirm.
3. The summary lists ECE, reliability curves, per-closure breakdowns and three-way pass
   metrics as exploratory only.

## Left out, kept on the rig

Sealed answer keys, per-item rows and the sealed score rows; item text and prompts.

## Studio relevance

relevance: `act` (selected, not adopted: settle the binary-task and transfer questions before adopting `d3-mini`).

Promoted: not yet.
