---
id: 2026-11-26-nvidia-alpamayo-2-edge-a-2b-driving-model-that-reasons-only-
title: NVIDIA Alpamayo 2 Edge: a 2B driving model that reasons only when it needs to
date: 2026-11-26
kind: release
relevance: watch
fields: [machine-learning, evaluation, robotics]
tags: [alpamayo, nvidia, adaptive-reasoning, vla, openmdw]
---

## Summary

Alpamayo 2 Edge is NVIDIA's open vision-language-action model for self-driving. About 2.65B parameters sit in front of a
small diffusion decoder. From six camera views and the car's recent motion, it writes a short causal explanation of what
it will do and outputs a 6.4-second path. It is built on the Cosmos 3 Edge vision-language backbone. It reasons
adaptively: it spends reasoning only when the scene calls for it, to fit onboard compute. It is NVIDIA's first Alpamayo
model post-trained with closed-loop reinforcement learning in a driving simulator.

It is not a model rdlab can run as a judge or as a worder. It needs multi-camera video and motion history, and it outputs
trajectories. Two of its ideas do bear on our work: reasoning on demand, and rewards from a checker rather than a judge.

## Key points

- **Shape.** The backbone is 2.45B parameters (1.96B language model, 0.41B SigLIP2 vision encoder, 0.08B projector), plus
  a 0.2B action expert, in BF16.
  - Driving mode takes 22 frames from six cameras, a text navigation instruction, and 20 past ego poses at 0.1 s steps.
  - It returns 64 waypoints (0.1–6.4 s), and each candidate path comes with its own sampled reasoning text.
  - A free-form question mode answers questions about a driving scene.
- **Reasoning on demand.** The card frames it as adaptive reasoning that conserves onboard compute. The chat template
  enables thinking by default; the driving prompt ends with an empty think block, and the model writes its causal
  reasoning after it. How the model decides when to reason is not specified on the card.
- **Explanations tied to an outcome.** About 3.7M "Chain-of-Causation" traces link each driving decision to its causes.
  The closed-loop RL scores what the car actually does in simulation (AlpaSim), not the text alone.
- **Reported results.** LingoQA judge score 75.2. In closed loop (875 AlpaSim scenarios, 3 rollouts each), 15.15 km per
  at-fault incident. Open loop on 1,392 samples, minADE₆ at 5 s of 0.52 m.
- **Footprint.** On one H100: 12.06 GiB peak GPU memory for one 22-image sample with six candidate paths. 16 GB or more
  is recommended. Only H100 is validated, so a 5090 run would be untested territory.
- **Licence.** The weights are under OpenMDW-1.1 and the code under Apache-2.0. The driving datasets it was trained and
  evaluated on carry their own access terms, which must be accepted separately.

## Studio relevance

`watch`. Running it is not worth a GPU grant today: no studio repo has camera-and-motion driving data, and its datasets
need their own terms accepted. The ideas are worth carrying:

- **For rdlab's judges and readers:** reasoning only when needed is an open question for us. We pay for long thinking on
  every item. When a model should reason, and how to measure whether skipping reasoning cost accuracy, is the subject of
  Deep Research seed 66.
- **For rdlab's item design:** a decision whose consequence a small simulator can compute is the same principle as
  rdlab's "code proves the key". It suggests a possible future item family: motion and physics questions whose keys a
  simulator proves. This is an idea, not a plan.
- **For a robotics direction:** whether this model fits an existing studio repo or needs a new physical-AI repo is the
  subject of Deep Research seed 67.
- **Licence registry:** OpenMDW-1.1 is already listed as allowed. Alpamayo 2 Edge and its base, Cosmos 3 Edge, should be
  added to the registry's model list before any use.

## Claims

- [verified] The weights are released under OpenMDW-1.1, and the source code under Apache-2.0. (via: the Hugging Face
  model card and the repo's LICENSE file, read 2026-11-26)
- [verified] OpenMDW-1.1 puts no restriction or obligation on outputs. Distributing the model materials requires keeping
  the agreement and its notices. (via: the LICENSE file in nvidia/Alpamayo2-Edge, read 2026-11-26)
- [verified] The backbone is 2.45B parameters plus a 0.2B action expert, BF16, built on Cosmos 3 Edge. (via: model card,
  2026-11-26)
- [verified] The driving input is six cameras and 22 frames, plus 20 past ego poses. The output is 64 waypoints over
  6.4 s. (via: model card, 2026-11-26)
- [verified] Measured peak GPU memory on one H100 is 12.06 GiB for one sample with six candidate paths; only H100 is
  validated. (via: model card, 2026-11-26)
- [unverified] It is the first Alpamayo model post-trained with closed-loop RL in AlpaGym, and it reasons only when
  needed. These come from NVIDIA's announcement video description. The model card names adaptive reasoning but does not
  describe the gating mechanism.
- [unverified] Benchmark figures (LingoQA 75.2, 15.15 km per at-fault incident, minADE₆ 0.52 m) are as reported by
  NVIDIA on the card and were not reproduced here.

## Sources

- [primary] https://huggingface.co/nvidia/Alpamayo2-Edge — NVIDIA model card and LICENSE (read 2026-11-26)
- [primary] https://github.com/NVlabs/alpamayo2-edge — NVIDIA source repository (named on the card)
- [primary] https://developer.nvidia.com/blog/running-av-reasoning-models-within-onboard-compute-and-latency-limits/ —
  NVIDIA technical blog (linked from the announcement; not read for this entry)
- [primary] https://openmdw.ai/license/1-1/ — OpenMDW-1.1 licence text
