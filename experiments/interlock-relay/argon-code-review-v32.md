# Argon code review: interlock's debug-only tracer (design amendment v3.2)

**For Argon, from R&D. 2026-10-14.** You wrote this build from excerpts; R&D applied it to the real code, with six departures listed below. Review the commit as it stands, rule on each departure, and give a verdict. Your findings are advice: R&D decides what to act on and records why.

## Where the code is

- **Repository:** `E:/AI/switchyard` (the interlock repository, on this rig).
- **Branch:** `relay-stage0`, local and unpushed. The commit to review is **`64d0801`**, "relay: debug-only tracer (design amendment v3.2)". Its parent `a43cc31` is the code stage 1 ran on.
- **Work in your own worktree, read-only.** For example `git worktree add E:/AI/interlock-argon-v32 64d0801`. Don't push, don't edit the branch, and don't touch `E:/AI/interlock-relay-s0` (R&D's worktree, which holds the stage 1 receipts untracked).
- **The diff:** `git diff a43cc31 64d0801`. Seven files: `src/interlock/calltrace.py`, `relay_sink.py`, `adapters/ollama.py`, `harness/runner.py`, `harness/receipts.py`, `tests/test_calltrace.py`, and the new `tests/test_relay_debug_only.py`.
- **The environment:** Python 3.12, `uv sync --frozen --extra relay` into a path outside the repository (`UV_PROJECT_ENVIRONMENT`), nemo-relay 0.10.1. Run the suite yourself: `pytest` (coverage is on by default, floor 90) and `ruff check src tests`. The five new tests: `pytest tests/test_relay_debug_only.py`.
- **R&D's results on this rig:** 789 passed, 6 skipped; coverage 93.29%; ruff clean; `interlock check` 509 receipts ok.

## What this is for

Stage 1 on the 5090 (`relay-s1-20261014b`) gave `stage1_holds = false`:
- H1 failed by exactly one request per step: the runner's empty-card guard sent `GET /api/ps` through the adapter before the tracer was attached.
- The companion step had three spans outside any slot: the companion's stop (an unload) ran after `end_slot()`.
- H2's client-time gate failed for real: Relay's per-call work on a CPU waking from the barrier's rest.

The Director ruled **debug-only tracing**, as design amendment v3.2. The pre-registered tree said reject; the departure is recorded as his. The stage 1 verdict stands. This commit is the build the amendment requires, before `--trace` is adopted for debugging runs. No device time is involved.

## The four requirements

Check each against the code and the tests, not against this brief.

1. **Sent = counted.** Every request the adapter sends in a run, the card guard's included, is in `logs/<run_id>.calls.json`. Test: `test_every_request_is_counted_with_the_guard_and_the_companion_stop_inside_the_window`, which counts below the hook (a patched `http.client.HTTPConnection.request`, as the stage 1 driver did) over the whole of `run_spec`.
2. **No traced row in the table.** Any row of a run with tracing on (`--trace relay` or `events`, per-arm or run-wide) is `descriptive: true` in its receipt, never reaches `table/routing.jsonl` by `write_run`, `import_receipt` or `interlock import`, and an aborted traced run adds no `gaps.md` line. The rule we chose: the whole run is descriptive, its untraced arms included. Tests: the one above, and `test_a_traced_runs_rows_never_route_and_an_untraced_run_still_does`.
3. **`--trace off` is byte-for-byte unchanged.** An untraced run's receipt and table rows are what they were at `a43cc31`. The existing suite's golden and receipt tests cover this; say if you find a path where an untraced run's output could differ. The one new thing on the untraced path is `default_transport`'s `on_send=None` check, which does nothing when no tracer asked.
4. **E4b is still refused under `--trace`.** `runner.py` ~2214, before any tracer or adapter is built. Unchanged by this commit; confirm it.

## R&D's six departures from your diffs

Rule on each: keep, or change back, with the reason.

1. **`set_emitting()` no longer switches per-arm mode on.** Your diff made `set_emitting()` set `_per_arm = True` as a side effect. Plain tracers call `set_emitting()` too (stage 1's own tests, and any run-wide caller), and that side effect would have made them go silent after the next `end_slot()`. In the commit, `set_per_arm()` is the only switch; `Tracer(per_arm=...)` sets it at construction; `end_slot()` turns emission off only when per-arm is on.
2. **The size goes straight onto the record.** Your diff carried the byte count through a `nonlocal` in `_TracedTransport.__call__` and a new `end(request_bytes=)` keyword on the tracer. In the commit, the transport's `on_send` callback sets `record.request_bytes` directly, and `Tracer.end()` is unchanged. Same result, fewer moving parts. Check the ordering: the request record Relay gets at `start` has `bytes: None`, because the size is only known when the transport serialises; the size is on the end metadata (`request_bytes`) in both sinks.
3. **One helper, `mark_debug_rows()`, at the three receipt writers, and one filter at the one way into the table.** Your diff repeated the traced-row check inside each writer's comprehensions and in `_append_table`. The commit marks rows descriptive in `write_receipt`, `write_run` and `import_receipt` through the one helper (a row is traced when it carries `artifacts.trace` or any slot with a `traced` key, or when the run's trace log is beside the receipt), and `_append_table` drops descriptive, aborted and traced rows. `import_receipt` passes only non-descriptive aborted rows to `append_aborted_runs`.
4. **No fake `nemo_relay` module.** Your test shipped a ~100-line stub of Relay's ATOF API for CI runs without the extra. The suite already gates Relay tests with the `relay` marker and `importorskip`; the new relay-mode test does the same and ran here against the real 0.10.1. A stub would have tested our guess at Relay's schema, not Relay.
5. **The test spec mirrors stage 1's `experiments/relay-s1/companion.yaml`,** with a fourth `companion` arm and pairs without `contrast`, instead of your spec, which used the alone arm as its own companion. It reuses the suite's helpers (`_bind`, `Fake`, the stage 1 test's `_run`, `MODES`, `_need`) rather than re-implementing them. The fake Ollama is an in-process `ThreadingHTTPServer` on 127.0.0.1 port 0, as you asked, and the adapter is the real `OllamaAdapter` with its real transport, reached by pointing `URL_5090` at the fake.
6. **`psutil` is set to `None` for the HTTP-driven tests** (`runner.psutil`), so the runner's two 0.2 s CPU samples per slot don't dominate a test whose server answers in microseconds. The rows then carry no CPU figures. Say if you'd rather the test paid the 8 s and kept them.

Also, a note you flagged correctly: `tests/test_calltrace.py` had one test asserting the old `json.dumps` sizing (`test_the_request_size_is_measured_only_for_relay`). It is rewritten as `test_the_request_size_comes_from_the_transport_and_is_known_by_the_end`: a reporting transport gives the exact byte count (and 0 for a GET), a bare transport gives `None`, in both sinks.

## A finding from stage 1's trace, fixed by your passthrough

In stage 1's ATOF, every `show` request record carried `bytes: 13` and every `generate` carried `bytes: 15`, whatever the body (21 and 240 bytes in the decode run). The sink built the request record as `{"bytes": n}`, and Relay's request sanitizer then re-measured that record: `len(json.dumps({"bytes": 21}))` is 13. Your `_length_only` passthrough fixes it: a `{"bytes": int | None}` record now passes through unmeasured. Stage 0's H4b size ceiling was measured on span records, not this field, so no verdict changes; the field is simply correct now. Confirm the passthrough can't let a real payload through: it accepts only a dict whose sole key is `bytes` with an int (not bool) or None.

## Questions

1. **Does the commit meet the four requirements?** Name any path where a request escapes the count, a traced row reaches the table, an untraced run's output changes, or E4b runs traced.
2. **The six departures:** keep or change back, each with a reason.
3. **The per-arm invariant.** With `set_per_arm(True)`, emission is off outside slots and `end_slot()` is the only off switch. Is there any call between `begin_slot()` and `end_slot()` that should *not* be traced, or any after `end_slot()` that should? The companion's start still runs before `begin_slot()` and is counted in `_run`, not emitted. Right, or should the start be inside the slot too?
4. **The receipts rule.** Marking a run descriptive when its trace log sits beside the receipt (`_has_trace_log`) is defence in depth for receipts written before this commit. Is there a case where a *non-traced* receipt could have a same-named trace log and be wrongly withheld from the table?
5. **The companion stop inside the slot** moves one unload (on a worker thread, up to `unload_timeout`) into the measured slot's `hook_us` and `call_ids`, in both arms. The measured call's latency and throughput are taken before it. Is anything else in the row affected?
6. **Verdict:** approve as is, approve with named changes, or reject, and what would change your mind.

## Argon's verdict (Gemini, in Antigravity on the rig, 2026-10-14) and R&D's disposition

**Approve as is.** Argon reproduced the figures in its own read-only worktree at `64d0801`: 789 passed, 6 skipped, coverage 93.30%, ruff clean, `interlock check` 509 ok. All four requirements hold, with one qualification below. All six departures: **keep**, each with its reason accepted.

**Kept from the review:**
- **Requirement 3 holds for every speed field and every untraced non-5090, non-companion run, but not byte-for-byte for the artifacts of untraced 5090 and companion runs.** The counter is always on, so moving the card guard inside the tracer's window shifts every later `call_id` by one on a 5090 run, and stopping the companion inside the slot gives an untraced paired slot three call ids instead of two, its unload's hook time, and the unload counted under the arm instead of `_run`. R&D records this as the price of requirement 1: the guard's request is a call, and a counted call takes an id. Nothing a route reads changes. Recorded here rather than hidden.
- **The stale trace-log collision (Q4):** a traced attempt refused at the card guard leaves `logs/<id>.atof.jsonl` with no receipt, and a later untraced run under that name would have been marked descriptive and withheld from the table. **Fixed in `ca4aa8e`:** `run_spec` refuses the name, as it already refuses a name with a receipt. One test.
- **Partial flushes** now stamp a traced run's rows descriptive directly (`_debug_only`, in `ca4aa8e`), not only through the receipt writer's trace-log check.
- **The calltrace docstring** said a companion starts and stops inside its slot. It starts before the slot opens; fixed in `ca4aa8e`.
- **The per-arm invariant (Q3):** the companion's start stays before `begin_slot()`, counted in `_run`, so the load is already running when the measured call goes out. Argon's caveat is noted for future specs: a `dataset.target_tokens` prompt is sized lazily on the first slot that needs that model, so a spec that put a traced arm first would trace those sizing calls inside its cold slot. ABA specs put the untraced arm first.
- **Q5:** the companion's stop now runs inside `state_lock`, before `keep_sample`; the watcher's halt uses a bounded acquire, so it cannot deadlock, and a failed unload now aborts the slot before the sample is recorded rather than after.

**Not taken:** nothing. The review raised no blocking finding.

The build round's commits on interlock `relay-stage0`: `a43cc31` (the interpreter preflight), `64d0801` (the build), `ca4aa8e` (the review's items). The branch stays local until the Publisher says otherwise.

