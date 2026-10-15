# Diagnosis v6 result: the 13.4 backend's difference from stock is cuBLAS (2026-10-15)

**Decision, by the rule set before the run:** the studio's CUDA 13.4 Update 2 backend (S2) is **eligible** for
activation.
- Activation is a separate go, under its own plan, with the stock CUDA 13.0 backend kept as a switchable fallback.
- Nothing is activated by this result.

## Why this run

The 2026-10-15 sandbox test (`sandbox-result-cu1343.md`) failed its identity criterion. The studio build matched stock
on one prompt in three and forked on the other two, at points that weren't near-ties. The ab_dataminer then showed
the two builds disagreeing on the very first generated token of every prompt. That pointed at the prompt's prefill,
not at drift built up during decoding.

This run was built to find the cause. It isolates three candidates: the cuBLAS library, the FlashAttention kernels,
and the rest of the natively compiled kernels.

## The arms

The model is qwen3:8b Q4_K_M on Ollama 0.40.4 (llama.cpp b11521), on an RTX 5090 with driver 617.42.

Each GPU arm ran as a sandbox server on port 11500 from its own copy of the Ollama tree, one arm at a time:

| arm | ggml-cuda.dll | cuBLAS | FlashAttention |
|---|---|---|---|
| S0 | stock: PTX only (compute_75 to compute_120a), compiled by the driver at load | stock 13.0.x (file 6.14.11.1300) | auto |
| S1 | studio, CUDA 13.4.1: sm_120a SASS | 13.4.1's | auto |
| S2 | studio, CUDA 13.4.3: sm_120a SASS, all FA quants, speed compression | 13.4.3's, libcublas 13.8.0.4 (file 6.14.11.1380) | auto |
| S0_cb1343 | stock | 13.4.3's | auto |
| S0_nofa | stock | stock | off |
| S2_nofa | studio 13.4.3 | 13.4.3's | off |
| REF | stock, running qwen3:8b-q8_0 | stock | auto |
| S0p (S0′) | stock, repeated last | stock | auto |

**Prompts and settings:** 15 prompts (the 3 from the sandbox test, plus 12 with task checks), greedy decoding with
seed 42, a 2,048-token context, 64 new tokens, and the top 10 log-probabilities per step.

**The harness:** `diag/diag_test.py` v6 (sha256 18a5f757…23c6c), run with abmine.py f87f0daf…b0778, both frozen
after outside review.

## The rule (pre-registered)

S2 is eligible only if all three hold, and only if stock repeats itself (S0 = S0′):
- **(a)** S2 matches S1 token for token on all prompts;
- **(b)** the S0 vs S2 shift is attributed, by the arm matrix, to the cuBLAS 13.0 → 13.4 change or to native sm_120a
  kernels;
- **(c)** S2 has no task failures, and its chosen-token MAE against REF is within 0.005 nats of S0's.

## What happened

The run took 167.7 s under one GPU grant, with no breach, no CPU stop and no error record:

| check | result |
|---|---|
| S0 = S0′ | **yes, bit for bit**: every token and every top-10 log-probability, all 15 prompts |
| (a) S2 = S1 | **yes, bit for bit** |
| (b) the shift | S0 vs S2: identical on 11 of 15 prompts; forks on orig_sky (step 15, Δz 0.770), orig_hammer (step 6, Δz 1.345), prose_library (step 1, Δz 0.693) and prose_advice (step 37, Δz 0.188) |
| (b) attribution | **cuBLAS 13.0 → 13.4**, the only attribution that held: **S0_cb1343 = S2 bit for bit** |
| (c) task failures in S2 | 0 of 15 |
| (c) MAE against REF | S0 0.0246, S2 0.0275: a difference of 0.0029, within 0.005 |
| criterion 1 (each arm's log) | all 8 arms: their own tree's DLL, compute 12.0, the expected FA resolution, KV cache f16 |

**Step-0 Δz between S0 and S2 is nonzero on every prompt:** from 0.073 to 0.853, with a mean of 0.469.

**The sandbox test's two forks were reproduced to the digit** (Δz 0.770 and 1.345), on another day's server starts and
under another harness.

**Pairs that matter:**

| pair | identical prompts | mean \|step-0 Δz\| |
|---|---|---|
| S0 vs S1, S0 vs S2, S0 vs S0_cb1343 | 11/15 | 0.469 |
| S1 vs S2, S2 vs S0_cb1343 | 15/15, bit-identical | 0 |
| S0_nofa vs S2_nofa | 14/15 | 0.599 |
| any arm vs REF (q8_0) | 7/15 | about 4.0 |

**Card memory peaked** at 7,955 MiB over the six S arms before REF (cap 9,216), and at 10,991 MiB on REF (cap
14,336). The sampler keeps one running peak, so S0′'s own peak, after REF, isn't separable. It ended back at
2,230 MiB, with both servers empty and no runner left.

## How to read it

**Everything is in cuBLAS.**
- Putting only CUDA 13.4.3's cuBLAS into stock Ollama reproduces the studio build bit for bit.
- Holding cuBLAS at 13.4 and swapping ggml-cuda.dll changes nothing for this model's outputs. The three versions are
  stock PTX compiled by the driver, 13.4.1 SASS, and 13.4.3 SASS with all FA quants.
- So the natively compiled kernels (MMQ, MMVQ, MMVF, the FlashAttention kernels, norms, RoPE) aren't where the
  difference comes from.

**Where cuBLAS runs.** In this model one weight is not quantized: attn_v.weight is f16 in all 36 layers.
- Reading the prompt routes that projection to `cublasGemmEx`, with f16 accumulation (`CUBLAS_COMPUTE_16F`). The
  prompts here are 24–43 tokens, all over the 16-token limit of ggml's own f16 kernel.
- Every quantized matrix goes to ggml's own kernels, and generating each new token uses ggml's own vector kernel.
- So cuBLAS touches the prompt only, which is why the builds already disagree at step 0. → `diag-v6-pre-run-notes.md`,
  written before the run.

**Why 13.0 and 13.4 differ.** The outside reviewer read NVIDIA's cuBLAS 13.2 release notes as retuning the fp16 kernels
for this chip's family (GB202). A different kernel or split for the same GEMM changes the order of the fp16 sums, so
the low bits change in every layer. `[unverified here: the release notes weren't re-read for this write-up]`

**With FlashAttention off,** the prompt's attention products also become cuBLAS GEMMs. Those go through the batched
pointer-array path, because qwen3 has 32 query heads and 8 KV heads. That's why the FA-off pair differs too. Their mean
step-0 Δz is a little higher than with FA on (0.599 against 0.469).

**Neither build is closer to the q8_0 reference.**
- At the four forks, the reference sided with stock once (orig_hammer) and with S2 once (prose_library). At the other
  two it had already diverged earlier.
- The chosen-token MAE puts the two builds 0.003 nats apart.

**REF is a closeness yardstick, not a quality oracle.** The q8_0 reference failed two task checks that every Q4 arm
passed:
- math_sum: it explained the arithmetic-series formula and hit the 64-token limit before giving 210;
- json_price: it wrote `"price": "4 dollars"` where the check wants 4.

Both are about following the format, not about knowing the answer.

## Corrections to the outside reviewer's notes (none changes the result)

- **Stock's first arm took 21 s against 14 s for S2.** The reviewer put that down to the driver compiling stock's PTX
  on first use. But S0′, also stock and also compiled by the driver, took 14 s. The 21 s was the first arm's cold load
  of the model.
- **With FA off, KQ and KQV go to cuBLAS during prefill only.** Decoding one token at a time uses ggml's own MMVF
  kernel.
- **S1 holds sm_120a SASS, not plain sm_120** (cuobjdump: 144 entries). The 12X → 12Xa rewrite applies to every build.

## Caveats

- One model, 15 prompts, 64 greedy tokens, and prompts of 24–43 tokens. A model with more f16 or bf16 weights, or
  longer prompts, routes more work through cuBLAS and could show larger differences.
- **Untested prediction:** a prompt of 16 tokens or fewer keeps that projection in ggml's own kernel, so it should
  show no step-0 difference at all. It's a cheap check if the mechanism ever needs confirming.
- "The native kernels change nothing" is shown for these inputs on this model. It isn't a general equivalence proof.
- The difference is between two correct cuBLAS versions. Identity with stock was the bar, and identity isn't quality.

## The v5 abort, and what changed

The first run, of v5, stopped after 8.5 s at the first arm's start record. Nothing had loaded, and the GPU wasn't
used:
- **The bug:** `record("arm_start", ..., kind=kind)` collided with `record(kind, **data)`.
- **How long it had been there:** it was present since v4, and no review caught it.
- **Why the tests missed it:** they reached `run_arm` only up to its DLL check, which exits before that line.

v6 renames the field to `arm_kind`. It also adds an offline dry run (`diag/test_diag_test.py`, class `DryRun`) that
runs the real `main()` through all 8 arms, the verdict and the analysis file:
- **Faked:** nvidia-smi, typeperf, PowerShell, both Ollama servers and each arm's process.
- **Real:** the self-check, the model-pin check and the sampler thread.
- **Negative control:** against v5, it fails on the same TypeError.

It runs in the rnd suite (`tests/test_diag_harness.py`), so this class of bug fails in CI, not under a GPU grant.

Also:
- v5 should have gone back to the outside reviewer before it was frozen. The v6 review covered v4 → v5 as well (round
  2).
- The order now is: fixes, then the reviewer reads the fixed diff, then the Publisher's check, then the freeze, then
  the grant.

## Outside review (Argon)

| round | outcome |
|---|---|
| v4 | three fixes: FA-off resolution, a memory cap per arm, the FA-off arms on all prompts |
| v6, round 1 | the rename and the dry run approved |
| v6, round 2 | the three fixes confirmed as applied, and the green light stands; agreed with two rig-check corrections |
| after the run | agreed with the reading: the isolation is clean and the mechanism holds |

## Files

| file | what it is |
|---|---|
| `diag/diag_test.py`, `diag/diag_test.FROZEN.sha256` | the frozen v6 harness, byte for byte (`-text` in `.gitattributes`) |
| `diag/test_diag_test.py` | its tests: evidence, caps, verdict combinations and the offline dry run |
| `diag_test-v3-to-v4.diff`, `diag_test-v4-to-v5.diff`, `diag_test-v5-to-v6.diff` | each revision's change |
| `diag-record-v6.jsonl`, `diag-analysis-v6.json` | the run's record, and the ab_dataminer's analysis of it |
| `diag-record-v5-aborted.jsonl` | the aborted v5 run's record |
| `diag-v6-pre-run-notes.md` | the cuBLAS routing and the known-issues check, written before the run |
| `argon-review-diag-v6.md`, `-round2.md`, `-round2-additions.md` | the review briefs as sent |

The arm trees, DLLs and server logs stay on the rig. Every DLL is pinned by sha256 in the harness's `ARMS`.
