# CUDA 13.4 PyTorch on a RunPod CUDA 13.0 host

**Question (2026-10-08).** The studio trains on a CUDA 13.4 PyTorch nightly. RunPod's newest host is CUDA
13.0: its pod-create API's `allowedCudaVersions` enum tops out there. Does the nightly work on such a host
under CUDA's minor-version compatibility? The risk is code that compiles at run time (Triton,
`torch.compile`), which that compatibility doesn't cover.

**Answer: yes, on an A100.** Every GPU path the studio uses passed.

## Run

- **Pod.** offrig plan 2, `job` profile (host CUDA floor 13.0). The pod was an NVIDIA A100-SXM4-80GB,
  driver 580.159.04, host CUDA 13.0, compute capability 8.0. 13 minutes cost $0.39.
- **Env.** The same pins as `experiments/kev-judge-finetune/env`:
  - torch 2.16.0.dev20261008+cu134 (CUDA 13.4, cuDNN 9.26), Triton 3.9.0;
  - transformers 5.19.0, peft 0.21.2, accelerate 1.15.0;
  - Python 3.12.15.
  - Freeze: `results/2026-10-08-a100-freeze.txt`.
- **Probe.** `cu134_probe.py`, one pass or fail per check, with the full log in
  `results/2026-10-08-a100-probe.log`.

| Check | Result | Measure |
|---|---|---|
| basic tensor ops | pass | |
| matmul vs CPU float64 | pass | rel. error fp32 2.6e-7, bf16 2.9e-3 |
| cuDNN conv forward and backward | pass | max abs error 1.4e-6, grads finite |
| SDPA flash attention, bf16, forward and backward | pass | max abs error 7.7e-3 vs fp32 |
| raw Triton kernel (JIT on the pod) | pass | Triton 3.9.0 |
| `torch.compile` training step (forward and backward) | pass | 5 steps 5.3 s, including compile |
| `torch.compile(mode="reduce-overhead")` | pass | identical to eager |
| CUDA graph capture and replay | pass | identical to eager |
| LoRA training, 30 steps, small Llama built from a config | **probe "fail", in fact a pass** | see below |

**The LoRA line.** The probe asked for a 20% loss drop in 30 steps. The loss fell 10% (7.6616 → 6.8746),
so the check reported a fail. Two measurements show the threshold was wrong, not the GPU:
- re-run on the pod, the CUDA run gave the same numbers exactly (deterministic);
- the same script on a CPU (local, the same torch nightly, GPU hidden) traced the same curve,
  7.6617 → 6.9072.

The CPU and GPU curves differ by bf16 rounding (0.03 at step 30). A rank-8 LoRA on two projections of a
random model just learns slowly. The probe's 20% assumption was a guess made before any run; its raw
output stays in the log as written.

## What this means

- **Cloud training on CUDA 13.4 is viable** on RunPod hosts with CUDA 13.0, with the same env as
  local. offrig PR mcp-tool-shop-org/offrig#37 adds `cuda_runtime = "13.4"` to a profile, so plans rent
  only those hosts.
- **Limits.** One GPU family (Ampere, sm_80), one host. A Blackwell or Hopper host could differ: Triton
  compiles per architecture. A new card type gets this probe first (about $0.40).
- **A first real cloud training run still reproduces a known result** before its numbers are trusted, the
  same gate as the local env.
