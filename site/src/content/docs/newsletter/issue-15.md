---
title: "Is the expensive pod the cheap one?"
description: Renting GPUs by the hour invites one question, which card is cheapest per hour, and it's usually the wrong question. Here's what our own rental records show, one costly lesson from this week, and the rules of thumb we now work by. Most of this is experience, not a controlled test, and we say which is which.
issue: 15
date: 2026-10-19
highlights:
  - "<strong>Price the job, not the hour.</strong> This week the same 249 GB download took 19 minutes on a $1.79/hr pod and 3.4 minutes on a $2.49/hr pod. The cheaper pod then spent $3.05 and produced nothing. The dearer one finished the whole job for $2.34."
  - "<strong>Failures are paid in time.</strong> Across 45 RunPod plans, three never got a pod at all, for lack of capacity. Across our Colab A100 windows, three VMs were lost mid-run and six windows were lost to our own tooling."
  - "<strong>Find the bottleneck before you pick the card.</strong> The slow conversion wasn't the card's fault: it was single-threaded Python on a 128-core machine. Changing the method made the same work about 13 times faster per byte written."
---

The studio rents GPUs for jobs too big for its own machine: converting large models, serving critics, training runs.
Two services do most of it: RunPod, through our `offrig` tool, and Google Colab. Both show a price per hour, so the
first question is always "which card is cheapest?" This issue is about why that's usually the wrong question.

**A note on what follows.** Some of it is measured: the timings and the spend are from our receipts. A lot of it
is opinion, built from our experience of running these jobs. The opinion is labelled as such. The last section says
where every figure comes from.

## One job, two pods

This week we converted a 120-billion-parameter model, Nemotron-3.5-Super-VL, for use as a critic. The job downloads
249 GB of weights, then rewrites them in a compressed 8-bit format.

| | First pod | Second pod |
|---|---|---|
| Card | A100 80 GB | RTX PRO 6000 Blackwell Server |
| Price | $1.79/hr | $2.49/hr |
| Host | 128 cores, 2 TB RAM | 2 × EPYC 9575F (256 threads), 1.5 TB RAM |
| Download, 249 GB | 19 min | 3.4 min |
| Conversion method | direct 8-bit, in Python | 16-bit first, then a multithreaded quantizer |
| Conversion rate | 0.9 GB/min of output | 11.6 GB/min (16-bit write), then about 2 min to quantize |
| Outcome | stopped by our one-hour limit at 55 of 127 GB | finished |
| Spent | $3.05, nothing usable | $2.34 for the whole job, measured (about $1.29 to the first usable file) |

Both pods ran the same pinned code apart from the conversion route. Even so, two things changed at once, so this isn't a
clean comparison:
- **The card and host changed.** The second pod downloaded nearly six times faster.
- **The method changed too.** The first pod spent its hour in single-threaded Python while 127 of its 128 cores sat
  idle. The quantizer we switched to uses every core.

We can't say how much of the gain came from the host and how much from the method. That would need the old method run on the new host.

## What 45 rented pods say

offrig keeps a record of every pod it plans. Across the studio's projects that's 45 plans, $59.60 measured in total.

offrig records the cards a plan *allowed*, not the one it got. So the classes below are inferred from each pod's
measured cost per hour, and rows near a class boundary could move.

| Inferred class | Plans | Wall hours | Spent |
|---|---|---|---|
| A40 class (about $0.49–0.56/hr) | 14 | 3.9 | $1.97 |
| A100 class (about $1.59–1.81/hr) | 7 | 4.5 | $8.08 |
| RTX PRO 6000 Server (about $2.09–2.49/hr) | 14 | 19.3 | $40.07 |
| Two-GPU writer pods (about $4.98/hr) | 2 | 1.4 | $7.13 |
| B200 (about $7.98/hr) | 1 | 0.3 | $2.35 |
| No pod (no capacity, never launched, or still running at export) | 7 | 0 | $0 |

What these records can and can't tell us:
- **Capacity is a cost.** All three plans that ended with no pod at all had asked only for the RTX PRO 6000 Server,
  and none was free. Each one cost nothing in money and some time in waiting and retrying. Popular cards are popular.
- **Three pods ended with a failed job** (a non-zero exit from the work).
- **The records don't say why a pod stopped:** a normal shutdown and our deadline watchdog look the same, which we
  plan to fix.
- **The rest is cheap work.** The A40-class pods are mostly the singing renders for another project: short, cheap jobs
  where a slow card costs little.

## What 26 Colab A100 windows say

Colab is different. Its A100 is the only big card our plan offers, so there's no card choice to compare. But the
failure side is clear:

| How a window ended | Windows | Compute units |
|---|---|---|
| Got its results | 9 | 65.0 |
| Partial results | 7 | 49.1 |
| Our own tooling's fault | 6 | 13.9 |
| VM lost mid-run | 3 | 18.3 |
| Stopped at its spending cap | 1 | 14.0 |

Over half the units (95 of 160) bought less than a full result. A good part of that loss came from failures: lost VMs,
cap stops and our own tooling. It didn't come from the price of the hour. [Issue 13](../issue-13/) tells how we brought that down.

## What we now do (opinion, from experience)

- **Price the finished job.** Cost = hours to done × price per hour, plus the time and money of any failed attempt.
  A cheaper hour that runs twice as long, or fails once, isn't cheaper.
- **Find the bottleneck first.**
  - A model conversion is CPU-, RAM- and network-bound, not GPU-bound, so a pod's processor and download speed matter
    more than its card.
  - Serving a model is GPU-bound, so there the card's memory and speed matter.
  - Read the tool's own code to find which step is slow. Our slow conversion was a single-threaded step that no card
    upgrade would have fixed.
- **Record the host.** Two pods with the same card can have very different processors. We now record the CPU, RAM and
  disk of every pod at boot.
- **Count time as the scarce resource.** A failed cheap run costs a little money and a lot of time: the wait for
  capacity, the re-download, the redo, and a person's attention. A failed cheap run costs the money and the time.
- **When a strong host is free, take it for heavy jobs.** This week's RTX PRO 6000 Server pod finished the job for
  $2.34, less than the $3.05 the cheaper pod spent failing at it. One pod is one data point, not a law, but it matches what we've seen.

## What we haven't tested

We drafted a controlled comparison: the same job on four card types, every attempt and failure recorded. We parked it
for now; it costs about $12, and the records above answer the practical question well enough for now. If we run it, it'll be its
own issue.

## Where the figures come from

- **The two Super-VL pods:** the Publisher's run receipts. The host specs are from `lscpu`, `free` and `df` at boot.
  The rates are from the conversion's own log and its disk readings. Both pods' spend is measured.
- **The 45 RunPod plans:** offrig's own plan database, exported read-only. The aggregate is
  [`experiments/pod-records/offrig-plans-by-class.csv`](https://github.com/mcp-tool-shop-org/rnd/blob/main/experiments/pod-records/offrig-plans-by-class.csv).
  The card classes are inferred from cost per hour; offrig doesn't record the card it rented.
- **The Colab windows:** [`experiments/colab-golden-path/data/windows.csv`](https://github.com/mcp-tool-shop-org/rnd/blob/main/experiments/colab-golden-path/data/windows.csv),
  as summarised in issue 13.
- **The tools:** [offrig](https://github.com/mcp-tool-shop-org/offrig) for RunPod, and
  [role-set](https://github.com/mcp-tool-shop-org/role-set)'s `pin_window` for the conversion.
