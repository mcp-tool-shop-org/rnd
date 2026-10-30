---
title: '29 October: repaired test sets certify 44 of 50, long tool lists cost a model its "no", and Cosmos 3 on one rented card'
description: "Rewritten so that every pair is a clear contradiction, and keyed blind before any reader saw them, the reasoning-dataset-lab sets certified 44 of 50, against 26 before; the thinking setting we suspected turned out not to be what cut the length stops. A test of tool lists from 5 to 100 found that two local models kept picking the right tool, but one of them declined less often when the prompt grew long, and retrieving five tools kept its \"no\" intact. NVIDIA's Cosmos 3 made its first clips on rented cards: one Nano clip on one card, a 30-second rollout from the two-armed robot checkpoint, and five shrunk versions of the bigger Super model, of which Intel's int4 export is our provisional choice. Then the raw files behind our figures get a public home, a read of GitHub's Universe announcements, notes in brief, and the daily watch."
issue: 34
date: 2026-10-29
highlights:
  - "<strong>44 of 50 sets certified.</strong> Every pair rewritten to be a clear contradiction and keyed blind first, the sets certified 44 of 50, against 26 before. The cleaner sets, not the thinking setting, cut the length stops."
  - "<strong>Long tool lists held; the \"no\" slipped.</strong> With 5 to 100 tools, Granite 4.2 8B and Qwen3.8-27B kept picking the right tool. Granite declined 19 of 30 no-tool requests at 40 tools and 18 on a padded 10-tool prompt; retrieving five tools kept it at 27 to 30."
  - "<strong>A world model on one rented card.</strong> Cosmos 3 Nano made an 8-second clip on one RTX PRO 6000 card in a 628-second window, about 1.55 compute units, with generation within 2% of our estimate."
  - "<strong>Super on one card, for now in int4.</strong> Five shrunk versions of Cosmos 3 Super ran on one G4. Intel's int4 export wasn't separable from FP8 on fidelity, and ran faster in less memory, so it's our provisional choice."
  - "<strong>rnd-data is public.</strong> The raw files behind our figures, 111 runs so far, now have a repository of their own."
  - "<strong>GitHub Universe 2026.</strong> We read the agent-centred announcements on GitHub's own pages, and checked an AI search summary of them against those pages."
---

Results from 28 October: a repaired test set and its rerun, a test of long tool lists, and NVIDIA's Cosmos 3 on
rented cards, from one clip to five shrunk versions of its biggest model. Then the raw files behind our figures get a
public home, a read of GitHub's Universe announcements, notes in brief, and the daily watch.

**In this issue:**

1. [The repaired sets: 44 of 50 certified](#the-repaired-sets-44-of-50-certified-and-the-thinking-setting-wasnt-the-fix)
2. [How many tools can a local model take?](#how-many-tools-can-a-local-model-take-the-list-held-the-no-slipped)
3. [A world model on one rented card](#a-world-model-on-one-rented-card)
4. [Cosmos 3, continued: the robot-arm checkpoint, and Super on one card](#cosmos-3-continued-the-robot-arm-checkpoint-and-super-on-one-card)
5. [rnd-data: the raw files behind the research](#rnd-data-the-raw-files-behind-the-research)
6. [GitHub Universe 2026: the platform turns toward agents](#github-universe-2026-the-platform-turns-toward-agents)
7. [In brief](#in-brief)
8. [The daily watch](#the-daily-watch)

## The repaired sets: 44 of 50 certified, and the thinking setting wasn't the fix

Issue 33 showed that two readers agreeing on a set of values is a weak filter: most of the sets they "certified" held
pairs that were arguable, not contradictions. This is the repair and the rerun.

**The repair.** All 50 five-value sets in reasoning-dataset-lab were rewritten so that every ordered pair is a
contradiction no one could argue with. New tests catch the faults we found before: an attribute must name one property,
no relative terms, no value whose label contains another, and no two values a single machine can hold at once. Then an
outside model keyed all 1,000 pairs blind, before any reader saw them. It took three rounds: 120 of the 1,000 pairs came
back "arguable" in the first, 16 of the 560 re-keyed in the second, and none of the 60 in the third. On the old certified
sets, only 3 of 26 had been clean on all 20 pairs.

**What "certified" means now:** a set passed the blind key first, and then both readers called every one of its 20 pairs
a contradiction.

**The rerun.** 44 of 50 sets certified, against 26 before. 2,000 reader calls, none failed. Eleven pairs kept the other
six sets out, and we read each one:

- 6 are faults in the pairs that the blind key passed. Four are "accelerating" pairs in two operating-mode sets (a
  variable-speed compressor can speed up while loaded; a turbine "accelerating" can read as a load ramp while online). Two
  are in a metering-device set, where an electronic valve can run a constant-pressure mode. The readers were right to
  refuse them, so those three sets belong in the queue.
- 5 are reader mistakes: 3 by one reader, 2 by the other.

A read of 10 of the 44 certified sets found 9 clean and 1 with a mild wording note. The same read of the old sets found 5
of 10 clean.

![Three blind-key rounds, then the rerun. Round 1 found 120 of 1,000 pairs arguable across all 50 sets, round 2 16 of 560 pairs across the 28 sets re-keyed, and round 3 none of 60 across the last 3. In 2,000 reader calls with none failed, certified sets rose from 26 of 50 to 44 of 50. Six sets were queued on 11 refused pairs, 6 pair faults and 5 reader mistakes. Length stops for one reader: 25 at full and 22 at medium on the old sets, 2 at medium on the repaired sets.](/rnd/charts/issue-34-certification-repair.svg)

**The thinking setting.** One reader (Nemotron 3.5 Lightning) now runs at "medium", an effort hint its template
understands, not a cap on thinking. In the rerun it hit the token limit only twice in 1,000 pairs, against 25 before. That
looked like the setting at work, so we ran it at medium on the old pairs too: 22 limit stops against 25 at full thinking,
and mostly on different pairs. The drop came from the cleaner sets, not the setting. Medium did give the same verdict as
full thinking on 95.5% of the pairs that got a verdict at both, in about 8% less time, so it stays; it just isn't the fix
for length stops.

**Limits.** Our read of the 11 pairs and of the sample is one reader's judgement, and the blind keys come from one outside
model. Where the 35 flipped verdicts between settings sit hasn't been read yet.

**Next:** reword or replace the three faulty sets, and add a generator rule for modes a variable-speed machine can hold
together.

**The data is public.** Everything above is in reasoning-dataset-lab under
[`certification/v3/`](https://github.com/mcp-tool-shop-org/reasoning-dataset-lab/tree/main/certification/v3): the
manifest of the 44 certified sets, the queue of 6, both reader controls, and the findings. `medium-arm/` holds the
medium run on the old pairs, filed as an addendum to the earlier run so the two settings are never pooled, and
`second-keying/` holds all three blind-key rounds (1,000, 560 and 60 pairs). Before it merged, a separate model
recomputed every figure from the committed files. Every number comes from those JSON files except run times and peak
memory, which come from the run logs, so you can redo the arithmetic yourself.

Code: reasoning-dataset-lab PRs 21 and 23; data: PR 24.

## How many tools can a local model take? The list held; the "no" slipped

Agent setups hand a model a list of tools and expect two things: it picks the right one when one fits, and it declines
when none does. A common worry is that a long list breaks the first. We tested both on two local models, Granite 4.2 8B
and Qwen3.8-27B, with lists of 5 to 100 tools.

**The setup.** Each list size got 200 calls: 170 where a tool fits and 30 where none does. The same 30 no-tool requests
ran in every cell, so cells compare request by request. Two more arms separated the causes:

- **A length control:** 10 tools, padded with neutral text to the length of the 100-tool prompt.
- **A retriever:** it picks the 5 most relevant tools from the full list, so the prompt stays about 1,040 tokens.

Settings: temperature 0, each model's own tool template, one A100 40 GB card.

**Picking the right tool held.** Granite chose correctly on 164 to 170 of the 170 calls in every cell, its lowest at
100 tools. Qwen managed 169 or 170 throughout. Up to 100 tools there was no cliff for either.

**Declining is where Granite slipped,** and it followed the prompt's length, not the number of tools:

| Tools in the prompt | Prompt length (tokens) | Granite declined | Qwen declined |
|---|---|---|---|
| 5 | 1,004 | 28 of 30 | 30 of 30 |
| 10 | 1,737 | 29 of 30 | 30 of 30 |
| 20 | 3,184 | 26 of 30 | 30 of 30 |
| 40 | 6,108 | 19 of 30 | 29 of 30 |
| 70 | 10,457 | 22 of 30 | 27 of 30 |
| 100 | 14,804 | 27 of 30 | 28 of 30 |
| 10, padded to 100-tool length | 13,270 | 18 of 30 | 29 of 30 |
| retriever's top 5 | about 1,040 | 27–30 of 30 | 29–30 of 30 |

The prompt lengths are Granite's. Qwen3.8-27B ran as two halves of the design, split by seed, and its counts pool both.

![Tool lists from 5 to 100. Picking the right tool held flat: Granite 4.2 8B 164 to 170 of 170, Qwen3.8-27B 169 to 170. Declining on 30 no-tool requests, plotted against Granite's prompt length with 95% intervals and no trend line: Granite 28 of 30 at 5 tools, 29 at 10, 26 at 20, 19 at 40, 22 at 70, 27 at 100, 18 on the 10-tool prompt padded to 100-tool length, and 27 to 30 with the retriever's top 5. Qwen, pooled from two halves, 27 to 30 of 30 everywhere. Only the 40-tool and padded drops are significant after correction (p 0.02 and 0.011); the 70-tool drop is not (p 0.35). Interim: Gemma 4 31B is still running.](/rnd/charts/issue-34-tool-count-abstention.svg)

- **Two drops are real after correcting for the number of comparisons:** 40 tools, and the padded 10-tool prompt. The
  padded prompt carries only 10 tools, yet does as badly as any list, so length alone can do it.
- **It isn't a steady slide.** 100 tools came back to 27 of 30, and the 70-tool drop doesn't survive the correction.
  "The longer the list, the less it declines" would overstate it.
- **With the retriever,** Granite declined 27 to 30 of 30 at every list size.
- **Qwen stayed flat,** with no change near significance.

**Limits.** 30 no-tool requests per cell is small: one request is 3.3 points, and most intervals overlap. This is
two model families, with one template each. The padding was neutral text, so it shows that length alone can do this,
not which part of a real tool list does. The retriever is one retriever. A third family, Gemma 4 31B, is running now,
so these results are interim.

**What we take from it:** here, retrieving a few tools kept the prompt short and protected Granite's "no". Whatever the
setup, test declining on its own. Accuracy alone didn't show this.

## A world model on one rented card

Robotics in simulation is our next research track, and NVIDIA's Cosmos 3 is where it starts: open world models that
predict what a camera would see next, including checkpoints tuned to show how a scene changes after a robot acts. The
first rung asked only one thing: does it run on the cloud GPUs we rent, and what does a clip actually cost?

**Which model.** NVIDIA ships Cosmos 3 Super (64B) only in BF16, about 128 GB of weights, so it fits on no single Colab card.
Cosmos 3 Nano (16B, about 35 GB, under the OpenMDW-1.1 licence) fits.

**The run.** One clip of the model card's own example prompt (1280×720, 189 frames, 35 steps, one seed) on one RTX PRO
6000 Blackwell card:

| Stage | Measured |
|---|---|
| Download, 35 GB | 97 s (362 MB/s) |
| Setup (environment and pinned wheels) | 53 s |
| Generate 35 steps and decode | 430 s (about 11.6 s a step) |
| Whole window | 628 s, about 1.55 compute units |

Peak GPU memory was about 42 GiB allocated and 51 GiB reserved, with roughly 45 GB of the card to spare; host memory
barely moved (2.9 GB). The output is an 8-second, 24 fps clip of a robot arm scrubbing a plate.

**Estimate against measurement.** The design scaled NVIDIA's published figure (93 s a clip on a B300) to this card and
predicted about 420 s of generation; it came in at 430, within 2%. Setup and download were much faster than guessed, so
the window cost under half the design's projection of about 3.6 units.

**How it was run.** A free CPU stub ran every install step first, for about 0.005 units. A test suite against a fake
Colab command line checked that the launcher refuses a wrong card, too little memory or disk, or a changed script before
anything downloads, and it caught a launcher defect before any spend. An outside model reviewed the harness and the
licence.

**Limits.** One clip and one seed: this says the model runs and what it costs, not how good its output is. The next rung,
a simulation checkpoint on its own example, gets its own design.

## Cosmos 3, continued: the robot-arm checkpoint, and Super on one card

The Nano clip above was the first rung. Three more runs followed the same day: a checkpoint built for a two-armed robot,
five shrunk versions of the bigger Super model on one Colab card, and Super at full precision on one rented
B200 to serve as their reference.

### The two-armed robot checkpoint

Cosmos3-Nano-Sim-Bimanual predicts what a camera sees as a simulated two-armed robot carries out a list of actions. We
ran one 30-second rollout (901 frames at 832×480, one seed) through its own video API on a G4 card (RTX PRO 6000
Blackwell, 96 GB).

- **Inference took 29.1 s,** which is 31.0 frames a second. The model card gives 20.6 for this card at 480p.
- **Peak GPU memory** was 51,980 MB, and the whole window took 5 min 27 s and 0.81 compute units.
- **Two earlier tries failed on the install, not the model.** First a dependency needed a Rust compiler, which a free
  CPU stub caught. Then on the paid run, the serving stack's just-in-time CUDA compile found no compiler. A toolchain
  step now fixes that, and every stub proves it.

![The two-armed robot checkpoint's 327-second window on one G4: 110.8 s of setup, 91.2 s downloading 31.8 GB at 348.9 MB/s, 35.0 s starting the server, 29.1 s of inference for a 901-frame rollout at 31.0 frames a second against the model card's 20.6, and 60.9 s for opening, the VM check, stopping and fetching. Closed-loop control is planned, not yet measured.](/rnd/charts/issue-34-bimanual-window.svg)

This run plays back a fixed action file, with no controller in the loop, so it says the checkpoint runs and how fast.
It says nothing about whether the robot does its task well. Faster than the card is one run on one card type, not a
benchmark. Closed-loop control is the next rung, and it isn't designed yet.

### Super, shrunk to fit one card

*Corrected 30 October: see the last limit below.*

Super won't fit a single Colab card in BF16. Uploads on Hugging Face shrink it, so we asked which of them
run on one G4, how fast, and in how much memory. Each made the same three 61-frame clips at 480p (35 steps, the same
prompts and seed), plus a 50-step still:

| Version | Time a step | 61-frame clip | Peak memory allocated | Window cost |
|---|---|---|---|---|
| FP8 (made with NVIDIA ModelOpt) | 3.83 s | 137–139 s | 69,954 MiB | 3.09 units |
| NVFP4 (ModelOpt) | 7.14 s | 253–254 s | 47,396 MiB | 3.07 units |
| NF4 (bitsandbytes) | 3.37–3.38 s | 122 s | 39,750 MiB | 2.52 units |
| int4 (AutoRound, a second export) | 3.33–3.35 s | 120–125 s | 41,066 MiB | 1.59 units |

- **All four ran every clip they were given,** and none ran out of memory. The four windows cost 10.27 units together.
- **At 720p** (FP8 and NF4 only), a clip took 339 s and 326 s, at a peak of 76,054 and 45,851 MiB.
- **Cutting the steps from 35 to 20** cut the FP8 clip from 138.6 s to 80.0 s, 42% less, with no change in memory.
- **A fifth version,** Intel's own int4 AutoRound export, needed changes to its config files to load and joined later.
  It took 3.36 s a step, at a peak of 39,581 MiB at 480p and 45,680 MiB at 720p.

The table shows what runs and what it costs. How close each version looks to full precision is a separate measure.
We scored every clip against the B200 reference below in two ways: LPIPS, a learned measure of how different two
frames look (0 means identical), and the cosine similarity of DINOv2 image features (1 means identical). A first round
used one seed, three prompts and a still. A wider round then used 8 prompts and 3 seeds; these are the 21 clips that all
five versions share:

| Version | LPIPS (lower is closer) | DINOv2 (higher is closer) |
|---|---|---|
| int4 (AutoRound, Intel's export) | 0.320 | 0.765 |
| FP8 | 0.341 | 0.770 |
| NVFP4 | 0.387 | 0.724 |
| NF4 (bitsandbytes) | 0.401 | 0.716 |
| int4 (AutoRound, a second export) | 0.406 | 0.723 |
| Nano at full precision (a different model) | 0.578 | 0.558 |

Paired clip by clip against FP8:

- **Intel's int4 and FP8 can't be told apart.** FP8 was closer on 9 of 21 clips (sign test p = 0.66). FP8's mean LPIPS
  was 0.021 higher, with a 95% bootstrap interval of −0.014 to +0.058, which takes in zero.
- **FP8 is closer than the other three.** It was closer than NVFP4 on 16 of 21 clips (p = 0.027), and than NF4 and the
  second int4 export on 15 of 21 each (p = 0.078). Its mean was 0.045 to 0.065 lower, and all three intervals stay below
  zero.
- **Nano is a baseline, not a shrunk Super.** Its distance shows how different the smaller model's clips are, not what
  shrinking costs.

The two are not separable on fidelity, and on everything else measured Intel's int4 is ahead. It took 3.36 s a step against
FP8's 3.83 in the wider round, and peaked at 39,581 MiB at 480p against 69,954. It ran 720p in 45,680 MiB against
76,054, and had the narrowest spread across the three seeds of any Super version (0.311 to 0.328). So it's our
provisional choice. It stays provisional until a re-run with prompts that fit a 2.5-second clip and a blind ranking by
people, both still being designed, support it; it goes back to FP8 if they prefer FP8 by more than their own
run-to-run spread.

The scores have limits:

- **Similarity, not preference.** They measure closeness to full precision, not which clip a person would pick.
- **One card type,** and 8 prompts at 480p, 61 frames and 35 steps.
- **Repeats.** Repeats of FP8, NF4 and the second int4 export matched the first run byte for byte, so on one card type the
  differences come from the prompt and the seed, not from noise between runs. NVFP4 and Intel's int4 weren't repeated.
- **The card counts too.** Part of each gap comes from the card, not from the shrinking. On the first round's clips,
  FP8 on the B200 scored 0.345 against full precision on that same card, and FP8 on the G4 scored 0.193 against FP8 on
  the B200.
- **Three prompts ask too much of the clip.** Three of the eight prompts (a box picked up and placed on a pallet, a
  bowl handed between grippers into a rack, and a robot walking through a door) ask for more than a 2.5-second clip
  can show, so no version finishes them. The scores compare each version with full precision on the same prompt, so
  they still hold, but they don't show whether any clip is good. We are re-running the comparison with prompts that
  fit.

Why FP8 is no faster than the 4-bit versions here hasn't been looked into.

![Five shrunk versions of Cosmos 3 Super against the full-precision model over 21 shared clips (8 prompts and 3 seeds), plus the smaller 16B Nano model at full precision as a separate baseline. Mean LPIPS distance to full precision (0 is identical, lower is closer), with the range of the three seed means, time a step and peak memory at 480p: Intel's int4 AutoRound 0.320 (seeds 0.311–0.328; 3.36 s; 39,581 MiB), FP8 0.341 (0.311–0.363; 3.83 s; 69,954 MiB), NVFP4 0.387 (0.337–0.426; 7.12 s; 47,396 MiB), NF4 (bitsandbytes) 0.401 (0.372–0.441; 3.37 s; 39,753 MiB), a second int4 AutoRound export 0.406 (0.383–0.438; 3.39 s; 41,066 MiB), and Nano 0.578 (0.575–0.581; 0.81 s; 36,002 MiB). Paired against FP8, Intel's int4 is not separable on fidelity (FP8's mean 0.021 higher, 95% interval −0.014 to +0.058, FP8 closer on 9 of 21 clips, p = 0.66); the other three trail FP8, with intervals entirely below zero. Intel's int4 is the provisional choice, to be re-checked in a re-run with prompts that fit the clip and a blind ranking by people.](/rnd/charts/issue-34-super-shrunk-comparison.svg)

### The reference: full precision on one B200

The scoring needs Super's own clips at full precision, with the same prompts and seed. No Colab card holds it, so this
one run went to a rented B200 (about 180 GB) on RunPod.

- **The 132.7 GB download** took 42.6 s (3,116 MB/s), and the model loaded in 29.1 s.
- **A 61-frame 480p clip** took 37.9–44.0 s (1.03 s a step), the still 10.5 s, and the 720p clip 98.3 s.
- **Peak memory allocated** was 129,206–129,207 MiB at 480p and 135,320 MiB at 720p.
- **The run** took about 7.5 minutes and was booked at $1.09.

The B200's times aren't a speed comparison with the shrunk versions: it is a different card at a different precision.

## rnd-data: the raw files behind the research

Each issue quotes figures from runs: a window's log, a reader's verdicts, a cost ledger. Those files now have a public
home of their own, [rnd-data](https://github.com/mcp-tool-shop-org/rnd-data), so a reader can check a figure against
the run that produced it, not only against our summary of it.

**What's in it.** 111 runs so far, from two ingests on October 19 and 20: 83 Colab runs (each retry of a window counts as its own run), the weekly watch's runs and
reports, a handful of RunPod and tool receipts, and 11 xrpl-lab runs on the XRP Ledger's test network. Each run has a
manifest listing its files, and every public file in it carries its SHA-256, its size and its licence. There are 1,274
public files:
- **1,096 small files** (256 KB or less, about 5.7 MB in all) are in git.
- **178 larger ones** are stored once each, by hash, so they come to only 13 distinct files, about 430 MB. Most are one
  llama.cpp server build that many Colab windows uploaded. These sit in a blob store on the studio's backup drive for
  now, and are due to go public as a Hugging Face dataset in a later phase.

The data is CC BY 4.0; scripts are MIT, and a third-party file such as the llama.cpp build keeps its own licence
(MIT), which its manifest names.

**What stays private, and how that shows.** Open is the default, and a file is private only for a named reason. Of the
files held back, 566 are private for their content (381 hold test-item text, 185 are plans not yet approved). They are
left out of the manifests and only counted by reason. Another 192 are private only because the identity scan flagged
them; these are listed by path and size, with no hash. No private file's hash is published, because the hash of a
short file can be matched by guessing its contents. The private copies are held in a separate private repository.

**How to check a figure.** Download a file and compare its SHA-256 with its manifest; `sha256sum` is enough, and the
README gives a one-line command that checks every file in git at once. CI does the same on every pull request: it
re-hashes every file, and fails on a file no manifest names, a private entry with a hash, or a machine path in a
manifest. An experiment in the rnd library points to its runs by id: the stage-1 regeneration experiment names 74 of
them.

**What's not done yet.** The runs in this issue (the certification rerun, the Cosmos clip, the current sweep) haven't
been ingested yet, so for now their receipts are only in the experiment write-ups. The small read-only Python package
that lists and shows runs (`rnd-data`, version 0.1.0) has its release workflow in place, but it isn't on PyPI yet.

Read more: [the landing page and handbook](https://mcp-tool-shop-org.github.io/rnd-data/).

## GitHub Universe 2026: the platform turns toward agents

GitHub's Universe announcements on 2026-10-28 have one theme: the unit of work is no longer a line of code a person
writes, but a task an agent carries from issue to merge. We read the announcements on GitHub's own pages, and we also
checked an AI search summary of them against those pages. The summary was mostly right, and the places it went wrong
are worth a look.

**What GitHub shipped**
- **The Copilot app,** a separate app built around agent work. Inside it, **Copilot Projects** (preview) splits a goal
  into parallel agent sessions across one or more repositories. **Computer use** (preview, macOS and Windows) lets
  Copilot operate desktop apps. It asks before it takes control, and organizations can switch it off.
- **Copilot Fusion** decides per task whether to use one model or combine several, at a Standard, High or Max effort
  setting. GitHub's figure: on the Artificial Analysis Coding Agent Index, Fusion Max scored within 2 points of Opus 5.5
  Max, at half the cost and 40% less time per task.
- **Security.** AI Scan checks a whole repository on demand and hands what it finds to Copilot to fix. It also checks
  pull requests in languages CodeQL doesn't cover. AI push protection blocks unstructured secrets, such as plain
  passwords, at push time. A package firewall stops malicious or risky npm packages before they install, and
  reachability analysis shows which vulnerable functions a JavaScript codebase actually calls.
- **The platform.** Stacked pull requests split a large change into linked PRs that are reviewed apart and merged as a
  stack. Copilot Automations run tasks on demand, on a schedule or from a trigger. Copilot Connectors give one sign-in
  to MCP servers such as Vercel, Cloudflare and Sentry.
- **Capacity.** GitHub reports adding 4 million CPU cores, 160 PB of fast storage and 50 Tb/s of network capacity this
  year. Its Git architecture now separates storage from compute, and its move to a multi-region Azure deployment is due
  to finish early next year.

**The Octoverse numbers** (October 2025 to September 2026, public and private repositories)

| Measure | Figure |
|---|---|
| Commits | 34.3 billion |
| Pushes | 17.9 billion, more than 2024 and 2025 combined |
| Developers | over 225 million (United States 38.3 million, India 32.0 million) |
| Pull requests begun as an agent's first draft | over 40% in September, against 17% in March |

The agent share counts only agents GitHub can detect, so it is a floor. TypeScript is still the most used language by
contributors. Rust grew fastest of the top languages; the report's text says it doubled, while its chart puts the
growth at 162%.

**Where the summary drifted.** The AI summary had most of this right, but:
- It put Fusion at "40% faster" and "up to 77%" cheaper. GitHub's own figure is half the cost and 40% less time, and
  only for the Max setting on one benchmark against one model. None of GitHub's pages gives a 77% figure.
- It dropped two qualifiers: that Projects and computer use are previews, and that the agent share is a floor.
- It gave Rust's growth as a plain doubling, without the chart's 162%.

None of these is a big error, but each one makes the claim stronger than GitHub's own, which is why we check a
summary against the page it summarises.

**For the studio.** We publish npm packages, so the package firewall and reachability analysis apply to our work. AI
push protection would add a check alongside the identity scan we run before each push. Fusion's figures are GitHub's
own benchmark; we haven't measured them. Relevance: watch.

Sources: [the Universe recap](https://github.com/events/universe/recap),
[GitHub's announcement](https://github.blog/news-insights/company-news/github-universe-2026-evolving-every-layer-of-the-stack/),
[the Copilot app changelog](https://github.blog/changelog/2026-10-28-github-copilot-app-universe-releases/),
[Octoverse 2026](https://github.blog/news-insights/octoverse/octoverse-commits-pushes-reach-new-highs-in-2026-as-developers-build-with-agents/).

## In brief

**CUDA Rust, live.** NVIDIA Developer streamed "CUDA Live: Introduction to CUDA Rust" on 2026-10-28 at 18:00 UTC
([recording](https://www.youtube.com/live/6DKmniAOhok)): the team writes, builds and runs Rust GPU kernels and explains
when to use each of its two tracks. The code is [NVIDIA/cuda-rust](https://github.com/NVIDIA/cuda-rust) (Apache-2.0),
which its README calls an early-stage research project, with API breakage to be expected.
- **cuda-oxide** is the SIMT track: a custom rustc codegen backend that compiles Rust kernels ahead of time to PTX, with
  threads, blocks, warps and shared memory in your hands. It pins its own Rust toolchain, needs CUDA Toolkit 13.0+ and a
  13.x driver, and is tested on Linux (Ubuntu 24.04).
- **cutile-rs** is the Tile track: you work on tensor tiles, with no thread indexing or synchronization to write, and it
  compiles at first launch to the CUDA Tile IR. It runs on stable Rust 1.89+ and lists Ampere, Ada, Hopper and Blackwell
  GPUs (consumer Blackwell, sm_120, included). It is on crates.io as `cutile` 0.4.0. (The crates.io name `cuda-oxide` belongs to an unrelated
  2021 crate.)
- Both tracks carry Rust's borrow rules across the kernel launch, and kernels from the two can be used together.

For the studio: the rig's RTX 5090 is sm_120, so cutile-rs lists our card, but both tracks are tested on Linux only and
the rig runs Windows; trying it would mean WSL or a Linux box. Relevance: watch.

**JAX on a Colab TPU: a fix to flax.nnx's import, then a first training smoke.** The single-chip TPU runtime we opened on 2026-10-29 (a v5e-1) comes with jax, jaxlib and flax all at 0.11.2, and `flax.nnx` fails to import against that jax:

- flax 0.11.2 asks for `jax.array_ref` and `jax.ArrayRef`, which jax 0.11.2 now calls `new_ref` and `Ref`. Its fallback names aren't in jax 0.11.2 either.
- It also calls `jax.core.get_opaque_trace_state`, which jax removed from `jax.core` in 0.11.0 (it now lives in `jax.extend.core`).

We worked around those two breaks with three one-line aliases, set only inside our own training process. An outside review read both libraries' sources and judged them the same objects under new names. That holds for these two versions only, and images change, so check yours. A newer flax pinned in your own environment, matched to the image's jax, is the cleaner fix.

With the aliases in place, a first training smoke passed on one v5e chip. It was a 10-million-parameter `flax.nnx` transformer, run for 50 steps after a CPU stub of the same path:

- The first step took 4.71 s with compilation, and a steady step took 1.69 ms. A model this small is limited by dispatch, so that is not a chip-speed figure.
- Peak TPU memory was 345 MB of 15.75 GiB.
- JAX's persistent compile cache cut a second process's compile to 0.65 s, 7.2 times faster.
- An Orbax checkpoint restored bit for bit, all 208 arrays, with the same next-step loss.
- The session ran under two minutes, at 2.92 units an hour.

It trained on one fixed random batch, so the loss falling to 0.01 is memorisation: it shows the loop works and nothing more. Next is a 181-million-parameter nanoGPT on the same card, where throughput starts to mean something. Sources: [flax 0.11.2](https://github.com/google/flax/blob/v0.11.2/flax/nnx/variablelib.py) and [jax 0.11.2](https://github.com/jax-ml/jax/blob/jax-v0.11.2/jax/core.py).

**RunPod's REST v1 is closing.** RunPod's public APIs have enforced a rate limit since 2026-10-27, and REST v1 is
being wound down. Its limit is 180 requests a minute, 3,600 an hour and 43,200 a day now. Those halve on November 2
(90, 1,800, 21,600) and halve again on November 9 (45, 900, 10,800). From November 16 every v1 request returns
410 Gone. Clients should back off exponentially on a 429. REST v2 is the long-term replacement, and GraphQL for
integrators is due to be deprecated in early 2027. (Source: RunPod's service notice to account holders.)

For the studio: offrig already calls REST v2 for pods, volumes and the GPU catalog, and waits for `Retry-After` on a
429 when it creates a pod. It still reads the account balance and the data-centre list over GraphQL, which has to move
before early 2027.

## The daily watch

4 new since [issue 33](/rnd/newsletter/issue-33/).

- **PyTorch 2.15.0** (2026-10-28): the deep-learning framework's new release makes CUDA 13.2 the default wheel (13.4 alongside), adds `torch.compile` on Python 3.15, and says 4-bit NVFP4 decoding is faster on Blackwell GPUs. Breaking: `import torch` now runs once per process, and its distributed checkpoints won't load in 2.14 ([release notes](https://github.com/pytorch/pytorch/releases/tag/v2.15.0)).
- **llama.cpp v0.8.0** (2026-10-28): a tagged stable release of the local inference engine; its numbered builds are pre-releases. It adds Liquid AI's LFM3 models (including speech in and out), `/v1/realtime` and `/tts` server endpoints, a selectable reasoning effort, and Nemotron 3.5 Embed support. Scripts beware: the CLI now requires `--model` or `-hf` ([release notes](https://github.com/ggml-org/llama.cpp/releases/tag/v0.8.0)).
- **Ollama v0.40.13** (2026-10-28): Liquid AI's LFM3 models, including the text-to-speech `lfm3-audio` and `lfm3-omni`, now run on Linux and Windows, where 0.40.12 had them on Apple silicon only. That makes a small local speech model a one-line pull on most machines; check the model's licence before you build on it ([release notes](https://github.com/ollama/ollama/releases/tag/v0.40.13)).
- **NVIDIA skills catalogue** (2026-10-28): NVIDIA's public catalogue of agent skills added 53 skills for its DOCA 3.5 networking bundle, six for the PVA SDK (vision accelerators), Omniverse Content Services 0.1.0, and Run:ai quota-audit, cluster-health and utilization-overview skills ([commit history](https://github.com/NVIDIA/skills/commits/main)).
