# Sandbox test of the 13.4 Update 2 build: FAIL on criterion 2

**Run:** 2026-10-15, 14:08:39–14:09:25 local (wall 46.0 s), under grant `publisher-5090-cu1343-sandbox-2026-10-15`. This was after the outside reviewer's round-3 green light.

**Script:** `sandbox_test-v3.py`. It passed its self-check against the frozen sha256 `af3044100ed046042f7f83cdcc0c56518afa4bb68e9bda7790ea8491d0aff1d8`.

**Build under test:** Ollama 0.40.4 with `ggml-cuda.dll` `0ebc0e61…`, CUDA 13.4 Update 2, sm_120a (`build-0.40.4-cuda-13.4.3.md`).

**Record:** `sandbox-record-cu1343.jsonl`. It's the run's own record, line for line, with one change: the PATH and CUDA_PATH values in one log line are removed for publication.

**Verdict, by the rule registered before the run:** criterion 2 fails, so **nothing is activated** and the stock backend stays.

## The four criteria

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | The new DLL loads | **pass** | The log names `…\ollama-cu1343-0404\run\lib\ollama\cuda_v13`, library CUDA and compute 12.0, and `load_backend: loaded CUDA backend from …\cuda_v13\ggml-cuda.dll`. The DLL at that path is `0ebc0e61…`, the new build |
| 2 | The outputs match stock | **fail** | 1 of 3 prompts exact; 2 diverge at positions that aren't near-ties (below) |
| 3 | No slower | **pass** | The mean sandbox/stock-A token rate is 1.194. Against stock B it's about parity |
| 4 | Cleanup | **pass** | Both servers unloaded and empty. 11500 stopped, no sandbox runner left. `memory.used` ended at 1,750 MiB against a baseline of 1,767 |

The peak `memory.used` was 7,390 MiB against a cap of 9,216, with no breach and no read errors. Model qwen3:8b, `think: false`, `num_ctx` 2048, `num_predict` 128, `temperature` 0, `top_k` 1, `seed` 42, `top_logprobs` 2.

## The outputs

**Stock against itself:** stock A and stock B, the same server twice, match token for token on all three prompts.

**The sandbox against stock A:**

| Prompt | Result | First divergence | Stock A's top two there | The sandbox's top two there | Gap in stock A | Sandbox chose |
|---|---|---|---|---|---|---|
| 0, why the sky is blue | diverges | token 15 | " When" −0.479, " Short" −1.177 | " Short" −0.704, " When" −0.776 | 0.698 | " Short" |
| 1, Fibonacci function | **exact**, 128 of 128 tokens | none | | | | |
| 2, five uses of a hammer | diverges | token 6 | line break −0.369, " or" −1.181 | " or" −0.462, line break −0.995 | 0.813 | " or" |

The rule allows a divergence only at a near-tie: stock A's top two within 0.001, with the sandbox choosing the second. Both gaps are far wider, so both prompts fail.

## How large the difference is

- **On the matching tokens,** the chosen token's log-probability differs by a mean of 0.0057, 0.0033 and 0.0006 (prompts 0, 1 and 2) and a maximum of 0.065.
- **Away from the chosen token it's larger.** At prompt 0, token 14, stock A's runner-up is at −9.21 and the sandbox's at −7.91.
- **At the two divergence points,** the distributions move by about 0.3–0.6 log-probability.

That's more than reordered floating-point sums usually give, but the cause isn't identified. The candidates are the build options (all FlashAttention quants, fatbin compression, explicit sm_120a SASS) and the toolkit (13.4 Update 2 and its cuBLAS). Neither answer is wrong. The test's bar is identity with stock, and identity isn't quality.

## Speed (tokens/s, from `eval_count / eval_duration`)

| Prompt | Stock A | Stock B | Sandbox |
|---|---|---|---|
| 0 | 150.3 | 184.0 | 181.7 |
| 1 | 159.1 | 181.8 | 181.1 |
| 2 | 145.7 | 131.5 | 179.8 |

Stock A ran first and is slower throughout. Stock B's prompt 2 is low.

A read-only load sample (performance counters, plus one `/api/ps` on each port) overlapped the run's last seconds. It can't have changed the outputs, but note it against the sandbox timings.

## Next

The diagnosis is a separate decision, with its own outside review and GPU grant. The suggested isolation is the same test on the 13.4.1 build (FA_ALL_QUANTS off, default compression), to separate build options from the toolkit, alongside a quality check of the outputs.
