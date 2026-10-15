# Diagnosis v5: notes written before the run (2026-10-15)

Frozen: diag_test.py c787f0e92cc8b43a39212ef3c36024efdfd3cfd35abcacf3a83c7d07e27efb7f, abmine.py
f87f0daf0736fe2131e87820b1a3696ee7e1457ce8697352157763443f7b0778 (rnd 40f7400). These notes were written
after the freeze and before the grant, so nothing here was shaped by the run's records.

## Where cuBLAS runs (llama.cpp b11521, qwen3:8b Q4_K_M, RTX 5090 compute 12.0)

- The model's matrices are q4_K or q6_K except attn_v.weight, which is f16 in all 36 layers (GGUF header).
- On 12.0, quantized matmuls go to MMQ/MMVQ (mmq.cu:409).
- The f16 V projection depends on the step:
  - prefill: 27-30 tokens, over MMF's 16-column limit (mmf.cu:176), so it runs as cublasGemmEx with f16 in and out,
    CUBLAS_COMPUTE_16F and CUBLAS_GEMM_DEFAULT_TENSOR_OP (ggml-cuda.cu:1552);
  - decode: the native MMVF kernel.
- So cuBLAS touches prefill only, with FA on or off. Prefill decides step 0, where the cu1343 build disagreed on
  every prompt.
- With FA off, prefill KQ and KQV are also f16 GEMMs on cuBLAS. So the FA-off pair differs in cuBLAS on attention
  shapes as well as in native kernels.

## cuBLAS 13.x known issues

- **Device alpha/beta read before cudaGridDependencySynchronize (PDL): does not apply.**
  - ggml-cuda never calls cublasSetPointerMode, so every call uses the default host pointer mode.
  - alpha and beta are host statics (ggml-cuda.cu:1374-1403).
- **GEMV with a non-accumulation dimension over 3,145,680: does not apply.**
  - The vocab is 151,936.
  - Decode sends no single-token matmul to cuBLAS.

## How to read the labels

- **cuBLAS:** stock ggml-cuda with 13.4.3's cuBLAS reproduces S2. That points at the prefill V projection above.
- **fattn:** with FA off, S0 and S2 agree on all prompts.
- **"native sm_120a MMQ/MMVQ":** cuBLAS changes nothing on the FA-on path, and FA off doesn't remove the shift.
  - The class is every kernel nvcc 13.4 compiled for sm_120a (rms_norm, rope, softmax, MMVF, ...), not only MMQ/MMVQ.
  - The FA-off disagreement can include cuBLAS on attention GEMMs that production (FA auto) never runs.
- **No attribution:** a compound cause. b fails, and the decision is DO NOT ACTIVATE.

## Follow-ups (not in this run)

- If cuBLAS is attributed: try GGML_CUDA_CUBLAS_COMPUTE_TYPE=f32 (fp32 accumulation in that GEMM). It needs only an
  env change.
- GGML_CUDA_PDL=0 turns off ggml's own PDL launches.
