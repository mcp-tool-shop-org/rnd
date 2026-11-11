---
title: "11 November: a warning line, read before it was acted on"
description: "A memory warning in aspire-si's second seed crossed its line, and the reading turned out to measure the wrong thing. Also: Blender 5.3 against our scene tool, a Colab training run stopped by its own guard after it had finished training, a model whose licence changed between versions, and the daily watch."
issue: 43
date: 2026-11-11
draft: true
highlights:
  - "<strong>A warning line, read before it was acted on.</strong> The card-memory warning in aspire-si's seed 46 crossed its line at one save. The peak, the floor and the trainer's own memory said nothing had grown. The two-minute reading had caught one half of a cycle, so we made it ten minutes long."
  - "<strong>Blender 5.3 arrived, and armature didn't notice.</strong> Every one of armature's 3,166 Blender tests passes on 5.3, and the ones that start real Blender pass on both graphics backends."
  - "<strong>Finished, then stopped.</strong> A style-training run on a rented 96 GB card reached all 500 steps and saved both checkpoints. Then its own stall guard fired on a phase it wasn't meant to watch."
---

A night of readings that needed a second look. A memory warning crossed its line and turned out to be measuring when
we sampled, not how much was used. A guard stopped a training run that had already finished. And one model's licence
turned on a version number.

**In this issue:**

1. [A warning line, read before it was acted on](#a-warning-line-read-before-it-was-acted-on)
2. [Blender 5.3 arrived, and armature didn't notice](#blender-53-arrived-and-armature-didnt-notice)
3. [Finished, then stopped](#finished-then-stopped)
4. [One model name, two licences](#one-model-name-two-licences)
5. [The daily watch](#the-daily-watch)

## A warning line, read before it was acted on

[aspire-si](https://github.com/mcp-tool-shop-org/aspire-si)'s pre-registered training series, S2 v1.1, runs three seeds
of 197 updates each on our RTX 5090. Seed 45 finished yesterday ([issue 42](/rnd/newsletter/issue-42/)). **Seed 46 ran
four of its five chunks overnight, and the run's own checker passed all four.** The fifth and last chunk, the final 37
updates, started at 03:24 ET this morning.

**The line.** Besides the guards inside the run, we watch the card from outside. At every save, every 10 updates, we
take a short series of memory readings with `nvidia-smi`. One of our report-at-once lines: if the middle reading of a
series is above 15,500 MiB, the Publisher hears about it straight away. A report-at-once line is not a stop.

**What happened.** At the save after update 170, a series of 24 readings, 5 seconds apart, came in at:

| | lowest | middle (median) | highest |
|---|---|---|---|
| chunk 5, update 170 | 10,176 MiB | **15,742 MiB** | 15,916 MiB |
| chunk 1 (for comparison) | 10,429 MiB | 12,406 MiB | 15,749 MiB |

The middle reading was 242 MiB over the line.

**Why we didn't stop.** A memory problem in a training run usually shows as growth: the floor rises, or the peak climbs
from one save to the next. Neither had happened. The lowest reading was in line with chunk 1, and the highest was within
about 170 MiB of chunk 1's highest. The trainer's own measure of the memory it had allocated peaked at 18,466 MiB in this
chunk, lower than the 19,677 MiB peak in chunk 3. Nothing else was on the card.

**What the reading was really measuring.** Each training update has two halves: the model writes answers (the memory-
heavy half), then it learns from them. Two minutes of readings is shorter than one update, so a series lands mostly in
one half or the other. This one landed in the heavy half, and its middle reading moved up with it. A second short series
a few minutes later did the same: 10,529, 15,781 and 22,943 MiB.

**What we changed.** From the next save, the series runs for ten minutes (120 readings), long enough to cover both
halves. The rule for stopping is now written down in advance: hold the run at a save only if the ten-minute middle
reading is over the line **and** the lowest or highest reading has risen past what the earlier chunks showed.

<!-- PLACEHOLDER: the step-180 ten-minute series result goes here before publish. -->

## Blender 5.3 arrived, and armature didn't notice

[armature](https://github.com/mcp-tool-shop-org/armature) stages a character in headless Blender and renders the
per-frame control sequences a video model has to follow. Blender 5.3.0 came out yesterday, so before installing it we
read what it changes, at the release notes.

Two changes could have touched armature:
- **The compositor now runs a stack of effects** instead of one compositor node group. armature builds its render passes
  by assigning one node group, so this was the change we expected to break something.
- **Vulkan is now the default graphics backend** on Windows and Linux, and published reports say Vulkan and OpenGL
  don't produce pixel-identical renders.

The headline feature, a DLSS denoiser for Cycles, turned out not to matter to us: the release notes say it runs in the
interactive viewport only, and armature renders headless.

**What we measured.** We installed 5.3 beside 5.2 and ran armature's Blender tests against it:
- **3,166 passed, 18 skipped**, on 5.3 with its default backend.
- The tests that start a real Blender process (107 of them, in 8 files): **107 passed, 5 skipped on Vulkan, and 107
  passed, 5 skipped with OpenGL forced.**

So the old single-group compositor path still drives a background render on 5.3, and armature's checks pass on either
backend. Production renders stay on 5.2 for now anyway; it's the long-term-support release.

One thing we found in the research and checked: a widely repeated name for 5.3's new rotation-conversion call was wrong.
The Python API notes call it `convert_rotation_mode`, a method on objects and pose bones.

## Finished, then stopped

For the first time in four days, a rented Colab card ran one of our jobs: a 500-step style-training rung for
[style-dataset-lab](https://github.com/mcp-tool-shop-org/style-dataset-lab), on an RTX PRO 6000 Blackwell with 96 GB.

**What went right.** The 57.7 GB base model downloaded in 163 seconds. Training reached step 500 of 500, and both
checkpoints were saved, at step 250 and at the end. The window cost 3.395 Colab compute units (1,216 seconds at 10.05 per
hour) and closed cleanly.

**What went wrong.** As the run handed over from training to making its final sample images, the launcher's own
**stall guard** stopped it. That guard watches the setup log during setup, and it fires if the log stops growing for
10 minutes. But setup had ended long before: the run was training, and a training run isn't supposed to write to the
setup log.

**Why the guard got it wrong.** The launcher reads the run's health from a log of status blocks. The last block it read
had been cut off mid-write, so it held no phase at all, and the guard treated a missing phase as "still in setup". A
second guard in the same launcher, one that watches memory on the rented machine, already skips half-written blocks.
The stall guard didn't. While reading the run's files we found one more: the memory guard read about 340 MB, against
the trainer's roughly 13 GB, because it was reading the wrong process group.

The fix, in review now, makes the stall guard skip half-written blocks, records both memory readings and uses the
larger, and adds three facts to the run record: steps done, whether the final checkpoint exists, and whether training
completed. The run record had said `trained: false` for a run that trained.

Elsewhere on Colab, a judge test for another study asked for an A100 three times and was refused all three ("no
capacity"). A refusal costs nothing; it tries again in daytime.

## One model name, two licences

Video models that follow a 3D render need help turning that render into what they read: depth, outlines, a body pose.
A lot of that help comes from small preprocessing models, and the research we read this week found the licence traps
there rather than in the video models.

The clearest case is **Depth Anything 3**. We read the licence tag on every one of its published checkpoints:

| Checkpoint | Licence |
|---|---|
| DA3-Small, DA3-Base, DA3-Mono-Large, DA3-Metric-Large | Apache 2.0 |
| **DA3-Large** (the first release) | **CC BY-NC 4.0** (no commercial use) |
| **DA3-Large-1.1** (the December update) | **Apache 2.0** |
| DA3-Giant, DA3-Giant-1.1, both Nested Giant-Large versions | CC BY-NC 4.0 |

The same model name changed licence between versions. And every one of these repositories ships its weights in a file
with the same name, `model.safetensors`, so a check that only reads file names can't tell an allowed checkpoint from a
forbidden one.

armature already refuses a paid run whose workflow loads a known non-commercial model, but its list named only two pose
models. A change in review adds the larger Depth Anything models, InsightFace, and the SMPL body models. Its first draft
blocked DA3-Large-1.1 along with 1.0; the review caught it, and the fix ties each entry to a repository and revision
rather than a name.

## The daily watch

<!-- PLACEHOLDER: R&D's morning watch block (11 November) goes here. -->
