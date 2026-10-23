# Colab drift v3: does a fixed-seed call give the same answer on another VM? (2026-10-23)

**Question:** with the seed honoured and the prompt cache off, does the same critic or writer request return the same
bytes on two different Colab VMs? And does a different card or binary change that?

**Why it was asked:** in window 16w (one paid Colab GPU session), three writer requests were re-run on a second A100.
The model's top five candidate tokens and their log-probabilities were identical on both VMs, but the token each VM
picked differed. So the model computed the same thing and the sampling step diverged. The cause was rnd's proxy, which
dropped the per-call `seed` before the request reached the model server (fixed in rnd 1.1.23.1.28, ed4fafc). A second
possible factor, llama-server's prompt cache, was turned off per request (`"cache_prompt": false` in the card's
sampling block).

## Conditions (every arm unless stated)

- **llama-server:** build b4659b3f (llama.cpp 620d2225), with one slot, so requests run one at a time (batch 1).
- **Cards:** card-values v3 2927865f (`cache_prompt: false`), with the seed passed through the rnd proxy at ed4fafc.
- **role-set:** 8b55129a. Each journal row carries `messages_sha256`, `slot` and `attempt`, so any unmatched request can
  be explained from the record, and a retry uses a different seed from the first ask.
- **Models:** muse-glimmer-30b Q8_0 as critic and gemma-4-31b-it Q8_0 as writer, on the T10 pilot. The run resumes
  after the first writing wave (w0) from 15w's sealed drafts, so every arm critiques the same drafts.
- **GPU:** Colab A100-SXM4-40GB. G4 and C80 are the exceptions, below.
- **Comparison:** compare.py matches calls by request key and compares the completions byte for byte. A "decision
  drift" is a change in a verdict field.

## Cache off, verified on every arm that returned its log

A checker reads llama-server's `timings.cache_n` and `usage.cached_tokens` on every generation record. It fails on any
cached token, and on any record that has neither field.

| Arm | Role, GPU | Records | With cached tokens |
|---|---|---|---|
| W1 | writer, A100 | 3 | 0 |
| W2 | writer, A100 | 3 | 0 |
| E1 | critic-eval, A100 | 318 | 0 |
| P1r | critique, A100 | 178 | 0 |
| G4 | critique, RTX PRO 6000 | 179 | 0 |
| C80 | critique, A100 80 GB | 178 | 0 |

The checker also passes a positive control: on 16w, run with the cache on, it flags 3 of 4 calls as reusing cached
tokens: 3 of 4 calls, with 7,016, 350 and 350 cached tokens.

## Result: A100 against A100, byte-identical everywhere

| Comparison | Role | Calls matched | Exact | Drift |
|---|---|---|---|---|
| P1r vs P2 | critique | 176 | 176 | 0 |
| P1r vs P1 (partial) | critique | 72 | 72 | 0 |
| P2 vs P1 (partial) | critique | 72 | 72 | 0 |
| E2 (partial) vs E1 | critic-eval flaw votes | 101 | 101 | 0 |
| W2 vs W1 | writer (16w's three slots) | 3 | 3 | 0 |

**Three A100 VMs agree byte for byte on every critique call they share, across all 176 calls.** Critic-eval
and the writer agree too. The writer requests that diverged in 16w now match, which confirms the seed fix on the path
where the bug showed.

Calls are paired by request key. P1r and C80 each made 178 calls to 176 distinct requests: role-set sent two
attempt-0 verdict requests twice, identically (T10-D-01 and T10-D-09, a known role-set defect, ticket item 17). P2's
rebuilt journal holds 176 calls to 174 distinct requests. A third replicate (P3) was held in reserve and not run, because neither of its triggers fired
(an isolated mismatch, or a split between hosts).

## A different GPU and binary: G4 (RTX PRO 6000 Blackwell, build 39742d8a)

G4 sent the same requests, with the cache off, to its own sm_120 build of the same llama.cpp commit. Against P1r:
- **113 of 178 calls exact, and 65 drifted, every one with a decision change.** The first divergence is at T10-C-01's
  first trait call. G4 made 179 calls: one extra retry (T10-C-04's verdict, attempt 1) that no A100 run needed, a
  knock-on of its drift.
- Both the GPU and the binary differ, so this run can't say which one causes the drift. C80, below, changes only the
  A100's memory size.
- **Don't pool G4 results with A100 results.**

**Throughput,** medians over the same 178 requests, which have near-equal token counts:

| | A100 | G4 | G4 / A100 |
|---|---|---|---|
| prompt tok/s | 1,264 | 3,863 | 3.06× |
| generation tok/s | 33.6 | 44.3 | 1.32× |
| total model time | 11,118 s | 8,350 s | **1.33×** |

G4 costs about 1.68× the A100 per hour (8.90 against 5.3 units), so for this work, one request at a time and limited
by generation speed, it costs about 26% more per call. Its 3× faster prompt reading would pay off on prompt-heavy jobs
or large batches, and its 96 GB on models that don't fit in 80 GB. The outputs diverge early, so no two calls generated
the same tokens in the same order to compare one to one; the ratio comes from total model time over the same requests.

## The 80 GB card, same binary: C80

C80 ran on a Colab A100-SXM4-80GB with the same llama-server binary (b4659b3f) and the same requests, with the cache
off (178 records, 0 with cached tokens). Against P1r:
- **178 of 178 calls exact, no drift.** The 80 GB card gives the same bytes as the 40 GB card.
- So G4's drift doesn't come from the amount of memory on the card. Among the things this study varied, it comes from
  the Blackwell GPU, its sm_120 binary, or both.
- C80's results can be pooled with the 40 GB A100 arms.

**Throughput,** over the same 178 requests:

| | A100 40 GB | A100 80 GB | 80 GB / 40 GB |
|---|---|---|---|
| prompt tok/s | 1,264 | 1,280 | 1.01× |
| generation tok/s | 33.6 | 37.2 | 1.11× |
| total model time | 11,118 s | 10,046 s | **1.11×** |

The 80 GB card costs about 1.28× the 40 GB per hour (6.77 against 5.3 units), so for this job it costs about 15% more
per call. It's worth choosing only when a model or batch needs more than 40 GB.

## Lost VMs, and what the logs kept

Three of the six long A100 windows lost their VMs:
- P1 at 1 h 30 m, partway through a wave;
- P2 at 3 h 16 m. Its rebuilt record stops 2 calls before the end of the run;
- E2 at 1 h 16 m.

Each loss happened while 3–4 Colab sessions were running. Two of the three lost VMs were the oldest session running,
and one wasn't. Three losses are too few to name a cause, so this is recorded, not explained.

Each call writes its journal row into the job's log as a compressed line, and the rig downloads that log from the VM
every 2 minutes while the job runs (`smoke_window.sh`, `PIN_WATCH_S` default 120). When a VM is lost, the rig keeps
its last copy, at most about 2 minutes behind, and the journals were rebuilt from it. P1r closed normally, and its
rebuilt journal equals the official one on 178 of 178 rows, so the rebuild itself is faithful. On one lost VM it
stopped short: P2's rebuilt journal (176 checkpoint lines in its log) is missing
exactly P1r's last two calls, T10-D-AP-06's trait retries (attempts 1 and 2). The log can't show whether P2 made
those calls and lost them in the final fetch interval, or the VM died first. What a loss does cost is the generations log (timings and cache readings) and
the run record. Streaming those into the log the same way is filed as role-set work.

## Cost

In Colab compute units (the A100 40 GB costs about 5.3 an hour):
- **Critique:** P1 (lost) 7.90, P2 (lost) 17.19, P1r 17.62.
- **Critic-eval:** E1 16.15, E2 (lost) 6.64.
- **Writer:** W1 1.37, W2 1.37.
- **G4:** the build window 16g 0.93, and the run 21.85.
- **C80:** 20.47.
- **Earlier windows:** 16w 1.26 (the cache-on control cited above) and 16s 0.18. 16s was halted about a minute in,
  when the seed was found not to reach the model.
- **CPU stubs:** 16y 0.01, 16v 0.04, 17b 0.03, 17a 0.03 and 16x 0.02 (16x's booking is pending).

**Total: 113.06 units,** 112.93 of them on GPU windows and 0.13 on stubs. Every line was reconciled against the units
ledger.
