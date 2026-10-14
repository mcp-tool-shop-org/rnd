---
title: The tracer that kept every promise but one
description: We put NVIDIA's NeMo Relay inside our local-model harness under a pre-registered test. It traced faithfully and leaked nothing, and it still failed, on a cost we had set a hard budget for. How the verdict stood, what the diagnosis found in our own harness, and why the decision departed from the rule on purpose.
issue: 7
date: 2026-10-14
highlights:
  - "<strong>A frozen analysis said no, and no was kept:</strong> the verdict was computed by code frozen before the run, and nothing was re-scored afterwards."
  - "<strong>Two of the three failures were ours:</strong> an off-by-one request from a card check outside the tracing window, and three stray spans from a teardown after its slot closed."
  - "<strong>The third was real and reproducible without the GPU:</strong> about a quarter of a millisecond per call, on a CPU waking from the rest between measurements."
  - "<strong>The decision departed from the pre-registered rule, on purpose and on record:</strong> Relay stays as a debugging tracer, never on counted runs, and the build landed the same day."
---

Every claim below links to the record it came from.

## The question, and the rule set before the run

[interlock](https://github.com/mcp-tool-shop-org/interlock) measures local models: it drives them through Ollama on the RTX 5090 and writes a receipt for every measurement. [NeMo Relay](https://github.com/NVIDIA/NeMo-Relay) is NVIDIA's open tracing library for agents. The question was narrow: **can Relay trace interlock's model calls without changing what interlock measures?**

The design was pre-registered and reviewed by a model from a different family at each step, with the analysis code frozen before any counted run. → [The design, v3.1 to v3.2](https://github.com/mcp-tool-shop-org/rnd/blob/main/experiments/interlock-relay/design.md)

Three hypotheses, and a decision rule written as a tree:
- **H1:** the trace accounts for every request the harness sends. Fail this, and Relay is rejected.
- **H2:** tracing doesn't move the measurements, within a band taken from the run's own noise, and it costs the harness under **0.5 ms** per two-call measurement on the client side. Fail this, and Relay is kept for debugging runs only.
- **H3:** nothing leaks: no prompt text, no paths, no machine or user names.

Stage 0, on fakes, held. Stage 1 ran on the 5090 on 2026-10-14, under a grant with a time cap, a VRAM watch and a preflight that checked the card, the CPU and the environment before every step. The first attempt refused itself after eight seconds, because it had been launched from the wrong Python environment; the driver now checks that too. → [The stage 1 plan](https://github.com/mcp-tool-shop-org/rnd/blob/main/experiments/interlock-relay/stage1-plan.md)

## What the frozen analysis said

**stage1_holds = false.**
- **H1 failed in every step,** by exactly one request each time: 204 sent against 203 counted, 217 against 216, and so on. The companion step also had three spans that belonged to no measurement.
- **H2 held on every model number.** Decode speed, prompt speed and latency were equivalent with tracing on. The client-time budget failed: medians of 0.548 ms and 0.682 ms against 0.5.
- **H3 held everywhere.**

Under the tree, H1 failing means reject. The analysis is byte-identical to its freeze, and nothing was re-scored. → [The result note](https://github.com/mcp-tool-shop-org/rnd/blob/main/experiments/interlock-relay/stage1/result-note.md)

## The diagnosis: two of ours, one real

Read-only, from the run's own records.

- **The off-by-one was the harness's empty-card check.** Before a 5090 run, interlock asks the server what's loaded. That request went through the adapter, so the driver's counter saw it, but it went out before the tracer was attached. With that one request set aside, every count matched exactly. No traced call was missed.
- **The stray spans were the companion's stop.** The harness closed the measurement, then unloaded the companion model, then switched tracing off. The unload was traced but belonged to nothing.
- **The client time was real.** A traced call cost about 270 µs more than an untraced one. A CPU-only bench against a stub transport, with the same 250 ms rest before each measurement, reproduced the live figure within about 10%, with no GPU at all. Most of the cost is Relay's own work per call; the rest was our own serialisation of long prompts to measure their size. Removing ours would not have passed the gate.

The outside reviewer checked all three and agreed, and added a test we hadn't thought of: the four large deviations in the import check split three faster to one slower, which is noise, not a slowdown from importing the library.

## The decision, and why it departed from the rule

The rule said reject. The Director chose **debug-only tracing** instead, recorded as a dated amendment (v3.2) and as his call: H1's failure was a counting-window bug with every request accounted for, so H2's branch is the one that fits. The stage 1 verdict stands as frozen. A rerun was ruled out, because the cold bench shows the client-time gate would fail again. No further GPU or NPU time goes to Relay.

**The build landed the same day.** The reviewer wrote it from the result note; we applied it with six recorded departures (one of them a real defect in the draft that would have silenced ordinary traces); the reviewer then checked the branch itself and approved. The card check now runs inside the tracing window, the companion stops inside its own measurement, request sizes come from the bytes actually sent, and every row of a traced run is marked and kept out of the routing table, which the trial's rows had reached. A deterministic test drives the real adapter and real HTTP client against a fake server and checks that every request is counted, every span is matched and closed, and nothing leaks. → [The build round's review](https://github.com/mcp-tool-shop-org/rnd/blob/main/experiments/interlock-relay/argon-code-review-v32.md)

One more defect fell out of the review: the request-size field in Relay's records had never held the request size. The sanitizer was re-measuring its own `{"bytes": n}` record, so every value was 13 or 15. It's fixed, and no verdict depended on it.

## What we'd do the same, and what we learned

- **Freeze the analysis before the run, and keep the verdict even when the cause is yours.** A rerun is a new pre-registration, and a departure is a dated amendment with a name on it. That is what made the diagnosis trustworthy.
- **Count below the hook.** The off-by-one was only visible because the driver counted requests independently of the tracer. A tracer checking itself would have passed.
- **Bench the cold case.** The warm bench put Relay at 30 µs per call; the live rig said 270. Putting the stage's own rest before each measurement on a CPU-only bench explained the gap without touching the GPU.
- **Settle a ruling with the outside reviewer's input before sending it.** Two reversals in one evening on another repository cost a paste and a re-read each. That's now a working rule.

→ [The NeMo Relay brief](/rnd/briefs/agent-tracing-nemo-relay/), now measured.
