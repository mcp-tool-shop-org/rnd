# Code review brief for Argon, round 2: NeMo Relay inside interlock, stage 0

R&D, 2026-10-14. In round 1 you reviewed the stage 0 code at interlock commit `1065753` and found blocking issues (B1–B3 and I1). This is the code after R&D acted on your findings, along with three further defects R&D found while doing so (the watcher halt never closed the trace; the transport wrapper hid `cancel`; a Relay scope can't be popped from another thread). Review it fresh, as if seeing it for the first time, then check each round 1 finding against the new code. Your findings are advice: R&D decides what to act on and records why.

The background is the same as round 1:
- **interlock** measures local models on an RTX 5090 (Ollama) and an Intel NPU and iGPU (OpenVINO).
- **Stage 0 runs on fakes only** and decides whether NVIDIA NeMo Relay 0.10.1 can trace interlock's model calls completely and safely, and whether its ordered trace beats interlock's per-kind counter (H4a), and Relay beats a native event log (H4b).
- **H1** is complete capture. **H3** is safety: no content, host, user or home path in the trace; no non-loopback socket; a clean trace after a stop; and receipts that pass `interlock check`.

## What changed since round 1

R&D's disposition of each round 1 finding, with the reasons:

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


## Two rulings where R&D differed from your fix

Check these specifically:
- **B2:** your concrete scenario can't occur, because `_bounded_call` never returns a third value. R&D added the defensive mapping anyway.
- **B3:** instead of per-instance sanitizer names, a second live `RelaySink` in the process is refused. Relay's plugin activation is process-wide, so two concurrent sinks aren't a valid state to support. A failed start now releases everything it acquired.

Is either choice wrong?

## What to do

1. **Review the new diff** (below) for correctness, thread safety, every exit path (especially the watcher halt, which runs on the watcher thread and is followed by `os._exit`), and Relay API use.
2. **Check each round 1 finding:** resolved, partly resolved or unresolved, with one line of evidence each.
3. **Find anything the fixes introduced.**

## How to answer

- **Rank the findings:** blocking (wrong results or unsafe), important, minor.
- **For each:** the file and line, a concrete failure scenario, and the fix.
- **End with a verdict:** "blocking issues remain", or "no blocking issues; stage 0 can finish".

## Test results at the new head

At interlock `88b8eeb`:
- With the `relay` extra: 729 passed, 6 skipped, coverage 93.3% (`calltrace.py` 100%, `relay_sink.py` 91%).
- Without it: 719 passed, 16 skipped, coverage 92.5%.
- `ruff` is clean.

The frozen stage 0 evaluation, run 5 at this head (diagnose.py and the key are unchanged since round 1):

```json
{
 "answers": {
  "q1_count_growth": {
   "from_events": "grew",
   "from_receipt": "can't tell",
   "from_relay": "grew"
  },
  "q2_companion": {
   "from_events": "overlapped",
   "from_receipt": "can't tell",
   "from_relay": "overlapped"
  },
  "q3_unload_order": {
   "from_events": "unload-generate-unload",
   "from_receipt": "unload-generate-unload",
   "from_relay": "unload-generate-unload"
  },
  "q4_count_timeout": {
   "from_events": "retried and succeeded before",
   "from_receipt": "can't tell",
   "from_relay": "retried and succeeded before"
  },
  "q5_openvino_runaway": {
   "from_events": "call 2; later calls ran: yes",
   "from_receipt": "can't tell",
   "from_relay": "call 2; later calls ran: yes"
  }
 },
 "cost": {
  "added_over_counter_ms": {
   "events": {
    "median": 0.0031,
    "p99": 0.051
   },
   "relay": {
    "median": 0.0263,
    "p99": 0.1015
   }
  },
  "bytes_per_call": {
   "events": 257.4385,
   "relay": 1130.1905
  },
  "calls": 2000,
  "per_call_ms": {
   "bare": {
    "median": 0.0001,
    "p99": 0.0002
   },
   "events": {
    "median": 0.0053,
    "p99": 0.0532
   },
   "off": {
    "median": 0.0022,
    "p99": 0.0038
   },
   "relay": {
    "median": 0.0285,
    "p99": 0.1037
   }
  },
  "relay_byte_gate": true,
  "relay_time_gate": true,
  "relay_vs_native_gate": true,
  "relay_vs_native_median_ms": 0.023200000000000002
 },
 "h4": {
  "from_events_correct": 5,
  "from_receipt_correct": 1,
  "from_relay_correct": 5,
  "h4a_holds": true,
  "information_parity": true,
  "key": {
   "q1_count_growth": "grew",
   "q2_companion": "overlapped",
   "q3_unload_order": "unload-generate-unload",
   "q4_count_timeout": "retried and succeeded before",
   "q5_openvino_runaway": "call 2; later calls ran: yes"
  }
 },
 "safety": {
  "canary": 0,
  "home": false,
  "host": false,
  "user": false
 }
}
```

## The diff since round 1 (interlock 1065753 to 88b8eeb)

```diff
diff --git a/src/interlock/adapters/openvino.py b/src/interlock/adapters/openvino.py
index af6b25d..2e3c4e4 100644
--- a/src/interlock/adapters/openvino.py
+++ b/src/interlock/adapters/openvino.py
@@ -596,7 +596,8 @@ def _timed_call(fn, timeout_s: float, *, kind: str = "generate", model: str | No
     status = "exception"
     try:
         result = _bounded_call(fn, timeout_s)
-        status = "timeout" if result[0] == "hang" else "ok"
+        # _bounded_call returns ("ok", value) or ("hang", None), or re-raises. Anything else is not called ok.
+        status = {"ok": "ok", "hang": "timeout"}.get(result[0], "exception")
         if status == "timeout":
             record.extra["worker_still_running"] = True
         return result
diff --git a/src/interlock/calltrace.py b/src/interlock/calltrace.py
index 06a45bf..4d8350b 100644
--- a/src/interlock/calltrace.py
+++ b/src/interlock/calltrace.py
@@ -12,7 +12,10 @@ That is a summary, not a log.
   (``logs/<run_id>.atof.jsonl``). Relay is imported only on this path.
 
 Calls are classified from the request itself, so counts and unloads made on
-worker threads need no context. Every timestamp comes from one clock: an epoch
+worker threads need no context. A call is attributed to the slot whose window
+it starts in, whatever its thread: a companion session is started and stopped
+inside its slot, so its calls belong to that slot by construction, under their
+own kind (``companion``). Every timestamp comes from one clock: an epoch
 offset taken once when the run opens, plus ``perf_counter_ns``. Prompts and
 responses are never recorded, only their byte lengths.
 """
@@ -47,6 +50,8 @@ def classify(method: str, url: str, body: dict | None) -> str:
         return "ps"
     if path.endswith("/api/show"):
         return "show"
+    if path.endswith(("/api/embed", "/api/embeddings")):
+        return "embed"
     if path.endswith("/api/generate") and isinstance(body, dict):
         if body.get("companion") == "start":
             return "companion"
@@ -94,6 +99,8 @@ class _EventSink:
         self.path = path
         self._file = path.open("w", encoding="utf-8")
         self._lock = threading.Lock()
+        # The watcher may close the log while a worker or the run thread still calls in; later calls are dropped.
+        self._closed = False
 
     def start(self, record: CallRecord) -> None:
         return None
@@ -116,20 +123,25 @@ class _EventSink:
         }
         text = json.dumps(line, sort_keys=True) + "\n"
         with self._lock:
-            self._file.write(text)
+            if not self._closed:
+                self._file.write(text)
 
     def mark(self, name: str, t_ns: int, data: dict) -> None:
         with self._lock:
-            self._file.write(json.dumps({"mark": name, "t_ns": t_ns, **data}, sort_keys=True) + "\n")
+            if not self._closed:
+                self._file.write(json.dumps({"mark": name, "t_ns": t_ns, **data}, sort_keys=True) + "\n")
 
     def flush(self) -> None:
         with self._lock:
-            self._file.flush()
+            if not self._closed:
+                self._file.flush()
 
     def close(self, end_ns: int | None = None) -> None:
         with self._lock:
-            self._file.flush()
-            self._file.close()
+            if not self._closed:
+                self._closed = True
+                self._file.flush()
+                self._file.close()
 
 
 class Tracer:
@@ -233,7 +245,9 @@ class Tracer:
 
     # -- calls ------------------------------------------------------------------
 
-    def start(self, kind: str, endpoint: str, *, model: str | None, device: str | None, request_bytes: int = 0) -> CallRecord:
+    def start(
+        self, kind: str, endpoint: str, *, model: str | None, device: str | None, request_bytes: int = 0
+    ) -> CallRecord:
         record = CallRecord(
             call_id=next(self._ids),
             kind=kind,
@@ -265,7 +279,8 @@ class Tracer:
     def _finish(self, record: CallRecord) -> None:
         arm = record.extra.get("arm") or "_run"
         with self._lock:
-            entry = self._counts.setdefault(arm, {}).setdefault(record.kind, {"n": 0, "ms": 0.0, "errors": 0, "timeouts": 0})
+            fresh = {"n": 0, "ms": 0.0, "errors": 0, "timeouts": 0}
+            entry = self._counts.setdefault(arm, {}).setdefault(record.kind, fresh)
             entry["n"] += 1
             entry["ms"] = round(entry["ms"] + (record.ms or 0.0), 3)
             if record.status == "timeout":
@@ -295,27 +310,43 @@ class Tracer:
         return out
 
 
-def traced_transport(transport, tracer: Tracer, *, device: str | None = None):
-    """Wrap an Ollama transport: every request is classified, timed and counted on the calling thread."""
+class _TracedTransport:
+    """An Ollama transport, classified, timed and counted on the calling thread.
+
+    Every other attribute goes to the wrapped transport, so methods the adapter looks for on its transport (such
+    as ``cancel``, which ends an in-flight request before an unload) still reach it."""
+
+    def __init__(self, transport, tracer: Tracer, device: str | None):
+        self.__wrapped__ = transport
+        self._tracer = tracer
+        self._device = device
+
+    def __getattr__(self, name):
+        return getattr(self.__wrapped__, name)
 
-    def wrapped(method: str, url: str, body: dict | None, *args, **kwargs):
+    def __call__(self, method: str, url: str, body: dict | None, *args, **kwargs):
+        tracer = self._tracer
         kind = classify(method, url, body)
         model = body.get("model") if isinstance(body, dict) else None
-        size = len(json.dumps(body)) if body is not None else 0
-        record = tracer.start(kind, urlsplit(url).path, model=model, device=device, request_bytes=size)
+        # Only Relay's request record uses the size. Serialising a long prompt again costs measured time.
+        size = len(json.dumps(body)) if body is not None and tracer.mode == "relay" else 0
+        record = tracer.start(kind, urlsplit(url).path, model=model, device=self._device, request_bytes=size)
         status, payload = "exception", None
         try:
-            payload = transport(method, url, body, *args, **kwargs)
+            payload = self.__wrapped__(method, url, body, *args, **kwargs)
             status = "ok"
             return payload
         except Exception as exc:
-            status = "timeout" if "timed out" in str(exc) else "http_error"
+            status = "timeout" if isinstance(exc, TimeoutError) or "timed out" in str(exc).lower() else "http_error"
             raise
         finally:
             tracer.end(record, status, payload)
 
-    wrapped.__wrapped__ = transport
-    return wrapped
+
+def traced_transport(transport, tracer: Tracer, *, device: str | None = None):
+    """Wrap an Ollama transport: every request is classified, timed and counted on the calling thread."""
+
+    return _TracedTransport(transport, tracer, device)
 
 
 def instrument(adapters: dict, tracer: Tracer) -> None:
diff --git a/src/interlock/cli.py b/src/interlock/cli.py
index fefad22..9953971 100644
--- a/src/interlock/cli.py
+++ b/src/interlock/cli.py
@@ -97,7 +97,10 @@ def main(argv: list[str] | None = None) -> int:
         "--trace",
         choices=("off", "events", "relay"),
         default="off",
-        help="log every model call in order under logs/: events (stdlib) or relay (NeMo Relay ATOF, needs interlock[relay])",
+        help=(
+            "log every model call in order under logs/: events (stdlib) or relay "
+            "(NeMo Relay ATOF, needs interlock[relay])"
+        ),
     )
     run.add_argument(
         "--pairs",
diff --git a/src/interlock/harness/fill.py b/src/interlock/harness/fill.py
index 41d0ebf..74910b0 100644
--- a/src/interlock/harness/fill.py
+++ b/src/interlock/harness/fill.py
@@ -1473,9 +1473,13 @@ def run_fill_card(
     notes: str = "",
     supervisor=None,
     models: list[str] | None = None,
+    tracer=None,
 ) -> list[dict]:
     """Measure each roster model. Unload at the end of the model and on any exit.
 
+    ``tracer`` (interlock.calltrace) counts and, when tracing, logs every model call. Each roster model is one slot,
+    its unload included, and its row carries the counts.
+
     ``models`` is a subset of the spec roster, in spec order. None measures
     every model. The subset is written on each row.
     """
@@ -1535,6 +1539,8 @@ def run_fill_card(
             repair: list[tuple[str, str]] = []
             if supervisor is not None:
                 supervisor.begin_measurement()
+            if tracer is not None:
+                tracer.begin_slot(arm=entry["model"], index=f"fill:{entry['model']}")
             try:
                 row = _measure_model(
                     spec,
@@ -1553,6 +1559,8 @@ def run_fill_card(
                 extra = _unload(adapter, entry["model"])
                 if supervisor is not None:
                     supervisor.end_measurement()
+                if tracer is not None:
+                    tracer.end_slot()
             if models is not None:
                 row.setdefault("settings", {})["models"] = [item["model"] for item in roster]
                 validate_row(row)
@@ -1601,6 +1609,14 @@ def run_fill_card(
         try:
             if rows:
                 _stamp_restarts(rows, marker)
+                if tracer is not None:
+                    from interlock.receipt import CAPABILITY_OUTCOMES
+
+                    for row in rows:
+                        # The slot is named by the roster tag, which a row keeps as model.repo_or_tag.
+                        tag = (row.get("model") or {}).get("repo_or_tag")
+                        if row.get("outcome") not in CAPABILITY_OUTCOMES and tag:
+                            row.setdefault("artifacts", {}).update(tracer.artifacts(tag))
                 write_receipt(root, run_id, rows)
         finally:
             if marker.entered:
diff --git a/src/interlock/harness/runner.py b/src/interlock/harness/runner.py
index 876bd8f..6416902 100644
--- a/src/interlock/harness/runner.py
+++ b/src/interlock/harness/runner.py
@@ -696,6 +696,14 @@ def run_interleaved(
         finally:
             if held:
                 state_lock.release()
+            # The watcher exits the process next (os._exit), so the run's tracer never reaches its own close.
+            # Close it here: the call in flight is closed as abandoned and the trace is flushed whole.
+            if tracer is not None:
+                try:
+                    tracer.mark("halt", error=error, operator=operator)
+                    tracer.close()
+                except Exception as exc:  # the process must still end
+                    print(f"interlock: the trace could not be closed: {exc}", file=sys.stderr)
 
     def _on_compile_timeout(info: dict) -> None:
         arm = arms[current.step_id] if current is not None else None
@@ -1081,6 +1089,10 @@ def run_interleaved(
                             cache_dirs.get(companion["id"]),
                             prompt_cache,
                         )
+                    # A failed or refused slot still ends here, so recovery calls between slots are not
+                    # attributed to it (Argon I1). The success path has already taken its call ids.
+                    if tracer is not None and slot_calls is None:
+                        tracer.end_slot()
                 if pending is not None:
                     _resume_after_repair(slot, block_id, arm, pending[0], pending[1])
         finally:
@@ -2133,10 +2145,12 @@ def run_spec(
         if spec.get("procedure") != "fill-card":
             raise RunnerError("--models is for a fill-card spec")
         _chosen, recorded_models = resolve_models(spec, models)
-    if trace != "off" and (spec.get("id") == "E4b" or spec.get("procedure") == "fill-card"):
-        # Stage 0 of the interlock-relay design wires the interleaved path first. A trace that would silently
-        # record nothing is refused instead.
-        raise RunnerError(f"REFUSED: --trace {trace} is wired for interleaved specs only; run this spec with --trace off")
+    if trace != "off" and spec.get("id") == "E4b":
+        # E4b's model calls go through its own injected seams, not the hook points. A trace that would silently
+        # record nothing is refused instead (interlock-relay amendment A3).
+        raise RunnerError(
+            f"REFUSED: --trace {trace} is not wired for E4b; run this spec with --trace off"
+        )
     if spec.get("id") == "E4b":
         from interlock.harness.e4b import run_from_cli
 
@@ -2193,22 +2207,31 @@ def run_spec(
                 chosen = quiet_fill_seams()
             else:
                 chosen = real_fill_seams(adapters["ollama"])
-            return run_fill_card(
-                spec,
-                adapters=adapters,
-                seams=chosen,
-                grant=grant,
-                root=root,
-                spec_rel=spec_rel,
-                run_id=name,
-                date=stamp,
-                heartbeat=heartbeat_path(heartbeat),
-                wall=wall,
-                marker=marker,
-                notes=notes,
-                supervisor=supervisor,
-                models=recorded_models,
-            )
+            from interlock.calltrace import Tracer, instrument, release
+
+            tracer = Tracer(root=root, run_id=name, mode=trace)
+            with tracer:
+                instrument(adapters, tracer)
+                try:
+                    return run_fill_card(
+                        spec,
+                        adapters=adapters,
+                        seams=chosen,
+                        grant=grant,
+                        root=root,
+                        spec_rel=spec_rel,
+                        run_id=name,
+                        date=stamp,
+                        heartbeat=heartbeat_path(heartbeat),
+                        wall=wall,
+                        marker=marker,
+                        notes=notes,
+                        supervisor=supervisor,
+                        models=recorded_models,
+                        tracer=tracer,
+                    )
+                finally:
+                    release(adapters)
         if spec["procedure"] != "interleaved":
             raise GuardError(
                 f"REFUSED: a {spec['procedure']!r} spec has no run path; this command runs interleaved specs"
diff --git a/src/interlock/relay_sink.py b/src/interlock/relay_sink.py
index 2443685..3ed1200 100644
--- a/src/interlock/relay_sink.py
+++ b/src/interlock/relay_sink.py
@@ -14,15 +14,17 @@ The sink refuses to start if Relay would layer in any configuration file
 from __future__ import annotations
 
 import asyncio
+import contextvars
 import json
-from datetime import datetime, timezone
+import threading
+from datetime import UTC, datetime
 from pathlib import Path
 
 from interlock.calltrace import CallRecord, TraceError
 
 
 def _when(t_ns: int) -> datetime:
-    return datetime.fromtimestamp(t_ns / 1e9, tz=timezone.utc)
+    return datetime.fromtimestamp(t_ns / 1e9, tz=UTC)
 
 
 def _length_only(payload, _context=None) -> dict:
@@ -40,15 +42,25 @@ def _request_length_only(request, _context=None):
 
 _REQUEST = "interlock-length-only-request"
 _RESPONSE = "interlock-length-only-response"
+# Relay's plugin activation and its sanitizers are process-wide, so one sink is live at a time.
+_LIVE = threading.Lock()
 
 
 class RelaySink:
+    """One run's Relay trace. Calls arrive from the run thread and from worker threads (unloads, OpenVINO
+    companions), so every Relay call goes through one lock (Argon B1)."""
+
     def __init__(self, logs: Path, filename: str, start_ns: int, run_id: str):
         import nemo_relay
         from nemo_relay import guardrails, plugin, scope
 
         self._relay = nemo_relay
         self._scope = scope
+        self._guardrails = guardrails
+        self._lock = threading.Lock()
+        self._spans: dict[int, object] = {}
+        # The watcher may close the sink while a thread still calls in; later calls are dropped.
+        self._closed = False
         config = {
             "version": 1,
             "components": [{
@@ -66,53 +78,93 @@ class RelaySink:
         report = plugin.validate(config)
         if report.get("config_paths"):
             raise TraceError("REFUSED: Relay would layer in other plugins.toml files; remove them before tracing")
-        self._loop = asyncio.new_event_loop()
-        self._activation = self._loop.run_until_complete(plugin.initialize(config))
-        self._guardrails = guardrails
-        guardrails.register_llm_sanitize_request(_REQUEST, 0, _request_length_only)
-        guardrails.register_llm_sanitize_response(_RESPONSE, 0, _length_only)
-        self._run = scope.push(f"interlock-run {run_id}", scope.ScopeType.Agent, timestamp=_when(start_ns))
-        self.scope_id = self._run.uuid
-        self._spans: dict[int, object] = {}
+        if not _LIVE.acquire(blocking=False):
+            raise TraceError("REFUSED: a Relay trace is already open in this process; one run traces at a time")
+        # Anything acquired below is released if a later step fails (Argon B3).
+        self._loop = None
+        self._activation = None
+        registered: list[str] = []
+        try:
+            self._loop = asyncio.new_event_loop()
+            self._activation = self._loop.run_until_complete(plugin.initialize(config))
+            guardrails.register_llm_sanitize_request(_REQUEST, 0, _request_length_only)
+            registered.append("request")
+            guardrails.register_llm_sanitize_response(_RESPONSE, 0, _length_only)
+            registered.append("response")
+            self._run = scope.push(f"interlock-run {run_id}", scope.ScopeType.Agent, timestamp=_when(start_ns))
+            self.scope_id = self._run.uuid
+            # Relay keeps its scope stack in a context variable. The watcher closes the trace from its own
+            # thread on a halt, so the pop runs in the context the scope was pushed in.
+            self._context = contextvars.copy_context()
+        except BaseException:
+            self._release(registered)
+            raise
+
+    def _release(self, registered=("request", "response")) -> None:
+        try:
+            if "request" in registered:
+                self._guardrails.deregister_llm_sanitize_request(_REQUEST)
+            if "response" in registered:
+                self._guardrails.deregister_llm_sanitize_response(_RESPONSE)
+            if self._activation is not None:
+                self._loop.run_until_complete(self._activation.close())
+        finally:
+            if self._loop is not None:
+                self._loop.close()
+            _LIVE.release()
 
     def start(self, record: CallRecord) -> None:
         request = self._relay.LLMRequest({}, {"bytes": record.request_bytes})
-        handle = self._relay.llm.call(
-            "ollama" if record.endpoint.startswith("/api/") else "openvino",
-            request,
-            handle=self._run,
-            model_name=record.model,
-            metadata={"call_id": record.call_id, "kind": record.kind, "endpoint": record.endpoint,
-                      "device": record.device, "thread": record.thread, **record.extra},
-            timestamp=_when(record.start_ns),
-        )
-        self._spans[record.call_id] = handle
+        with self._lock:
+            if self._closed:
+                return
+            handle = self._relay.llm.call(
+                "ollama" if record.endpoint.startswith("/api/") else "openvino",
+                request,
+                handle=self._run,
+                model_name=record.model,
+                metadata={"call_id": record.call_id, "kind": record.kind, "endpoint": record.endpoint,
+                          "device": record.device, "thread": record.thread, **record.extra},
+                timestamp=_when(record.start_ns),
+            )
+            self._spans[record.call_id] = handle
 
     def end(self, record: CallRecord) -> None:
-        handle = self._spans.pop(record.call_id, None)
-        if handle is None:
-            return
-        self._relay.llm.call_end(
-            handle,
-            {"status": record.status},
-            # extra carries what is only known at the end, such as an OpenVINO timeout's worker_still_running.
-            metadata={**record.extra, "call_id": record.call_id, "status": record.status, "ms": record.ms,
-                      "prompt_tokens": record.prompt_tokens, "completion_tokens": record.completion_tokens},
-            timestamp=_when(record.end_ns),
-        )
+        with self._lock:
+            handle = self._spans.pop(record.call_id, None)
+            if handle is None or self._closed:
+                return
+            self._relay.llm.call_end(
+                handle,
+                {"status": record.status},
+                # extra carries what is only known at the end, such as an OpenVINO timeout's worker_still_running.
+                metadata={**record.extra, "call_id": record.call_id, "status": record.status, "ms": record.ms,
+                          "prompt_tokens": record.prompt_tokens, "completion_tokens": record.completion_tokens},
+                timestamp=_when(record.end_ns),
+            )
 
     def mark(self, name: str, t_ns: int, data: dict) -> None:
-        self._scope.event(name, handle=self._run, data=data, timestamp=_when(t_ns))
+        with self._lock:
+            if self._closed:
+                return
+            self._scope.event(name, handle=self._run, data=data, timestamp=_when(t_ns))
 
     def flush(self) -> None:
-        self._relay.subscribers.flush()
+        with self._lock:
+            if not self._closed:
+                self._relay.subscribers.flush()
 
     def close(self, end_ns: int | None = None) -> None:
-        try:
-            self._scope.pop(self._run, timestamp=_when(end_ns) if end_ns is not None else None)
-        finally:
-            self._relay.subscribers.flush()
-            self._guardrails.deregister_llm_sanitize_request(_REQUEST)
-            self._guardrails.deregister_llm_sanitize_response(_RESPONSE)
-            self._loop.run_until_complete(self._activation.close())
-            self._loop.close()
+        with self._lock:
+            if self._closed:
+                return
+            self._closed = True
+            try:
+                self._context.run(
+                    self._scope.pop, self._run, timestamp=_when(end_ns) if end_ns is not None else None
+                )
+            finally:
+                try:
+                    self._relay.subscribers.flush()
+                finally:
+                    self._release()
```

## The test changes since round 1

```diff
diff --git a/tests/test_calltrace.py b/tests/test_calltrace.py
index 1898ca9..3083277 100644
--- a/tests/test_calltrace.py
+++ b/tests/test_calltrace.py
@@ -8,8 +8,8 @@ from pathlib import Path
 import pytest
 
 from interlock.calltrace import (
-    Tracer,
     TraceError,
+    Tracer,
     classify,
     instrument,
     release,
@@ -29,6 +29,8 @@ URL = "http://127.0.0.1:11434"
         ("/api/generate", {"model": "m", "keep_alive": 0, "prompt": ""}, "unload"),
         ("/api/generate", {"model": "m", "raw": True, "prompt": "x"}, "count"),
         ("/api/generate", {"model": "m", "companion": "start"}, "companion"),
+        ("/api/embed", {"model": "m", "input": "x"}, "embed"),
+        ("/api/embeddings", {"model": "m", "prompt": "x"}, "embed"),
         ("/api/generate", None, "other"),
         ("/api/version", None, "other"),
     ],
@@ -64,7 +66,8 @@ def test_the_events_log_writes_one_parsable_line_per_call_and_marks(tmp_path: Pa
         tracer.end_slot()
         tracer.mark("stop_file", reason="test")
         tracer.flush()
-    lines = [json.loads(line) for line in (tmp_path / "logs" / "r.events.jsonl").read_text(encoding="utf-8").splitlines()]
+    text = (tmp_path / "logs" / "r.events.jsonl").read_text(encoding="utf-8")
+    lines = [json.loads(line) for line in text.splitlines()]
     calls = [line for line in lines if "call_id" in line]
     assert [c["kind"] for c in calls] == ["count", "generate"]
     assert calls[0]["status"] == "timeout"
@@ -183,3 +186,83 @@ def test_instrument_wraps_ollama_once_and_sets_the_openvino_tracer(tmp_path: Pat
     assert openvino._TRACER is tracer
     release(adapters)
     assert openvino._TRACER is None
+
+
+def test_a_timeout_with_no_message_is_still_a_timeout(tmp_path: Path):
+    def transport(method, url, body, **kwargs):
+        raise TimeoutError()
+
+    tracer = Tracer(root=tmp_path, run_id="r")
+    with tracer:
+        with pytest.raises(TimeoutError):
+            traced_transport(transport, tracer)("POST", URL + "/api/tags", None)
+    assert tracer.counts_for("_run")["tags"]["timeouts"] == 1
+
+
+def test_the_request_size_is_measured_only_for_relay(tmp_path: Path):
+    seen = []
+
+    class Sink:
+        scope_id = None
+
+        def __init__(self, *args):
+            pass
+
+        def start(self, record):
+            seen.append(record.request_bytes)
+
+        def end(self, record):
+            pass
+
+        def mark(self, *args):
+            pass
+
+        def flush(self):
+            pass
+
+        def close(self, end_ns=None):
+            pass
+
+    body = {"model": "m", "prompt": "x" * 100}
+    for mode in ("events", "relay"):
+        tracer = Tracer(root=tmp_path, run_id=mode, mode=mode, relay_factory=Sink)
+        with tracer:
+            traced_transport(lambda *a, **k: {}, tracer)("POST", URL + "/api/generate", body)
+    assert seen == [len(json.dumps(body))]
+
+
+def test_an_openvino_worker_fault_is_an_exception_not_ok(tmp_path: Path):
+    from interlock.adapters import openvino
+
+    def boom():
+        raise RuntimeError("device said no")
+
+    tracer = Tracer(root=tmp_path, run_id="ov")
+    openvino.set_tracer(tracer)
+    try:
+        with tracer:
+            with pytest.raises(RuntimeError):
+                openvino._timed_call(boom, 1.0, kind="embed", model="m", device="NPU")
+            status, _ = openvino._timed_call(lambda: 1, 1.0, kind="embed", model="m", device="NPU")
+            assert status == "ok"
+    finally:
+        openvino.set_tracer(None)
+    counts = tracer.counts_for("_run")["embed"]
+    assert (counts["n"], counts["errors"], counts["timeouts"]) == (2, 1, 0)
+
+
+def test_the_traced_transport_keeps_the_transports_own_methods(tmp_path: Path):
+    class Transport:
+        cancelled = 0
+
+        def __call__(self, method, url, body=None, **kwargs):
+            return {}
+
+        def cancel(self):
+            self.cancelled += 1
+
+    inner = Transport()
+    wrapped = traced_transport(inner, Tracer(root=tmp_path, run_id="r"))
+    wrapped.cancel()
+    assert inner.cancelled == 1
+    assert not hasattr(traced_transport(lambda *a: {}, Tracer(root=tmp_path, run_id="s")), "cancel")
diff --git a/tests/test_relay_stage0.py b/tests/test_relay_stage0.py
index f4ccefc..0a4449f 100644
--- a/tests/test_relay_stage0.py
+++ b/tests/test_relay_stage0.py
@@ -14,7 +14,7 @@ from pathlib import Path
 import pytest
 
 from interlock.adapters.ollama import OllamaAdapter
-from interlock.calltrace import Tracer, TraceError, instrument, release
+from interlock.calltrace import TraceError, Tracer, instrument, release
 
 CANARY = "AMU_CANARY_PROMPT_7c1e"
 MODES = ["events", pytest.param("relay", marks=pytest.mark.relay)]
@@ -62,7 +62,7 @@ def test_h1_every_request_the_fake_received_is_in_the_trace_once(tmp_path: Path,
     with tracer:
         instrument({"ollama": adapter}, tracer)
         tracer.begin_slot(arm="B", index="measure:0:B")
-        with pytest.raises(Exception):
+        with pytest.raises(TimeoutError):
             adapter.count_tokens("qwen3:8b", CANARY)
         assert adapter.count_tokens("qwen3:8b", CANARY) == 9
         adapter.transport("POST", "http://127.0.0.1:11434/api/generate", {"model": "qwen3:8b", "prompt": CANARY})
@@ -138,6 +138,19 @@ def test_h3_tracing_opens_no_socket(tmp_path: Path, mode, monkeypatch):
                 raise AssertionError(f"bind to {address}")
             return super().bind(address)
 
+        def connect_ex(self, address):
+            opened.append(("connect_ex", address))
+            if not loopback(address):
+                raise AssertionError(f"connect_ex to {address}")
+            return super().connect_ex(address)
+
+        def sendto(self, data, *args):
+            address = args[-1]
+            opened.append(("sendto", address))
+            if not loopback(address):
+                raise AssertionError(f"sendto {address}")
+            return super().sendto(data, *args)
+
     monkeypatch.setattr(socket, "socket", Guard)
     tracer = Tracer(root=tmp_path, run_id="net", mode=mode)
     with tracer:
@@ -192,9 +205,153 @@ def test_a_traced_run_writes_receipts_check_accepts(tmp_path: Path, mode):
 
 def test_trace_is_refused_where_it_is_not_wired(tmp_path: Path):
     from interlock.harness.runner import RunnerError, run_spec
-    from tests.test_run_path import E5
 
-    # The committed fill-card spec: the refusal comes before any adapter, card probe or run marker.
-    with pytest.raises(RunnerError, match="interleaved specs only"):
-        run_spec(E5, root=tmp_path, adapters={}, date="2026-10-10", trace="events")
+    # E4b's calls go through its own seams. The refusal comes before any adapter, seam or run marker.
+    spec = Path(__file__).resolve().parents[1] / "experiments" / "e4b" / "spec.yaml"
+    with pytest.raises(RunnerError, match="not wired for E4b"):
+        run_spec(spec, root=tmp_path, adapters={}, date="2026-10-10", trace="events")
     assert not (tmp_path / "receipts").exists()
+
+
+@pytest.mark.parametrize("mode", MODES)
+def test_h1_the_fill_card_path_traces_every_call_its_transport_received(tmp_path: Path, mode):
+    _need(mode)
+    from interlock.adapters.ollama import OllamaAdapter
+    from interlock.harness.runner import run_spec
+    from interlock.receipt import check_tree, load_jsonl
+    from tests.test_fill_card_live import _bind, _fresh, _model, _seams, _spec, _Transport
+
+    transport = _Transport(None)
+    seams = _seams(transport)
+    repo = tmp_path / "repo"
+    spec_path = _bind(repo, _spec([_model()], max_ctx=8192, confirm_num_predict=1))
+    rows = run_spec(spec_path, root=repo, grant="g", adapters={"ollama": OllamaAdapter(transport=transport)},
+                    heartbeat=_fresh(tmp_path), date="2026-10-11", run_id="fill-1", seams=seams, trace=mode)
+    assert rows and check_tree(repo) == []
+    calls = _trace_calls(repo, mode, "fill-1")
+    assert len(calls) == len(transport.calls) > 0
+    row = load_jsonl(repo / "receipts" / "fill-1.jsonl")[0]
+    counts = row["artifacts"]["call_counts"]
+    # The row counts its own slot. Run-level calls, such as the card-empty check before the model, are not its.
+    in_slot = [c for c in calls if (c.get("slot") or "").startswith("fill:")]
+    assert sum(v["n"] for v in counts.values()) == len(in_slot) > 0
+    assert all(c["kind"] in ("ps", "tags") for c in calls if c not in in_slot)
+    assert row["artifacts"]["trace"]["file"].startswith("logs/fill-1.")
+
+
+
+@pytest.mark.relay
+def test_relay_keeps_every_span_whole_under_two_threads(tmp_path: Path):
+    pytest.importorskip("nemo_relay")
+    import threading
+
+    tracer = Tracer(root=tmp_path, run_id="threads", mode="relay")
+
+    def loop(kind):
+        for _ in range(50):
+            record = tracer.start(kind, "/api/generate", model="m", device="5090")
+            tracer.end(record, "ok")
+
+    with tracer:
+        tracer.begin_slot(arm="A", index="measure:0:A")
+        workers = [threading.Thread(target=loop, args=(k,)) for k in ("generate", "companion")]
+        for w in workers:
+            w.start()
+        for w in workers:
+            w.join()
+        tracer.end_slot()
+    text = (tmp_path / "logs" / "threads.atof.jsonl").read_text(encoding="utf-8")
+    events = [json.loads(x) for x in text.splitlines()]
+    llm = [e for e in events if e.get("category") == "llm"]
+    starts = {e["uuid"] for e in llm if e["scope_category"] == "start"}
+    ends = {e["uuid"] for e in llm if e["scope_category"] == "end"}
+    assert len(starts) == len(ends) == 100 and starts == ends
+    ids = {e["metadata"]["call_id"] for e in llm if e["scope_category"] == "end"}
+    assert ids == set(range(1, 101))
+
+
+@pytest.mark.relay
+def test_a_second_live_relay_sink_is_refused_and_a_failed_start_releases(tmp_path: Path, monkeypatch):
+    pytest.importorskip("nemo_relay")
+    from nemo_relay import scope
+
+    from interlock.relay_sink import RelaySink
+
+    first = RelaySink(tmp_path, "a.atof.jsonl", 0, "a")
+    try:
+        with pytest.raises(TraceError, match="already open"):
+            RelaySink(tmp_path, "b.atof.jsonl", 0, "b")
+    finally:
+        first.close()
+
+    def broken(*args, **kwargs):
+        raise RuntimeError("push failed")
+
+    with monkeypatch.context() as patch:
+        patch.setattr(scope, "push", broken)
+        with pytest.raises(RuntimeError, match="push failed"):
+            RelaySink(tmp_path, "c.atof.jsonl", 0, "c")
+    # Nothing leaked: the lock, the sanitizers and the activation were all released.
+    RelaySink(tmp_path, "d.atof.jsonl", 0, "d").close()
+
+
+def test_a_failed_slot_still_ends_its_tracer_slot(tmp_path: Path, monkeypatch):
+    from interlock.adapters.base import AdapterError
+    from interlock.calltrace import Tracer as T
+    from interlock.harness.runner import RunnerError, run_spec
+    from tests.test_run_path import Fake, _arm, _bind, _result, _spec
+
+    begun, ended = [], []
+    real_begin, real_end = T.begin_slot, T.end_slot
+    monkeypatch.setattr(T, "begin_slot", lambda self, **s: (begun.append(s), real_begin(self, **s))[1])
+    monkeypatch.setattr(T, "end_slot", lambda self: (ended.append(1), real_end(self))[1])
+    repo = tmp_path / "repo"
+    spec_path = _bind(repo, _spec([_arm("A", "CPU"), _arm("B", "CPU")]))
+    adapter = Fake({"A": [_result(10), _result(11), _result(12)], "B": [AdapterError("hang: no result within 60 s")]})
+    with pytest.raises(RunnerError, match="hang"):
+        run_spec(spec_path, root=repo, adapters={"fake": adapter}, date="2026-10-10", run_id="slot-1", trace="events")
+    assert begun and len(ended) == len(begun)
+
+
+@pytest.mark.parametrize("mode", MODES)
+def test_h3_the_real_stop_file_leaves_a_closed_parsable_trace(tmp_path: Path, mode):
+    """interlock's operator stop: the watcher writes the receipt, then ends the process with os._exit. The halt
+    must close the trace first, with the call in flight closed as abandoned."""
+
+    _need(mode)
+    import threading
+
+    from interlock.adapters.base import AdapterError
+    from tests.test_rest_removed_stops import StopAdapter
+    from tests.test_run_guard import Clock, Exits, _hooks, _invoke, _spec
+
+    repo, spec_path = _spec(tmp_path)
+    clock, gate = Clock(), threading.Event()
+    exits = Exits(repo / "receipts" / "run-1.jsonl", gate)
+    hooks, _ram = _hooks(clock, exits)
+    tracer = Tracer(root=repo, run_id="run-1", mode=mode)
+
+    class Traced(StopAdapter):
+        def run(self, request):
+            record = tracer.start("generate", "/api/generate", model="m", device=request.step_id)
+            if request.step_id != "npu":
+                tracer.end(record, "ok")
+            return super().run(request)  # the npu call stays in flight until the watcher ends the run
+
+    adapter = Traced(clock, gate, compile_spent_s=1, in_compile=False, stop_file=repo / "receipts" / "run-1.stop",
+                     text="stop for the test")
+    with tracer:
+        with pytest.raises(AdapterError, match="released"):
+            _invoke(repo, spec_path, adapter, hooks, tracer=tracer)
+    assert exits.codes == [77]
+    text = next((repo / "logs").glob("run-1.*")).read_text(encoding="utf-8")
+    lines = [json.loads(x) for x in text.splitlines()]
+    if mode == "events":
+        calls = [x for x in lines if "call_id" in x]
+        assert [c["status"] for c in calls] == ["ok", "abandoned"]
+        assert any(x.get("mark") == "halt" for x in lines)
+    else:
+        llm = [x for x in lines if x.get("category") == "llm"]
+        assert sum(x["scope_category"] == "start" for x in llm) == sum(x["scope_category"] == "end" for x in llm) == 2
+        assert [x["scope_category"] for x in lines if x.get("category") == "agent"] == ["start", "end"]
+        assert any(x.get("kind") == "mark" and x.get("name") == "halt" for x in lines)
```

## The two trace modules in full at 88b8eeb

### src/interlock/calltrace.py

```python
"""Every model call interlock makes, counted per kind and optionally logged in order.

The counter is always on. Each receipt row carries ``artifacts.call_counts``:
per call kind, how many calls, their client-side time, errors and timeouts.
That is a summary, not a log.

``--trace`` adds an ordered log of the same calls under ``logs/``:

- ``events``: one JSON line per finished call, written by this module
  (``logs/<run_id>.events.jsonl``);
- ``relay``: NVIDIA NeMo Relay's ATOF events, through its Python API
  (``logs/<run_id>.atof.jsonl``). Relay is imported only on this path.

Calls are classified from the request itself, so counts and unloads made on
worker threads need no context. A call is attributed to the slot whose window
it starts in, whatever its thread: a companion session is started and stopped
inside its slot, so its calls belong to that slot by construction, under their
own kind (``companion``). Every timestamp comes from one clock: an epoch
offset taken once when the run opens, plus ``perf_counter_ns``. Prompts and
responses are never recorded, only their byte lengths.
"""

from __future__ import annotations

import itertools
import json
import os
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

KINDS = ("generate", "embed", "count", "show", "tags", "ps", "unload", "companion")
MODES = ("off", "events", "relay")


class TraceError(RuntimeError):
    """A tracer that cannot start safely refuses the run."""


def classify(method: str, url: str, body: dict | None) -> str:
    """The call kind of one Ollama request, from its endpoint and body."""

    path = urlsplit(url).path
    if path.endswith("/api/tags"):
        return "tags"
    if path.endswith("/api/ps"):
        return "ps"
    if path.endswith("/api/show"):
        return "show"
    if path.endswith(("/api/embed", "/api/embeddings")):
        return "embed"
    if path.endswith("/api/generate") and isinstance(body, dict):
        if body.get("companion") == "start":
            return "companion"
        if body.get("keep_alive") == 0 and body.get("prompt", "") == "":
            return "unload"
        if body.get("raw") is True:
            return "count"
        return "generate"
    return "other"


def _usage(payload: object) -> tuple[int | None, int | None]:
    if not isinstance(payload, dict):
        return None, None
    prompt = payload.get("prompt_eval_count")
    completion = payload.get("eval_count")
    return (prompt if isinstance(prompt, int) else None, completion if isinstance(completion, int) else None)


@dataclass
class CallRecord:
    call_id: int
    kind: str
    endpoint: str
    model: str | None
    device: str | None
    thread: str
    start_ns: int
    end_ns: int | None = None
    status: str = "open"
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    request_bytes: int = 0
    extra: dict = field(default_factory=dict)

    @property
    def ms(self) -> float | None:
        return None if self.end_ns is None else (self.end_ns - self.start_ns) / 1e6


class _EventSink:
    """The native ordered log: one JSON line per finished call."""

    def __init__(self, path: Path):
        self.path = path
        self._file = path.open("w", encoding="utf-8")
        self._lock = threading.Lock()
        # The watcher may close the log while a worker or the run thread still calls in; later calls are dropped.
        self._closed = False

    def start(self, record: CallRecord) -> None:
        return None

    def end(self, record: CallRecord) -> None:
        line = {
            "call_id": record.call_id,
            "t_ns": record.start_ns,
            "end_ns": record.end_ns,
            "thread": record.thread,
            "kind": record.kind,
            "endpoint": record.endpoint,
            "model": record.model,
            "device": record.device,
            "ms": record.ms,
            "status": record.status,
            "prompt_tokens": record.prompt_tokens,
            "completion_tokens": record.completion_tokens,
            **record.extra,
        }
        text = json.dumps(line, sort_keys=True) + "\n"
        with self._lock:
            if not self._closed:
                self._file.write(text)

    def mark(self, name: str, t_ns: int, data: dict) -> None:
        with self._lock:
            if not self._closed:
                self._file.write(json.dumps({"mark": name, "t_ns": t_ns, **data}, sort_keys=True) + "\n")

    def flush(self) -> None:
        with self._lock:
            if not self._closed:
                self._file.flush()

    def close(self, end_ns: int | None = None) -> None:
        with self._lock:
            if not self._closed:
                self._closed = True
                self._file.flush()
                self._file.close()


class Tracer:
    """One run's call counter, and its ordered log when tracing is on."""

    def __init__(self, *, root: Path, run_id: str, mode: str = "off", relay_factory=None):
        if mode not in MODES:
            raise TraceError(f"unknown trace mode {mode}")
        self.root = Path(root)
        self.run_id = run_id
        self.mode = mode
        self._relay_factory = relay_factory
        self._ids = itertools.count(1)
        self._lock = threading.Lock()
        self._counts: dict[str, dict] = {}
        self._slot: dict = {}
        self._slot_calls: list[int] = []
        self._open: dict[int, CallRecord] = {}
        self._sink = None
        self._offset_ns = 0
        self.trace_file: str | None = None
        self.scope_id: str | None = None

    # -- the run --------------------------------------------------------------

    def open(self) -> Tracer:
        """Take the one epoch offset and open the sink. Refuses before any device."""

        self._offset_ns = time.time_ns() - time.perf_counter_ns()
        if self.mode == "off":
            return self
        if any(key.startswith("OTEL_") for key in os.environ):
            raise TraceError("REFUSED: an OTEL_* variable is set; tracing must stay on this machine")
        logs = self.root / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        if self.mode == "events":
            name = f"{self.run_id}.events.jsonl"
            self._sink = _EventSink(logs / name)
        else:
            name = f"{self.run_id}.atof.jsonl"
            factory = self._relay_factory
            if factory is None:
                from interlock.relay_sink import RelaySink as factory
            self._sink = factory(logs, name, self.now_ns(), self.run_id)
        self.trace_file = f"logs/{name}"
        self.scope_id = getattr(self._sink, "scope_id", None)
        return self

    def close(self) -> None:
        """Close any call left open, then flush and close the sink. Runs on every exit path."""

        with self._lock:
            leftover = list(self._open.values())
            self._open.clear()
        for record in leftover:
            record.end_ns = self.now_ns()
            record.status = "abandoned"
            self._finish(record)
        if self._sink is not None:
            sink, self._sink = self._sink, None
            sink.close(self.now_ns())

    def __enter__(self) -> Tracer:
        return self.open()

    def __exit__(self, *exc) -> None:
        self.close()

    def now_ns(self) -> int:
        return self._offset_ns + time.perf_counter_ns()

    def mark(self, name: str, **data) -> None:
        if self._sink is not None:
            self._sink.mark(name, self.now_ns(), data)

    def flush(self) -> None:
        if self._sink is not None:
            self._sink.flush()

    # -- slots and rows ---------------------------------------------------------

    def begin_slot(self, **slot) -> None:
        with self._lock:
            self._slot = dict(slot)
            self._slot_calls = []

    def end_slot(self) -> dict:
        """The slot's calls: their ids, and the measured call's id."""

        with self._lock:
            calls = list(self._slot_calls)
            self._slot = {}
            self._slot_calls = []
        return {"call_ids": calls}

    def counts_for(self, arm_id: str) -> dict:
        """``artifacts.call_counts`` for one arm's row."""

        with self._lock:
            return {kind: dict(value) for kind, value in sorted(self._counts.get(arm_id, {}).items())}

    # -- calls ------------------------------------------------------------------

    def start(
        self, kind: str, endpoint: str, *, model: str | None, device: str | None, request_bytes: int = 0
    ) -> CallRecord:
        record = CallRecord(
            call_id=next(self._ids),
            kind=kind,
            endpoint=endpoint,
            model=model,
            device=device,
            thread=threading.current_thread().name,
            start_ns=self.now_ns(),
            request_bytes=request_bytes,
        )
        with self._lock:
            self._open[record.call_id] = record
            if self._slot:
                self._slot_calls.append(record.call_id)
                record.extra = {"arm": self._slot.get("arm"), "slot": self._slot.get("index")}
        if self._sink is not None:
            self._sink.start(record)
        return record

    def end(self, record: CallRecord, status: str, payload: object = None) -> None:
        record.end_ns = self.now_ns()
        record.status = status
        record.prompt_tokens, record.completion_tokens = _usage(payload)
        with self._lock:
            if self._open.pop(record.call_id, None) is None:
                return
        self._finish(record)

    def _finish(self, record: CallRecord) -> None:
        arm = record.extra.get("arm") or "_run"
        with self._lock:
            fresh = {"n": 0, "ms": 0.0, "errors": 0, "timeouts": 0}
            entry = self._counts.setdefault(arm, {}).setdefault(record.kind, fresh)
            entry["n"] += 1
            entry["ms"] = round(entry["ms"] + (record.ms or 0.0), 3)
            if record.status == "timeout":
                entry["timeouts"] += 1
            elif record.status != "ok":
                entry["errors"] += 1
        if self._sink is not None:
            self._sink.end(record)

    @contextmanager
    def call(self, kind: str, endpoint: str, *, model: str | None, device: str | None):
        record = self.start(kind, endpoint, model=model, device=device)
        box: dict = {"status": "exception", "payload": None}
        try:
            yield box
        finally:
            self.end(record, box["status"], box["payload"])

    def artifacts(self, arm_id: str) -> dict:
        """What a receipt row carries for one arm: the counts, and the trace pointer when tracing."""

        out: dict = {"call_counts": self.counts_for(arm_id)}
        if self.trace_file is not None:
            out["trace"] = {"file": self.trace_file}
            if self.scope_id:
                out["trace"]["span"] = self.scope_id
        return out


class _TracedTransport:
    """An Ollama transport, classified, timed and counted on the calling thread.

    Every other attribute goes to the wrapped transport, so methods the adapter looks for on its transport (such
    as ``cancel``, which ends an in-flight request before an unload) still reach it."""

    def __init__(self, transport, tracer: Tracer, device: str | None):
        self.__wrapped__ = transport
        self._tracer = tracer
        self._device = device

    def __getattr__(self, name):
        return getattr(self.__wrapped__, name)

    def __call__(self, method: str, url: str, body: dict | None, *args, **kwargs):
        tracer = self._tracer
        kind = classify(method, url, body)
        model = body.get("model") if isinstance(body, dict) else None
        # Only Relay's request record uses the size. Serialising a long prompt again costs measured time.
        size = len(json.dumps(body)) if body is not None and tracer.mode == "relay" else 0
        record = tracer.start(kind, urlsplit(url).path, model=model, device=self._device, request_bytes=size)
        status, payload = "exception", None
        try:
            payload = self.__wrapped__(method, url, body, *args, **kwargs)
            status = "ok"
            return payload
        except Exception as exc:
            status = "timeout" if isinstance(exc, TimeoutError) or "timed out" in str(exc).lower() else "http_error"
            raise
        finally:
            tracer.end(record, status, payload)


def traced_transport(transport, tracer: Tracer, *, device: str | None = None):
    """Wrap an Ollama transport: every request is classified, timed and counted on the calling thread."""

    return _TracedTransport(transport, tracer, device)


def instrument(adapters: dict, tracer: Tracer) -> None:
    """Count every model call the run's adapters make: Ollama through its
    transport, OpenVINO through its bounded call."""

    for engine, adapter in adapters.items():
        if engine == "ollama" and hasattr(adapter, "transport"):
            if getattr(adapter.transport, "__wrapped__", None) is None:
                adapter.transport = traced_transport(adapter.transport, tracer, device=getattr(adapter, "device", None))
        elif engine == "openvino":
            import importlib

            module = importlib.import_module("interlock.adapters.openvino")
            module.set_tracer(tracer)


def release(adapters: dict) -> None:
    """Undo ``instrument`` for the OpenVINO module, whose tracer is module-wide."""

    if "openvino" in adapters:
        import importlib

        module = importlib.import_module("interlock.adapters.openvino")
        module.set_tracer(None)
```

### src/interlock/relay_sink.py

```python
"""NeMo Relay as the ordered call log (``--trace relay``). Imported only on that path.

Relay is driven through its Python API on a private event loop: an
observability plugin with one ATOF file sink and nothing else, one run scope,
and one ``llm.call``/``llm.call_end`` span per model call. Every timestamp is
interlock's own, so spans and the run scope share one clock. Payload
sanitizers replace prompts and responses with their byte lengths. Token counts
go in the span's metadata, which the ATOF file keeps.

The sink refuses to start if Relay would layer in any configuration file
(user or system ``plugins.toml``), so the only sink is the one named here.
"""

from __future__ import annotations

import asyncio
import contextvars
import json
import threading
from datetime import UTC, datetime
from pathlib import Path

from interlock.calltrace import CallRecord, TraceError


def _when(t_ns: int) -> datetime:
    return datetime.fromtimestamp(t_ns / 1e9, tz=UTC)


def _length_only(payload, _context=None) -> dict:
    return {"bytes": len(json.dumps(payload, default=str))}


def _request_length_only(request, _context=None):
    """Relay's request sanitizer must hand back an ``LLMRequest``: one whose content is only its byte length."""

    import nemo_relay

    content = getattr(request, "content", request)
    return nemo_relay.LLMRequest({}, _length_only(content))


_REQUEST = "interlock-length-only-request"
_RESPONSE = "interlock-length-only-response"
# Relay's plugin activation and its sanitizers are process-wide, so one sink is live at a time.
_LIVE = threading.Lock()


class RelaySink:
    """One run's Relay trace. Calls arrive from the run thread and from worker threads (unloads, OpenVINO
    companions), so every Relay call goes through one lock (Argon B1)."""

    def __init__(self, logs: Path, filename: str, start_ns: int, run_id: str):
        import nemo_relay
        from nemo_relay import guardrails, plugin, scope

        self._relay = nemo_relay
        self._scope = scope
        self._guardrails = guardrails
        self._lock = threading.Lock()
        self._spans: dict[int, object] = {}
        # The watcher may close the sink while a thread still calls in; later calls are dropped.
        self._closed = False
        config = {
            "version": 1,
            "components": [{
                "kind": "observability",
                "enabled": True,
                "config": {
                    "version": 4,
                    "enable_full_payloads": False,
                    "atof": {"enabled": True, "sinks": [
                        {"type": "file", "output_directory": str(logs), "filename": filename, "mode": "overwrite"}
                    ]},
                },
            }],
        }
        report = plugin.validate(config)
        if report.get("config_paths"):
            raise TraceError("REFUSED: Relay would layer in other plugins.toml files; remove them before tracing")
        if not _LIVE.acquire(blocking=False):
            raise TraceError("REFUSED: a Relay trace is already open in this process; one run traces at a time")
        # Anything acquired below is released if a later step fails (Argon B3).
        self._loop = None
        self._activation = None
        registered: list[str] = []
        try:
            self._loop = asyncio.new_event_loop()
            self._activation = self._loop.run_until_complete(plugin.initialize(config))
            guardrails.register_llm_sanitize_request(_REQUEST, 0, _request_length_only)
            registered.append("request")
            guardrails.register_llm_sanitize_response(_RESPONSE, 0, _length_only)
            registered.append("response")
            self._run = scope.push(f"interlock-run {run_id}", scope.ScopeType.Agent, timestamp=_when(start_ns))
            self.scope_id = self._run.uuid
            # Relay keeps its scope stack in a context variable. The watcher closes the trace from its own
            # thread on a halt, so the pop runs in the context the scope was pushed in.
            self._context = contextvars.copy_context()
        except BaseException:
            self._release(registered)
            raise

    def _release(self, registered=("request", "response")) -> None:
        try:
            if "request" in registered:
                self._guardrails.deregister_llm_sanitize_request(_REQUEST)
            if "response" in registered:
                self._guardrails.deregister_llm_sanitize_response(_RESPONSE)
            if self._activation is not None:
                self._loop.run_until_complete(self._activation.close())
        finally:
            if self._loop is not None:
                self._loop.close()
            _LIVE.release()

    def start(self, record: CallRecord) -> None:
        request = self._relay.LLMRequest({}, {"bytes": record.request_bytes})
        with self._lock:
            if self._closed:
                return
            handle = self._relay.llm.call(
                "ollama" if record.endpoint.startswith("/api/") else "openvino",
                request,
                handle=self._run,
                model_name=record.model,
                metadata={"call_id": record.call_id, "kind": record.kind, "endpoint": record.endpoint,
                          "device": record.device, "thread": record.thread, **record.extra},
                timestamp=_when(record.start_ns),
            )
            self._spans[record.call_id] = handle

    def end(self, record: CallRecord) -> None:
        with self._lock:
            handle = self._spans.pop(record.call_id, None)
            if handle is None or self._closed:
                return
            self._relay.llm.call_end(
                handle,
                {"status": record.status},
                # extra carries what is only known at the end, such as an OpenVINO timeout's worker_still_running.
                metadata={**record.extra, "call_id": record.call_id, "status": record.status, "ms": record.ms,
                          "prompt_tokens": record.prompt_tokens, "completion_tokens": record.completion_tokens},
                timestamp=_when(record.end_ns),
            )

    def mark(self, name: str, t_ns: int, data: dict) -> None:
        with self._lock:
            if self._closed:
                return
            self._scope.event(name, handle=self._run, data=data, timestamp=_when(t_ns))

    def flush(self) -> None:
        with self._lock:
            if not self._closed:
                self._relay.subscribers.flush()

    def close(self, end_ns: int | None = None) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
            try:
                self._context.run(
                    self._scope.pop, self._run, timestamp=_when(end_ns) if end_ns is not None else None
                )
            finally:
                try:
                    self._relay.subscribers.flush()
                finally:
                    self._release()
```
