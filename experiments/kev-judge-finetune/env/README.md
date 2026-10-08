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

Median step time is reported, not gated.

**2. Confirm score with the existing seed-0 judge** (`KEV_VENV=.venv-cu134 bash score_set.sh confirm-cu134 /mnt/e/AI/aspire-si-runs/2026-10-08-kev-confirm/fresh/confirm_set.json 0`, which writes `results/judge-4b-full-s0-confirm-cu134.json` beside the cu128 `judge-4b-full-s0-confirm.json`):
- the same weights the cu128 env scored: order-averaged 0.9799, CI [0.9536, 1.0];
- pass needs order-averaged accuracy ≥ 0.9536 (the reference's CI low);
- **and** order-averaged per-pair decisions agreeing with the cu128 run on at least 146 of 149 pairs.

The second condition matters most. With the same weights, only numeric kernels differ.

A fail on either keeps training off cu134, and is reported with the failing numbers. **The fallback is stable cu132 (to
be built; Director, 2026-10-08), not cu128.** Until a cu132 env exists, nothing trains on the old cu128 env as a
fallback without asking the Publisher first.
