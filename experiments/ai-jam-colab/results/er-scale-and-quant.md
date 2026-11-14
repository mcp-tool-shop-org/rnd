# 3C: scale and licence ablation, and the 12-cell GGUF survival

Source: Antigravity reply, 2026-11-13 (UTC), final window `jam-er-sq-g4-2`.
`[unverified]`: the reply's own figures; no record here re-ran them.

## Setup

- 47 held-out validation windows (35 in the publishable subset), greedy decoding, the same
  split as 3B. The reply states a disjointness guard ran before every run and the sealed
  holdout song was never read.
- **Ablation (bf16):** `Qwen3-4B-Instruct-2507` and `Qwen2.5-7B-Instruct`, each trained on
  the 129 publishable rows or on all 408 verified rows, on the one-shot `full_voiced`
  surface with no inference-time voicing helper.
- **GGUF survival:** the two all-408 LoRAs merged on GPU, exported to `F16` GGUF, quantised to
  `Q8_0`, `Q6_K`, `Q5_K_M`, `Q4_K_M` and `IQ4_XS` (no importance matrix) with the same pinned
  `llama.cpp` revision as 3A, evaluated with `llama-server` at temperature 0.

## 1. Scale and open-licence ablation (bf16)

| Model | Corpus | Train rows | full_voiced pass@1 (n=47) | Publishable pass@1 (n=35) | Chord fidelity | Non-triviality | Chromatic ratio |
|---|---|---:|---:|---:|---:|---:|---:|
| 4B | base (3B reference) | 0 | 6.38% (3/47) | 5.71% (2/35) | 48.14% | 78.51% | 0.0912 |
| 4B | publishable-only LoRA | 129 | 65.96% (31/47) | 60.00% (21/35) | 94.41% | 95.21% | 0.0644 |
| 4B | all-verified LoRA (3B) | 408 | 87.23% (41/47) | 88.57% (31/35) | 98.67% | 91.49% | 0.0663 |
| 7B | base, full_voiced | 0 | 0.00% (0/47) | 0.00% (0/35) | 31.24% | 56.78% | 0.0831 |
| 7B | base, abc_decompose reference | 0 | 87.23% (41/47)* | 88.57% (31/35)* | 100.00%* | 83.05% | 0.0955 |
| 7B | publishable-only LoRA | 129 | 65.96% (31/47) | 71.43% (25/35) | 94.68% | 92.82% | 0.0644 |
| 7B | all-verified LoRA | 408 | 93.62% (44/47) | 97.14% (34/35) | 99.20% | 90.43% | 0.0663 |

\* The reply's footnote says that on `abc_decompose` the voicing helper supplies chords and
gives 59.57% as the 100%-measure-complete rate for the base 7B. That does not match the 87.23%
shown in the row; the row is copied as written and flagged (see the experiment README).

Reply's takeaways: the base 7B scores 0 of 47 on `full_voiced`; the 129 open-licence rows
alone lift both models to 65.96% with chord fidelity about 94.5%, so an all-open-licence
release is viable; tripling the data (129 to 408) adds 21.28 points on the 4B and 27.66
points on the 7B (recomputed here: 87.23 - 65.96 = 21.27 and 93.62 - 65.96 = 27.66; the
reply's 21.28 is a rounding difference).

## 2. GGUF quantisation survival, `full_voiced` (n=47)

`Qwen3-4B-Instruct-2507` + all-408 merged:

| Rung | Size | pass@1 | Delta vs F16 | Publishable (n=35) | Parseable | Chord fidelity | Eval wall (s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| F16 | 8.05 GB | 91.49% (43/47) | 0.00 pt | 91.43% (32/35) | 47/47 | 98.94% | 28.90 |
| Q8_0 | 4.28 GB | 89.36% (42/47) | -2.13 pt | 91.43% (32/35) | 47/47 | 98.94% | 20.63 |
| Q6_K | 3.31 GB | 89.36% (42/47) | -2.13 pt | 91.43% (32/35) | 47/47 | 98.94% | 19.87 |
| Q5_K_M | 2.89 GB | 85.11% (40/47) | -6.38 pt | 91.43% (32/35) | 47/47 | 98.94% | 18.81 |
| Q4_K_M | 2.50 GB | 68.09% (32/47) | -23.40 pt | 71.43% (25/35) | 45/47 | 95.28% | 18.67 |
| IQ4_XS | 2.29 GB | 91.49% (43/47) | 0.00 pt | 91.43% (32/35) | 47/47 | 98.67% | 16.79 |

`Qwen2.5-7B-Instruct` + all-408 merged:

| Rung | Size | pass@1 | Delta vs F16 | Publishable (n=35) | Parseable | Chord fidelity | Eval wall (s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| F16 | 15.24 GB | 89.36% (42/47) | 0.00 pt | 91.43% (32/35) | 47/47 | 98.94% | 41.73 |
| Q8_0 | 8.10 GB | 93.62% (44/47) | +4.26 pt | 97.14% (34/35) | 47/47 | 99.47% | 25.42 |
| Q6_K | 6.25 GB | 91.49% (43/47) | +2.13 pt | 94.29% (33/35) | 47/47 | 99.20% | 23.41 |
| Q5_K_M | 5.44 GB | 93.62% (44/47) | +4.26 pt | 94.29% (33/35) | 47/47 | 99.20% | 21.66 |
| Q4_K_M | 4.68 GB | 91.49% (43/47) | +2.13 pt | 91.43% (32/35) | 47/47 | 98.40% | 19.90 |
| IQ4_XS | 4.25 GB | 95.74% (45/47) | +6.38 pt | 97.14% (34/35) | 47/47 | 99.47% | 18.05 |

Reply's reading: the 4B's `Q4_K_M` cliff (91.49% to 68.09%, two windows no longer parse)
is absent at `IQ4_XS`, which is 211 MB smaller and matches `F16`; on the 7B `IQ4_XS` is the
best cell of the track. With 3A (where `Q4_K_M` lost 2.16 points in 5 of 5 seeds and
`IQ4_XS` recovered 91% of that) the reply calls this "two-architecture, two-task proof"
and recommends `IQ4_XS` (or `Q5_K_M`) in place of `Q4_K_M`. R&D's reading: a consistent
direction across two models and two tasks, but it is one quantiser revision, no importance
matrix, 47 windows (one window is 2.13 points, so the 7B's +6.38 for `IQ4_XS` is three
windows), and the merged `F16` of the 4B (91.49%) differs from its `bf16` adapter score
(87.23%) by four windows without explanation. "Proof" overstates it; "supports" is fair.

## Windows and units

| Window | Card | Elapsed (s) | Units | Outcome |
|---|---|---:|---:|---|
| `jam-er-sq-cpustub-2` | CPU high-mem | 659.782 | 0.047651 | ok; 16 of 16 dry acceptance (a first stub was refused before opening, 0 units) |
| `jam-er-sq-g4-1` | G4 | 159.049 | 0.444010 | input hash mismatch on the adapter manifest (case-insensitive versus case-sensitive file sort); pin updated |
| `jam-er-sq-g4-2` | G4 | 1,947.904 | 5.437898 | ok; 16 of 16 units |

Total 5.929559 units (recomputed; matches the reply). The reply also reports 0 leaks and a
balance of 1,699.20 units after the run.

## Kept on the rig (not filed)

The summary JSON (14,570 B, sha256 `a5c2847839e9d514f77840dbe6fa97b4bae2599f113aab8db844aff241cef3c8`),
the per-item JSON (214,923 B, sha256 `40b669d38d68947d57e63b4d0c8f4d7d35620a9dab778e23e45bc36672f8f405`),
the progress JSONL.gz (5,841 B, sha256 `473146d0ef49e5ecc6a63932852d8e7961b07d108c91f5922b0b699b474e5fa1`), and five
trained adapters (the 4B and 7B publishable-129 and the 7B all-408 listed with sha256
`53d46524...`, `84a7f31e...` and `c0b43e79...`). Two scripts' hashes the reply gives:
`vm_er_scale_and_quant.py` `7608dc81...`, `run_er_scale_and_quant.py` `a3fa14c0...`.
