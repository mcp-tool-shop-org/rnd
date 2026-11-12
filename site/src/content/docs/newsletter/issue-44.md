---
title: "12 November: the GPU work moves to Colab, and a BIOS update quiets the log"
description: "A long look at running our GPU work on Google Colab in parallel lanes: how a paid window works, what we measured on the way (upload limits, a missing driver library, cards that would not open), what the research says about the field, and where each lane stands. Also: the firmware update that stopped 915 hardware-error records, a freshness watcher for our software stack, three training seeds finished with their guards quiet, and why dataset-desk 0.3.0's README translations needed hand fixes."
issue: 44
date: 2026-11-12
draft: true
highlights:
  - "<strong>Colab, in parallel lanes.</strong> We started moving GPU work off our own RTX 5090 and onto rented Colab cards. Ten windows ran today for 1.081 compute units in total. The most useful ones were the cheap ones that failed."
  - "<strong>A BIOS update quieted the hardware log.</strong> Windows had logged 915 hardware-error records in five weeks. After HP's BIOS update, four full training chunks ran with none."
  - "<strong>Three seeds finished, guards quiet.</strong> Zero guard trips in 57 guard windows, two single-window canary crossings, and a memory reading that looked like a leak and was a change in what we were sampling."
---

<!-- src-roots (legend for the src comments below; each comment is path:line unless it names a JSON key):
LEDGER = E:/AI/Publisher/receipts/colab/units-ledger.md
H18 = E:/AI/rnd-local/projects/deep-research/2026-11-12-18-parallel-colab-lanes-HARVEST.md
R18 = E:/AI/rnd-local/projects/deep-research/2026-11-12-18-parallel-colab-lanes-REPORT.md
SKILL = C:/Users/mikey/.claude/skills/colab/SKILL.md
MEM = C:/Users/mikey/.claude/projects/(the E drive Publisher project folder, name has two hyphens after E)/memory
BOARD = MEM/BOARD.md
PROBE = E:/AI/rnd-local/projects/sdlab-colab/colab-runs/probe-upload-limit-2026-11-12/probe_upload_limit.json
DESIGN = E:/AI/rnd-local/projects/sdlab-colab/DESIGN-v3.md
PLAN = E:/AI/rnd-local/projects/sdlab-colab/PLAN-sdlab-l1-gpu-rung-2026-11-10.md
RIG = E:/AI/Publisher/receipts/rig/gpu-windows-5090.md
H11 = E:/AI/rnd-local/projects/deep-research/2026-11-10-11-whea-boot-records-HARVEST.md
WHEA = entries/2026/2026-11-10-robot-rig-whea-records-at-boot-and-driver-install.md (this repository)
S2 = E:/AI/rnd-local/projects/aspire-si-s2/V11-RUN-NOTES.md
S2R = E:/AI/rnd-local/projects/aspire-si-s2/READOUT-guard-quantities-s45-s47.md
FRESH = E:/AI/Publisher/receipts/freshness-2026-11-11.md
FSRC = E:/AI/Publisher/src/freshness/freshness.mjs
H17 = E:/AI/rnd-local/projects/deep-research/2026-11-11-17-keeping-the-stack-current-HARVEST.md
DD = E:/AI/_worktrees/dataset-desk-0.3.0
TL = E:/AI/_worktrees/translations-2026-11-12 (the base log; -rerun and -desk are siblings)
-->

The lead is the biggest change of the day: we have started moving GPU work off the one graphics card in our own rig and
onto rented cards on Google Colab, several jobs at once. We read back through the ledger of Colab windows to write it,
and today's ten windows, most of which cost almost nothing, taught us more than the expensive ones did.

Around it: the firmware update that ended five weeks of hardware-error records on our RTX 5090 machine, the tool we
built to tell us when our software is behind, the end of the three training seeds (run health only, since what they
measured stays sealed), and the translation checks that caught dataset-desk 0.3.0's READMEs coming back wrong.

**In this issue:**

1. [Moving the GPU work to Colab, in parallel lanes](#moving-the-gpu-work-to-colab-in-parallel-lanes)
2. [A BIOS update, and the hardware errors that stopped](#a-bios-update-and-the-hardware-errors-that-stopped)
3. [Keeping the studio current](#keeping-the-studio-current)
4. [Seeds 45 to 47 finished: how the runs stayed healthy](#seeds-45-to-47-finished-how-the-runs-stayed-healthy)
5. [dataset-desk 0.3.0, and why the translations needed hand fixes](#dataset-desk-030-and-why-the-translations-needed-hand-fixes)
6. [The daily watch](#the-daily-watch)

## Moving the GPU work to Colab, in parallel lanes

Our rig has one serious graphics card, an RTX 5090, and it does one thing at a time. When it is busy with a
multi-hour training chunk, everything else waits: a README translation, a batch of renders, a model check. Meanwhile we
hold a prepaid balance of rented-GPU time on Google Colab (1,803.43 "compute units" this morning) that expires
around 22 November. <!-- src: LEDGER:395 (balance 1,803.43 before and after BL 99); MEM/feedback-colab-first-path.md:13 (units expire about 11-22) --> A balance that expires
and a card that is always busy is an obvious mismatch.

So today the studio decided to move GPU work toward Colab wherever it fits, and to run it in several parallel
**lanes**: separate jobs, each with its own card, side by side. The point is twofold: to keep the 5090 free for the work
that has to stay local (the sealed training series, exact local comparisons), and to make the Colab path solid enough that
more can go there. <!-- src: MEM/feedback-colab-first-path.md:11-16 -->

<!-- DIAGRAM: the anatomy of a Colab window as a ladder of rungs: written request (launcher, checksum, card, cap, wall clock) -> free dry run -> open the VM -> rate gate reads the live price and can stop the window -> CPU stub rung on the real install path -> paid rung -> copy results back, stop own session, check it is gone -> run record and ledger row. Source: LEDGER:385,395-404; SKILL:52-98 -->

### How a window works

A **window** is one rented Colab session doing one job, with a written limit on what it may spend and a folder of
receipts at the end. Every window passes through the same steps:

- **A written request.** It names the launcher script and that script's checksum (so we know it is the file we
  reviewed), the card, a **cap** in compute units and a **wall clock** in seconds. The effective ceiling is whichever is
  smaller: the cap, or the wall time multiplied by the card's hourly rate. <!-- src: SKILL:73-77 --> The G4 pilot that ran today had a
  cap of 9.40 units, a maximum acceptable rate of 10.5 units an hour and a wall of 1,800 seconds. <!-- src: LEDGER:403 -->
  At its real rate, 10.05 an hour, 1,800 seconds would cost 5.025 units, so the wall, not the cap, was what bound it.
  <!-- src: derived from LEDGER:403 (1,800 s x 10.05/h) -->
- **A free dry run.** The launcher runs every check that costs nothing, such as whether the files match their checksums and
  whether the request is complete, before it opens a session. <!-- src: LEDGER:399,400,403 (free dry run PASS) -->
- **The rate gate.** After the session opens, the launcher reads the live price and stops if it is above the request's
  limit. It earned its place on 6 November: an A100 card with 80 GB was expected at 6.77 units an hour, read 8.88, and
  was stopped 53 seconds in, for 0.131 units. <!-- src: LEDGER:385 -->
- **A CPU stub rung before any paid step.** The same path runs first on a cheap CPU-only session: it installs the same
  software, from the same pinned files, on the real Colab image, and stops before the expensive part. Today's stub of the
  translation job ran 81 seconds and cost 0.0059 units; the paid run that followed it cost 0.879. <!-- src: LEDGER:399,403 --> A stub is
  roughly 150 times cheaper than the thing it protects. <!-- src: derived from LEDGER:399,403 (0.879 / 0.0059) -->
- **Copy back, stop, check.** The results come back to our machine with checksums. The launcher stops its own session
  and, five minutes later, looks again to confirm it is gone. Every log is also searched for a login token, because the
  `colab` command-line tool prints one in the web address of a failed upload; none has ever been committed. <!-- src: SKILL:119-122; LEDGER:398-404 (token grep 0, identity scan clean) -->
- **A run record and a ledger row.** Each window is booked at its own hourly rate times its own runtime, whatever the
  account balance happened to do, so numbers from different windows can be added honestly. <!-- src: LEDGER:3 (booking basis); SKILL:156-160 -->

Colab lets us hold up to twenty sessions at once, in separate pools: three A100-40 cards, three A100-80, three G4, three
L4, three T4 and five CPU. At that ceiling it billed 71.14 units an hour. A fourth session in a full pool is
refused; a fourth on a different card type is fine. <!-- src: MEM/colab-parallel-windows.md:32 --> Our own rule is stricter than the limit: parallel
windows only across separate studies, one card type per study, one request at a time inside each window, so that any run can
be replayed exactly. <!-- src: MEM/colab-parallel-windows.md:12-18 --> The reason for care is that rented machines
disappear: in the first week of measuring, 4 of 53 GPU sessions were lost, and the losses leaned toward the times when several
sessions were live at once. <!-- src: MEM/colab-parallel-windows.md:33 -->

### The lanes, and where each stands

| Lane | What it does | Where it stands today |
|---|---|---|
| **Render** | Runs ComfyUI (an image-generation program built from connected nodes) with no window, rendering the images our canon briefs call for | The CPU stub passed on 6 November, rendering two fixture images with matching hashes in 83 seconds. <!-- src: LEDGER:379 --> The GPU rung needs a new `--render` mode in the launcher, which is out for build. <!-- src: PLAN:1-12; BOARD:32 --> |
| **Canon writing** | A large open model drafts the written canon and prompts for a game, for a human to approve | Not built. The model we would use carries a usage policy we treat as binding, which means recording which words the model wrote. <!-- src: DESIGN:303; BOARD:32 --> |
| **LoRA training** | Trains a LoRA (a small add-on that teaches an image model one visual style) | Done on a G4 up to a full 500-step run: the first complete rung, 20 steps, took 495 seconds; the second reached 500 of 500 steps and was stopped by a guard that was wrong (see issue 43); the third, with that guard fixed, passed in 1,298 seconds for 3.624 units. <!-- src: LEDGER:390-392 --> The first paid run on real data waits on one more fix. <!-- src: BOARD:32,36 --> |
| **Captions** | A vision model drafts descriptions for images flagged as poorly described, for a person to review | The launcher is out for build; the plan is a stub first, then an L4 card at a cap of 3.0 units. <!-- src: BOARD:32 --> (More on the tool in article 5.) |
| **Translation** | Translates README files with TranslateGemma 27B | The stub passed and the first paid run on a G4 ran to the end, today. Details below. <!-- src: LEDGER:399,403 --> |

Two other jobs share the pool: judge-model windows for the rdlab study, and a probe for Ripple-65B Preview,
an open, Apache-2.0 coding model of 64.78 billion parameters that is too big for our own card. <!-- src: LEDGER:393-394,397-398,404; MEM/feedback-size-new-models-for-colab-runpod.md:13 -->

One question we have not settled: our plan names an A100 with 40 GB as the first render card, but the benchmark the
research cites has Qwen-Image-2512, the render model, peaking near 46 GB in full precision, which is more than that card
holds. <!-- src: PLAN:38; H18:16 --> Either the plan's card changes or a measurement shows it spills gracefully. We would rather learn that on a
cheap rung.

### Today, window by window

Ten windows ran between 4:16 and 11:50 a.m. Eastern. Together they cost **1.081 units**. <!-- src: derived from LEDGER:395-404 (sum of booked column; pot 164.728 to 165.809) -->

| # | Time (ET) | Job | Card | What happened | Units |
|---|---|---|---|---|---|
| 99 | 04:16 | translation pilot | A100-40 | no capacity | 0 |
| 100 | 04:48 | translation pilot, try 2 | A100-40 | opened; stopped at setup, no `zstd` | 0.140 |
| 101 | 08:40 | Ripple stub | CPU | refused at the library check (no CUDA on the CPU image); chunked upload worked | 0.012 |
| 102 | 08:49 | upload and download probe | CPU | passed; ceiling found | 0.037 |
| 103 | 09:03 | translation stub, real install path | CPU | passed | 0.006 |
| 104 | 09:11 | translation pilot, try 3 | A100-40 | no capacity | 0 |
| 105 | 09:42 | translation pilot, try 4 | A100-40 | no capacity | 0 |
| 106 | 10:14 | translation pilot, try 5 | A100-40 | no capacity | 0 |
| 107 | 10:18 | translation pilot | G4 | ran to the end in 315 seconds | 0.879 |
| 108 | 11:50 | Ripple library probe | L4 | refused: shape mismatch | 0.007 |

<!-- src: LEDGER:395-404 (every row; times converted from UTC at -5 h) -->

<!-- CHART: the ten windows of 12 November (BL 99 to 108) as bars of booked units, with a marker for no-capacity refusals (4, cost 0) and the single paid window (BL 107, 0.879) standing against the rest; source: LEDGER:395-404 -->

#### How big a file can we send? (and what that decides)

The first Ripple stub tried to upload its 216 MB program to the Colab machine last night and got an HTTP 500 error about
nine seconds in. <!-- src: LEDGER:394 --> Rather than guess, we measured. A probe uploaded files of 16, 32 and 64 MB, and all three arrived with
matching checksums at about 1.8 MB a second. At 96 MB the server answered **HTTP 400** in two seconds. The probe stops at its first
failure, so 128 to 200 MB were never tried; the single-upload ceiling sits somewhere between 64 and 96 MB.
<!-- src: PROBE:56 (64 MB, 35.2 s), PROBE:62-66 (96 MB, http_status 400); LEDGER:398 -->

The fix, built before the probe and confirmed by the first stub that used it, is to send big files in **chunks**: seven
parts of 32 MiB for the 216 MB program, put back together on the machine and checked against the whole file's checksum.
All ten input files matched. <!-- src: LEDGER:397 --> Downloads were never the problem: we pulled files from 256 MB up to 2,048 MB, every one
intact, at 16.3 to 18.2 MB a second, and found no ceiling. <!-- src: PROBE:82-142 (rates computed from size over seconds) -->

The practical rule falls out of the speeds. Pushing a model's weights up from our rig at 1.8 MB a second would take
hours, so the Colab machine fetches them itself from Hugging Face: the 57.7 GB Qwen-Image model arrived in about 165
seconds, at 343 MB a second. <!-- src: LEDGER:390,391 (57.7 GB in 168 s and 163 s) --> Small files go up; big ones come down from the source.

<!-- CHART: upload sizes 16, 32, 64 MB passing and 96 MB failing with HTTP 400, beside download sizes 256 to 2,048 MB all passing at 16.3 to 18.2 MB/s; source: PROBE (uploads[], downloads[]) -->

#### The cheap machine has no CUDA

The second Ripple stub was meant to check the program's **library dependencies**. Before paying for a GPU, a launcher can
run `ldd`, a standard tool that asks, for a program, "which shared libraries do you need, and can this machine find
them?" On the CPU-only image the answer was no: the three CUDA libraries the program needs (`libcudart`, `libcublas`,
`libcublasLt`) were not there, there was no `/usr/local/cuda`, and `nvidia-smi`, the tool that talks to the card,
was absent. <!-- src: LEDGER:397 --> That is not a fault; a CPU image has no use for CUDA. But it means a CPU stub cannot answer
that question, and a GPU has to. The cheapest GPU is an L4, so a probe on an L4 followed.

It was **refused at the shape check**, within eleven seconds, for 0.007 units. The launcher had assumed an L4 comes in a
high-memory "shape", and the session reported the standard one. Our own earlier measurement, from 9 November, already said an L4
has exactly one shape, the standard one; the request had not been checked against it. <!-- src: LEDGER:404 --> The check did its job: a refusal that early is a far cheaper way to find a wrong assumption than an upload. The library question is still unanswered, and
the fix to the launcher's table of shapes is owed.

#### The A100-40 would not open; the G4 always did

The translation pilot was meant for an A100 with 40 GB. Of five attempts today, four were refused with "Service
Unavailable": Colab had none of that card free. <!-- src: LEDGER:395,396,400-402 (BL 99, 104, 105, 106 refused; BL 100 opened) --> A refusal costs nothing, and there is a
rule to match: three tries, at least half an hour apart, then stop and report. Across the last week the ledger counts the
A100-40 opening twice and refusing about a dozen times, while the G4 had opened six times out of six before today's
pilot, and opened again for it. <!-- src: LEDGER:402 -->

That fits what Colab's own client documents. Its code distinguishes **HTTP 412**, a permanent "too many assignments"
that should never be retried, from 502, 503 and 504, which mean the pool is out of that card and are retried three times
with 10, 20 and 40 seconds of backoff. All our refusals today were the second kind. <!-- src: H18:40 --> The G4 costs more an hour (10.05
units, against 6.73 for an A100-40) but opening at all beats a cheaper card that does not. <!-- src: LEDGER:403 (10.05/h), LEDGER:393,384 (6.73/h A100-40) -->

#### The translation pilot

On the G4 the pilot ran for **315 seconds, about five minutes, for 0.879 units** (the launcher's own estimate was
0.867). It produced seven translated READMEs, a bundle with matching checksums (8 of 8), and no stray carriage-return
characters. <!-- src: LEDGER:403 --> The 27-billion-parameter translation model sat entirely on the card, using 28,461 MiB. <!-- src: LEDGER:403 (translategemma:27b 100% on GPU, 28,461 MiB) -->
Two things are open. We told the model to use a 4,096-token window, but its own report says 131,072, with a
49,152 MiB memory cache, so the setting did not do what we thought. And the translations have not yet been compared with
what the 5090 produces. <!-- src: LEDGER:403 (PINNED_TRANSLATOR_CONTEXT 4096 vs fit_probe 131,072; acceptance 4 open) -->

#### The lesson: a first paid rung without a stub

The pilot's first try, at 4:48 a.m., did open an A100. It lasted 75 seconds. The translation program, Ollama,
is shipped as a `.tar.zst` archive, and the Colab image has no `zstd` tool to unpack it, so setup stopped. Cost: 0.140
units. <!-- src: LEDGER:396 --> We had booked the first paid rung with no CPU stub in front of it.

The sting is that we had met this exact fault before. On 23 October a stub that skipped the real Ollama install let two paid runs
fail on the same missing tool, and the guidance written then says: "a stub must run every install and unpack step the paid
run will." <!-- src: SKILL:68 --> It was in the file; this lane's request did not apply it. Two things changed. A stub that runs the real install path is
now a rule for **every** first paid rung of a lane. <!-- src: BOARD:31; LEDGER:396 --> And the stub at 9:03 a.m. ran the six steps in order (shred the
token, install Node from a pinned file, download Ollama from a pinned file, install `zstd` v1.5.5, unpack, start the
server), stopped before the model download, and passed in 81 seconds for 0.0059 units. <!-- src: LEDGER:399 --> The paid G4 run then found
`zstd` in place. <!-- src: LEDGER:403 -->

### What the field says

We asked a Deep Research report what is known about running parallel image-and-text pipelines on Colab, then checked its
claims against their sources. The checked results below are the ones that held; the claims that did not hold were left out.
<!-- src: H18:3-10 -->

- **Concurrency, and 412 against 503.** As above: the client documents them, and they match the per-pool limits we
  measured ourselves. A 412 means stop and wait; a 503 means try again later. <!-- src: H18:40 -->
- **Long connections go stale.** The login token lasts an hour, and ordinary commands refresh it but long-lived live
  connections do not. The safe pattern is to run work detached on the machine and poll with short commands. This agrees
  with what we saw: a long `colab exec` goes quiet at 50 to 60 minutes while the job carries on. <!-- src: H18:41; SKILL:124 -->
- **One balance, shared.** The account's unit balance is shared across every lane, and Colab's FAQ treats headless
  use of a web interface as a restriction on free accounts that a positive balance lifts. So a runaway lane could push
  every session onto free-tier rules, and a unit floor belongs in the ledger before any lane launches. <!-- src: H18:42 -->
- **Headless ComfyUI, under the terms.** Running ComfyUI with no window on the machine's own loopback address, on a
  funded paid account, looks fine under the FAQ's text, which we checked. Exposing it through any proxy is banned on every
  tier, so ours stays on loopback. <!-- src: H18:96 -->
- **Hugging Face 429 on parallel boots.** Hugging Face limits requests per user over five-minute windows, and
  anonymous traffic per address. Several machines booting together without a login token, or with it missing from
  one subprocess, hit "429 too many requests". Pass the token to every subprocess, or pre-stage the weights. <!-- src: H18:45 -->
- **Cost per accepted image.** The cost that matters is raw cost divided by the share of images accepted. We do not yet
  record acceptance in the ledger, so cost per keeper is invisible. <!-- src: H18:18,88 -->
- **Which card renders.** RunPod's published benchmark has Qwen-Image-2512 peaking near 46 GB, and an RTX PRO 6000
  (our G4) at 18.03 seconds an image against 29.12 for an A100-80, with the benchmark's own warning that host variance
  makes cross-card comparison soft. <!-- src: H18:16 --> Copy weights to the machine's local disk before starting: loading over a network or
  FUSE mount can be ten times slower. <!-- src: H18:17 -->
- **Model collapse in render-to-LoRA loops.** Training on your own model's renders narrows its range. The advice from the
  research (Gerstgrasser et al., 2024, arXiv 2404.01413, on accumulating real data beside synthetic; Drayson et al., EMNLP
  2025) is to keep human-made images as anchors, let synthetic images fill only named gaps, and keep the written canon
  fixed while validating model-written additions against a schema. <!-- src: H18:27,29 -->
- **Licences.** All nine licence claims the report relied on matched the sources. The ruled-out names were confirmed too:
  one FLUX.2 klein size under a non-commercial licence, one background-removal model under CC BY-NC 4.0 (BiRefNet, MIT,
  replaces it), and a translation-quality scorer under a non-commercial licence. TranslateGemma itself sits under the Gemma
  Terms rather than Apache 2.0; for translated README text, low risk, flagged. <!-- src: H18:4,35,63-82 -->
- **A question it raised about CC BY 4.0.** If we release renders under a Creative Commons attribution licence, the
  US Copyright Office's January 2025 view is that purely prompt-driven output may not be copyrightable, so an attribution
  requirement may not bind on raw renders. The choice is whether the art archive says so, or releases raw renders as
  public domain and edited work under CC BY 4.0. It is a decision for us, not yet taken. <!-- src: H18:95 -->

### What is next

The render lane's launcher, the LoRA lane's last fix and the caption lane's launcher are all in review; the paid runs wait
on them. The unit balance expires in about ten days, and we are holding Colab's command-line client at its current
version until a 25 November audit, because 0.8.0 removes one subcommand and changes what `--timeout` means. <!-- src: BOARD:31,32,36; FRESH:16 --> Total
spent from the backlog pot so far: 165.809 of 400 units. <!-- src: LEDGER:404 -->

## A BIOS update, and the hardware errors that stopped

For five weeks the Windows event log on our RTX 5090 machine had been filling with the same hardware-error record, and
we had been reading it as noise without being able to prove it. Today the record stopped, and for a reason we can name.

### What the record was

Windows keeps a hardware-error log (WHEA, Windows Hardware Error Architecture). On 10 November it held **915 records**,
going back to 5 October: 911 of **Event 17**, a report about the PCI Express connection (the wiring between the card
and the motherboard), and four of **Event 1**, a different record. <!-- src: WHEA:13,22-23,94 -->

Every one of the 911 Event 17 records was identical in content: an "Unsupported Request", reported as an advisory
non-fatal error, with a "header log overflow" flag. Each followed either a boot (within 22 seconds) or an
installation of the display driver (within 5), and none fell inside a training window we checked. <!-- src: WHEA:25-41,68-70 --> Each driver install was followed by a burst of exactly 37. <!-- src: WHEA:41 -->

Read plainly, an Unsupported Request is the card answering "there is nothing here" to a question aimed at a spot
where no device exists. The records fit something scanning the card's bus for devices that are not there. Nothing in
them was a link error. That reading came from an analysis we then checked against the records; the status bits and
timing fit it, and nothing in the log contradicts it. <!-- src: WHEA:101 (unverified status as written there) -->

The four Event 1 records were different. They were the firmware handing Windows a crash log from the processor
platform at four boots in late October. Comparing them byte by byte showed **one capture replayed four times**: of
9,496 bytes, 11 differ, ten of them the record's own time and number. In other words one platform event, not four. <!-- src: H11:13,15,35 -->

<!-- DIAGRAM: the mechanism of Event 17: a host component reads configuration space for functions and devices on the card's bus that do not exist; the card completes each read with Unsupported Request; the platform logs each answer as an advisory non-fatal error with the header log overflow bit set; bursts of 2 at a boot, up to 33-39, 37 after a driver install. Mark the mechanism as our reading, not a measurement. Source: WHEA:25-47,101-103; H11:33 -->

### What the research found

We sent the records to a Deep Research report and then checked what it said against the machine and the sources.
Several things it said turned out wrong or unsupported: three of the six web pages we opened were misdescribed (an
issue number, a date, a release number), one article number could not be found, and the claim that a Windows
build ended the cluster was not supported. <!-- src: H11:18,20,22,24,53 --> The useful results were that Fast Startup is off on the machine, so it did not explain the
boot records, and that the Event 1 records are not about the graphics card at all. <!-- src: H11:19,34 --> Its advice on that day was to change no
setting on the rig, which we did not. <!-- src: H11:59 --> We filed written reports with NVIDIA, Microsoft and HP on 10 November. <!-- src: E:/AI/Publisher/docs/drafts/vendor/filing-texts.md:44; E:/AI/Publisher/docs/board-history/BOARD-2026-11-11-1055.md:19 -->

### The fix

Reading HP's release notes for the machine's BIOS, we found that version F.21 lists a fix for Event ID 17 warnings
that led to a black screen and the GPU fans running at full speed. Over 30 days the machine had logged 743 of them,
all on the 5090, 37 to 74 for every boot. (That is a shorter count than the 915 above, read over a different span.) <!-- src: S2:391-394 (T15a) -->

On 11 November, between seed 47's first and second training chunks, the BIOS was updated from F.20 to F.22 (F.22 is dated
27 May 2026). <!-- src: S2:388-389 (F.22 dated 05/27/2026); RIG:26 --> The flash had a side effect we are glad we have a guard for: the card's power limit,
which we hold to 480 watts, had reset to 575, and the next chunk's launcher would have refused to start
until it was re-applied by hand. <!-- src: S2:398-400 -->

### The evidence

- **Before:** 37 to 74 Event 17 records at each boot, and none inside any training window. <!-- src: RIG:26; WHEA:68-70 -->
- **After:** the log since the first F.22 boot at 16:25 held zero WHEA records when chunk 2 ended, and each of the four
  full training chunks on F.22 (chunks 2 to 5, about three hours each) closed with zero Event 17 and zero Event 1.
  <!-- src: RIG:21,23,24,26 -->
- Seed 47's first chunk, on the old BIOS, also had zero in its window. The change is at the boots, not the load. <!-- src: S2:567-568 -->

<!-- CHART: Event 17 records per boot before F.22 (range 37 to 74, source RIG:26 and S2:391-394) against 0 after at each of chunks 2 to 5 (source RIG:21,23,24,26); training windows at 0 both sides (RIG, WHEA:68-70); label it as counts of one machine -->

Caveats we would put on any claim: one machine; "four clean chunks" is four observations, and only the chunk-2 reading
covered a whole boot; and the log we first read went back only five weeks, with older records already
rolled out of it. We are not saying the card was ever unhealthy, or that the BIOS is the only thing that changed. We
are saying a record that appeared at every boot for at least five weeks has not appeared since. The note to the three
vendors, that F.22 fixed it, is the next step. <!-- src: RIG:26 ("one chunk is one observation"); BOARD:39 (waiting on the vendor note); E:/AI/Publisher/docs/board-history/BOARD-2026-11-12-0800.md:26 -->

## Keeping the studio current

On 11 November an audit found a training base, ComfyUI, llama.cpp and a BIOS fix all months behind with nothing in
our tooling to say so. <!-- src: FSRC:1-4 --> So we built a freshness watcher the same day, and asked a Deep Research report what good practice looks like.

### The watcher

For every component the studio depends on, it records what we run, what upstream's latest is, when that was released, how many
days ago, and a status:

- **current**: we have the latest;
- **pinned**: behind on purpose, with an owner, a reason and an expiry written down;
- **drift**: behind with no stated reason, which is the failure we are hunting.

Its first table (11 November) had twelve components: **6 in drift, 4 pinned, 2 current, 0 unknown**. <!-- src: FRESH:3 --> The drifters were the rig's Python
(3.10.11, against 3.15.2 released 25 October), uv, Ollama, ComfyUI (0.23.0 against 0.45.0), Node.js (22.22.3 against
26.13.1) and our llama.cpp build (b11433 against b12292). <!-- src: FRESH:7-12 --> The four pinned ones carry their reasons: the training stack's torch and
transformers are "sealed until 2026-11-30", the LoRA trainer pin is deliberate until the same date, and Colab's
command-line client stays at 0.7.4 until 25 November. <!-- src: FRESH:13-16 -->

The program is a set of plain functions with its network reads injected, so its tests run with no network. It also compares
build numbers like llama.cpp's `b12292` and commit hashes, not only dotted versions, and refuses to compare things that are not
comparable. It also watches watched **model families** for new releases, and flags any with a licence that is not on
our permissive list for a human to read. In the first run, five new models turned up: three FLUX klein repositories (licence "other", gated) went to review, and
two (one Apache 2.0, one MIT) did not. <!-- src: FSRC:11,26-47,146-152; FRESH:22-28 -->

<!-- CHART: the twelve components of the 11 November freshness table by status (6 drift, 4 pinned, 2 current), with the days since each latest release; source: FRESH:3-16 -->

Some things it cannot see, and says so: NVIDIA's driver (no public interface), the HP BIOS page (needs a browser), the
Windows build and fleet repositories' dependency advisories. <!-- src: FRESH:30-34 -->

### What the research said

Seed 17 asked how a small team keeps a stack current. Its answers, as we kept them:

- **Split discovery from promotion.** Detect every release automatically, wait out a cooldown (seven days is common;
  security fixes skip it), run an equivalence test, and only then adopt, at the boundary between experiments. A sealed
  series never moves mid-series.
- **Watch what the dependency bots cannot.** A tool called nvchecker (MIT) can watch GitHub releases, package indexes and web
  pages, including the HP BIOS page; model hubs can be watched by organisation, since new models arrive under new
  repository names (Qwen-Image became Qwen-Image-2512).
- **Pins carry intent.** An owner, a reason and an expiry. A pin with no reason counts as drift.
- **Python has two answers.** Pure-Python packages can test on 3.15; environments built on CUDA and torch should stay on
  3.12 or 3.13 until the big libraries ship verified wheels. Python 3.10 reached end of life on 1 October, so the rig's
  default was past it.
- **Count the hardware.** Check for WHEA errors, GPU errors and the PCIe link speed on a schedule, and flash firmware only
  between series.
- **Keep a local copy of production weights** with checksums, since upstream repositories get deleted.

<!-- src: H17:15-35 -->

It also raised two risks for the rig itself: Windows Insider builds, which the rig runs, carry flight certificates that
expire and a short limit on pausing updates, and a Windows policy exists to stop Windows Update replacing the NVIDIA driver.
Neither has been checked against this machine yet. <!-- src: H17:39-42; E:/AI/Publisher/docs/drafts/vendor/whea-event17-rtx5090-omen45l-report.md:14 (rig runs Windows 11 Insider); BOARD:40 --> One recommendation, using Renovate to open and automerge
dependency pull requests, conflicts with our own standing rule on dependency bots, so it is a decision rather than a
to-do. <!-- src: H17:24-26 -->

### Today's upgrades

With seed 47 finished, the safe window the research describes opened, and three of the six drifters moved. <!-- src: BOARD:27 -->

- **uv** 0.13.4 → **0.13.7**. <!-- src: FRESH:8; live check `uv version` on 2026-11-12 reads 0.13.7 -->
- **Node.js** 22.22.3 → **26.13.1**. <!-- src: FRESH:11; live check `node version` on 2026-11-12 reads v26.13.1 -->
- **Python** 3.10.11 → **3.15.2** as the rig's default interpreter. <!-- UNSOURCED: that 3.15.2 is now the rig default comes from the request for this issue; the Python launcher lists CPython 3.15.2 installed (uv-managed), but the shell we checked from still resolved python to 3.10.11 --> Training and Colab environments are pinned
  separately and do not follow the default: the Colab launchers, for example, pin exact interpreter builds. <!-- src: LEDGER:377,381 (cpython 3.14.9 and 3.12.15 pinned by build) -->

**Ollama** (0.40.15, with 0.40.16 out), **llama.cpp** (b11433, with b12292 out) and ComfyUI (0.23.0, with 0.45.0 out) are
not yet moved; Ollama and llama.cpp are still being built and gated, for the reason the watcher is built around. The last time we changed the model server, on 9 November, we did it only after a gate: a
first try with 50 prompts failed because the stock server gave different answers on 45 of them depending on its state, and
the second, with the cache off, 401 teacher-forced items and a comparison of probability distributions, passed (mean KL
divergence 0.0005, speed 0.987 of the old one). <!-- src: RIG:11,15 --> Both new builds go through the same gate, and the
board flags a CUDA FP8 change in llama.cpp's notes to read first. <!-- src: BOARD:27 -->

<!-- DIAGRAM: the adoption pipeline: watcher detects every upstream release -> cooldown (7 days; security fixes skip it) -> equivalence gate (e.g. the Ollama gate: 401 items, KL, speed) -> promote at an experiment boundary; sealed series never move mid-series; every pin carries owner, reason, expiry. Source: H17:15-20; RIG:11,15 -->

## Seeds 45 to 47 finished: how the runs stayed healthy

The last of the three training seeds in [aspire-si](https://github.com/mcp-tool-shop-org/aspire-si)'s pre-registered series, S2 v1.1, finished at 10:06 this
morning, after seeds 45 and 46 over the previous two days (see [issue 42](/rnd/newsletter/issue-42/) and [issue 43](/rnd/newsletter/issue-43/)).
Each seed is 197 updates, run in five chunks of three to six hours, on the RTX 5090. What the seeds measured stays sealed until the registered analysis is
done. This is only their health. <!-- src: RIG:21 (RUNNER-EXIT 10:06:07); S2:565-566; FRESH:13 -->

### Guards: counts

The run carries **guards**: checks, roughly every ten updates (19 windows across 197), that can halt it if something has gone wrong, and **canaries**,
which are measurements that watch for one particular kind of failure. A canary counts as crossed only if the line is
passed in two windows in a row. Counting the guard history of all 15 chunk files (counts only, no text read):

| Seed | Guard windows | Guard trips | Confirmations | Canary crossings | Stop-and-report |
|---|---|---|---|---|---|
| 45 | 19 | 0 | 0 | 1 (one window) | no |
| 46 | 19 | 0 | 0 | 0 | no |
| 47 | 19 | 0 | 0 | 1 (one window) | no |

<!-- src: S2R:31-36 -->

That is **0 guard trips in 57 windows**. <!-- src: S2R:45-46 --> Both crossings were a single window over the line, so neither counted. <!-- src: S2R:39-41 -->
A rule of thumb for "none seen in n tries" is that the true rate is probably below 3 in n: here about 0.053 per window at
95% confidence. The windows within a run are not independent, so that is a rough ceiling, not an estimate. <!-- src: S2R:47-48 --> The honest
reading of the single-window crossings is a calibration note for the next study: a one-window rule would have fired twice in 57 windows
on healthy runs. <!-- src: S2R:49-51 -->

<!-- CHART: 19 guard windows per seed for seeds 45, 46, 47 with the two single-window canary crossings marked (seed 45 step 149 window 15, seed 47 step 59 window 6) and zero guard trips; source: S2R:31-36 -->

### The memory median that was not a leak

As in issue 43, we sampled the card's memory every five seconds after each save. At step 190, in seed 47's last chunk, the
middle reading was **15,918.5 MiB**, over our 15,500 report line. The hold rule did not fire: the highest reading stayed
under the 23,372 reference and the lowest fell (10,179 to 9,654). <!-- src: S2:550-551,554-555 -->

We reported it at once and then split the readings by what the trainer was doing at that moment. The median during the
rollout (the model writing its answers) fell from 13,726 to 12,882. The rise came from **20 readings that fell in no recorded
phase**, with a median of 16,904. It was a change in what we happened to sample, not memory creeping up. What that
unphased stretch is, between updates or an evaluation, we have not measured. <!-- src: S2:556-558 --> It is the same lesson as the previous two issues from a third angle: a middle reading is a
poor alarm; the floor and the ceiling say whether memory is growing, and the phase says what you are looking at.

### The 184, not 312, correction

Before training, the run takes a "step 0" pass: every item is run once at temperature zero, which means the model
always picks its likeliest next word, so the same input gives the same output. Our notes had said that pass covered 312 items and ran at about 27 seconds
an item. On 12 November we corrected it: two of the sets are nested (one is drawn from the other), and the code runs
their union, which is **184 items**. Step 0 took about 141.5 minutes, so the rate is about **46 seconds an item**. <!-- src: S2:12-18 -->
No seed ran a confirmation pass, so no decision rested on the wrong figure. <!-- src: S2:18-19 --> It matters for planning: the next study wants these
passes batched, and a batched speed-up has to be measured against 46 seconds, not 27. <!-- src: S2:24-25; BOARD:14 (item D: batched greedy passes) -->

Run totals in brief: all five of seed 47's chunks were valid, as were seed 46's; the card peaked between 23,270 and 23,588 MiB per
chunk, and its highest power readings were 494 to 496 watts against a 480-watt cap; and the BIOS change in article 2 fell between seed 47's first and second chunks and is recorded in
the run notes so any difference between chunks can be read against it. <!-- src: S2:565-571; E:/AI/Publisher/docs/board-history/BOARD-2026-11-12-0800.md:38 (seed 46 all chunks VALID); S2:386-397 -->

## dataset-desk 0.3.0, and why the translations needed hand fixes

[dataset-desk](https://github.com/mcp-tool-shop-org/dataset-desk) is a desk for making and reviewing visual datasets: it
finds the copies, near-copies and odd ones out, searches a set by words or by picture, and checks that each image's
description really describes it. <!-- src: DD/README.md:17-18 --> A style LoRA learns from images and captions, and two quiet
defects spoil both. Repeats teach one image twice. And descriptions that are not descriptions (a caption copied from the
generation prompt, one ruling pasted onto 54 images) tell the model nothing about the picture. <!-- src: DD/README.md:25-28 --> It never changes a project folder and never removes anything
automatically. <!-- src: DD/README.md:29 -->

### What 0.3.0 adds

0.3.0 (released 12 November, with 235 tests at 94% line coverage) is about **training captions**. <!-- src: DD/CHANGELOG.md:10; git log 3b08d4f message in DD (235 tests, 94%) -->

- **Drafts only for flagged records.** A model-free gate flags captions that are not descriptions. Only flagged records are
  drafted by a vision model (Qwen3-VL-8B-Instruct, Apache 2.0, pinned to a revision), and only into a review queue and a
  **blind worksheet**: each flagged image beside three to five similar ones, with no prompt shown. A person edits it, and
  the edits are re-imported with the reviewer's name. A draft is never written straight into a training caption. <!-- src: DD/CHANGELOG.md:19-30,32-35 (drafter, flagged-only); DD/README.md:63 (blind worksheet) -->
- **Provenance on every piece.** Each part of a final caption records where it came from: a configuration line, a drafter and
  its revision, a reviewer, a record, or a sidecar file. Every item carries whether it passed the gate, so flagged items are
  marked and all are kept. <!-- src: DD/CHANGELOG.md:21-24 (per-part writers, gate_status) -->
- **The image lock.** Some image sets are kept out of training so they can be used to test. A project can be tagged as such, and a
  folder that shares any image, by checksum, with a configured locked set is refused for every command unless explicitly
  allowed. The lock is **fail-closed**: a malformed or empty list of locked sets stops every command rather than quietly
  turning the lock off, and one shared rule governs how folders are walked and hashed, so a renamed byte-copy is refused
  the same as the original. <!-- src: DD/CHANGELOG.md:36-45,56-75 --> A stated limit: a resized or re-encoded copy does not share a checksum, so such projects have to be
  tagged. <!-- src: DD/CHANGELOG.md:107-109 -->
- **A change worth knowing:** `--draft` now takes an optional drafter name, and a bare `--draft` means the old default. <!-- src: DD/CHANGELOG.md:92-95 -->

Released on GitHub (tag and release); the PyPI upload was waiting on an approval when we wrote this. <!-- src: BOARD:20 -->

### Why the translations needed hand fixes

dataset-desk's README ships in seven other languages, translated on our own card by TranslateGemma 27B through a tool
called polyglot-mcp. The tool does not trust its output. Before translating, it swaps inline code and links for numbered
placeholders so the model cannot alter them, then swaps them back, and two gates check the result: a **protected-span**
gate (links, numbers and code must survive) and an **untranslated** gate (prose must not come back in English).

Between 6:03 and 6:48 this morning three READMEs went through, and all three failed the gates before they passed. <!-- src: TL.log:1,1741; TL-rerun.log:1,191; TL-desk.log:1 -->

| README | Spans lost | Lines left in English |
|---|---|---|
| tool-compass 2.5.6 | 2 | 2 |
| backpropagate 1.9.0 | 11 (zh 1, ja 2, fr 5, hi 1, it 2) | 15 |
| dataset-desk 0.3.0, first run | 2 | 41 |

<!-- src: TL.log:1532-1538,2850-2865; TL-desk.log:548-554; TL-rerun.log:195-205 -->

What went wrong, by kind:

- **Placeholders that did not survive a batch.** The tool sends text in batches. When a batch had many inline code
  snippets, the model returned the sentences with placeholders moved, dropped or changed, so they could not be put back
  safely, and the tool kept the English and flagged it. In dataset-desk, 41 prose lines came back in English at first.
  A segment is then retried on its own, and in dataset-desk three of eight retries recovered a translation. <!-- src: TL-desk.log:554-597 -->
- **Numbers written in local style.** French writes 4,096 as "4 096", and the number check, which counts digits, saw the
  pieces and reported "0 096 18 20 4 7" where it expected "0 18 20 4096 7". French also writes decimals with a comma (the
  shipped French README has "18,7" in its table). In Japanese, a first draft turned the "700" of "700M" into a "7". A
  translation can be right and still fail a check that counts characters. <!-- src: TL-rerun.log:397-407 (fr and ja lines); DD sibling E:/AI/_worktrees/backpropagate-1.9.0/README.fr.md:418 (18,7) -->
  <!-- UNSOURCED: decimal commas as a cause of a lost span: the request for this issue names them; the log shows only the spaced thousands (4 096), and the checker splits numbers at punctuation -->
- **Links dropped.** The gate caught Japanese text where a handbook link vanished entirely, and French and Italian
  sentences where two different links had been replaced by one of the issue-tracker links. <!-- src: TL-rerun.log:398,403-404,406-407 -->
- **Full-width parentheses.** The shipped Japanese README wraps that same "700M MAU" clause in full-width parentheses (
  "（" and "）"), the way Japanese and Chinese are normally written. <!-- src: E:/AI/_worktrees/backpropagate-1.9.0/README.ja.md:417 --> <!-- UNSOURCED: that full-width parentheses cause links to be dropped comes from the request for this issue; the logs and pins show the characters but not the mechanism -->

**The pins.** When a segment will not translate cleanly, a person fixes it by hand and **pins** it: the correction is
saved in `.polyglot-pins.json` against a fingerprint of the English sentence and the language, so a rerun reuses
the fix instead of asking the model again. dataset-desk's release holds seven pins, written at 6:50 a.m., and backpropagate's holds nine, across five
languages. <!-- src: git log 3b08d4f message in DD (7 hand-fixed segments); E:/AI/_worktrees/backpropagate-1.9.0 git log 1c41555 message (9 pinned); DD/.polyglot-pins.json (pinnedAt 2026-11-12T11:50Z = 06:50 ET) --> All seven languages then passed both gates. <!-- src: git log 3b08d4f message in DD -->
It matters for release order: a release tag cannot be changed after it is cut, so translations are finished first, and
our release check blocks a release whose README translations are stale. <!-- src: E:/AI/Publisher/.claude/CLAUDE.md (Hard rules: translations before the tag) -->

<!-- DIAGRAM: the translation path: README -> swap code and links for placeholders -> batch to the model -> restore placeholders -> two gates (protected spans: links, numbers, code; untranslated lines) -> pass, or retry the segment alone, or hand-fix and pin; show a lost link and a French "18,7" as the examples that trip the gate. Source: TL-desk.log:540-597; TL-rerun.log:361-372; DD/.polyglot-pins.json -->

### What the field says

The research from article 1 has a section on translation checks that need no fluent reader of the target language: the
same placeholder, code-block and link parity our gates run; parity of glossary terms and proper nouns; a reference-free
quality score (MetricX-24, Apache 2.0, licence checked at source); and a back-translation compared by a second model
family. It names two scorers, CometKiwi and XCOMET, as non-commercial and to avoid. <!-- src: H18:34-37 --> We already do the first; the others are candidates, and none has been built.

### What is next

The fix belongs in polyglot itself, so that placeholders survive a batch: a ticket for it is open, ahead of more
hand-fixing. <!-- src: BOARD:36 (polyglot code-span ticket) --> The Colab translation lane in article 1 will run the same tool, so the same gates apply there. <!-- src: LEDGER:403 -->

## The daily watch

<!-- DAILY WATCH SLOT: the watch run picks up where issue 43's ended (2026-11-11 13:35 UTC) and runs to the morning of 12 November; the entries (version, date, link, description from the release notes, licence status) come from the watch output, which was not among the sources for this draft. Left empty on purpose. -->
