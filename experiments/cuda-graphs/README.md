# CUDA graphs for aspire-si's critic heads

Asked for by the Director through ASPIRE (2026-10-08). Starting point: entry
`2026-10-07-cuda-graphs`. The question is where CUDA graphs pay on the RTX 5090, what the
Windows path is, and how to prove that a graphed run gives the same answer.

## What is here

| File | What it does |
|---|---|
| `graphed_heads.py` | A drop-in for aspire-si's `train_head` and `score_set`: GPU-resident features, batched scoring, and an optional CUDA-graph training step (`graphs=True`). The docstring lists the capture rules it follows. |
| `test_graphed_heads.py` | CPU tests. The eager path reproduces aspire-si's own weights and scores, and the batch order matches the original loop. |
| `bench.py` | Times original, fast and graphed runs on the real Llama cache, per form, and applies the gates below. It also reports the GPU-busy share of one eager step. |
| `triton_probe.py` | Checks whether `torch.compile` (`default`, `reduce-overhead`) runs on Windows with triton-windows and the cu134 nightly. |

## Measured before any GPU run (2026-10-08)

- **The workload.** The Llama cache has 603 train pairs (1,206 answers), D = 3072, fp16, up to
  1,040 tokens. Training is 8 pairs per batch over 5 epochs, so 380 steps per head: 75 full
  batches and one of 3 pairs per epoch.
- **Mean, span and mid forms.** Each answer is pooled to one vector before training. The step is a
  tiny MLP on 16 × 3072, which is the launch-bound case where graphs should pay.
- **Attention form.** The original keeps per-token states on the CPU. Every step pads about
  16 × 1,040 × 3072 values to fp32 on the CPU and copies them to the GPU. That is copy-bound, so
  moving the states onto the GPU (`stack_features`, 7.7 GB in fp16 for train) should matter more
  than graphs.
- **Scoring.** `score_set` runs one pair per forward and calls `float()` twice per pair. Each call
  is a device sync. Batching removes this without graphs.
- **Windows Triton.** The newest triton-windows is 3.8.0.post29 (PyPI, 2026-09-28). The WSL cu134
  nightly bundles Triton 3.9.0. In a probe venv borrowing aspire-cu134's torch, triton-windows 3.8
  imports and Inductor detects it. Whether it compiles and runs is the GPU probe's question.
- **CPU equivalence.** The eager fast path matches aspire-si's `train_head` and `score_set` on
  synthetic data: weights within 1e-5 and scores within 1e-4, for attention and length-1 mean
  pooling (4/4 tests).

## Gates (fixed before the run)

- **Exact (dropout 0, seed 42).**
  - Confirm scores: original vs fast, and original vs graphed, differ by at most **1e-3** on the
    0–10 scale. The measured cross-card noise is 0.002.
  - Per-step losses: fast vs graphed differ by at most **1e-4**.
  - **0** pairs change win or loss.
- **Outcome (dropout 0.1 as trained, seeds 42–44).** The seed-mean confirm pair-win rate of fast
  and of graphed lies inside the original's 95% prompt-clustered bootstrap interval
  (`critic_heads.boot`).
- A fail on either gate means the graphed path is not used, and the failing numbers are reported.
- A speedup is reported as the median over the three seeds, original time ÷ mode time. Capture
  time is included in the graphed training time.

## Why not Kev or the 8B scoring passes (to be measured, not assumed)

- **Kev:** a 4B LoRA step on long sequences. **Typicality scoring:** one 8B forward over hundreds
  of tokens.
- Both are large-kernel work, where the GPU should be busy and launch overhead small. Graph capture
  of a Hugging Face forward with variable lengths also needs a fixed-shape bucket per length.
- **The check:** sample `nvidia-smi` GPU utilisation during the Kev cu134 smoke, which is already
  booked. If it sits near 100%, graphs cannot help there. The scoring pass gets the same
  `busy_fraction` measurement if ASPIRE wants it.

## Run (after the Publisher grants the card)

```
E:/AI/envs/aspire-cu134/Scripts/python.exe bench.py --aspire E:/AI/aspire-si --cache E:/AI/aspire-si-runs/2026-10-08-auditor/cache/llama --out results/2026-10-08-llama.json
E:/AI/envs/triton-probe/Scripts/python.exe triton_probe.py
```

The probe venv (E:/AI/envs/triton-probe, guarded by the VRAM watchdog): `uv venv --python 3.12`, then `uv pip install triton-windows==3.8.0.post29`, plus
a `.pth` file naming `E:/AI/envs/aspire-cu134/Lib/site-packages`.

## Results (2026-10-08, RTX 5090, torch 2.16.0.dev20261008+cu134, Windows)

Llama-3.2-3B cache (D = 3072), 603 train pairs, scored on 149 confirm pairs. Speedups are original time ÷ mode
time, the median over seeds 42–44, with capture time included. Full numbers are in `results/2026-10-08-llama.json`.

| Form | Exact gate (dropout 0) | Outcome gate (dropout 0.1) | Train: fast | **Train: graphed** | Score: batched |
|---|---|---|---|---|---|
| auditor:mean | pass | pass (0.964 vs 0.966) | 1.19× | **7.25×** | 25× |
| auditor:attention | pass | pass (0.935 vs 0.924) | 11.0× | **25.4×** | 31× |
| advocate:mean | **fail** (score Δ 0.052, loss Δ 7.2e-4, 0 flips) | pass (0.951 vs 0.953) | 1.05× | **7.31×** | 13× |
| advocate:span | pass | pass (0.884 vs 0.895) | 1.07× | **7.20×** | 29× |
| auditor:mid | pass | pass (0.960 vs 0.960) | 1.04× | **7.67×** | 27× |

- **Pooled forms, about 0.9 s → 0.12 s per head.** The work was launch-bound: an eager step kept the GPU
  only 12–15% busy, and graphs removed that cost. Moving features onto the GPU alone gained almost nothing.
- **Attention form, 11.3 s → 0.44 s per head.** Most of the gain (11×) came from moving features onto the GPU,
  which ended the per-step CPU padding and copy. Graphs added a further 2.3×. The stack costs 9.6 GB of VRAM
  in fp16.
- **Scoring:** batching removes the per-pair syncs, a 12–31× gain without graphs.
- **The exact-gate failure is the optimizer, not the graph.** Diagnosed in the same slot:
  - training with `AdamW(capturable=True)` eagerly (no graph) and with the graph gives identical losses
    (max Δ 0.0);
  - both differ from standard AdamW from step 93 on (max Δ 7.2e-4), because capturable AdamW computes bias
    correction with device tensors;
  - so the gate measured an optimizer change it wasn't meant to. The outcome gate, which is what a result
    rests on, passes on all five forms.
- **Not run this slot:** the Windows torch.compile/Triton probe (`triton_probe.py`). It needs its own short ask.

**Recommendation for aspire-si:**
- Take the GPU-resident features and batched scoring now: they're exact (≤ 6e-6) and give 11× training on
  attention and 12–31× scoring.
- Take the graphed step where training volume matters (7× more on pooled forms). Run the eager comparison
  with `capturable=True` too, so the two are bit-identical, and record that the optimizer variant changed.
