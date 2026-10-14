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

## Argon's code review, 2026-10-14, and what R&D did with it

Argon (Gemini, run by hand from [the brief](../argon-code-review-stage0.md)) reviewed the stage 0 code and the evaluation. Its verdict was "blocking issues remain": B1–B3, plus I1.

- **The evaluation:** Argon found it fair. The counter's 1 of 5 is honest, the planted cases are realistic enough for stage 0, and H4a and H4b are supported.
- **The amendments:** all seven were judged legitimate. A3 must be closed before stage 0 finishes.
- **Where the code is right,** in Argon's view: the single clock offset, OpenVINO spans kept on the calling thread, the refusal of layered configs, and the lazy import of Relay.

| # | Finding | Disposition |
|---|---|---|
| B1 | `RelaySink` has no lock, and calls arrive from worker threads (unloads; OpenVINO companions run on a background thread across a slot) | **Adopted.** One lock around every Relay call. New test: two threads × 50 calls, giving 100 whole spans with ids 1–100 |
| B2 | `_timed_call` could label a non-`ok`, non-`hang` result as `ok` | **Not a defect today:** `_bounded_call` returns only `("ok", value)` or `("hang", None)`, or re-raises. **A defensive mapping was added anyway** (`ok` → ok, `hang` → timeout, anything else → exception), so a future third value can't be called ok. New test: a worker fault counts as an error |
| B3 | A failed `RelaySink` start leaks the event loop and the sanitizers. Two live sinks could deregister each other's sanitizers | **Adopted, differently.** A start that fails releases everything it acquired. A second live sink in the process is refused, rather than given per-instance names, because Relay's plugin activation is process-wide. Test: refusal, then a failed start, then a clean start |
| I1 | A failed slot never calls `end_slot`, so calls between slots are charged to it | **Adopted.** The slot ends in the slot's `finally`, after the companion stops. The test fails without the fix |
| I2 | A companion's calls are charged to the foreground slot | **Documented, not changed.** A companion session starts and stops inside its slot, so its calls belong to that slot by construction, under their own kind (`companion`). Measured-kind counts stay clean |
| I3 | `json.dumps(body)` on every call, even with tracing off | **Adopted.** The request size is computed only for Relay. A second serialisation of a long prompt would sit inside measured time |
| I4 | `_ns` assumes a `+00:00` zone suffix | **Declined for now.** `diagnose.py` is frozen. ATOF timestamps are RFC 3339 UTC, and both producers write `+00:00`. Revisit when a producer differs |
| M1 | `/api/embed` and `/api/embeddings` classified as `other` | **Adopted** |
| M2 | A `TimeoutError` with an empty message is counted as `http_error` | **Adopted** (an `isinstance` check) |
| M3 | The cost loop has no per-slot flush | **Noted for stage 1.** The design's barrier after every slot (flush, `gc.collect`, a 250 ms rest) belongs to the stage 1 harness and must exist before stage 1 |
| Add | Widen the socket guard to `connect_ex` and `sendto` | **Adopted** |
| Eval | Q3's two options differ in their call counts, which is why the counter gets Q3 | **Agreed, and left as frozen.** A sharper Q3 would compare the same kinds in opposite order. Recorded for any future round |

**Run 3**, on the fixed code with the frozen evaluation unchanged ([run-3.json](results/run-3.json)):
- Relay 5 of 5, the native log 5 of 5, the counter 1 of 5.
- 1,130 bytes per call.
- Added time per call: a 0.028 ms median and a 0.093 ms 99th percentile. The new lock adds about 0.002 ms against run 2.
- 0.025 ms over the native log.
- The safety scan is clean.

**Then the rest of the round 1 list:**
- **The real stop file:** a new test through interlock's own operator stop found a defect the `KeyboardInterrupt` test couldn't.
  - The watcher writes the receipt, then ends the process with `os._exit`, so the tracer never closed. The end of the trace, the in-flight call and the run scope were lost.
  - **Fixed:** the halt now marks `halt` and closes the tracer before the exit, and both sinks drop calls that arrive after the close.
  - Relay keeps its scope stack in a context variable, so the run scope is popped in the context it was pushed in. That works from the watcher's thread too.
  - The test passes in both modes: the finished call is `ok`, the in-flight call is `abandoned`, and the run scope is closed.
- **Fill-card (A3):** traced. Each roster model is one slot, its unload included, and its row carries its counts and the trace pointer.
  - H1 holds: the trace holds exactly the requests the fake transport received.
  - Calls outside a model's slot, such as the card-empty check, count to the run.
- **E4b (A3, narrowed by amendment A8):** still refused.
- **A defect the fill-card tests found,** which round 1 missed: the traced transport was a plain function, so it hid the transport's own methods.
  - `OllamaAdapter.cancel()` looks for `transport.cancel` to end an in-flight request before an unload, and three fill-card tests failed (a hanging unload waited its full deadline).
  - The interleaved path has had the same wrapper since round 1.
  - **Fixed:** the wrapper is now a callable that passes every other attribute through to the transport. New test: `cancel` reaches the wrapped transport.

| # | What changed | Why |
|---|---|---|
| A8 | `--trace` stays refused for E4b, and stage 0 finishes without it | E4b's model calls go through its own injected seams (a run-owned server and an Intel lane), not through the hook points. Its block is complete, and stages 1 and 2 don't run it. Wiring it faithfully means passing the tracer through its live seams, with E4b's own step boundaries as slots. That waits until an E4b-family run needs a trace |

**Run 4,** on the final round 1 code with the frozen evaluation ([run-4.json](results/run-4.json)):
- Relay 5 of 5, the native log 5 of 5, the counter 1 of 5.
- 1,130 bytes per call.
- Added time per call: a 0.028 ms median and a 0.094 ms 99th percentile.
- 0.025 ms over the native log.
- The safety scan is clean.

**Run 5,** after the transport fix, at interlock `88b8eeb` ([run-5.json](results/run-5.json)):
- Relay 5 of 5, the native log 5 of 5, the counter 1 of 5.
- 1,130 bytes per call.
- Added time per call: a 0.026 ms median and a 0.10 ms 99th percentile.
- 0.023 ms over the native log.
- The safety scan is clean.

**The suites at `88b8eeb`:**
- With the `relay` extra: 729 passed, 6 skipped, coverage 93.3% (`calltrace.py` 100%, `relay_sink.py` 91%).
- Without it: 719 passed, 16 skipped, coverage 92.5%.
- `ruff` is clean.

**Before stage 1:**
- Argon's round 2 review of this code;
- the per-slot barrier (M3), which is stage 1 harness work;
- the Director's go, and the Publisher's grant.

## Argon round 2, 2026-10-14, and stage 0 complete

Argon (run by hand from [the round 2 brief](../argon-code-review-stage0-round2.md)) found **no blocking issues: stage 0 can finish.**
- **B2:** R&D's ruling was judged sound.
- **B3:** the single live `RelaySink` was judged better than Argon's own round 1 suggestion.
- Every round 1 finding is resolved, or accepted as deferred (I4, M3).
- The three further defects R&D found were judged properly fixed.

| # | Round 2 finding | Disposition |
|---|---|---|
| M-New-1 | `Tracer.start` can race the watcher's `Tracer.close`: a start logged with no end, or state changed after the close | **Adopted.** `Tracer` has its own closed flag, and every sink call happens under `Tracer._lock`, with the lock order tracer then sink. A call after the close is neither counted nor logged, and a second close does nothing. Tests: a late call after the close, and a close racing three calling threads, which leaves every logged start with its end |
| M-New-2 | `release()` doesn't unwrap the Ollama transport, so a reused adapter counts into the previous run's closed tracer | **Adopted.** `release()` restores `adapter.transport` from `__wrapped__`. Test: one adapter through two runs, each counting its own call |

**Run 6,** at interlock `95d6844`, with the evaluation frozen since `37db35d` ([run-6.json](results/run-6.json)):
- Relay 5 of 5, the native log 5 of 5, the counter 1 of 5.
- 1,130 bytes per call.
- Added time per call: a 0.027 ms median and a 0.089 ms 99th percentile.
- 0.024 ms over the native log.
- The safety scan is clean.

**The suites at `95d6844`:**
- With the `relay` extra: 732 passed, 6 skipped, coverage 93.3% (`calltrace.py` 100%, `relay_sink.py` 91%).
- Without it: 722 passed, 16 skipped, coverage 92.5%.
- `ruff` is clean.

**Stage 0 is complete.**
- H4a and H4b hold, and H1 and H3 hold on fakes for the interleaved and fill-card paths.
- E4b is excluded by amendment A8.
- The interlock code is on the local branch `relay-stage0` at `95d6844`, not pushed.
- Next is [the stage 1 plan](../stage1-plan.md): the stage 1 harness on fakes, then the Director's go and the Publisher's grant.
