# CUDA 13.4 PyTorch on a RunPod CUDA 13.0 host

**Question (2026-10-08).** The studio trains on a CUDA 13.4 PyTorch nightly. RunPod's newest host is CUDA
13.0: its pod-create API's `allowedCudaVersions` enum tops out there. Does the nightly work on such a host
under CUDA's minor-version compatibility? The risk is code that compiles at run time (Triton,
`torch.compile`), which that compatibility doesn't cover.

**Answer: yes, on an A100 and a B200.** Every GPU path the studio uses passed. The B200 run is in the
last section.

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
- **Limits.** Two GPU families so far: Ampere (sm_80) here and Blackwell (sm_100, B200) below. Hopper
  is untested, and Triton compiles per architecture. A new card type gets this probe first: about $0.40
  on an A100, $2.35 on a B200.
- **A first real cloud training run still reproduces a known result** before its numbers are trusted, the
  same gate as the local env.

## Follow-up: a real CUDA 13.4 driver on RunPod through forward compatibility (same day)

The 13.4 driver features need a 13.4 driver:
- locality domains: `CU_DEVICE_ATTRIBUTE_LOCALITY_DOMAIN_COUNT` = 149, localized pools and allocations,
  green contexts on a domain's SMs;
- the unified-memory residency query `cudaMemGetLocationInfo`.

RunPod hosts stop at 13.0. NVIDIA's forward-compatibility package puts a newer user-mode driver in the
container, on top of the host's kernel driver.

Run: offrig plan 3, an A100-SXM4-80GB on driver 580.159.04 (host CUDA 13.0), $0.24.
- **Install:** `cuda-compat-13-4` from NVIDIA's ubuntu2204 repo. User-mode driver 615.71.09, in
  `/usr/local/cuda-13.4/compat`.
- **Use:** `LD_LIBRARY_PATH=/usr/local/cuda-13.4/compat`.
- **Read:** `compat_probe.py` queries libcuda through ctypes.
- **Full log:** `results/2026-10-08-a100-compat.log`.

| | host driver only | with cuda-compat-13-4 |
|---|---|---|
| `cuDriverGetVersion` | 13000 | **13040** |
| locality domain count (attr 149) | error 1 (invalid value) | **1** |
| SMs per locality domain (attr 157) | error 1 | 108 (all of the A100's) |
| `cuMemGetLocationInfo` symbol | absent | present |
| `cu134_probe.py` | 8 of 9 pass | 8 of 9 pass, numerically identical (LoRA losses equal to every printed digit) |

`nvidia-smi` itself reports CUDA 13.4 once the compat path is loaded.

**Meaning.** On a datacenter GPU, offrig can give a pod a real CUDA 13.4 driver API: install
`cuda-compat-13-<minor>` and set the library path. Forward compatibility is supported on datacenter
parts, not on GeForce cards.

The A100 is a single die, so it has one domain. A multi-domain part (B200 or B300, both listed on RunPod
at $7.99 and $8.99/hr) is where locality domains could pay off.

## B200: the same compat run on Blackwell (same day)

Run: offrig plan 4, profile `probe-blackwell`. The pod was an NVIDIA B200 (183 GB) on driver 580.167.08,
host CUDA 13.0, compute capability 10.0. About 18 minutes cost $2.35.
- **Same script, same pins:** `setup_compat.sh` and the A100 env, with one change. The LoRA check now
  asks only that the loss falls.
- **Full log:** `results/2026-10-08-b200-compat.log`.

| | A100 host only | A100 with compat | B200 host only | B200 with compat |
|---|---|---|---|---|
| `cuDriverGetVersion` | 13000 | 13040 | 13000 | **13040** |
| locality domain count (attr 149) | error 1 | 1 | error 1 | **2** |
| SMs per locality domain (attr 157) | error 1 | 108 of 108 | error 1 | **70 of 148** |
| `cuMemGetLocationInfo` symbol | absent | present | absent | present |
| `cu134_probe.py` | 8 of 9 | 8 of 9 | not run | **9 of 9** |

B200 probe measures under compat:

| Check | Result | Measure |
|---|---|---|
| matmul vs CPU float64 | pass | rel. error fp32 5.7e-7, bf16 2.9e-3 |
| cuDNN conv forward and backward | pass | max abs error 1.9e-6 |
| SDPA flash attention, bf16 | pass | max abs error 7.4e-3 |
| raw Triton kernel (JIT for sm_100) | pass | Triton 3.9.0 |
| `torch.compile` training step | pass | first 5 steps 16.9 s, including compile |
| `torch.compile(mode="reduce-overhead")` | pass | max abs error 8.9e-8 vs eager |
| CUDA graph capture and replay | pass | identical to eager |
| LoRA training, 30 steps | pass | 7.6616 → 6.8773 (A100: 6.8746) |

**What it shows.**
- The CUDA 13.4 nightly runs on Blackwell under a 13.0 host, Triton and `torch.compile` included.
  Ampere and Blackwell are now covered; Hopper is not.
- The B200 reports **two locality domains**, one per die, so the 13.4 locality-domain API reaches
  a real multi-domain part on RunPod.
- **Not explained yet:** 2 × 70 = 140 SMs, not the 148 the device reports. Attribute 157 may count
  differently from a simple split. Read the per-domain resources (`cuDeviceGetDevResource`) before
  relying on it.
- **Not tested:** whether domain-local allocation or green contexts make any training job faster.
  That is the next question, and it needs a workload, not a probe.
- Compile and LoRA wall times on the B200 were slower than on the A100: 78 s vs 5 s, and 85 s.
  The job dir sits on RunPod's network filesystem, and these are first-run times with a cold cache.
  They are not a speed comparison.
