# Training environment: CUDA 13.4 (Director rule, 2026-10-08)

Training runs on the newest stack the rig can handle. On 2026-10-08 PyTorch's stable wheels stopped
at CUDA 13.2, so this env uses a **date-pinned nightly**: `torch==2.16.0.dev20261008+cu134`
(CUDA runtime 13.4.49, cuDNN 9.26, Triton 3.9), with the latest transformers (5.19.0), peft (0.21.2)
and accelerate (1.15.0). `requirements-cu134.lock` lists every package.

It becomes the training env only after it reproduces a known result:
1. a 1-step smoke with a finite loss and grad_norm > 0;
2. one existing measurement, the judge-ft confirm accuracy, inside its CI.

Kev's own project pins `torch>=2.6,<2.9`, so Kev is installed with `--no-deps` here, and this gate
is what shows whether it still trains correctly.

Rebuild (WSL, from the kev checkout):

```bash
uv venv --python 3.12 .venv-cu134
. .venv-cu134/bin/activate
uv pip install --pre "torch==2.16.0.dev20261008+cu134" --index-url https://download.pytorch.org/whl/nightly/cu134
uv pip install -r <this folder>/requirements-cu134.lock   # the rest, pinned
uv pip install --no-deps -e .
```

uv gives `--extra-index-url` priority over `--index-url`, so install torch from the nightly index
alone, or uv resolves stable torch from PyPI instead.

## Pass band for the reproduction (fixed 2026-10-08, before the run)

The reference is the cu128 env on the same data and seed.

**1. 30-step smoke** (`KEV_VENV=.venv-cu134 bash train.sh smoke 0`, which writes `runs/judge-4b-smoke-s0-cu134`, never the reference run). The reference
(`judge-4b-smoke-s0/training_metrics.json`) has 30 steps, peak device 10.48 GB, grad_norm mean 9.07
(max 18.54), a 5.2 s median step and 219 s wall time. Pass needs all of:
- a finite loss and grad_norm > 0 on every step;
- grad_norm mean within [4.5, 18.1], half to twice the reference;
- no truncated or rejected records;
- peak device memory at most 13 GB.

**Speed gate (added 2026-10-08, before the rerun):** median step time at most 1.25× the reference, so **≤ 6.55 s**. GPU utilisation is sampled each second and reported. The first cu134 smoke passed every other gate but ran a 18.75 s median step at 21% utilisation. Its env lacked the fast kernels (see below), so a slow env must not pass.

**2. Confirm score with the existing seed-0 judge** (`KEV_VENV=.venv-cu134 bash score_set.sh confirm-cu134 /mnt/e/AI/aspire-si-runs/2026-10-08-kev-confirm/fresh/confirm_set.json 0`, which writes `results/judge-4b-full-s0-confirm-cu134.json` beside the cu128 `judge-4b-full-s0-confirm.json`):
- the same weights the cu128 env scored: order-averaged 0.9799, CI [0.9536, 1.0];
- pass needs order-averaged accuracy ≥ 0.9536 (the reference's CI low);
- **and** order-averaged per-pair decisions agreeing with the cu128 run on at least 146 of 149 pairs.

The second condition matters most. With the same weights, only numeric kernels differ.

A fail on either keeps training off cu134, and is reported with the failing numbers. **The fallback is stable cu132 (to
be built; Director, 2026-10-08), not cu128.** Until a cu132 env exists, nothing trains on the old cu128 env as a
fallback without asking the Publisher first.

## Fallback env: CUDA 13.2 stable (built 2026-10-08, not wired in)

Built on the Director's order as the fallback if cu134 fails its gate: `~/kev/kev/.venv-cu132` in WSL.
- **torch 2.14.1+cu132**: the newest stable release on 2026-10-08. CUDA 13.2, cuDNN 9.24, Triton 3.8.0.
- **Same package set as `.venv-cu134`**: transformers 5.19.0, peft 0.21.2, accelerate 1.15.0. Only two
  packages are missing, the 13.4-only CUDA extras `cupti-python` and `nvidia-cuda-cccl`.
- **Lock:** `requirements-cu132.lock`.

Build gotcha: the cu134 lock pins CUDA metapackages (`cuda-toolkit==13.4.1`, `cuda-bindings`,
`cuda-pathfinder`, `cupti-python`). Installing the cu134 lock over stable torch makes uv quietly
replace torch with 2.9.1+cu128 from PyPI to satisfy them. Install torch and the rest in **one**
resolution, with those pins removed, and assert the torch version afterwards:

```bash
uv venv --python 3.12 .venv-cu132
uv pip install "torch==2.14.1+cu132" -r <lock without torch, triton, nvidia-*, cuda-*, cupti-python> \
  --index-url https://pypi.org/simple --extra-index-url https://download.pytorch.org/whl/cu132 \
  --index-strategy unsafe-best-match
uv pip install --no-deps -e .
```

Checked once, on the device: the RTX 5090 is visible, and a float64 matmul matches the CPU to 4.6e-14
(33 MB). No training has run on it. The VRAM watchdog's pattern does not cover `.venv-cu132`, so it
runs no GPU work until the Director wires it in.

## First cu134 attempt, 2026-10-08: the env was incomplete, so it reruns

**Smoke:** every gate passed. 30 steps, loss 0.704 → 0.164, grad_norm mean 8.94 (ref 9.07), peak 11.02 GB,
0 truncated, 0 rejected. But the **median step was 18.75 s against 5.24 s, with the GPU about 21% busy**
(`results/2026-10-08-cu134-gpu-util.csv`).

**Cause:** kev is installed `--no-deps`, so the cu134 lock lacked packages the cu128 env had:
- **flash-linear-attention / fla-core 0.5.2 and einops:** Qwen3.5's gated-delta-rule layers call fla's
  kernel when it is present (`modeling_qwen3_5.py`, `use_kernel_func_from_hub_with_fallback(...,
  "fla")`) and a pure-PyTorch fallback otherwise;
- **fastapi, uvicorn and starlette:** the confirm score's server couldn't start, so nothing was scored.

**Fix,** at cu128's exact versions, in both `.venv-cu134` and `.venv-cu132`. fla 0.5.2 **fails to import under
Triton 3.9** (the cu134 nightly): one autotune key names an argument the kernel doesn't take, which Triton 3.9
rejects.
- Upstream fixed it in fla commit `b8ff84870` (#1330, 2026-10-06, one line), but no release contains it yet.
- `apply_fla_1330.sh <venv>` applies exactly that line to 0.5.2, refusing any other state. The patched file's
  sha256 is `1725556d…70aa`.
- cu132 (Triton 3.8) imports 0.5.2 without the patch.
- So the cu134 env differs from cu128 only in the CUDA stack and that one upstream line, and the reproduction
  still isolates CUDA.

When fla releases 0.5.3 or later with #1330, move both envs to it and drop the patch.

## Result, 2026-10-08: cu134 PASSES the full band, so it is the Kev training env

The rerun used `.venv-cu134` with fla 0.5.2 plus the #1330 line (patched-file sha256 `1725556d…70aa`).

| Gate | Band | cu128 ref | cu134, no fla (1st try) | **cu134** |
|---|---|---|---|---|
| steps, finite loss | 30 | 30 | 30 | **30** (final loss 0.163) |
| grad_norm mean | 4.5–18.1 | 9.07 | 8.94 | **8.91** |
| peak device | ≤ 13 GB | 10.48 | 11.02 | **10.50** |
| truncated / rejected | 0 / 0 | 0 / 0 | 0 / 0 | **0 / 0** |
| median step | ≤ 6.55 s | 5.24 | 18.75 ✗ | **5.45** |
| wall | reported | 219 s | 578 s | 201 s |
| confirm, order-averaged | ≥ 0.9536 | 0.9799 | not run | **0.9799**, CI [0.954, 1.0] |
| per-pair agreement with cu128 | ≥ 146/149 | — | — | **149/149** (max Δp 0.011) |

- **Output:** the smoke is `runs/judge-4b-smoke-s0-cu134`; the first try's slow run stays as
  `runs/judge-4b-smoke-s0-cu134-nofla`.
- **Confirm file:** `results/judge-4b-full-s0-confirm-cu134.json`.
- **Utilisation:** `results/2026-10-08-cu134-rerun-gpu-util.csv`.

**The GPU is not saturated:** about 35% busy (median 35%, p90 61%) during the smoke. Kev trains with
batch 1 plus checkpointing. `causal_conv1d` is missing in every env, cu128 included, and transformers warns
that its fallback is "much slower". causal_conv1d is a compiled CUDA extension, so a CUDA 13.4 build needs
nvcc 13.4 in WSL; WSL has 12.8 today. It's a candidate speed-up, not done.

## causal-conv1d for cu134 (built 2026-10-08, GPU test pending)

**Why:** Qwen3.5's short convolution falls back to PyTorch without `causal_conv1d`, which transformers
warns is "much slower". The cu134 smoke kept the GPU only about 35% busy.

**The build:** CPU only, with no system change (the Director approved nvcc 13.4 in WSL; the Publisher set the
guardrails).
- NVIDIA's wsl-ubuntu apt repo has no `cuda-toolkit-13-4` (it stops at 13-3), so nvcc comes from the pip wheel
  `nvidia-cuda-nvcc==13.4.59`.
- It lives in a separate build venv, `~/kev/kev/.venv-cu134-build`, with the same torch pin. That venv
  isn't on the watchdog pattern, so it is CPU-only.
- Settings: `CUDA_HOME=<build venv>/site-packages/nvidia/cu13`, `TORCH_CUDA_ARCH_LIST=12.0` (sm_120, the
  5090 only), `CAUSAL_CONV1D_FORCE_BUILD=TRUE`, `MAX_JOBS=16`.
- The cu13 wheels ship `libcudart.so.13` but no `libcudart.so`, so a private link stub
  (`~/kev/cuda134-linkstubs/libcudart.so` → `.so.13`) goes on `LIBRARY_PATH` for the link step.
- **Wheel:** `~/kev/wheels/causal_conv1d-1.7.0-cp312-cp312-linux_x86_64.whl`, sha256 `5c704322…109bd`. It's
  installed `--no-deps` in `.venv-cu134`, the only change to that env. It imports with the GPU hidden.
- **Cloud cards** (sm_80 A100, sm_100 B200) need their own build, with those arches added.

**GPU test (needs a slot):**
- the same smoke and confirm band;
- the speed gate's reference stays 5.24 s; the question is how far below 5.45 s it goes;
- a direct check that causal_conv1d's forward matches transformers' PyTorch fallback.
