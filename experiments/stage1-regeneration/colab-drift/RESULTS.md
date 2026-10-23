# Colab drift v3: does a fixed-seed call give the same answer on another VM? (2026-10-23)

**Question:** with the seed honoured and the prompt cache off, does the same critic or writer request return the same
bytes on two different Colab VMs? And does a different card or binary change that?

**Why it was asked:** window 16w re-ran three writer requests on a second A100 and saw identical top-5
log-probabilities but different chosen tokens. The cause was rnd's proxy stripping the per-call `seed` (fixed in rnd
1.1.23.1.28, ed4fafc). A second factor, llama-server's prompt cache, was turned off per request
(`"cache_prompt": false` in the card sampling block).

## Conditions (every arm unless stated)

- **llama-server:** build b4659b3f (llama.cpp 620d2225), one slot, so batch 1 and calls one at a time.
- **Cards:** card-values v3 2927865f (`cache_prompt: false`), with the seed passed through the rnd proxy at ed4fafc.
- **role-set:** 8b55129a, so journal rows carry `messages_sha256`, `slot` and `attempt`, and retry seeds are disjoint.
- **Models:** muse-glimmer-30b Q8_0 as critic, gemma-4-31b-it Q8_0 as writer. T10 pilot, resumed after w0 from 15w's
  sealed drafts.
- **Card:** Colab A100-SXM4-40GB. G4 and C80 are the exceptions, below.
- **Comparison:** compare.py, by request key, byte for byte on the completion; a "decision drift" is a change in a
  verdict field.

## Cache off, verified on every arm that returned its log

A checker reads llama-server's `timings.cache_n` and `usage.cached_tokens` on every generation record, and fails on
any cached token or on a record with neither field.

| Arm | Role, card | Records | With cached tokens |
|---|---|---|---|
| W1 | writer, A100 | 3 | 0 |
| W2 | writer, A100 | 3 | 0 |
| E1 | critic-eval, A100 | 318 | 0 |
| P1r | critique, A100 | 178 | 0 |
| G4 | critique, RTX PRO 6000 | 179 | 0 |
| C80 | critique, A100 80 GB | 178 | 0 |

The control run 16w, with the cache on, shows 3 of 4 calls hitting the cache: 7,016 and 350 tokens.

## Result: A100 against A100, byte-identical everywhere

| Comparison | Role | Keys matched | Exact | Drift |
|---|---|---|---|---|
| P1r vs P2 | critique | 176 | 176 | 0 |
| P1r vs P1 (partial) | critique | 72 | 72 | 0 |
| P2 vs P1 (partial) | critique | 72 | 72 | 0 |
| E2 (partial) vs E1 | critic-eval flaw votes | 101 | 101 | 0 |
| W2 vs W1 | writer (16w's three slots) | 3 | 3 | 0 |

**Three A100 VMs agree byte for byte on every critique request they share, across all 176 unique keys.** Critic-eval
and the writer agree too. The writer probe that diverged in 16w now matches, which confirms the seed fix on the path
where the bug showed. A third replicate (P3) was held: neither of its triggers (an isolated mismatch, or a host split)
fired.

## A different card and binary: G4 (RTX PRO 6000 Blackwell, build 39742d8a)

G4 used the same requests, cache off, with its own sm_120 build of the same llama.cpp commit. Against P1r:
- **113 of 178 keys exact, and 65 drifted, every one with a decision change.** The first divergence is at T10-C-01's
  first trait call.
- The card and the binary both differ, so this run can't say which causes the drift. C80, below, changes only the
  A100's memory size.
- **Don't pool G4 results with A100 results.**

**Throughput,** medians over the same 178 requests, which have near-equal token counts:

| | A100 | G4 | G4 / A100 |
|---|---|---|---|
| prompt tok/s | 1,264 | 3,863 | 3.06× |
| generation tok/s | 33.6 | 44.3 | 1.32× |
| total model time | 11,118 s | 8,350 s | **1.33×** |

G4 costs about 1.68× the A100 per hour, so for decode-bound, batch-1 critic work it costs about 26% more per call. Its
3× prefill would pay on prompt-heavy jobs or large batches, and its 96 GB on models that don't fit in 80 GB. No calls
matched token for token in order, because the outputs diverge early, so the ratio comes from total model time over the
same requests.

## The 80 GB card, same binary: C80

C80 ran on a Colab A100-SXM4-80GB with the same llama-server binary (b4659b3f) and the same requests, cache off
(178 records, 0 with cached tokens). Against P1r:
- **178 of 178 keys exact, no drift.** The 80 GB card gives the same bytes as the 40 GB card.
- So G4's drift does not come from the card's memory size. Among the things this study varied, it comes from the
  Blackwell card, its sm_120 binary, or both.
- C80's results can be pooled with the 40 GB A100 arms.

**Throughput,** over the same 178 requests:

| | A100 40 GB | A100 80 GB | 80 GB / 40 GB |
|---|---|---|---|
| prompt tok/s | 1,264 | 1,280 | 1.01× |
| generation tok/s | 33.6 | 37.2 | 1.11× |
| total model time | 11,118 s | 10,046 s | **1.11×** |

The 80 GB card costs about 1.28× the 40 GB per hour (6.77 against 5.3), so for this job it costs about 15% more per
call. It is worth choosing only when a model or batch needs more than 40 GB.

## Lost VMs, and why no data was lost

Three of the six long A100 windows lost their VMs:
- P1 at 1 h 30 m, mid-wave;
- P2 at 3 h 16 m, after its last call;
- E2 at 1 h 16 m.

Each loss happened with 3–4 Colab assignments active. Two of the three were the oldest session running, and one
wasn't. That's too few to name a cause, so it is recorded here, not explained.

No call data was lost: the job writes every call's journal row into its log as it goes, and the rows were rebuilt from
there. On P1r, which closed normally, the rebuilt journal equals the official one, 178 of 178, so the rebuilt P1, P2
and E2 journals are faithful. What a loss does cost is the generations log (timings and cache readings) and the run
record. Streaming those the same way is filed as role-set work.

## Cost

Colab units:
- **Critique:** P1 (lost) 7.90, P2 (lost) 17.19, P1r 17.62.
- **Critic-eval:** E1 16.15, E2 (lost) 6.64.
- **Writer:** W1 1.37, W2 1.37.
- **G4:** 21.85.
- **C80:** 20.47.
- **CPU stubs:** under 0.1 each.
