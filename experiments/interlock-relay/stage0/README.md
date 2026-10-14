# interlock-relay, stage 0: code and tests on fakes

Stage 0 of the [interlock-relay design](../design.md) (v3.1, approved 2026-10-13). No device, GPU, NPU or model was used. The interlock code is on a local branch, `relay-stage0`, which isn't pushed yet.

## What was built (in interlock)

- **`calltrace.py`:**
  - the always-on per-kind call counter (`artifacts.call_counts`);
  - the `Tracer`, with one epoch offset per run, and open calls closed as `abandoned`;
  - `--trace off | events | relay`. `events` is the native event log at `logs/<run_id>.events.jsonl`, about 45 lines of stdlib.
  - `OTEL_*` refuses tracing.
- **`relay_sink.py`:**
  - NeMo Relay 0.10.1 through its Python API, on a private event loop, with one run scope and one span per model call;
  - length-only sanitizers, registered while the sink is open and removed when it closes;
  - a refusal if Relay would layer in another `plugins.toml`.
- **Hooks:** `OllamaAdapter.transport` (instrumented per run) and OpenVINO's `_timed_call`, which closes a hang as `timeout` with `worker_still_running: true`.
- **The run path:** `run_spec(trace=...)` covers the interleaved path. `--trace` is refused for E4b and fill-card until their hooks are wired (amendment A3).
- **`interlock[relay]` extra:** `nemo-relay==0.10.1` (it has a Windows wheel).

## What the evaluation is (here, in rnd)

- `diagnose.py`: `read_studio_trace` (one ATOF reader, with no branch on which tool wrote the file), `read_events`, and the five questions from a trace, from the native log, and from a receipt's counter.
- `cases.py`: the five planted cases and their key, the shared-reader test, the safety scan and the cost measurement.
- `fixtures/claude-code-wrapper.atof.jsonl`: the trace from the 2026-10-13 sandbox trial (Claude Code under Relay's CLI wrapper). It was trimmed inside the sandbox to structural fields: ids, timestamps, model name and status, and no content.
- **The freeze:** `diagnose.py`, `cases.py` and the key were frozen in commit `37db35d` before the first run.

## Results

Two runs, both kept: [run-1.json](results/run-1.json) and [run-2.json](results/run-2.json).

**H4a, does an ordered trace carry facts the counter loses?** It holds.

| Source | Correct of 5 |
|---|---|
| The receipt's counter | 1 (Q3 only, by elimination) |
| Native event log | 5 |
| Relay trace, run 1 | 4 (missed Q5) |
| Relay trace, run 2 | **5** |

- **Run 1's miss was our integration's defect,** not Relay's: the sink didn't carry the call's end-time fields (`worker_still_running`) into the span's end.
- **Fixed in interlock `c208fc9`, between the runs.** The readers and the key are unchanged.

**H4b, does Relay earn its place over the native log?** All the frozen criteria pass.

| Criterion | Gate | Run 2 |
|---|---|---|
| Information parity | Relay answers what the native log answers | 5 = 5 |
| Bytes per call | ≤ 2,048 | 1,130 (native 257) |
| Added client time over the counter, median | < 0.5 ms | 0.026 ms (native 0.003 ms) |
| Added client time over the counter, 99th percentile | < 2 ms | 0.084 ms |
| Relay's median minus the native log's | < 0.25 ms | 0.023 ms |
| Shared reader | One function reads both producers' ATOF into the same eight fields | Yes, with the caveat below |

- **The caveat:** the sandbox wrapper recorded no token usage (full payloads were off). So for that producer the reader returns null tokens, and token parity across producers isn't shown.
- **Cost on the other side:** Relay adds a native dependency and about 110 lines. The native log adds about 45 lines and no dependency.

**H1 and H3 on fakes** (interlock `tests/test_relay_stage0.py` and `tests/test_calltrace.py`, both trace modes):
- Every request the fake transport received is in the trace exactly once, with the right kind and status, including a timeout and an unload on its worker thread.
- No span is left unclosed.
- The canary appears zero times. No host name, user name or home path appears.
- An interrupted run leaves a closed, parsable trace, with the call in flight closed as `abandoned`.
- Tracing opens no socket except asyncio's loopback self-pipe (amendment A4).
- Receipts from a traced run pass `interlock check`.

**The test suites:** 716 passed with the `relay` extra, coverage 93% (`calltrace.py` 100%, `relay_sink.py` 91%). Without Relay (the base environment): 710 passed, 12 skipped (the Relay tests), coverage 92.7%. There, a stub sink covers the `relay` path in `calltrace.py`, and `relay_sink.py` isn't imported.

## Amendments, dated 2026-10-14

| # | What changed | Why |
|---|---|---|
| A1 | Capability rows (hang, device lost, compile refused or timed out, native binary refused) carry no `artifacts` | interlock's receipt rule: a capability row isn't a speed. Their calls stay in the ordered trace. The counter can't speak for a hung row |
| A2 | `artifacts.trace.span` names the run scope (Relay). The native log gives a file only. Each sample lists its `call_ids` | A receipt row aggregates one arm's measured calls, so there's no single "measured call" per row. `call_ids` link each sample to its calls in either log |
| A3 | `--trace` is refused for E4b and fill-card | Only the interleaved path is wired in stage 0. A trace that silently records nothing is refused instead. Wiring `urllib_exchange` and the fill-card path is needed before stage 1's fill-card triples |
| A4 | The socket guard allows only loopback, port 0 binds and loopback connects | On Windows, asyncio's event loop makes its self-pipe from a loopback socket pair. That's Python's, and it never leaves the machine. The native log opens no socket at all |
| A5 | No mark or scope sanitizer is registered | Reading real lines (run 2 and the sandbox fixture) shows Relay adds no host, user, environment or path field to marks or scopes. The H3 test scans the whole file for host, user and home |
| A6 | The shared-reader fixture is the sandbox trial's trace, trimmed | Relay's repository commits no ATOF fixture for its CLI wrapper |
| A7 | Run 1 to run 2: the sink's span end carries the call's end-time fields. A crash in the safety helper was fixed (blank lines between joined files) | Integration defects. `diagnose.py` and the key are unchanged since the freeze |

## Where this leaves the decision tree

- H4a and H4b hold, so Relay goes forward.
- Stage 0 isn't finished:
  - the E4b and fill-card hooks (A3), with their H1 and H3 tests;
  - the stop file through interlock's real stop mechanism (the test interrupts with `KeyboardInterrupt`).
- Then stage 1 on the 5090, under the Publisher's grant.
