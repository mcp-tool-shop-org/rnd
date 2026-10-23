# offrig --jobs 30-item measurement: results (2026-10-23, 5090, plan f680591b, runner 8ff170ba, offrig 7e99996a)

| Arm | jobs / parallel / KV | elapsed s | items/h | vs A1 | final_verdict == label | truncated | on card | peak VRAM (card total) |
|---|---|---|---|---|---|---|---|---|
| A1 | 1 / 1 / f16 | 784.2 | 137.7 | 1.00x | 26 | 4 | yes (20.28 GB model) | 25,575 MiB |
| A2 | 1 / 1 / f16 | 790.7 | 136.6 | 0.99x | 26 | 4 | yes | 25,564 MiB |
| B | 2 / 2 / f16 | 492.6 | 219.3 | **1.59x** | 27 | 3 | yes (21.54 GB model) | 29,266 MiB |
| C | 4 / 4 / f16 | — | — | — | — | — | skipped: estimate 35.8 GiB > 26 | — |
| D | 4 / 4 / q8_0 + FA | — | — | — | — | — | skipped: estimate 29.0 GiB > 26 | — |

Answer changes, per field (of 30 items):

| Field | A2 vs A1 (noise floor) | B vs A1 |
|---|---|---|
| final_verdict | 0 | 1 |
| model_verdict | 0 | 1 |
| evidence_quote | 0 | 2 |
| reasoning | 0 | 15 |
| error_code | 0 | 1 (one A1 truncation answered in B) |

- **The noise floor is zero.** A single stream at temperature 0 / seed 0 is byte-identical run to run on every field.
- **B changes answers beyond it:** 1 verdict, 2 quotes and 15 of 30 reasoning texts. Two requests decoding together
  change the numerics (batched kernels), which is the batching-drift effect. It isn't noise.
- **Decision rule** (at least 1.5x, no offload, answers not differing more than A2): throughput passes (1.59x),
  offload passes, answers FAIL. **Verdict: no `--jobs` above 1 on any pinned study run** (teacher legs included).
  `--jobs 2` is fine for unpinned work where speed matters more than byte-identity.
- **Measured KV cost:** B − A1 = **3,691 MiB per extra sequence**, against the theory of 1,440. Ollama caches gemma4
  far above the sliding-window estimate. B itself peaked at 28.6 GiB card total, over the 26 GB plan line (B wasn't
  gated; record it). Card totals include about 1.9 GB of other processes' baseline.
- **Card:** utilization 87 / 86 / 80 % mean, max 74 °C, mean 505 / 507 / 484 W, max 553 W. All in bounds.
- **Defects on record:**
  1. Attempt 1 failed in A1 on offrig's 16 s cold-load timeout (ticket filed).
  2. In attempt 2, a bug in my edit to the C/D gate (an escaped newline became a literal one inside an f-string)
     crashed the estimator. The runner logged "does not fit" with an empty estimate. The skips stand on the corrected
     estimates above, which are computed from the run's own smi files; the logged reason was wrong.
