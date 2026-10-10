---
title: A verifier, a cliff, a dead NPU and a missing input
description: Two days of measurements, from a provisional verifier calibration to why the Intel NPU disagreed with itself.
issue: 1
date: 2026-10-09
highlights:
  - "<strong>Verifier calibration is provisional</strong>: it ran on synthetic, Claude-written gold. It will be re-measured on public human-labelled data before any default is named."
  - "<strong>Thinking on vs off</strong>: on the same synthetic gold, thinking mattered much more for the qwen3 models than for gemma4:31b (provisional)."
  - "<strong>The NPU never miscomputed.</strong> All 19 E1 mismatches came from one missing model input, found on the CPU."
  - "<strong>CUDA 13.4 is usable</strong> locally and on rented RunPod GPUs; the judge fine-tune's speed-up came from a kernel, not from CUDA."
  - "<strong>Specialize models, verify hand-offs</strong>: a five-lane study-swarm on making thinking cheaper, and what it means for Role OS."
---

> **⚠ Provisional (2026-10-10):** these verifier numbers were measured on synthetic gold, claims and labels
> written by Claude, not checked against human labels. They are not results until re-measured on a public
> human-labelled set. Further runs on this gold are stopped.

Every claim below links to a research brief, and every brief links to its receipts. Interim and wrong results
stay visible and labelled.

## The verifier

offrig's `verify` step needed a default local model to check claims about code. Six models ran against a gold
set built for the job, with every label assigned blind. None passed the first run. gemma4:31b was fooled almost
never, but ran out of reply budget while still thinking.

A rerun with a larger budget and offrig's improved quote rule passed reasoning claims on tune, then on the
held-out split. On this gold, gemma4:31b was the pick for reasoning claims; **no default is named** until the
re-measure on public human-labelled data.
Grounded claims failed on one deterministic thinking loop: gemma repeated two lines 307 times because the
contract allowed only one quote. offrig's next contract allows several quotes and kills loops.
→ [Which local model can check claims for offrig?](../../briefs/verifier-calibration/)

## Thinking on and off

The same tune claims, run again with thinking off, separate thinking from the model itself. Both qwen3 models were
fooled far more often with thinking off. On reasoning claims, the false-accept bound was 0.39 for qwen3:8b and
0.40 for qwen3:14b, against a limit of 0.10. gemma4:31b lost much less. It ran 3.3× faster and, on grounded
claims, passed the rule with thinking off: the first grounded pass of any model. We went looking for that after
seeing the data, so it names nothing until a held-out run confirms it. Model size and thinking interact, and
that is the case for a cascade: run a strong model cheaply first, and think only where it's needed.
→ [How do we make model thinking cheaper?](../../briefs/making-thinking-cheaper/)

## The math ladder

Generated arithmetic claims, from one step to many, show where each model stops checking reliably. The thinking
models held perfectly through level 5. Then every model hit the same cliff: answers in megabytes, false claims
off by exactly one.
→ [Where does each model's arithmetic checking fall off?](../../briefs/math-ladder/)

## The Intel NPU

The NPU runs small embedders 3–10× faster than the CPU. Batching nomic at 8×1024 crashed the device twice. When
the NPU disagreed with the CPU, Kimi traced it to one input the adapter never fed (`token_type_ids`). OpenVINO
read leftover memory in its place. With that fixed, parity is exact everywhere. A last diagnostic try will show
whether the crash was the same bug.
→ [What can the Intel NPU carry?](../../briefs/intel-npu/)

## CUDA 13.4

It runs on RunPod's CUDA 13.0 hosts through NVIDIA's compatibility package, on an A100 and a B200, and the judge
fine-tune passes its band on it. The speed-up came from the `causal-conv1d` kernel; plain 13.4 was slightly
slower than 12.8.
→ [Can the studio train on CUDA 13.4?](../../briefs/cuda-13-4/)

## Also measured

- **Sung hymns land within 10 ms of the beat** at the median. The aligner that cross-checks them is not yet
  validated. → [the brief](../../briefs/sung-vocal-timing-and-pitch/)
- **A Kimi-K3 piano arrangement costs $0.30–$1.01**, against offrig's $3.00 worst-case budget.
  → [the brief](../../briefs/arrangement-costs/)
- **Local translation broke a pinned sentence in 5 of 7 languages** on one README, so translations are now
  checked. → [the brief](../../briefs/local-translation-quality/)
- **ScalarScope's step-by-step comparisons fire on seed noise,** and its drift view measures the scoring teacher,
  not the run. → [the brief](../../briefs/reading-training-geometry/)
