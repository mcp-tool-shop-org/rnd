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
- The NPU wants static shapes and batch 1. `npu_serve.py` compiles each embedder at lengths 128, 256 and
  512, and sends each input to the smallest that fits.
- Don't push DeBERTa-sized cross-encoders through the NPU at batch 8; use the iGPU.
- Models named "…-NPU2" on Hugging Face (FastFlowLM) are for **AMD XDNA2** NPUs, not Intel. They don't run
  here.

## The tool: `npu_serve.py`

A loopback service on port 11491 that answers Ollama's embedding API (`/api/embed`, `/api/tags`,
`/api/version`), plus `/api/nli` for the cross-encoder. Anything that embeds through Ollama can use the NPU by
pointing its URL here. See `instruments/intel-npu.md` for when to reach for it.

```bash
E:/AI/envs/npu-openvino/Scripts/python.exe npu_serve.py --port 11491 --nli
OFFRIG_EMBED_URL=http://127.0.0.1:11491 offrig index <paths> --model bge-base-en-v1.5 --project <dir>
```

**offrig's default is not changed.** Moving its embedder from the CPU Ollama to the NPU is a design change
that the Publisher reviews: a design note and a PR, the model and dimension pinned so existing indexes stay
valid, or a forced `--rebuild`. It waits for the retrieval-quality measurement.

## Next: measure, then train it to fit the studio

1. **A retrieval benchmark from our own gold.** Every grounded claim names its source file at a pinned
   commit. Index those repos at those commits, query with each claim, and score recall@5 by file. Run it for
   nomic-embed-text (today's default), bge-base and bge-small. Pre-register it before it runs.
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
