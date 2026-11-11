---
title: "11 November: you block the shot, the model shoots it"
description: "A long look at armature, our tool for making AI video follow a 3D scene we authored: the idea, fourteen experiments and their wrong turns, and what the field looks like now. Also: Blender 5.3 against it, a memory warning whose first explanation didn't survive a fact-check, a training run stopped by its own guard after it had finished, one model name with two licences, what two single-chip TPUs are good for, and the daily watch."
issue: 43
date: 2026-11-11
draft: true
highlights:
  - "<strong>You block the shot. The model shoots it.</strong> armature stages a character in Blender and makes a video model follow it. Fourteen experiments in, the model reads geometry rather than tone, identity holds through a hosted model that has never seen our character, and the most confident predictions we wrote down were the ones that missed."
  - "<strong>Blender 5.3 arrived, and armature didn't notice.</strong> 3,166 of armature's Blender tests pass on 5.3 (18 skipped), and the ones that start real Blender pass on both graphics backends."
  - "<strong>Finished, then stopped.</strong> A style-training run on a rented 96 GB card reached all 500 steps and saved both checkpoints. Then its own stall guard fired on a phase it wasn't meant to watch."
---

This issue goes deep on one of our repositories. armature is the tool that is supposed to let us make cutscenes with
AI video while keeping our own characters, in our own staging, in every frame. It has run fourteen experiments in three
months, and almost every one changed what we thought it was. We read back through all of them for this issue.

The night also brought Blender 5.3, which armature depends on, a memory warning in a training run, a rented GPU job
that was stopped after it had finished, a licence that changed between two versions of the same model, and a first look
at what the single-chip TPUs on our Colab plan could do for us.

**In this issue:**

1. [You block the shot. The model shoots it.](#you-block-the-shot-the-model-shoots-it)
2. [Blender 5.3 arrived, and armature didn't notice](#blender-53-arrived-and-armature-didnt-notice)
3. [One model name, two licences](#one-model-name-two-licences)
4. [A warning line, read before it was acted on](#a-warning-line-read-before-it-was-acted-on)
5. [Finished, then stopped](#finished-then-stopped)
6. [What a single TPU chip is for](#what-a-single-tpu-chip-is-for)
7. [The daily watch](#the-daily-watch)

## You block the shot. The model shoots it.

A video model can do things no renderer of ours can: light that breathes, cloth that moves, a crowd that reacts. What
it can't be told is **who** is on screen and **where they are standing**. Ask it for "our knight walks to the bar" and
you get a knight, a walk and a bar, but not ours, and not where we put him.

[armature](https://github.com/mcp-tool-shop-org/armature) is our answer to that. Its own one-line description is
"image-to-video with a GLB instead of an image". A GLB is a 3D model file. Instead of handing the video model a picture
and hoping, we hand it a 3D character we built, posed and animated and placed in front of a camera we chose. The
geometry is ours; the life is the model's.

![Diagram titled "You block the shot. The model shoots it." Four columns, left to right. "Authored by us": a wooden mannequin, with "character mesh (GLB)", "pose and animation", "camera and staging". "Headless Blender": "renders, frame by frame:" depth, surface normals, silhouette mask, edges, pose sticks, each with a small thumbnail. "Three routes into a video model": "Driven: pose sticks steer the motion"; "Free: an authored start frame, the model moves the camera"; "Composed: authored reference images, the model decides the shots". "Footage": a film strip, "the same character, at a known pose, every frame". Along the bottom, an amber band: "Gates before every paid run: is the character named? is every model's licence commercial? does the graph actually load the weights it claims?"](/rnd/charts/issue-43-armature-pipeline.jpg)

### How it works

Blender runs with no window ("headless"), driven by scripts. For every frame of a shot it renders the scene several
ways at once:
- **depth**, how far each pixel is from the camera;
- **surface normals**, which way each bit of surface faces;
- a **silhouette mask** of the character;
- **edges**, a line drawing of the outlines;
- and **pose sticks**, the character's skeleton drawn as coloured lines, the format many video models were trained to
  follow.

Those images are the **control sequence**. The video model is told to obey them while it paints everything else.

### Fourteen experiments, in the order we learned things

armature was founded on 10 August. Its record is unusual: every experiment writes down its predictions before it runs,
and a closing ruling afterwards says what was learned. Reading them in order is the best way to understand the tool.

**E01: can Blender produce the same control images every time?** Yes, byte for byte, across two separate runs. On the
way, a check caught a real defect: Blender's model importer quietly adds a hidden sphere to the scene, and our script
swept it into the "character". The other lesson was humbler. The experiment's first choice of test subject was a sword,
fifteen times longer than it was wide, which tells you nothing about a body. And none of the four test models had
bones named for a body (three had bones, called things like bone_0 to bone_29), so pose sticks were impossible.

**E02: does a rendered control actually steer a video model?** This was the question the whole tool rested on. With the
control present, the model's motion tracked it (a timing correlation of +0.52); without it, nothing (−0.06). Then the
surprise: we inverted the control images, so bright became dark, and tracking held (+0.58). The model was reading
**geometry, not brightness**. Its own record puts it this way: whatever the model is reading, it is reading the geometry, not the tone. One more thing was written down that day: a first experiment's subject is the test's
input, not the product's ceiling. A turntable of one figure had started to look like "what armature is for".

**E03: does authored motion come through?** The arm the control swung moved 85 degrees; the arm we left still moved
0.06. So the motion transferred. But the result was poor, and the reason was obvious once seen: the subject was a bare
wire armature, and the model had no body to paint. It traced a stick figure. The thesis was "untested, not falsified",
and rigging a real character became the thing everything waited on.

**E04: how much does the same request vary?** Ten generations of one request. With the random seed fixed, the
variation was exactly zero; between seeds it was about 0.16 on our measure. That gave us a unit to judge every later
difference by. It also put E02's bright-against-dark gap in perspective: 0.37 of that unit, too small to call one
better than the other.

**E05: was never run.** It was designed to test whether the model only copies the control at full strength and paints
only below it. Then someone looked at an output already on disk from E02: at full strength, given a body to paint, the
model painted. The premise was false before the experiment existed, so it was withdrawn at no cost.

**An audit, between E06 and E07.** Twenty-two paid generations, and not one authored shot anyone would use. The audit's
verdict on our own process: every check we had made sure an experiment was valid, and nothing made sure it was worth
running. It called it a system with excellent brakes and no steering. Since then, every spec that spends money has to
say where it leads.

**E06: could a reference image stand in for a rig?** No. With a painted knight as reference and the control still a
stick, the result was "a stick figure wearing armour". It did pin down a rule we still use: **the control owns the
outline; the reference owns the surface**, its material and costume. Where the control is silent, like a pair of horns
the stick figure doesn't have, the reference can add shape.

**E07: building the skeleton.** Seven rounds and no money spent. A rigged character with 22 named bones. Two shortcuts
failed instructively: an automatic retopology tool reported a tiny overall error (0.14% to 0.34%) while gouging a trench
through the mouth, and a popular remeshing add-on was ruled not safe for commercial use. Repairing the
original mesh worked; rebuilding it didn't.

**E08: the first painted shot.** The character landed in the scene and moved as directed. Before the shot, we had
predicted the face would read as our character's in about 30% of frames; it did in 4 of 5 sampled frames. The bar the
character stood in came from the prompt alone. A check we added that day overlays the pose sticks on the Blender render
before anything is spent:

![Three frames, 0, 32 and 64, of a wooden mannequin dancing in a grey Blender studio, with its pose skeleton drawn over it: coloured lines and numbered joints at the head, shoulders, elbows, wrists, hips, knees, ankles and toes. The skeleton sits exactly on the body in every frame.](/rnd/charts/issue-43-armature-e08-sticks.jpg)

That overlay caught invented toe positions that no other check had caught. It now runs before every spend.

**E09 and E10: a cleaner chain.** E09 measured how faithfully a motion survives being lifted from video and put back
onto our rig. E10 fed the model more frames per second of the same motion: the step-to-step jumps in the driving signal fell by 41%,
while the performance itself barely changed (8.6%). It looked better, so it was adopted. E10 also showed something
uncomfortable: the **whole scene** changed. A person appeared in the bar who wasn't asked for. E10 had changed the seed
and the clip length together, so the record doesn't yet say which one did it. Since then, a claim about a scene needs two seeds before we believe it.

**E11: what happens with no control at all?** In three waves. Wave 1: give the model only a start frame. The character's
features survived to the last frame with no help, but our empty studio turned into a bar with at least four people in it
by frame 8, and the camera pushed in on its own. Wave 2 was a lesson about checks: every gate was green, and the result was
65 frames with nothing recognisable after the first. The graph had wired a camera input into a model that had no channel for it; our licence record was
for weights the graph never loaded. Hence a rule now in the repo's charter: **a licence row is not a wiring claim**,
and a new gate that checks the graph loads what it claims. Wave 3, with the right weights, held the camera to within a
pixel across 81 frames, and failed anyway: it faithfully kept the empty void we had handed it. Each wave was a single seed.

**E12: give it a real room.** With a real scene in the start frame, the world held to the last frame on two seeds. And a
setting we had inherited without testing fell. Two sampler settings were the only things changed between these panels:

![A grid comparing the same two seeds at frames 40 and 80, left column at the old settings and right column at the new ones, with the start frame, weights, steps and prompt byte-identical. On the left, the wooden figure is smeared and partly transparent in a crowded bar; on seed 2026081233 at frame 80 its head blurs into a fan of copies. On the right, the figure is sharp and solid, mid-dance, in the same bar. In the bottom-right panel, several people in the crowd have turned into wooden figures too.](/rnd/charts/issue-43-armature-e12-settings.jpg)

At the old settings (guidance 3.5, the "euler" sampler), seeds lost a head and grew a limb; at the settings the model's
own catalogue lists (6.0, "uni_pc"), the same seeds held the figure to frame 80. The cost is in the last panel, on one seed of the two: stronger
adherence pushed our "wooden figure" description onto the crowd. The fix is to scope that description to the subject.
Hands and arms at speed still fail by frame 80, at either setting.

**E13: through a model that has never seen our character.** We gave a hosted reference-to-video model only our authored
references, no control at all. Predictions written down blind beforehand expected a model trained on humans to overwrite a wooden figure's
structure, three of them in all. None was right: identity held on both arms and both seeds. The reference backgrounds also
steered the world, grey plates giving a grey studio and a warm bar clip a warm interior, though four generations
aren't enough to say whether that's the references bleeding through or the model's own default. Holes in the
character's texture came through too, and fixing them upstream is now the top priority. The record calls the wrong
predictions the third sighting in a row of one-directional pessimism about these models, and writes that down as
something to correct for.

**E14: a style lever.** A style LoRA (a small add-on that shifts a model's look) applied to the free route carried the new style on both arms, held the
character on one and lost it on the other, where an arm morphed and the legs fused by frame 80. Its blind
predictions broke the pessimism streak: this time a prediction erred the other way. Miscalibration runs both ways.

### Where it stands

armature's README calls the thesis "measured at product level". It holds three routes, and none is the default because
it came first:
- **Driven**: pose sticks steer a dance model. Proven at shot level, and parked.
- **Free**: an authored start frame, and the model moves the camera. Identity holds without help; a real room holds on
  two seeds.
- **Composed**: authored references into a hosted model. Identity held; the model decides the shots.

It is version 0.5.0 with 8,051 tests, and deliberately not 1.0: its definition of done is a shot the studio accepts and
uses in a real project, and that hasn't happened yet. What it says it can't do: hands and arms at speed, and any claim
about camera accuracy on photographic worlds until it has an instrument that can measure one.

### What the field looks like now

We ran a Deep Research report on controllable video in late 2026. We opened only a few of its sources ourselves (the
model listings for the two items below that matter most to us); the rest is the report's account. The headline: Lightricks has published **LTX-2.5 Layout-to-Render**, which turns a clay or simple-shape playblast from
Blender plus one painted start frame into styled video. That is armature's idea, built into a model. We confirmed the model is listed. Per the report, its card
also takes optional middle and end frames, and asks for two things we had learned the hard way: never use the raw grey render as the first frame, and keep words like "clay"
and "3D" out of the prompt. Its repository is gated behind Lightricks' own licence, which we haven't accepted, so for
now it's a candidate route, not a tool.

Three other findings, from the report, line up with what the experiments found:
- **Human-pose models force human proportions.** A stylized or non-human character driven by a standard human skeleton
  gets adult shoulders and limbs. Driving from depth, outlines and masks, or from the character's own rig, avoids that,
  which is what armature already does.
- **Identity scores need cropping.** A standard "subject consistency" score is corrupted by the background; cropping to
  the character fixes it. And a camera check has to come first, because a model that ignores the camera scores falsely
  well on identity.
- **The licence traps are in the small preprocessing models,** not the big ones. More on that below.

## Blender 5.3 arrived, and armature didn't notice

armature lives inside Blender, so a new Blender is a real event for it. Blender 5.3.0 came out yesterday, and before
installing it we read what it changes, at the release notes.

Two changes could have touched armature:
- **The compositor now runs a stack of effects** instead of one compositor node group. armature builds its render passes
  by assigning one node group, so this was the change we expected to break something.
- **Vulkan is now the default graphics backend** on Windows and Linux, and published reports say Vulkan and OpenGL
  don't produce pixel-identical renders. armature's control images are exact by design (E01), so this mattered too.

The headline feature, a DLSS denoiser for Cycles, turned out not to matter to us: the release notes say it runs in the
interactive viewport only, and armature renders headless.

**What we measured.** We installed 5.3 beside 5.2 and ran armature's Blender tests against it:
- **3,166 passed, 18 skipped**, on 5.3 with its default backend.
- The tests that start a real Blender process (107 of them, in 8 files): **107 passed, 5 skipped on Vulkan, and 107
  passed, 5 skipped with OpenGL forced.**

So the old single-group compositor path still drives a background render on 5.3, and armature's checks pass on either
backend. Production renders stay on 5.2 for now anyway; it's the long-term-support release.

One small correction to the research we read: a widely repeated name for 5.3's new rotation-conversion call was wrong.
The Python API notes call it `convert_rotation_mode`, a method on objects and pose bones.

## One model name, two licences

Some of armature's control signals could come from small preprocessing models rather than from Blender, and the
research we read this week found the licence traps there rather than in the video models. The clearest case is
**Depth Anything 3**. We read the licence tag on every one of its published checkpoints:

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
also blocked DA3-Large-1.1 along with 1.0. That is in review now, and the plan is to tie each entry to a repository and
revision rather than a name. The simpler protection is the one armature already has: it renders depth, masks and pose
straight out of Blender, so none of these models is needed at all.

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

**What we don't know yet.** Our first explanation was that two minutes of readings is shorter than one training
update, so a series lands mostly in one part of it. Our fact-check pushed back: nothing tied a reading to a part of
the update, so that was a guess. Each update spends about 259 seconds having the model write answers and about 28
seconds learning from them, so even a long series is mostly the first part. And the trainer's own peak, 18,466 MiB,
sat above every reading in that first series, which fits the peak falling in the short learning part that two minutes
can miss. A second short series a few minutes later read 10,529, 15,781 and 22,943 MiB.

**What we changed.** From the next save, the series runs for ten minutes (120 readings), with every reading
time-stamped so it can be lined up with the run's own record of when each part of the update started. The rule for
stopping is written down in advance: hold the run at a save only if the ten-minute middle reading is over the line
**and** the lowest or highest reading has risen past what the earlier chunks showed.

<!-- PLACEHOLDER: the step-180 ten-minute series result and its chart go here before publish. -->

## Finished, then stopped

For the first time in four days, a rented Colab card ran one of our jobs: a 500-step style-training rung for
[style-dataset-lab](https://github.com/mcp-tool-shop-org/style-dataset-lab), on an RTX PRO 6000 Blackwell with 96 GB.
It trains a LoRA, the small add-on that teaches an image model one style, on a set of images from our own canon.

**What went right.** The 57.7 GB base model downloaded in 163 seconds. Training reached step 500 of 500, and both
checkpoints were saved, at step 250 and at the end. The window cost 3.395 Colab compute units (1,216 seconds at 10.05 per
hour) and closed cleanly.

**What went wrong.** As the run handed over from training to making its final sample images, the launcher's own
**stall guard** stopped it.

![Diagram titled "The guard was watching a phase that had already ended". A timeline of one training run on a rented GPU: Setup (setup log grows), then Training: step 1 to 500 (setup log stops growing, as expected), with flags at save: step 250 and save: step 500, then Final sample images, marked with a stop sign and "stopped here", then a faded Close and fetch. Above it, a status log with two blocks reading "phase: run" and a torn third block, "half-written block: no phase". Arrows lead from the torn block to "Guard reads a missing phase as 'setup'", then to "Setup log unchanged for 14.5 min (limit 10 min) → stop", then down to the stop sign. At the bottom: "The fix: skip half-written blocks, as the memory guard already did."](/rnd/charts/issue-43-stall-guard.jpg)

That guard watches the setup log during setup, and fires if the log stops growing for 10 minutes. But setup had ended
long before: the run was training, and a training run isn't supposed to write to the setup log. The launcher reads the
run's health from a log of status blocks. The last block it read had been cut off mid-write, so it held no phase at all,
and the guard treated a missing phase as "still in setup". A second guard in the same launcher, one that watches memory
on the rented machine, already skips half-written blocks. The stall guard didn't.

While reading the run's files we found one more: the memory guard read about 340 MB, against the trainer's roughly
13 GB, because it was reading the wrong process group. A guard that sees a twentieth of the memory can't protect much.

The fix, in review now, makes the stall guard skip half-written blocks, records both memory readings and uses the
larger, and adds three facts to the run record: steps done, whether the final checkpoint exists, and whether training
completed. The run record had said `trained: false` for a run that trained.

Elsewhere on Colab, a judge test for another study asked for an A100 three times and was refused all three ("no
capacity"). A refusal costs nothing; it tries again in daytime.

## What a single TPU chip is for

Our Colab plan can open two kinds of TPU, Google's own AI chips, as well as GPUs: a **v5e-1** at about 2.92 compute
units an hour and a **v6e-1** at about 4.08, one chip each. We have barely used them, so we asked a Deep Research report
what they're good for, and checked what we could.

The short answer: a single TPU chip is a fast matrix engine that wants to be fed **many requests at once**, with shapes
it has already compiled for. It is not a drop-in GPU.

![Diagram titled "A single TPU chip wants many requests at once". Left panel, "One request at a time": a TPU chip reads the model weights from memory, with "memory: every weight read once per word", and one token comes out; caption: "Speed is set by memory bandwidth. Our RTX 5090 (1,792 GB/s) matches a v6e-1 (1,638 GB/s)." Right panel, "Many requests at once": the same chip and memory, with many request lanes going in and many token streams coming out; caption: "Each weight read now serves many answers at once. This is where a TPU chip earns its keep." An amber strip along the bottom: "First, it compiles for every input shape it sees: 1.5 to 34 minutes reported. Change the shape and it compiles again."](/rnd/charts/issue-43-tpu.jpg)

- **Where it would help us.** Running a translation model like TranslateGemma on a batch of text, while our own card is
  busy training. Today our README translations run on the RTX 5090 and wait whenever a training chunk holds it. Also
  batched scoring with small models, and small-model fine-tuning in JAX, Google's numerical library.
- **Where it wouldn't.** Generating one answer at a time is limited by memory bandwidth, and our RTX 5090 (1,792 GB/s,
  free to us) matches the v6e-1 (1,638 GB/s) and roughly doubles the v5e-1. Our image model, Qwen-Image, is too big
  for either chip, and none of the controlled video models armature uses has a TPU version.
- **The trap.** Before a TPU produces anything it compiles the model for the exact shapes it will see, and the report
  found that taking anywhere from 1.5 to 34 minutes. Change the length of the input and it compiles again. Colab's own
  `colab run` command gives up after 30 seconds without output by default; we checked that against our copy of the
  tool. Our TPU launcher uses a different command, so it isn't affected, but any new TPU job has to plan for it.
- **And the numbers differ.** A TPU rounds its arithmetic differently from a GPU, enough to change which word a model
  picks on a long answer. We already never pool results across hardware; the report gives one more reason.

We will try one small test: TranslateGemma on a v6e-1, translating one README in pieces small enough for its 2,000-token
limit. If it works, translations stop waiting for the training card.

## The daily watch

<!-- PLACEHOLDER: R&D's morning watch block (11 November) goes here. -->
