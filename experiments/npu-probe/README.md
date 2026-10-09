# The Intel side of the rig: NPU and iGPU

The Omen 45L's Core Ultra 9 285K has an NPU ("Intel AI Boost", driver 32.0.100.5540, August 2026) and an
Intel iGPU. Until 2026-10-09 nothing in the studio used either. They sit beside the RTX 5090, so work on them
**never waits for a card grant** and never competes with the judges, training or calibration on the 5090.

Everything here runs through OpenVINO 2026.4 in its own venv, `E:/AI/envs/npu-openvino` (Python 3.12, CPU-only
torch). OpenVINO also lists the 5090 as a GPU device, so every script here names its devices: `NPU`, `CPU`,
and the iGPU found by its "Intel" name. None of them can reach the 5090.

## Probe results, 2026-10-09 (`probe.py`, `results/2026-10-09-probe.json`)

Each model was timed on the NPU and the CPU at sequence length 512, and the NPU's outputs were checked
against the CPU's. The CPU was not idle: the 5090 was running another session's judge, so CPU times are
pessimistic.

| Model | Job | NPU | CPU | NPU vs CPU output |
|---|---|---|---|---|
| bge-small-en-v1.5 (33M) | embedding, batch 1 | 33.8 items/s | 11.2 | cosine 1.00000 |
| bge-base-en-v1.5 (110M, 768-d) | embedding, batch 1 | **20.5 items/s** | 2.1 | cosine 0.99999 |
| bge-base-en-v1.5 | embedding, batch 8 | 13.8 items/s | 9.8 | cosine 0.99999 |
| nli-deberta-v3-base | NLI, batch 1 | 3.7 items/s | 3.8 | logits within 0.009 |
| nli-deberta-v3-base | NLI, batch 8 | **device hung** (`DEVICE_LOST`), recovered | 4.2 | — |

The NLI model runs better on the **Intel iGPU**: 11.9 items/s at batch 8, against the CPU's 1.8, with the
same answers.

**Through offrig, unchanged** (`OFFRIG_EMBED_URL` pointed at `npu_serve.py`): indexing the R&D library's 46
entries (201 chunks) took **10 s** with bge-base on the NPU. The CPU-only Ollama offrig uses today took
**31 s** with nomic-embed-text. Both give 768-dimension vectors, but they are different models, so retrieval
quality still needs measuring (below).

**Quantization:** INT8 weights on bge-base gave no speed-up (25.5 against 26.0 ms per item, cosine 0.9998). A
110M encoder isn't limited by memory, and the NPU already computes in 16-bit. INT8 and INT4 are what put
*large* models on an NPU (LLMs through OpenVINO GenAI), not what speeds up small encoders.

**Lessons:**
- The NPU wants static shapes and batch 1. `npu_serve.py` compiles each embedder at a per-model length
  ladder — bge at 128/256/512, nomic at 128/256/512/1024/2048 — and sends each input to the smallest that
  fits. nomic's top rung is measured, not guessed: the longest offrig chunk over both pinned benchmark
  corpora is 1619 nomic tokens (the CJK README translations are the tail), per
  `results/2026-10-09-nomic-chunk-lengths.json`, so nothing in either corpus truncates.
- Don't push DeBERTa-sized cross-encoders through the NPU at batch 8; use the iGPU.
- Models named "…-NPU2" on Hugging Face (FastFlowLM) are for **AMD XDNA2** NPUs, not Intel. They don't run
  here.

## Raw engine rates (`mac_bench.py`, 2026-10-09)

Plain OpenVINO graphs with no model behind them: square matmuls, and a 3×3 convolution. INT8 is marked with
FakeQuantize, OpenVINO's way of asking for integer kernels. Results are in TOPS (10¹² operations a second).

**One call** (`results/2026-10-09-mac.json`):

| case | NPU fp16 | NPU int8 | iGPU fp16 | iGPU int8 | CPU |
|---|---|---|---|---|---|
| matmul 1024 | 0.82 | 0.82 | 0.93 | 0.92 | 0.31 |
| matmul 2048 | 1.25 | 1.51 | 1.22 | 1.06 | 0.37 |
| matmul 4096 | 1.87 | 2.38 | 1.70 | 1.71 | 0.37 |
| conv 3×3, 64→64, 224² | 0.48 | 0.47 | 0.53 | 0.51 | 0.11 |

**Eight matmuls chained in one graph,** so one transfer feeds 8× the arithmetic (medians of five
repeats, devices interleaved, per-case compile deadline; `results/2026-10-09-mac-chain.json`):

| case | NPU fp16 | NPU int8 | iGPU fp16 | iGPU int8 |
|---|---|---|---|---|
| 8 × 2048 | 2.80 | **5.20** | 2.30 | 2.09 |
| 8 × 4096 | compile timeout (5/5 at 180 s) | **5.26** | 2.41 | 2.23 |

**What it means:**
- **A single call is mostly overhead,** from dispatch and moving data. At 1024 the NPU takes 2.6 ms in either
  precision, where ~13 TOPS of pure compute would need ~0.2 ms. Chaining recovers it on the NPU, where INT8
  roughly triples, but barely moves the iGPU.
- **INT8 pays on the NPU for large matmuls,** about 2× FP16 once amortized, unlike the small encoders above.
  On the iGPU, INT8 ≈ FP16: the INT8 markers seem to compile to the same FP16 kernel.
- **Even amortized, about 5 INT8 TOPS** is roughly 40% of Intel's ~13 TOPS INT8 figure. Against the host CPU's
  flat ~0.37, the honest comparison for offloading, the NPU is 5–15×. Against the 5090 it is ~100× smaller.
  It's for the always-on small jobs, not big matmuls.
- **The conv shape is too small** to fill anything. It shows only that this shape is overhead-bound, not
  that the NPU is weak at convolutions.
- **The FP16 chain at 4096 stalls the NPU compiler** (eight 64 MB FP32 constants): 5/5 repeats hit the 180 s
  compile deadline on the clean rerun. That case hung the very first chain run; the bench now records a
  bounded timeout and moves on.

**Caveats, from Kimi K3's review (2026-10-09):**
- The chained numbers come from a **clean rerun on an idle NPU** in a Publisher-logged window (2026-10-09,
  ~02:00), after an earlier run the same night was contended by a second session and showed 8–11% spread
  (kept as `results/2026-10-09-mac-chain-contended.json`). Clean-run medians moved ≤5% from the contended
  ones; per-repeat spread within the clean run is 3–13% (worst on first-touch repeats). Every repeat's
  samples are in the receipt.
- **The NPU is one exclusive device**, like the 5090: two sessions on it slow each other and spoil timings.
  See the skill's rule.
- **The float64 slip:** under NumPy 2 (NEP 50), `float32_array / np.sqrt(n)` is float64, and the float64
  constant failed OpenVINO's MatMul type check. It was loud, not silent, so no receipt holds wrong numbers.
  `mac_bench.py` now asserts every constant is float32.

## The tool: `npu_serve.py`

A loopback service on port 11491 that answers Ollama's embedding API (`/api/embed`, `/api/tags`,
`/api/version`, `/api/show`), plus `/api/nli` for the cross-encoder and `/health` for device status.
Anything that embeds through Ollama can use the NPU by pointing its URL here. See
`instruments/intel-npu.md` for when to reach for it.

```bash
E:/AI/envs/npu-openvino/Scripts/python.exe npu_serve.py --port 11491 --nli
OFFRIG_EMBED_URL=http://127.0.0.1:11491 offrig index <paths> --model bge-base-en-v1.5 --project <dir>
```

**Hardening (0.2.0):**
- Models are pinned (repo + revision) in `MODELS`. `nomic-embed-text` is served straight from the pinned
  ONNX `nomic-ai/nomic-embed-text-v1.5` @ `e9b6763` (`onnx/model.onnx`), mean pooling over the attention
  mask then L2-normalize; bge keeps CLS pooling. The server adds **no task prefixes** — offrig adds
  `search_document: ` / `search_query: ` on its side.
- `/api/tags` reports each model's repo, revision and IR digest (file sha256 for ONNX, graph digest for
  optimum exports); `/api/show` reports dim and pooling.
- Fail loud, never silent: an inference error is a 503, a `DEVICE_LOST` latches the device until restart
  (`/health` reports it), and there is no CPU fallback. Unknown models are 404; bodies and batch sizes are
  bounded. `tests/test_npu_serve.py` drives all of this with fake models — no NPU needed.

**Cold start → embed → stop, recorded** (`results/2026-10-09-npu-serve-smoke.json` and
`results/2026-10-09-npu-serve-2048-probe.json`, both in Publisher-logged NPU windows): five-bucket nomic
loads on the NPU in ~53 s; the corpus-max 1,619-token chunk dispatches to the 2,048 rung (0.82 s first
call, 0.51 s warm) and matches the CPU's OpenVINO run at cosine 0.99947 — device-numerics drift grows a
little with sequence length (≥ 0.99999 at 512), which the parity receipt will show by length. Health
stayed clean (no `DEVICE_LOST`), and the port was released on stop. The 2,048 compile risk is retired.
- Lifecycle drafts: `start_npu_serve.ps1`, `stop_npu_serve.ps1`, `npu-serve-task.xml` are drafts —
  **not registered** — pending Publisher ledger rules for boot-time device grants.

**offrig's default is not changed.** Moving its embedder from the CPU Ollama to the NPU is a design change
that the Publisher reviews: a design note and a PR, the model and dimension pinned so existing indexes stay
valid, or a forced `--rebuild`. It waits for the retrieval-quality measurement.

## Next: measure, then train it to fit the studio

1. **A retrieval benchmark from our own gold,** pre-registered in `retrieval-benchmark.md`: recall@5 by file,
   for every grounded claim, against role-os and offrig at their pinned commits.
   - **Option C goes first: nomic itself on the NPU.** nomic v1.5 ships ONNX files, so OpenVINO runs it
     with no remote code: **31 ms per item on the NPU, against 122 ms on the CPU**, cosine 1.0 (minimum and
     mean) against the same ONNX on the CPU (revision `e9b6763`).
   - **It still has to match Ollama's GGUF nomic** at a minimum cosine ≥ 0.995 before it counts as a device
     change with no reindex. That check loads the CPU, so it runs after the overnight calibration.
   - The remote modeling code (nomic-bert-2048 @ `7710840`) was read anyway. Its only risky call,
     `torch.load`, is reached only for `.bin` weights, and this revision ships safetensors.
2. **Fine-tune the embedder on studio pairs:** claim to evidence chunk, and README sentence to the code it
   describes, from the gold tune splits only. Train on the 5090 (a short grant), export to OpenVINO, and serve
   from the NPU. It must beat its base model on the benchmark's held-out half to replace it.
3. **A no-LLM verifier floor:** score the NLI cross-encoder on the calibration gold, scored like the LLM
   candidates. Then fine-tune it on the tune split only, as a small code-claim checker, and score it once on
   held-out. If it gets close to the LLMs on grounded claims, it becomes a cheap pre-filter on the iGPU.
4. **Watch:** nomic-embed-text-v2-moe (multilingual, 768-d, Apache-2.0; it needs its publisher's remote code,
   so pin and read it first, and its routing may not compile for the NPU); OpenVINO GenAI INT4 LLMs on the
   NPU as an always-on small helper; nomic-embed-multimodal-3b for searching sprite and screenshot pages (on
   the 5090, and its licence needs checking).
