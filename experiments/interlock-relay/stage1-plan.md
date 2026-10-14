# interlock-relay: stage 1 plan (Ollama on the 5090)

R&D, 2026-10-14. Stage 0 finished on fakes after two rounds of Argon code review (the [stage 0 record](stage0/README.md)). This plan is for the Publisher's grant request to the Director. **Nothing runs before his go.**

## What stage 1 decides

**H2:** turning Relay tracing on doesn't change what interlock measures on the 5090.
- **The primary gate:** for each metric, the per-triple difference Δᵢ = Bᵢ − (A₁ᵢ + A₂ᵢ)/2, where B is the call with tracing on and the A calls are off. The 90% interval of the mean Δ must sit within ±δ, where δ is half the metric's historical relative noise band.
- **The tail gate.**
- **Added client time,** a hard gate: under 0.5 ms at the median and under 2 ms at the 99th percentile.

**H1 and H3 again on the live server:** every call is captured exactly once, against the server's own request count, and the trace and receipts are safe.

## Before any GPU time: the stage 1 harness, on fakes

Stage 0 built the hooks. Stage 1's own procedure isn't written yet. It is, in order:

1. **An emission switch.** `Tracer` turns the sink's events on and off per slot, and the counter stays on. The sink is opened once per run and never reopened, as the design says.
2. **The per-slot barrier,** after every slot in both arms: `flush`, `gc.collect()` and a fixed 250 ms rest. This is Argon's M3, deferred to here.
3. **The triples:** off–on–off, built on interlock's existing `schedule_aba`, for each call kind.
4. **The process-level import check:**
   - 15 interleaved process triples: P_no_import → P_idle_import → P_no_import.
   - Each process makes 1 warm-up call and 3 measured calls.
   - Start-up and import time are recorded apart.
   - The same check compares A calls with and without the barrier.
5. **The H2 analysis,** frozen in a commit before the counted run, like stage 0's `diagnose.py`:
   - the two one-sided tests, the tail gate and the client-time gate;
   - the number of triples per kind, fixed from committed receipts by the design's power rule and recorded by amendment. The working estimate is 30 per kind.
6. **The stage 1 spec files,** committed so `require_unmodified` holds.

R&D recommends an Argon review of the harness and the frozen analysis before the counted run, as was done for stage 0. That's the Director's call.

## The runs (on the 5090, under the grant)

| Step | Model and shape | Calls | Estimated time |
|---|---|---|---|
| 1. Short decode | qwen3:8b, warm, 256-token prompt, 128 tokens (E4's shape: about 0.45 s a call) | 30 triples, plus 3 warm-up calls | ~2 min |
| 2. Long prompt (fill-card-sized prefill) | qwen3:8b, about 32k-token prompt. Each call gets a distinct prefix so Ollama's prompt cache can't skip the prefill. About 4 s a call at E5's 8,700 tokens/s | 30 triples (the floor is 15, sized by the power rule) | ~8 min |
| 3. Unload and companion | one explicit unload-and-reload cycle and one companion load (llama3.1:8b at a 4,096 context), each in a traced and an untraced slot | about 12 | ~4 min |
| 4. Stop file | one short traced run stopped through `<run_id>.stop` | — | ~2 min |
| 5. Process import check | 15 process triples, each with a process start, 1 warm-up and 3 calls | 180 calls | ~6 min |

- **Measured time:** about 22 minutes.
- **With loads, preflights, rests and margin:** request **60 minutes of 5090 time**, with a hard cap of 90. The design estimated 60–90.
- **When:** outside interlock's measurement windows. The card must be idle and unassigned.

## Peak VRAM

From E5's committed receipts (Ollama 0.35.1, Q4_K_M, f16 KV cache, flash attention):
- **qwen3:8b** at its full 40,960 context: **13,587 MiB** peak. Steps 1, 2, 4 and 5 stay at or under this.
- **Step 3's companion** adds llama3.1:8b at a 4,096 context next to qwen3:8b.
  - The estimate is under 21 GiB in total. That's unmeasured: E5 measured llama3.1:8b only at 53,248 tokens (14,247 MiB).
  - The run's own guard aborts at 30,500 MiB, as in E5.
  - If the companion's first load measures over 21 GiB, step 3 drops the companion and keeps the unload-and-reload cycle alone.
- **Idle baseline before the run:** at or under about 2.2 GiB (E5 saw 2,008–2,169 MiB).

## Preflight (every item refuses before any model call)

- **The grant:** the Publisher's grant id is on the command line. The run is outside every interlock measurement window, and the watchdog heartbeat is fresh.
- **The card:**
  - `/api/ps` is empty, with no other process on the GPU (nvidia-smi);
  - the idle VRAM baseline is recorded;
  - the supervisor sees exactly one listener on 11434, and it's the Ollama install.
- **The server:**
  - Ollama 0.35.1;
  - the CUDA backend library, flash attention and the KV cache type are read from the first load and recorded, as E4b and E5 do.
- **Tracing:**
  - no `OTEL_*` variable;
  - `interlock[relay]` is installed with `nemo-relay==0.10.1`;
  - Relay reports no layered `plugins.toml`;
  - `logs/` is git-ignored.
- **The tree:** clean, with the spec committed and unmodified.
- **Disk:** the traces are about 1.2 KB a call, under 1 MB in all.
- **Stop:** the stop file's path is printed at start, and the halt closes the trace (tested in stage 0).

## What happens with the result

- **H1, H2 and H3 hold on the 5090:** stage 2 (OpenVINO on the NPU and iGPU) is planned and goes to the Director the same way.
- **Any of them fails:** stop and reject, with no stage 2. The native event log and the counter are the fallback, as the design says.
