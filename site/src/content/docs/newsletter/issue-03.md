---
title: A second opinion on the first live runs
description: switchyard's first live runs on the 5090, NPU and iGPU, what went wrong, and what an outside model's review changed.
issue: 3
date: 2026-10-12
highlights:
  - "<strong>An outside review of our first live runs</strong> (Kimi K3) proposed six changes. R&D accepted most, changed three and rejected one."
  - "<strong>E4 ran cleanly and decided nothing:</strong> all four device pairs were too noisy to call under the rules we set in advance."
  - "<strong>Four of the night's failures</strong> were test fakes that didn't behave like the real server. Real recorded replies now stand in for them."
  - "<strong>A new design rule:</strong> the harness owns the server it measures, and probes never change what they probe."
---

Every claim below links to the record it came from. Interim results are labelled as interim.

## The first live runs

switchyard is the studio's device router: it decides which model runs on the 5090, the Intel NPU or the iGPU, from
measurements rather than guesses. On 2026-10-11 and 12 its harness made its first live runs.
- **E4** asked whether the Intel devices can work beside the 5090 without slowing either side.
- **E5** asked how large a context window each model can hold on the card.

Getting there took a series of fixes, each logged with its evidence:
- a token count that Ollama read as "no limit";
- a prompt search that made thousands of calls;
- two missing input shapes;
- a crash on the NLI model's output.

→ [The live-run records](https://github.com/mcp-tool-shop-org/rnd/blob/main/instruments/switchyard.md)

**E4's result is inconclusive.** The run was valid. Nothing measured slower when paired, and the iGPU even ran
about 15% faster. But every "alone" baseline varied more than the pre-registered noise rule allows, so no pair can be
called. We traced the noise to three things:
- the GPU clocks hadn't settled during short calls;
- the NPU woke slowly after a pause;
- a control request was silently reloading the model.

E4 isn't re-run as it stands.
→ [E4: co-scheduling inconclusive](https://github.com/mcp-tool-shop-org/rnd/blob/main/entries/2026/2026-10-12-e4-co-scheduling-inconclusive.md)

## The outside review

The Director put the night's findings to Kimi K3, a model from outside the families that built the harness, which
read both experiment specs. R&D ruled on each of its six points.

- **E4's noise rule (accepted, with one change).** The old rule pooled every "alone" measurement, so it counted the
  very drift that alternating alone, paired, alone is meant to cancel. The redesign, E4b:
  - scores each alone–paired–alone triplet as its own log-ratio;
  - calls a pair free only when the 90% confidence interval of those ratios sits inside ±10% (an equivalence test);
  - throws out any single call that reloaded the model or whose GPU clock jumped.

  R&D's change: an interval wholly outside the band counts as "not free" on either side, faster included, as the
  original spec said, because either way the devices are affecting each other.
- **The spill signal (accepted in part).** A whole-adapter memory counter replaces the per-process counter, whose
  process lookup broke when the server ran as administrator. R&D rejected the proposed "two of three signals"
  rule: it would have loosened a rule we fixed in advance, after seeing the data.
- **A live test tier (accepted, changed).** The same recorded cases also run live against a tiny model on a CPU
  Ollama the harness starts for itself, before each live run and on every Ollama update. It doesn't run nightly, and
  it never touches the CPU instance another tool depends on.
- **Design rules (accepted).** The harness owns the server it measures: it starts it, or reads a declared record of
  how it was started. Probes only read; they never change the state they read. And state is read at the moment
  of measurement, never pieced together afterwards.
- **The iGPU speed-up (accepted, with a correction).** The suggested first check, CPU frequency from the existing
  receipts, can't work: Windows reported the same nominal 3,700 MHz on every call. A real frequency counter and a
  CPU-only control run come first.
- **Clock settling (accepted).** Use longer decodes, wait until the GPU clock holds steady before timing, and fix the
  clock reading that came back empty on every call.

→ [R&D's rulings on the review](https://github.com/mcp-tool-shop-org/rnd/blob/main/instruments/switchyard.md)

## Fakes that told the truth

Four of the night's failures had one cause: a test fake accepted something the real server treats differently.
- A completion limit of 0 meant "nothing" to the fake and "no limit" to Ollama.
- A search's cost was invisible to fakes, which take no time.
- A fake model returned rows the real one never does.

The remedy is to record real exchanges once, under a grant, and allow fakes to replay only those. The first
recording already overturned two assumptions:
- a very small context size is raised to a minimum, so it limits nothing;
- a request we treated as harmless loads the model.

→ [Ollama reads a zero limit as no limit](https://github.com/mcp-tool-shop-org/rnd/blob/main/entries/2026/2026-10-12-ollama-num-predict-zero-is-no-limit.md)
