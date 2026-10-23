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

## Colab A100 baseline (2026-10-23): does the same bench agree on another rig?

The 30-item bench above was run again, unchanged, on two rented Colab A100 VMs, to see whether its answers carry over
from the local RTX 5090.

**Pins (same as A1/A2):**
- offrig 7e99996a, Linux build 2f990850;
- bench30 0c88ec0f;
- Ollama 0.40.4, archive 15f31e95;
- gemma4:31b, manifest **6316f062**;
- `--jobs 1`.

**Arms:** two separate Colab A100-SXM4-40GB VMs, each running the bench through role-set's `PIN_ROLE=offrig-bench`
(role-set a621a793).

| Arm | Rig | item seconds (sum) | final_verdict == label | truncated | answer differences vs A1 | token-count differences vs A1 |
|---|---|---|---|---|---|---|
| A1 | local 5090 | 761 | 26 | 4 | — | — |
| A2 | local 5090 | 768 | 26 | 4 | 0 | 0 |
| C1 (17q) | Colab A100 VM 1 | 1,212 | 27 | 3 | 16 | 18 |
| C2 (17r) | Colab A100 VM 2 | 1,207 | 27 | 3 | 16 | 18 |

(Item seconds are the sum of each item's wall-clock time, as compare_offrig reports them. Whole-run elapsed, with load and
warm-up, was 784 s for A1, 791 s for A2, and 1,306 s and 1,301 s for C1 and C2.)

- **C1 and C2 agree exactly:** 0 answer differences and 0 token-count differences across all 30 items.
- **Colab and the 5090 agree on the verdict but not the text.** Against A1, 16 items differ, 15 of them only in the
  reasoning text. The final verdict matches on 29 of 30. The one exception, mlt-ladder-L7-15, was truncated on the 5090
  and answered `unsupported` on Colab.
- **Reading:** one request at a time (batch 1), the bench is reproducible on the same kind of GPU (5090 = 5090,
  A100 = A100). Moving to a different GPU, with its own compute kernels, changes the generated text and, rarely, a
  decision.
  - Colab results are reported as their own baseline, never pooled with the 5090's.
  - The same pattern held for llama-server in the drift study the same day: identical across A100 VMs, but different
    on another GPU and binary.
- **Speed:** the Colab A100 ran this job about 1.6× slower than the 5090 (1,207 and 1,212 item seconds, against 761).
- **The model pin needed a rebuild.** Ollama republished the `gemma4:31b` tag, so pulling the tag now gets a different
  build (manifest 17ba34c0: different weights, plus draft and vision layers) from the one the 5090 runs used.
  - The paid attempt 17l stopped at the digest guard, which refuses a model whose digest isn't the pinned one, before
    any bench call.
  - role-set #115 added a way to install the pinned model from its manifest, blob by blob. Every blob is sha-checked, a paid run
    accepts only an allow-listed registry, and nothing falls back to the tag.
  - C1 and C2 ran on that path, and pin-result records manifest 6316f062 with all four blobs checked.
  - The old blobs are kept on the rig and on the archive drive in case the registry drops them.
- **Cost,** in Colab compute units:
  - C1 2.93 and C2 4.08.
  - The first C1/C2 attempts, 16t 0.33 and 16u 0.18, were lost to a tooling fault before any bench call: the Colab
    image had no `zstd` to unpack Ollama's `.tar.zst` archive.
  - The digest-guard stop (17l) 0.33.
  - The CPU stubs 0.
  - **Total: 7.85 units.**
