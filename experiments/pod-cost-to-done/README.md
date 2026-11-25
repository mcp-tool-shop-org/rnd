# Is a faster pod cheaper per finished job? (design draft, 2026-10-19)

**Status:** draft. Nothing rents until the Director approves the spend. Template: rnd handbook "Experiments", with
the model-comparisons template's hardware-fit rules.

## The question

When we rent a GPU pod for a job, which choice gets the job **done** for the least time and money? Hourly price is
one input. Counting time is the point:
- **Hours-to-done multiply the rate.** A slower host takes longer, so its cheaper hour can cost more per job.
- **Failures cost time even when they cost little money.** That covers a pod that won't start, waits for capacity,
  a slow or broken host, a dropped VM and a job that has to be redone. Time is the studio's scarcest resource.

The hook is two runs of one job on 2026-10-19 (converting Super-VL-120B, 249 GB of BF16):

| Pod | $/hr | Download | Conversion | Outcome | Spent |
|---|---|---|---|---|---|
| A100-SXM4 job pod (128 cores, 2 TB RAM) | 1.79 | 19 min | direct Python Q8_0, 0.9 GB/min | timed out at 54.8 of ~127 GB | $3.05, nothing usable |
| RTX PRO 6000 Server (2× EPYC 9575F, 256 threads, 1.5 TB RAM) | 2.49 | 3.4 min | BF16 at ~11.9 GB/min, then llama-quantize | (in progress) | about $2–2.50 projected |

That pair isn't a fair comparison. The card, the host, the datacenter and the conversion route all changed at once.
This design separates them.

## What it measures

### Part 1: the same job on each pod type (planned runs)

- **The job:**
  - boot, then the environment, cmake and the llama-quantize build;
  - download Nemotron-3.5-Lightning's 65.8 GB BF16 at a pinned revision;
  - convert to BF16, then llama-quantize to Q8_0;
  - hash the result.
  - All of it runs through role-set's pinned `pin_window` (`via_bf16`) at one commit.
- **The pods** (one each; prices from `offrig_offers` at plan time):
  - RTX PRO 6000 Server;
  - A100-SXM4;
  - A40 (the jam class);
  - H100.
- **The route control:** on one of the pods (the RTX PRO 6000 Server), the same model also goes through the direct
  `--outtype q8_0` path. That separates the route from the card on the same host, and lets the output be checked
  against Lightning's known pin (`5bea2069`, a direct-path file).
- **Recorded on every attempt, failed ones included:**
  - **the host:** `lscpu`, `nproc`, `free`, `df` and the datacenter, read at boot;
  - **times:** capacity wait, boot-to-ready, download, BF16 write, quantize and hash;
  - **money:** $/hr and total spent;
  - **the outcome:** done, failed to start, cut, or failed mid-job, with the cause.
- **The determinism check:** the same route at the same commit should give identical Q8_0 bytes on every pod. A
  mismatch is a finding in itself.

### Part 2: failures and their time cost (records we already hold)

One run per pod type can't estimate a failure rate. The failure side comes from records already kept:
- `experiments/colab-golden-path/data/windows.csv`: every Colab window, with its card, outcome class (results,
  lost-vm, cap-stop, tooling-fault) and units spent;
- offrig's plan history for RunPod: each plan's GPU, the measured spend and how it ended.

These are observational, so they're reported as such: counts by card and outcome, and the time lost to each failure
class. They can't be read as a controlled failure rate.

## The metrics

These are fixed before any run. For each pod type:
1. **Time-to-done:** wall time from asking for the pod to holding a hashed result, including capacity waits.
2. **Cost-to-done:** money spent, including any failed attempt on the way.
3. **Throughput of each step** (GB/min for the download, the BF16 write and the quantize), so the bottleneck is visible.

The answer is reported as time first, then money. **A pod "wins" only if it's at least as fast and no dearer per
finished job.** Otherwise the trade-off is stated plainly: minutes saved per dollar spent.

## What it can't claim

- One pod per type is a pilot. Hosts vary within a type (today's A100 and RTX PRO 6000 Server pods had very
  different CPUs), so a single run describes that host, not the card.
- Prices and stock move by the hour, so every figure carries its read time.
- The job is CPU- and network-bound. GPU-bound work, like serving or training, may rank the cards differently, and
  this study says nothing about it.

## Cost and order

- **Price:** the Publisher's projection from live offers is $5.55–8.89 for the four pods, plus about $0.6 for the
  route control, with a cap of about $12.
- **Order:** the runs go in sequence, because a lane runs one pod at a time, and after the H200 critic run.
- **Before it rents:**
  - the RunPod balance is read live, and may need a top-up;
  - the Director gives his go on the spend.
- **The write-up:** a newsletter issue drafts from the results. Publishing waits for the Director's go.
