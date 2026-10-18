---
title: "Claude + Colab: the path we'd use again"
description: Three days of running model work on rented Colab GPUs from Claude Code, 49 windows, every unit accounted for. On the first night most of the spend bought nothing it was opened for. By the second day a 4-writer window finished under its projection and its cap. Here is what changed, the data behind it, and templates you can take.
issue: 13
date: 2026-10-18
highlights:
  - "<strong>From 31% to 69%.</strong> On night one, 31% of the units bought the results their windows were opened for, and 40% were lost to dropped VMs, cap stops and our own faults. On day two, 69% bought results, and 4% were lost."
  - "<strong>Test for free first.</strong> 13 test windows on CPU runtimes cost 0.46 units in all. One caught a refused step two review rounds had missed, before it could fail on paid time."
  - "<strong>Do the preparation on CPU.</strong> Converting a model on a CPU runtime cost 0.07 units. Downloading the finished files on the A100 took 684 seconds against 5,145 projected for converting them there."
  - "<strong>Byte-match or don't use it.</strong> Requiring every rebuilt model file to equal its earlier checksum caught a surprise: the same conversion gave different bytes on a CPU runtime than on the A100. The recorded environments differed in their PyTorch build; the host CPU's instruction set is still to be ruled out."
---

The studio runs its model work on rented GPUs. Claude Code drives Google's Colab from the command line: it asks for a
machine, sends the job, follows it and stops it. Nobody watches a notebook. Each of these sessions is a **window**,
paid in Colab compute units: about 5.3 an hour for an A100, 0.08 for a basic CPU runtime.

[Issue 11](../issue-11/) told how night one went: the writer screen got its answers, but about half of the first 71
units bought nothing their windows were opened for. This issue follows the same work through day two and sets out
the way of working that came out of it. The path itself, with templates, is a handbook page:
[Rented GPU windows (Claude + Colab)](../../handbook/rented-gpu-windows/). Every window's numbers are in the repo, one
row each, and the last section says where each figure comes from.

## The two days in one table

Each window is classed by what it gave back: **results** (what it was opened for), **partial** (some of it),
**lost** (a dropped VM, a cap stop, or a fault in our own tooling), or **test** (a free run on a CPU runtime).

| | Night one (Oct 17) | Day two (Oct 18) |
|---|---|---|
| Windows | 33 | 15 |
| Units spent | 141.1 | 31.6 |
| Bought results | 43.3 (31%) | 21.9 (69%) |
| Partial | 41.1 (29%) | 8.0 (25%) |
| Lost | 56.6 (40%) | 1.3 (4%) |
| Test runs | 0.03 | 0.43 |

Two caveats. Day two's paid work was smaller and better rehearsed, so the comparison flatters it somewhat. And some
spend figures are estimates where two windows shared a cap: summed window by window, the three days come to 172.7
units, while the account's balance fell by 166.5 over the same span. The balance is the measure; the per-window rows
were booked on the high side.

## What changed, step by step

**1. Two lanes.** CPU runtimes do the preparation: converting models, testing, measuring. The A100 only serves models.
On night one, every A100 window downloaded and converted its own models, 15 to 21 minutes each, before any real work.
Now a CPU runtime converts each model once, at 0.26 units an hour, and the A100 downloads the finished file.

**2. Measure first, then budget.** Every projection uses a measured rate with its receipt. Every window has a cap at
the projection plus 15%, and opens only if the cap plus 2 units is left. When one cost was still a guess (the
"twin" waves had never run on a GPU), the smaller window ran first and measured it: twin slots cost about twice a
normal slot, not the same.

**3. One script runs a window,** and it trusts nothing it hasn't checked. It refuses bad inputs before asking for a
machine, checks the machine before uploading anything, follows the job's own log file rather than the command's
output stream (which went quiet on us mid-run), counts only its own spend against the cap, and fetches the
job's log, and its results when the job got that far, on every way out.

**4. A health check on every new machine.** Before anything is uploaded, one short command reads the card, the disk,
the memory and the download speed. A bad machine is stopped and a fresh one requested. On day two it ran 12 times and
rejected 2: one machine whose first command died (two night-one windows had lost about 4.5 units that way, after
their uploads), and one downloading at 45 MB/s. Each rejection cost a few minutes of machine time, not a run.

**5. The job saves itself.** It writes every finished model call and every finished wave into its log, so a killed
window's work can be pulled out of the log, and the next window can resume from it. Each saved file carries a
checksum, and a file that doesn't match is refused.

**6. A test ladder before any paid run:** unit tests, then the real script against a fake command-line tool, then the
real job on a real CPU runtime with stand-in models, then the paid window. The 13 test windows cost 0.46 units in
all. One of them caught a step that would have been refused partway through a paid window: an older file format lost
a record of the model's settings on its way through the pipeline. Two review rounds had read that code and passed it.

**7. Three seats review everything.** One Claude session builds, a second reviews the actual diff (not the summary of
it), and an outside model from another company reviews from a written brief. The loop repeats until it passes, and a
reviewer who asked for fixes sees the fixed version before anything paid uses it.

**8. Pre-built models, checked byte for byte.** A converted model file goes into the studio's private repository only
if its checksum equals the one recorded when the arms first ran on it. A file that doesn't match is never used, and we
never change the recorded checksum to make a file fit.

**9. Tokens that can't leak far.** One access token per job type, each limited to the one private repository, sent to
the machine as a file in memory, read once at the start, and kept out of every log. A test pushes a fake token through
the real script and checks it appears nowhere.

## What the path caught

- **The stand-in run caught the lost model settings** described in step 6. Fixing it took a small rule for the older
  files, checked by checksum against the file they came from.
- **The first paid window after the ladder found what the ladder couldn't:** a writer whose two twin attempts both
  failed was still sent to a critique, which then refused. No stand-in model had ever failed every attempt. The fix is
  one line, and the lesson is in the handbook: give your stand-ins the failures you expect from real models.
- **The byte-match rule caught a surprise.** Qwen3.8, converted again on a CPU runtime, came out the same size as
  before with different bytes. The recorded package lists differed in one material place: the A100 image's Python
  carried the GPU build of PyTorch 2.11.0, the CPU image the CPU build. Models converted in their own environment (which
  always gets the CPU build) matched on both machines, and Qwen3.8 matched again when rebuilt on an A100. We think the
  PyTorch build is the cause; the host's CPU instruction set hasn't been ruled out yet.
- **An upload failed after a conversion had already matched.** The job had installed packages into the very Python it
  was running, partway through, and its final step tripped over the mix of old and new library code. The upload now runs
  in a fresh process.
- **The health check's speed test reads low.** Its short 200 MB read gave 88–115 MB/s on A100s that then downloaded at
  179–310 MB/s. Our first speed floor, set from full downloads, would have turned good machines away. The floor now only
  rejects a broken connection.

## The payoff: one window, under its projection

Window W-A resumed four writers (Qwen3.8, Gemma 4, Granite 4.2 and Bolt) from their saved drafts, with Muse as the
critic. It rewrote the one draft that had been sent back, then ran two "twin" practice rows per writer.

- It downloaded the four pre-built model files, 122.4 GB, in 684 seconds. Each matched its checksum.
- It finished on its own after 11,749 seconds: 17.55 units against a projection of 21.8 and a cap of 25.1.
- Every writer's saved results came back: 30 rows from the pilot and 6 accepted twins, with no model errors.
- The projection was 19% high: setup came in far under, and the twins ran over.

These rows come from a screen with a fixed set of eight slots, so they're not a releasable batch: they fail the
batch-mix rule a real batch must pass.

## Still open

- **Prove the PyTorch explanation** with a one-layer conversion before any full one, recording the machine's CPU.
- **Recalibrate the speed floor** from more paired readings, and try downloading files in parallel.
- **Record the CPU model on every health check,** so a machine difference can be seen, not inferred.
- **Pin new conversions in their own environment** with the exact PyTorch build, in the next study.

## Take it with you

The handbook page [Rented GPU windows](../../handbook/rented-gpu-windows/) has the full path and templates: a launch
file, a projection worksheet, a ledger row, a per-window results file, and a brief for an outside reviewer. The window
code is in role-set (`scripts/colab/`), and the data behind this issue is in rnd's
[`experiments/colab-golden-path/`](https://github.com/mcp-tool-shop-org/rnd/tree/main/experiments/colab-golden-path).

## Where each figure comes from

All paths are in [mcp-tool-shop-org/rnd](https://github.com/mcp-tool-shop-org/rnd) unless noted.

- **Units, windows and classes by day** (the table, 31% → 69%, 40% → 4%, 13 tests at 0.46 units, 172.7 summed):
  `experiments/colab-golden-path/figures.json`, computed by `figures.py` from `data/windows.csv`. Each window's class
  comes from its own `outcome.json`, written by the Publisher when the window closed (`outcome_source` says which).
- **166.5 units by the balance:** the first window's start balance, 1207.67 (`data/windows/window1-20261016/` and its
  ledger note), the last window's end balance, 1141.14 (window 13l), and the 100-unit top-up recorded in
  `data/units-ledger.md`.
- **Rates** (5.3, 0.08, 0.26 units an hour): `instruments/colab.md` and `data/windows/_top/highmem-rate-probe.txt`.
- **About half of the first 71 units:** [issue 11](../issue-11/).
- **15 to 21 minutes of setup per model:** night one's job logs, as measured in the W-A projection
  (window 13l's README in the Publisher's receipts, summarised in `data/windows/window13l-20261018/`).
- **Health check, 12 tries and 2 rejections, 45 MB/s:** `figures.json`'s `gate` block, from each window's
  `gate.jsonl`. **About 4.5 units lost to first-exec deaths:** windows 11c (3.2) and 12e (1.29) in `data/windows.csv`.
- **Twin slots about twice a normal slot:** window 13b (W-B) and 13l (W-A) results, per writer.
- **0.07 units and 15 minutes per CPU conversion:** window 13e (Muse) and 13g (Gemma) rows in `data/windows.csv`.
- **The PyTorch difference:** the pip freezes in windows 12f, 13f, 12h and 13e, and the outside review's reply on it;
  the A100 rebuild that matched is window 13j.
- **The failed upload:** window 13i. **The speed-test pairs** (88–115 against 179–310 MB/s): windows 13i, 13j, 13k and
  13l, short reads from `gate.jsonl` and download rates from their job logs.
- **W-A** (684 s, 122.4 GB, 11,749 s, 17.55 units, 21.8 and 25.1, 30 rows and 6 twins, 19%): window 13l's
  `pin-result.json` and README, summarised in `data/windows.csv`.
