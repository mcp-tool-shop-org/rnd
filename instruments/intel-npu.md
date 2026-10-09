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
where: "rnd experiments/npu-probe (npu_serve.py, probe.py, README) · venv E:/AI/envs/npu-openvino"
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
