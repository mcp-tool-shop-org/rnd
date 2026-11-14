# ai-jam-sessions on Colab: quantisation damage and E-R distillation

**Status: three tracks run (3A, 3B, 3C); findings recorded, none promoted.** Template: none.
Source: three Antigravity replies dated 2026-11-12 and 2026-11-13 (written as UTC
timestamps; the windows ran the night of 2026-11-12 into 2026-11-13 ET). Every claim is
`[unverified]` unless a line names a check; no verifier pass was run (Standing Rule 3).
Numbers are copied from the replies; recomputed ones are marked.

## The questions

- **3A (B-2 quantisation matrix):** how much does GGUF quantisation hurt the five selected
  B-2 LoRA seeds on a 7B model, rung by rung?
- **3B (E-R distillation):** can a 32B teacher's verifier-checked reharmonisations teach a
  4B student to write voiced reharmonisations in one shot?
- **3C (scale and licence ablation, plus GGUF survival):** how much of 3B survives training
  on only the 129 open-licence rows, how does a 7B base compare with the 4B, and does the
  `Q4_K_M` versus `IQ4_XS` pattern of 3A repeat on this task?

Details and full tables: [results/b2-quant-matrix.md](results/b2-quant-matrix.md),
[results/er-distill-sft.md](results/er-distill-sft.md),
[results/er-scale-and-quant.md](results/er-scale-and-quant.md).

## Findings in brief

1. **3A.** On `Qwen2.5-7B-Instruct` with all five B-2 seeds, `Q8_0`, `Q6_K` and `Q5_K_M` sit
   within 0.24 points of `F16` (5-seed mean composite 0.7656 for `F16`). `Q4_K_M` (the rung
   the project ships today) drops 2.16 points on the mean, in 5 of 5 seeds (worst 4.49
   points), mostly through abstention prose calibration. `IQ4_XS`, smaller than `Q4_K_M`,
   recovers to 0.7636 (0.19 points below `F16`).
2. **3B.** The teacher's candidates passed the verifier gate for 408 of 415 training
   windows (98.31%); the 4B student LoRA's one-shot voiced pass rate on 47 held-out windows
   rose from 6.38% (3 of 47) to 87.23% (41 of 47).
3. **3C.** Training on the 129 open-licence rows alone gives 65.96% (31 of 47) on both
   models; all 408 rows give 87.23% (4B) and 93.62% (7B), on the same 47 windows. In the
   GGUF ladder the 4B's `Q4_K_M` falls to 68.09% (from 91.49% at `F16`) while `IQ4_XS` holds
   91.49%; on the 7B `IQ4_XS` is the best cell at 95.74%.
4. **Antigravity's recommendation** (its words summarised, not R&D's verdict): replace
   `Q4_K_M` with `IQ4_XS` (or `Q5_K_M` when memory allows) as the default 4-bit rung.

## Cautions

- **Small n.** The 3B and 3C pass rates rest on 47 held-out windows from 5 songs (35 windows
  in the publishable subset): one window is 2.13 points, so most differences between
  adjacent rungs are one to three windows. 3A has 285 prompts per cell and five seeds.
- **One quantiser, one pin.** All quantisation used a single `llama.cpp` revision, without
  an importance matrix; no other revision or calibration was tried.
- **Numbers that disagree between the 3B and 3C replies** (both copied as written, the
  reason for the gap is not given): the base 4B's mean non-triviality is 0.9628 in 3B and
  78.51% in 3C; the all-408 LoRA's is 0.9122 in 3B and 91.49% in 3C. The 3C row for the 7B
  base on the decomposed surface shows 87.23% (41 of 47), the same value as the 4B all-408
  row, with a footnote that gives 59.57% for the same base.
- **Merged-GGUF `F16` versus adapter `bf16`:** the 4B all-408 model scores 87.23% as an
  adapter in `bf16` and 91.49% as a merged `F16` GGUF, on the same 47 windows; the reply
  does not explain the four-window gap.
- **Sealed holdouts untouched.** The replies state that a sealed holdout song and a sealed
  cohort file were never read or exported, and that the training and validation songs are
  disjoint from the 22 frozen gate songs. This page carries no prompts, item text or paths
  to sealed data.

## Costs (colab units, G4 at 10.05 per hour, CPU stubs at 0.26 per hour)

| track | windows | units |
|---|---:|---:|
| 3A | 7 (3 CPU stubs, 4 `G4`) | 23.311585 |
| 3B | 4 (1 CPU stub, 3 `G4`) | 19.447726 |
| 3C | 3 (1 CPU stub, 2 `G4`) | 5.929559 |
| all | 14 | 48.688870 |

Window-level rows are in the results files; totals were recomputed here from the ledger rows
(they agree with the replies' own totals: 19.448 and 5.929559).

## Studio relevance

relevance: `act` (the `IQ4_XS` versus `Q4_K_M` question for the shipping rung; the
verifier-gated distillation recipe).

Promoted: not yet.
