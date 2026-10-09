---
id: intel-npu
title: The Intel side of the rig — NPU embeddings and iGPU cross-encoders (npu-serve)
date: 2026-10-09
kind: instrument
relevance: act
fields: [studio-tooling, gpu-computing]
tags: [instrument, npu, openvino, embeddings]
instrument_status: shipped
invoke: "E:/AI/envs/npu-openvino/Scripts/python.exe experiments/npu-probe/npu_serve.py --port 11491 [--nli]; then any Ollama embed client at http://127.0.0.1:11491 (offrig: OFFRIG_EMBED_URL=http://127.0.0.1:11491 offrig index … --model bge-base-en-v1.5)"
when: "Embedding or cross-encoder work (indexing, retrieval, NLI scoring, reranking) that should not wait for or compete with the RTX 5090. No card grant needed: it never touches CUDA or the 5090."
where: "skill ~/.claude/skills/intel-npu · rnd experiments/npu-probe (npu_serve.py, probe.py, README) · venv E:/AI/envs/npu-openvino"
---

## Summary

The Core Ultra 9 285K's NPU ("Intel AI Boost") and Intel iGPU, through OpenVINO 2026.4.
- **Embeddings on the NPU:** bge-base is about 10× the CPU at batch 1, with cosine ≥ 0.99999 against it.
- **Cross-encoders (NLI) on the iGPU:** about 6× the CPU.
- **npu-serve** speaks Ollama's embedding API, so offrig and other Ollama clients use it by changing a URL.

## Key points

- Devices are named explicitly (NPU, CPU, the iGPU found by its "Intel" name). OpenVINO also lists the 5090,
  and these scripts never select it.
- The NPU wants static shapes and batch 1. DeBERTa NLI at batch 8 hung the NPU once (it recovered).
  A second batch-8 hang, 2026-10-09: switchyard E1 lost the NPU (`ZE_RESULT_ERROR_DEVICE_LOST`, driver
  reset) at nomic-embed static 8×1024. It re-enumerated afterwards. Batch 8 isn't always fatal: bge-small and
  bge-base ran at 8×512 cleanly in the probe. The two hangs are DeBERTa at 8×512 and nomic at 8×1024. Until
  the cause is known, treat NPU batch > 1 as a hang risk and run it last, in its own block.
- **NPU health check** (after a hang, before the next NPU booking): `probe.py --batches 1` from
  `experiments/npu-probe`, in the NPU venv. It passes when every NPU row has no error, embedding minimum
  cosine is ≥ 0.9999, the NLI argmax agrees with the CPU, and each NPU median is within 1.5× of the
  2026-10-09 probe receipt.
- INT8 weights don't speed up small encoders. Quantization matters for putting LLMs on the NPU (OpenVINO
  GenAI, INT4).
- "-NPU2" model builds on Hugging Face (FastFlowLM) are for AMD XDNA2 NPUs, not this Intel NPU.

## Studio relevance

- **act:** offrig's index could embed on the NPU instead of a CPU-only Ollama, at about 3× the speed
  end to end. It's not switched: the Publisher reviews that design change after a retrieval-quality benchmark.
- **next:** a no-LLM verifier floor (NLI on the gold sets), and embedders and cross-encoders fine-tuned on
  studio pairs, trained on the 5090 and served from the Intel side. See the experiment README.
- Status: works and is measured, but it lives in an experiment folder, not its own repo. It becomes a repo when
  offrig or another tool depends on it.

## Verified device facts and next models (2026-10-09)

- **OpenVINO's live enumeration on this rig** (Kimi, read-only, OpenVINO 2026.4.1):

  | id | name | type | vendor |
  |---|---|---|---|
  | `CPU` | Intel(R) Core(TM) Ultra 9 285K | | |
  | `GPU.0` | Intel(R) Graphics (iGPU) | INTEGRATED | 0x8086 |
  | `GPU.1` | NVIDIA GeForce RTX 5090 (dGPU) | DISCRETE | 0x10de; never use |
  | `NPU` | Intel(R) AI Boost | | 3720 |

  Decide the iGPU by vendor 0x8086 plus INTEGRATED, not by its name.
- **Advertised vs measured:** the NPU advertises 13.1 int8 TOPS but measured about 2.4, because it's
  transfer-bound. Routing tables claim measured numbers only.
- **Intel's NPU-optimized models** (the OpenVINO HF collection "LLMs optimized for NPU": channel-wise
  `-int4-cw-ov` builds) and **Qwen3-Embedding-0.6B** (NPU support added in OpenVINO 2026.0) are switchyard
  experiments E2 and E3. Avoid group-quant IRs on the NPU (reported compiler crashes).
- **The SigLIP checkpoint** `google/siglip2-so400m-patch14-384` is `model_type: siglip`, not `siglip2`.
  optimum-intel 2.2.0 exports it, through `export_from_model` with a custom vision-only config. Kimi's
  `npu-buildout` branch has the details.
