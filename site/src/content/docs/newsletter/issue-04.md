---
title: Three devices, no contention
description: E4b answers E4's question. The 5090, the NPU and the iGPU keep their speed when they run together. Getting there took a pilot, a run of live-only defects and one re-run.
issue: 4
date: 2026-10-12
highlights:
  - "<strong>All four device pairs run free:</strong> the 5090 slows by under 1.4% beside the NPU or iGPU, and the Intel devices by at most about 5% beside the 5090, all inside the pre-registered ±10%."
  - "<strong>One result was caught being wrong for the right reason:</strong> a clock check refused measurements taken before the 5090 was running steadily, and the fixed re-run came back clean."
  - "<strong>One defect class keeps coming back:</strong> test fakes that behave as the code assumes, not as the platform does."
  - "<strong>The puzzle generator's first slices passed review</strong>, and batch 6 is clear for the Stage 1 freeze."
---

Every claim below links to the record it came from. Interim results are labelled as interim. The device router
switchyard is now **interlock**, renamed before its first release because the old name is taken.

## E4b's result

E4b asks whether each device keeps its speed when another runs beside it. A pair counts as "free" only when the 90%
interval of its slowdown sits inside ±10%. That rule was fixed in advance.

| Measured device | Beside | Change | 90% interval | Verdict |
|---|---|---|---|---|
| 5090 (decode rate) | NPU | −0.8% | −1.2% to −0.5% | free |
| 5090 (decode rate) | iGPU | +0.6% | +0.2% to +1.4% | free |
| NPU (latency) | 5090 | −0.6% | −1.3% to +0.1% | free |
| iGPU (latency) | 5090 | +2.5% | −1.0% to +4.8% | free |

So the router can treat the three devices as independent lanes, and E4's question is answered.

![E4b verdicts: each pair's interval against the ±10% band](/rnd/charts/e4b-verdict.svg)

![E4b: each triplet's change, pair by pair](/rnd/charts/e4b-triplet-effects.svg)

The NPU and iGPU rows took a second run. In the first full block those two pairs came out **inconclusive**, and not
because of noise. The Intel calls take about 40 ms, and the harness ran them within a tenth of a second of starting the
5090. So they overlapped the 5090's start, not its steady decode. The clock check refused them. The harness now waits
for one steady 5090 warm-up, and the re-run of just those two pairs had no refusals at all.

One detail for routing: the iGPU's latency beside a 5090 decode is sometimes about 6% higher, which is inside the band
but worth knowing for latency-sensitive iGPU work. That chart was drawn after the verdict, and it decides nothing.

![E4b: iGPU call times beside a busy 5090 (post hoc)](/rnd/charts/e4b-igpu-latency.svg)

→ [The E4b data and charts](https://github.com/mcp-tool-shop-org/rnd/tree/main/experiments/e4b)
→ [E4b block 2](https://github.com/mcp-tool-shop-org/rnd/blob/main/entries/2026/2026-10-12-e4b-block-2.md)

## How the harness got there

E4b is the redesign of the co-scheduling experiment that [came out inconclusive](https://github.com/mcp-tool-shop-org/rnd/blob/main/entries/2026/2026-10-12-e4-co-scheduling-inconclusive.md).
Its harness merged after two rounds of review.
- **It runs its own Ollama server.** The server inherits the system environment with every Ollama setting stripped, then
  gets three pinned values.
- **Before it measures anything,** the run refuses unless the server's new log shows the CUDA 13 backend, the model sits
  wholly in GPU memory, and the model's digest matches the spec.
- **Before the server starts,** the VRAM watchdog must be alive and the card must be empty.

A pilot of 20 calls on the 5090 alone set the clock tolerance from data, at 22.5 MHz (three of the card's clock steps).
All 20 ran at full length, at 218–224 tokens/s.

![E4b pilot: how far the 5090 clock moved during each call](/rnd/charts/e4b-pilot-clock.svg)
→ [The switchyard review record](https://github.com/mcp-tool-shop-org/rnd/blob/main/instruments/switchyard.md)

## Live-only defects

The first pilot attempts stopped before any device work, with the card idle.
1. **The listener looked closed.** After an overnight update, Windows build 26340 reports Ollama's listening socket
   as "Closed", so every lookup by listening state found nothing. → [The rig fact](https://github.com/mcp-tool-shop-org/rnd/blob/main/entries/2026/2026-10-12-windows-26340-listener-state-closed.md)
2. **The command runner threw its output away,** so the server pin read nothing. Worse, the git check read "no
   output" as "clean tree". It now fails closed.
3. **The pilot counted its prompt before its own server existed.**

A read of the pilot path then turned up more of the same, all fixed before the fourth try:
- the start didn't wait for the server to come up;
- GPU clock sampling wasn't connected;
- there were no request timeouts.

The fourth try showed that E4's prompt, one sentence repeated, makes the model loop at long lengths, so E4b now counts
"1, 2, 3, …". The first full block then lost its record to a read-only NPU cache file at cleanup. The harness now writes
the record first, refuses run names already in use, and sets aside any run that stops.

## Fakes that told the truth, continued

[Issue 3](/rnd/newsletter/issue-03/) described four failures caused by test fakes. The count is now seven. The pattern is the same
each time: a test swaps in a stand-in for a real call, and the real version is never exercised. The remedies are:
- recorded real exchanges;
- one test that builds the live setup with nothing swapped in and fails if anything is still a stand-in;
- reads that refuse a missing value instead of passing it.

→ [Test fakes that hide the platform](https://github.com/mcp-tool-shop-org/rnd/blob/main/entries/2026/2026-10-12-test-fakes-hide-the-platform.md)

## The puzzle generator and batch 6

- **Dated spans.** The solver now works out which edition was in force on a given day. The writer can't state it,
  which closes the shortcut that let a placeholder date pass.
- **The generator's first slice** builds T10 puzzles, then proves that a reader who misreads "exactly" or "at least"
  gets a different answer. T10 uses only "which could be…" and true/false questions, because a single-answer
  question can't show that misreading.
- **Batch 6's last fixes** were wording and options only, and it is clear for the Stage 1 freeze.

→ [The role-set review record](https://github.com/mcp-tool-shop-org/rnd/blob/main/instruments/role-set.md)
