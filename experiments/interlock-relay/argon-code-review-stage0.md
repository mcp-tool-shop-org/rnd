# Code review brief for Argon: NeMo Relay inside interlock, stage 0

R&D, 2026-10-14. You're reviewing code, not a design. You audited the design in four rounds and passed it at v3.1. Stage 0 has now been built and run on fakes, and this is its code and its results. The author is the R&D session (Claude), which is why a different model family reviews it. Work independently, and attack it. Your findings are advice: R&D decides what to act on and records why.

## What stage 0 is (from the approved design)

- **interlock** is a local AI device router. It measures models on an RTX 5090 (Ollama) and on an Intel NPU and integrated GPU (OpenVINO), writes receipts, and routes from them. It never serves traffic.
- **The experiment** asks whether NVIDIA NeMo Relay 0.10.1 can trace interlock's model calls completely and safely, without changing what interlock measures. And does Relay's ordered trace show facts that interlock's per-kind call counter doesn't?
- **Stage 0 runs on fakes only,** with no device, GPU, NPU or model. It decides two hypotheses:
  - **H4a:** an ordered trace answers 5 pre-registered diagnostic questions, and the receipt's counter answers at most 2.
  - **H4b:** Relay against a native event log of our own. It needs information parity, a shared ATOF reader that works across Relay producers, at most 2,048 bytes per call, an added client time with a median under 0.5 ms and a 99th percentile under 2 ms, and a median less than 0.25 ms above the native log's.
- **It also checks:**
  - **H1 (complete capture):** every model call appears exactly once, with the right kind, status and duration.
  - **H3 (safety):**
    - receipts pass `interlock check`;
    - no prompt, host, user or home path appears in the trace;
    - no non-loopback socket is opened;
    - an interrupted run leaves a closed, parsable trace;
    - `OTEL_*` refuses tracing.

## Known open items (don't report these as findings)

- The E4b run path (`urllib_exchange`) and the fill-card path aren't wired yet. `--trace` refuses on them (amendment A3).
- The stop file isn't yet tested through interlock's real stop mechanism. The test interrupts with `KeyboardInterrupt`.
- Stages 1 and 2 (device runs) haven't happened.

## What to do

1. **Review the interlock code** (diff below) for:
   - correctness, especially thread safety (unload and OpenVINO calls run on worker threads), every exit path, and timestamps;
   - anything that could change what interlock measures, or leak content off the rig or into the trace;
   - Relay API misuse.
2. **Review the evaluation** (`diagnose.py`, `cases.py`):
   - Is the receipt's diagnosis given a fair best score, or rigged to lose?
   - Are the planted cases realistic enough that "5 of 5" means something?
   - Does the shared-reader test show what H4b asks?
   - Do the results support "H4a and H4b hold"?
3. **Judge amendments A1–A7:** is each a legitimate change, or does it weaken a pre-registered check?

## How to answer

- **Rank the findings:** blocking (wrong results or unsafe), important, minor.
- **For each:** the file and line, a concrete failure scenario, and the fix.
- **Say plainly** where you think the code is right.
- **End with a verdict:** "blocking issues remain", or "no blocking issues; stage 0 can finish". Before stage 1, list what you would add to stage 0, if anything.

## Results and amendments (the record)


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

## The interlock diff (against main at c89cc14)

```diff
diff --git a/pyproject.toml b/pyproject.toml
index 3baa895..062f4e5 100644
--- a/pyproject.toml
+++ b/pyproject.toml
@@ -28,6 +28,10 @@ intel = [
     "openvino-genai==2026.4.1.0",
     "transformers==5.10.1",
 ]
+# NVIDIA NeMo Relay for `--trace relay` (the interlock-relay experiment, stage 0). Nothing imports it otherwise.
+relay = [
+    "nemo-relay==0.10.1",
+]
 
 [project.scripts]
 interlock = "interlock.cli:main"
@@ -59,6 +63,7 @@ default-groups = ["dev"]
 testpaths = ["tests"]
 pythonpath = ["."]
 addopts = "--cov=interlock --cov-report=term-missing --cov-fail-under=90"
+markers = ["relay: needs the relay extra (nemo-relay); skipped without it"]
 
 [tool.coverage.run]
 source = ["interlock"]
diff --git a/src/interlock/adapters/openvino.py b/src/interlock/adapters/openvino.py
index 38d328d..af6b25d 100644
--- a/src/interlock/adapters/openvino.py
+++ b/src/interlock/adapters/openvino.py
@@ -575,7 +575,36 @@ def _bound(self, s: _Settings) -> float:
     return s.call_timeout_s if s.call_timeout_s is not None else self.call_timeout_s
 
 
-def _timed_call(fn, timeout_s: float):
+# The run's call tracer (interlock.calltrace), set by the runner. None is off.
+_TRACER = None
+
+
+def set_tracer(tracer) -> None:
+    global _TRACER
+    _TRACER = tracer
+
+
+def _timed_call(fn, timeout_s: float, *, kind: str = "generate", model: str | None = None, device: str | None = None):
+    """``_bounded_call``, counted and, when tracing, logged. The span opens and
+    closes on this calling thread: a hang closes as ``timeout`` with the worker
+    still running, and no tracer call is ever made inside the worker."""
+
+    tracer = _TRACER
+    if tracer is None:
+        return _bounded_call(fn, timeout_s)
+    record = tracer.start(kind, f"openvino/{kind}", model=model, device=device)
+    status = "exception"
+    try:
+        result = _bounded_call(fn, timeout_s)
+        status = "timeout" if result[0] == "hang" else "ok"
+        if status == "timeout":
+            record.extra["worker_still_running"] = True
+        return result
+    finally:
+        tracer.end(record, status)
+
+
+def _bounded_call(fn, timeout_s: float):
     """Run one measured call with a hard bound. A hang returns ("hang", None);
     the worker is a daemon and cannot outlive the process.
 
@@ -718,6 +747,9 @@ def _run_embed(self, request: StepRequest, s: _Settings, resolved: dict) -> Step
                 entry, ids, mask, tt, batch_rows if static is None else static[0], request.task
             ),
             bound,
+            kind="embed",
+            model=request.model,
+            device=ov_id,
         )
     except Exception as exc:
         if _is_device_lost(exc):
@@ -840,7 +872,10 @@ def _run_generate(self, request: StepRequest, s: _Settings, resolved: dict) -> S
     t0 = self.clock()
     try:
         bound = _bound(self, s)
-        status, out = _timed_call(lambda: pipe.generate([str(s.get("prompt") or "hello")], config), bound)
+        status, out = _timed_call(
+            lambda: pipe.generate([str(s.get("prompt") or "hello")], config), bound,
+            kind="generate", model=request.model, device=ov_id,
+        )
     except Exception as exc:
         if _is_device_lost(exc):
             self._lost_devices.add(ov_id)
@@ -1198,7 +1233,10 @@ def _start_session(self, request: StepRequest) -> None:
                 while not stop.is_set():
                     t0 = self.clock()
                     bound = _bound(self, s)
-                    status, _ = _timed_call(lambda: pipe.generate(str(s.get("prompt") or "hello"), config), bound)
+                    status, _ = _timed_call(
+                        lambda: pipe.generate(str(s.get("prompt") or "hello"), config), bound,
+                        kind="companion", model=request.model, device=ov_id,
+                    )
                     if status == "hang":
                         box["fault"] = AdapterError(f"hang: companion call exceeded {bound:g} s")
                         return
@@ -1223,7 +1261,8 @@ def _start_session(self, request: StepRequest) -> None:
                     t0 = self.clock()
                     bound = _bound(self, s)
                     status, _ = _timed_call(
-                        lambda: self._infer_embed(entry, ids, mask, tt, rows, request.task), bound
+                        lambda: self._infer_embed(entry, ids, mask, tt, rows, request.task), bound,
+                        kind="companion", model=request.model, device=ov_id,
                     )
                     if status == "hang":
                         box["fault"] = AdapterError(f"hang: companion call exceeded {bound:g} s")
diff --git a/src/interlock/calltrace.py b/src/interlock/calltrace.py
new file mode 100644
index 0000000..06a45bf
--- /dev/null
+++ b/src/interlock/calltrace.py
@@ -0,0 +1,343 @@
+"""Every model call interlock makes, counted per kind and optionally logged in order.
+
+The counter is always on. Each receipt row carries ``artifacts.call_counts``:
+per call kind, how many calls, their client-side time, errors and timeouts.
+That is a summary, not a log.
+
+``--trace`` adds an ordered log of the same calls under ``logs/``:
+
+- ``events``: one JSON line per finished call, written by this module
+  (``logs/<run_id>.events.jsonl``);
+- ``relay``: NVIDIA NeMo Relay's ATOF events, through its Python API
+  (``logs/<run_id>.atof.jsonl``). Relay is imported only on this path.
+
+Calls are classified from the request itself, so counts and unloads made on
+worker threads need no context. Every timestamp comes from one clock: an epoch
+offset taken once when the run opens, plus ``perf_counter_ns``. Prompts and
+responses are never recorded, only their byte lengths.
+"""
+
+from __future__ import annotations
+
+import itertools
+import json
+import os
+import threading
+import time
+from contextlib import contextmanager
+from dataclasses import dataclass, field
+from pathlib import Path
+from urllib.parse import urlsplit
+
+KINDS = ("generate", "embed", "count", "show", "tags", "ps", "unload", "companion")
+MODES = ("off", "events", "relay")
+
+
+class TraceError(RuntimeError):
+    """A tracer that cannot start safely refuses the run."""
+
+
+def classify(method: str, url: str, body: dict | None) -> str:
+    """The call kind of one Ollama request, from its endpoint and body."""
+
+    path = urlsplit(url).path
+    if path.endswith("/api/tags"):
+        return "tags"
+    if path.endswith("/api/ps"):
+        return "ps"
+    if path.endswith("/api/show"):
+        return "show"
+    if path.endswith("/api/generate") and isinstance(body, dict):
+        if body.get("companion") == "start":
+            return "companion"
+        if body.get("keep_alive") == 0 and body.get("prompt", "") == "":
+            return "unload"
+        if body.get("raw") is True:
+            return "count"
+        return "generate"
+    return "other"
+
+
+def _usage(payload: object) -> tuple[int | None, int | None]:
+    if not isinstance(payload, dict):
+        return None, None
+    prompt = payload.get("prompt_eval_count")
+    completion = payload.get("eval_count")
+    return (prompt if isinstance(prompt, int) else None, completion if isinstance(completion, int) else None)
+
+
+@dataclass
+class CallRecord:
+    call_id: int
+    kind: str
+    endpoint: str
+    model: str | None
+    device: str | None
+    thread: str
+    start_ns: int
+    end_ns: int | None = None
+    status: str = "open"
+    prompt_tokens: int | None = None
+    completion_tokens: int | None = None
+    request_bytes: int = 0
+    extra: dict = field(default_factory=dict)
+
+    @property
+    def ms(self) -> float | None:
+        return None if self.end_ns is None else (self.end_ns - self.start_ns) / 1e6
+
+
+class _EventSink:
+    """The native ordered log: one JSON line per finished call."""
+
+    def __init__(self, path: Path):
+        self.path = path
+        self._file = path.open("w", encoding="utf-8")
+        self._lock = threading.Lock()
+
+    def start(self, record: CallRecord) -> None:
+        return None
+
+    def end(self, record: CallRecord) -> None:
+        line = {
+            "call_id": record.call_id,
+            "t_ns": record.start_ns,
+            "end_ns": record.end_ns,
+            "thread": record.thread,
+            "kind": record.kind,
+            "endpoint": record.endpoint,
+            "model": record.model,
+            "device": record.device,
+            "ms": record.ms,
+            "status": record.status,
+            "prompt_tokens": record.prompt_tokens,
+            "completion_tokens": record.completion_tokens,
+            **record.extra,
+        }
+        text = json.dumps(line, sort_keys=True) + "\n"
+        with self._lock:
+            self._file.write(text)
+
+    def mark(self, name: str, t_ns: int, data: dict) -> None:
+        with self._lock:
+            self._file.write(json.dumps({"mark": name, "t_ns": t_ns, **data}, sort_keys=True) + "\n")
+
+    def flush(self) -> None:
+        with self._lock:
+            self._file.flush()
+
+    def close(self, end_ns: int | None = None) -> None:
+        with self._lock:
+            self._file.flush()
+            self._file.close()
+
+
+class Tracer:
+    """One run's call counter, and its ordered log when tracing is on."""
+
+    def __init__(self, *, root: Path, run_id: str, mode: str = "off", relay_factory=None):
+        if mode not in MODES:
+            raise TraceError(f"unknown trace mode {mode}")
+        self.root = Path(root)
+        self.run_id = run_id
+        self.mode = mode
+        self._relay_factory = relay_factory
+        self._ids = itertools.count(1)
+        self._lock = threading.Lock()
+        self._counts: dict[str, dict] = {}
+        self._slot: dict = {}
+        self._slot_calls: list[int] = []
+        self._open: dict[int, CallRecord] = {}
+        self._sink = None
+        self._offset_ns = 0
+        self.trace_file: str | None = None
+        self.scope_id: str | None = None
+
+    # -- the run --------------------------------------------------------------
+
+    def open(self) -> Tracer:
+        """Take the one epoch offset and open the sink. Refuses before any device."""
+
+        self._offset_ns = time.time_ns() - time.perf_counter_ns()
+        if self.mode == "off":
+            return self
+        if any(key.startswith("OTEL_") for key in os.environ):
+            raise TraceError("REFUSED: an OTEL_* variable is set; tracing must stay on this machine")
+        logs = self.root / "logs"
+        logs.mkdir(parents=True, exist_ok=True)
+        if self.mode == "events":
+            name = f"{self.run_id}.events.jsonl"
+            self._sink = _EventSink(logs / name)
+        else:
+            name = f"{self.run_id}.atof.jsonl"
+            factory = self._relay_factory
+            if factory is None:
+                from interlock.relay_sink import RelaySink as factory
+            self._sink = factory(logs, name, self.now_ns(), self.run_id)
+        self.trace_file = f"logs/{name}"
+        self.scope_id = getattr(self._sink, "scope_id", None)
+        return self
+
+    def close(self) -> None:
+        """Close any call left open, then flush and close the sink. Runs on every exit path."""
+
+        with self._lock:
+            leftover = list(self._open.values())
+            self._open.clear()
+        for record in leftover:
+            record.end_ns = self.now_ns()
+            record.status = "abandoned"
+            self._finish(record)
+        if self._sink is not None:
+            sink, self._sink = self._sink, None
+            sink.close(self.now_ns())
+
+    def __enter__(self) -> Tracer:
+        return self.open()
+
+    def __exit__(self, *exc) -> None:
+        self.close()
+
+    def now_ns(self) -> int:
+        return self._offset_ns + time.perf_counter_ns()
+
+    def mark(self, name: str, **data) -> None:
+        if self._sink is not None:
+            self._sink.mark(name, self.now_ns(), data)
+
+    def flush(self) -> None:
+        if self._sink is not None:
+            self._sink.flush()
+
+    # -- slots and rows ---------------------------------------------------------
+
+    def begin_slot(self, **slot) -> None:
+        with self._lock:
+            self._slot = dict(slot)
+            self._slot_calls = []
+
+    def end_slot(self) -> dict:
+        """The slot's calls: their ids, and the measured call's id."""
+
+        with self._lock:
+            calls = list(self._slot_calls)
+            self._slot = {}
+            self._slot_calls = []
+        return {"call_ids": calls}
+
+    def counts_for(self, arm_id: str) -> dict:
+        """``artifacts.call_counts`` for one arm's row."""
+
+        with self._lock:
+            return {kind: dict(value) for kind, value in sorted(self._counts.get(arm_id, {}).items())}
+
+    # -- calls ------------------------------------------------------------------
+
+    def start(self, kind: str, endpoint: str, *, model: str | None, device: str | None, request_bytes: int = 0) -> CallRecord:
+        record = CallRecord(
+            call_id=next(self._ids),
+            kind=kind,
+            endpoint=endpoint,
+            model=model,
+            device=device,
+            thread=threading.current_thread().name,
+            start_ns=self.now_ns(),
+            request_bytes=request_bytes,
+        )
+        with self._lock:
+            self._open[record.call_id] = record
+            if self._slot:
+                self._slot_calls.append(record.call_id)
+                record.extra = {"arm": self._slot.get("arm"), "slot": self._slot.get("index")}
+        if self._sink is not None:
+            self._sink.start(record)
+        return record
+
+    def end(self, record: CallRecord, status: str, payload: object = None) -> None:
+        record.end_ns = self.now_ns()
+        record.status = status
+        record.prompt_tokens, record.completion_tokens = _usage(payload)
+        with self._lock:
+            if self._open.pop(record.call_id, None) is None:
+                return
+        self._finish(record)
+
+    def _finish(self, record: CallRecord) -> None:
+        arm = record.extra.get("arm") or "_run"
+        with self._lock:
+            entry = self._counts.setdefault(arm, {}).setdefault(record.kind, {"n": 0, "ms": 0.0, "errors": 0, "timeouts": 0})
+            entry["n"] += 1
+            entry["ms"] = round(entry["ms"] + (record.ms or 0.0), 3)
+            if record.status == "timeout":
+                entry["timeouts"] += 1
+            elif record.status != "ok":
+                entry["errors"] += 1
+        if self._sink is not None:
+            self._sink.end(record)
+
+    @contextmanager
+    def call(self, kind: str, endpoint: str, *, model: str | None, device: str | None):
+        record = self.start(kind, endpoint, model=model, device=device)
+        box: dict = {"status": "exception", "payload": None}
+        try:
+            yield box
+        finally:
+            self.end(record, box["status"], box["payload"])
+
+    def artifacts(self, arm_id: str) -> dict:
+        """What a receipt row carries for one arm: the counts, and the trace pointer when tracing."""
+
+        out: dict = {"call_counts": self.counts_for(arm_id)}
+        if self.trace_file is not None:
+            out["trace"] = {"file": self.trace_file}
+            if self.scope_id:
+                out["trace"]["span"] = self.scope_id
+        return out
+
+
+def traced_transport(transport, tracer: Tracer, *, device: str | None = None):
+    """Wrap an Ollama transport: every request is classified, timed and counted on the calling thread."""
+
+    def wrapped(method: str, url: str, body: dict | None, *args, **kwargs):
+        kind = classify(method, url, body)
+        model = body.get("model") if isinstance(body, dict) else None
+        size = len(json.dumps(body)) if body is not None else 0
+        record = tracer.start(kind, urlsplit(url).path, model=model, device=device, request_bytes=size)
+        status, payload = "exception", None
+        try:
+            payload = transport(method, url, body, *args, **kwargs)
+            status = "ok"
+            return payload
+        except Exception as exc:
+            status = "timeout" if "timed out" in str(exc) else "http_error"
+            raise
+        finally:
+            tracer.end(record, status, payload)
+
+    wrapped.__wrapped__ = transport
+    return wrapped
+
+
+def instrument(adapters: dict, tracer: Tracer) -> None:
+    """Count every model call the run's adapters make: Ollama through its
+    transport, OpenVINO through its bounded call."""
+
+    for engine, adapter in adapters.items():
+        if engine == "ollama" and hasattr(adapter, "transport"):
+            if getattr(adapter.transport, "__wrapped__", None) is None:
+                adapter.transport = traced_transport(adapter.transport, tracer, device=getattr(adapter, "device", None))
+        elif engine == "openvino":
+            import importlib
+
+            module = importlib.import_module("interlock.adapters.openvino")
+            module.set_tracer(tracer)
+
+
+def release(adapters: dict) -> None:
+    """Undo ``instrument`` for the OpenVINO module, whose tracer is module-wide."""
+
+    if "openvino" in adapters:
+        import importlib
+
+        module = importlib.import_module("interlock.adapters.openvino")
+        module.set_tracer(None)
diff --git a/src/interlock/cli.py b/src/interlock/cli.py
index 561681d..fefad22 100644
--- a/src/interlock/cli.py
+++ b/src/interlock/cli.py
@@ -93,6 +93,12 @@ def main(argv: list[str] | None = None) -> int:
     run.add_argument("--notes", default="")
     run.add_argument("--dry-run", action="store_true")
     run.add_argument("--pilot", action="store_true")
+    run.add_argument(
+        "--trace",
+        choices=("off", "events", "relay"),
+        default="off",
+        help="log every model call in order under logs/: events (stdlib) or relay (NeMo Relay ATOF, needs interlock[relay])",
+    )
     run.add_argument(
         "--pairs",
         default=None,
@@ -348,6 +354,7 @@ def _cmd_run(args: argparse.Namespace) -> int:
                 heartbeat=heartbeat_path(None),
             ),
             pilot=args.pilot,
+            trace=args.trace,
             quarantine=getattr(args, "quarantine", None),
             pairs=pairs,
             models=models,
diff --git a/src/interlock/harness/runner.py b/src/interlock/harness/runner.py
index 8f4f844..876bd8f 100644
--- a/src/interlock/harness/runner.py
+++ b/src/interlock/harness/runner.py
@@ -81,7 +81,7 @@ from interlock.ollama_supervisor import (
     restart_policy_lines,
     retry_budget,
 )
-from interlock.receipt import validate_row
+from interlock.receipt import CAPABILITY_OUTCOMES, validate_row
 
 try:  # the CPU-window evidence of ruling #36's addendum; never a step failure
     import psutil
@@ -357,6 +357,7 @@ def run_interleaved(
     watch: WatchHooks | None = None,
     marker: RunMarker | None = None,
     supervisor=None,
+    tracer=None,
 ) -> list[dict]:
     """Run a committed spec.
 
@@ -640,6 +641,11 @@ def run_interleaved(
         window = {"start": _iso(started_at), "end": _iso(wall())}
         restarts = marker.restart_records()
         for row in rows:
+            # A capability row (hang, device lost, compile refused) carries no artifacts by the receipt rule:
+            # it is not a speed. Its calls stay in the ordered trace.
+            if tracer is not None and row.get("outcome") not in CAPABILITY_OUTCOMES:
+                arm_of_row = row["id"].rsplit("/", 2)[-2]
+                row.setdefault("artifacts", {}).update(tracer.artifacts(arm_of_row))
             row["settings"]["run_window"] = window
             row["settings"]["start_state"] = start_state
             row["settings"]["ram_guard"] = guard.ram_guard()
@@ -907,6 +913,9 @@ def run_interleaved(
                 if probe is not None:
                     adapter._slot_probe = probe
                     probe.open()
+                if tracer is not None:
+                    tracer.begin_slot(arm=arm["id"], index=f"{slot.phase}:{slot.round_index}:{slot.role}")
+                slot_calls = None
                 try:
                     kind = "ok"
                     error = ""
@@ -1011,6 +1020,9 @@ def run_interleaved(
                                 {"slot_start": cpu_start, "slot_end": cpu_end},
                                 _finish_slot_probe(probe, adapter),
                             )
+                            if tracer is not None:
+                                slot_calls = tracer.end_slot()
+                                sample["call_ids"] = slot_calls["call_ids"]
                             if epoch is not None:
                                 try:
                                     sample = supervisor.keep_sample(epoch, sample)
@@ -1517,6 +1529,8 @@ def _artifacts(records: list[dict], arm_id: str) -> dict | None:
         }
         if row.get("bound_s") is not None:
             item["bound_s"] = row["bound_s"]
+        if row.get("call_ids"):
+            item["call_ids"] = row["call_ids"]
         if row.get("cpu") is not None:
             item["cpu"] = row["cpu"]
         if row.get("sample"):
@@ -2095,6 +2109,7 @@ def run_spec(
     quarantine: Path | None = None,
     pairs: list[str] | None = None,
     models: list[str] | None = None,
+    trace: str = "off",
 ) -> list[dict]:
     """Run a committed spec. Every refusal lands before device contact.
 
@@ -2118,6 +2133,10 @@ def run_spec(
         if spec.get("procedure") != "fill-card":
             raise RunnerError("--models is for a fill-card spec")
         _chosen, recorded_models = resolve_models(spec, models)
+    if trace != "off" and (spec.get("id") == "E4b" or spec.get("procedure") == "fill-card"):
+        # Stage 0 of the interlock-relay design wires the interleaved path first. A trace that would silently
+        # record nothing is refused instead.
+        raise RunnerError(f"REFUSED: --trace {trace} is wired for interleaved specs only; run this spec with --trace off")
     if spec.get("id") == "E4b":
         from interlock.harness.e4b import run_from_cli
 
@@ -2200,22 +2219,31 @@ def run_spec(
             probe = _card_probe(adapters, spec)
             path = heartbeat_path(heartbeat)
             _card_guards(probe, path, wall())
-        return run_interleaved(
-            adapters,
-            grant=grant,
-            npu_session=npu_session,
-            cpu_window=cpu_window,
-            root=root,
-            repo=root,
-            spec_path=spec_path,
-            run_id=name,
-            date=stamp,
-            notes=notes,
-            wall=wall,
-            watch=watch,
-            marker=marker,
-            supervisor=supervisor,
-        )
+        from interlock.calltrace import Tracer, instrument, release
+
+        tracer = Tracer(root=root, run_id=name, mode=trace)
+        with tracer:
+            instrument(adapters, tracer)
+            try:
+                return run_interleaved(
+                    adapters,
+                    grant=grant,
+                    npu_session=npu_session,
+                    cpu_window=cpu_window,
+                    root=root,
+                    repo=root,
+                    spec_path=spec_path,
+                    run_id=name,
+                    date=stamp,
+                    notes=notes,
+                    wall=wall,
+                    watch=watch,
+                    marker=marker,
+                    supervisor=supervisor,
+                    tracer=tracer,
+                )
+            finally:
+                release(adapters)
     finally:
         if not marker.entered:
             marker.discard()
diff --git a/src/interlock/relay_sink.py b/src/interlock/relay_sink.py
new file mode 100644
index 0000000..2443685
--- /dev/null
+++ b/src/interlock/relay_sink.py
@@ -0,0 +1,118 @@
+"""NeMo Relay as the ordered call log (``--trace relay``). Imported only on that path.
+
+Relay is driven through its Python API on a private event loop: an
+observability plugin with one ATOF file sink and nothing else, one run scope,
+and one ``llm.call``/``llm.call_end`` span per model call. Every timestamp is
+interlock's own, so spans and the run scope share one clock. Payload
+sanitizers replace prompts and responses with their byte lengths. Token counts
+go in the span's metadata, which the ATOF file keeps.
+
+The sink refuses to start if Relay would layer in any configuration file
+(user or system ``plugins.toml``), so the only sink is the one named here.
+"""
+
+from __future__ import annotations
+
+import asyncio
+import json
+from datetime import datetime, timezone
+from pathlib import Path
+
+from interlock.calltrace import CallRecord, TraceError
+
+
+def _when(t_ns: int) -> datetime:
+    return datetime.fromtimestamp(t_ns / 1e9, tz=timezone.utc)
+
+
+def _length_only(payload, _context=None) -> dict:
+    return {"bytes": len(json.dumps(payload, default=str))}
+
+
+def _request_length_only(request, _context=None):
+    """Relay's request sanitizer must hand back an ``LLMRequest``: one whose content is only its byte length."""
+
+    import nemo_relay
+
+    content = getattr(request, "content", request)
+    return nemo_relay.LLMRequest({}, _length_only(content))
+
+
+_REQUEST = "interlock-length-only-request"
+_RESPONSE = "interlock-length-only-response"
+
+
+class RelaySink:
+    def __init__(self, logs: Path, filename: str, start_ns: int, run_id: str):
+        import nemo_relay
+        from nemo_relay import guardrails, plugin, scope
+
+        self._relay = nemo_relay
+        self._scope = scope
+        config = {
+            "version": 1,
+            "components": [{
+                "kind": "observability",
+                "enabled": True,
+                "config": {
+                    "version": 4,
+                    "enable_full_payloads": False,
+                    "atof": {"enabled": True, "sinks": [
+                        {"type": "file", "output_directory": str(logs), "filename": filename, "mode": "overwrite"}
+                    ]},
+                },
+            }],
+        }
+        report = plugin.validate(config)
+        if report.get("config_paths"):
+            raise TraceError("REFUSED: Relay would layer in other plugins.toml files; remove them before tracing")
+        self._loop = asyncio.new_event_loop()
+        self._activation = self._loop.run_until_complete(plugin.initialize(config))
+        self._guardrails = guardrails
+        guardrails.register_llm_sanitize_request(_REQUEST, 0, _request_length_only)
+        guardrails.register_llm_sanitize_response(_RESPONSE, 0, _length_only)
+        self._run = scope.push(f"interlock-run {run_id}", scope.ScopeType.Agent, timestamp=_when(start_ns))
+        self.scope_id = self._run.uuid
+        self._spans: dict[int, object] = {}
+
+    def start(self, record: CallRecord) -> None:
+        request = self._relay.LLMRequest({}, {"bytes": record.request_bytes})
+        handle = self._relay.llm.call(
+            "ollama" if record.endpoint.startswith("/api/") else "openvino",
+            request,
+            handle=self._run,
+            model_name=record.model,
+            metadata={"call_id": record.call_id, "kind": record.kind, "endpoint": record.endpoint,
+                      "device": record.device, "thread": record.thread, **record.extra},
+            timestamp=_when(record.start_ns),
+        )
+        self._spans[record.call_id] = handle
+
+    def end(self, record: CallRecord) -> None:
+        handle = self._spans.pop(record.call_id, None)
+        if handle is None:
+            return
+        self._relay.llm.call_end(
+            handle,
+            {"status": record.status},
+            # extra carries what is only known at the end, such as an OpenVINO timeout's worker_still_running.
+            metadata={**record.extra, "call_id": record.call_id, "status": record.status, "ms": record.ms,
+                      "prompt_tokens": record.prompt_tokens, "completion_tokens": record.completion_tokens},
+            timestamp=_when(record.end_ns),
+        )
+
+    def mark(self, name: str, t_ns: int, data: dict) -> None:
+        self._scope.event(name, handle=self._run, data=data, timestamp=_when(t_ns))
+
+    def flush(self) -> None:
+        self._relay.subscribers.flush()
+
+    def close(self, end_ns: int | None = None) -> None:
+        try:
+            self._scope.pop(self._run, timestamp=_when(end_ns) if end_ns is not None else None)
+        finally:
+            self._relay.subscribers.flush()
+            self._guardrails.deregister_llm_sanitize_request(_REQUEST)
+            self._guardrails.deregister_llm_sanitize_response(_RESPONSE)
+            self._loop.run_until_complete(self._activation.close())
+            self._loop.close()
```

## interlock tests: tests/test_calltrace.py

```python
"""The call counter and the ordered call log (``--trace``). No device and no Relay: Relay's sink has its own tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from interlock.calltrace import (
    Tracer,
    TraceError,
    classify,
    instrument,
    release,
    traced_transport,
)

URL = "http://127.0.0.1:11434"


@pytest.mark.parametrize(
    ("path", "body", "kind"),
    [
        ("/api/tags", None, "tags"),
        ("/api/ps", None, "ps"),
        ("/api/show", {"model": "m"}, "show"),
        ("/api/generate", {"model": "m", "prompt": "hi"}, "generate"),
        ("/api/generate", {"model": "m", "keep_alive": 0, "prompt": ""}, "unload"),
        ("/api/generate", {"model": "m", "raw": True, "prompt": "x"}, "count"),
        ("/api/generate", {"model": "m", "companion": "start"}, "companion"),
        ("/api/generate", None, "other"),
        ("/api/version", None, "other"),
    ],
)
def test_a_request_is_classified_from_its_endpoint_and_body(path, body, kind):
    assert classify("POST", URL + path, body) == kind


def test_the_counter_is_on_with_tracing_off_and_writes_nothing(tmp_path: Path):
    tracer = Tracer(root=tmp_path, run_id="r", mode="off")
    with tracer:
        tracer.begin_slot(arm="A", index="measure:0:A")
        with tracer.call("generate", "/api/generate", model="m", device="5090") as box:
            box["status"] = "ok"
            box["payload"] = {"prompt_eval_count": 12, "eval_count": 7}
        ids = tracer.end_slot()["call_ids"]
    assert ids == [1]
    art = tracer.artifacts("A")
    assert art["call_counts"]["generate"]["n"] == 1
    assert art["call_counts"]["generate"]["errors"] == 0
    assert "trace" not in art
    assert not (tmp_path / "logs").exists()


def test_the_events_log_writes_one_parsable_line_per_call_and_marks(tmp_path: Path):
    tracer = Tracer(root=tmp_path, run_id="r", mode="events")
    with tracer:
        tracer.begin_slot(arm="A", index="measure:0:A")
        record = tracer.start("count", "/api/generate", model="m", device="5090", request_bytes=40)
        tracer.end(record, "timeout")
        record = tracer.start("generate", "/api/generate", model="m", device="5090")
        tracer.end(record, "ok", {"prompt_eval_count": 3, "eval_count": 2})
        tracer.end_slot()
        tracer.mark("stop_file", reason="test")
        tracer.flush()
    lines = [json.loads(line) for line in (tmp_path / "logs" / "r.events.jsonl").read_text(encoding="utf-8").splitlines()]
    calls = [line for line in lines if "call_id" in line]
    assert [c["kind"] for c in calls] == ["count", "generate"]
    assert calls[0]["status"] == "timeout"
    assert calls[1]["completion_tokens"] == 2
    assert calls[0]["arm"] == "A"
    assert any(line.get("mark") == "stop_file" for line in lines)
    art = tracer.artifacts("A")
    assert art["trace"] == {"file": "logs/r.events.jsonl"}
    assert art["call_counts"]["count"]["timeouts"] == 1


def test_a_call_left_open_is_closed_as_abandoned(tmp_path: Path):
    tracer = Tracer(root=tmp_path, run_id="r", mode="events")
    with tracer:
        tracer.start("generate", "/api/generate", model="m", device="CPU")
    line = json.loads((tmp_path / "logs" / "r.events.jsonl").read_text(encoding="utf-8"))
    assert line["status"] == "abandoned"
    assert tracer.artifacts("_run")["call_counts"]["generate"]["errors"] == 1


def test_a_call_ended_twice_is_counted_once(tmp_path: Path):
    tracer = Tracer(root=tmp_path, run_id="r")
    with tracer:
        record = tracer.start("tags", "/api/tags", model=None, device=None)
        tracer.end(record, "ok")
        tracer.end(record, "ok")
    assert tracer.counts_for("_run")["tags"]["n"] == 1


def test_an_otel_variable_refuses_tracing(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://example.invalid")
    with pytest.raises(TraceError, match="OTEL_"):
        Tracer(root=tmp_path, run_id="r", mode="events").open()
    Tracer(root=tmp_path, run_id="r", mode="off").open().close()  # the counter alone is allowed


def test_an_unknown_mode_is_refused(tmp_path: Path):
    with pytest.raises(TraceError, match="unknown trace mode"):
        Tracer(root=tmp_path, run_id="r", mode="loud")


def test_the_relay_mode_uses_the_factory_it_is_given(tmp_path: Path):
    made = []

    class Sink:
        scope_id = "scope-1"

        def __init__(self, logs, name, start_ns, run_id):
            made.append((logs, name, run_id))
            self.events = []

        def start(self, record):
            self.events.append(("start", record.call_id))

        def end(self, record):
            self.events.append(("end", record.call_id))

        def mark(self, name, t_ns, data):
            self.events.append(("mark", name))

        def flush(self):
            self.events.append(("flush",))

        def close(self, end_ns=None):
            self.events.append(("close",))

    tracer = Tracer(root=tmp_path, run_id="r", mode="relay", relay_factory=Sink)
    with tracer:
        sink = tracer._sink
        with tracer.call("generate", "/api/generate", model="m", device="5090") as box:
            box["status"] = "ok"
        tracer.mark("grant")
        tracer.flush()
    assert made == [(tmp_path / "logs", "r.atof.jsonl", "r")]
    assert sink.events == [("start", 1), ("end", 1), ("mark", "grant"), ("flush",), ("close",)]
    assert tracer.artifacts("_run")["trace"] == {"file": "logs/r.atof.jsonl", "span": "scope-1"}


def test_the_traced_transport_records_ok_timeout_and_error(tmp_path: Path):
    def transport(method, url, body, **kwargs):
        if body and body.get("prompt") == "slow":
            raise TimeoutError("timed out")
        if body and body.get("prompt") == "bad":
            raise RuntimeError("HTTP 500")
        return {"eval_count": 4, "prompt_eval_count": 9}

    tracer = Tracer(root=tmp_path, run_id="r")
    with tracer:
        wrapped = traced_transport(transport, tracer, device="5090")
        assert wrapped.__wrapped__ is transport
        assert wrapped("POST", URL + "/api/generate", {"model": "m", "prompt": "ok"})["eval_count"] == 4
        with pytest.raises(TimeoutError):
            wrapped("POST", URL + "/api/generate", {"model": "m", "prompt": "slow"})
        with pytest.raises(RuntimeError):
            wrapped("POST", URL + "/api/generate", {"model": "m", "prompt": "bad"})
    counts = tracer.counts_for("_run")["generate"]
    assert (counts["n"], counts["timeouts"], counts["errors"]) == (3, 1, 1)


class _Ollama:
    def __init__(self):
        self.device = "5090"
        self.transport = lambda method, url, body=None: {"ok": True}


def test_instrument_wraps_ollama_once_and_sets_the_openvino_tracer(tmp_path: Path):
    from interlock.adapters import openvino

    tracer = Tracer(root=tmp_path, run_id="r")
    adapter = _Ollama()
    adapters = {"ollama": adapter, "openvino": object()}
    instrument(adapters, tracer)
    first = adapter.transport
    instrument(adapters, tracer)
    assert adapter.transport is first  # not wrapped twice
    assert openvino._TRACER is tracer
    release(adapters)
    assert openvino._TRACER is None
```

## interlock tests: tests/test_relay_stage0.py

```python
"""Stage 0 of the interlock-relay design, on fakes: H1 (complete capture) and H3 (safe with interlock's rules).

The Ollama ground truth is the fake transport's own request log, below the hook. The Relay tests need the
``relay`` extra and skip without it; the native event log runs everywhere.
"""

from __future__ import annotations

import json
import os
import socket
from pathlib import Path

import pytest

from interlock.adapters.ollama import OllamaAdapter
from interlock.calltrace import Tracer, TraceError, instrument, release

CANARY = "AMU_CANARY_PROMPT_7c1e"
MODES = ["events", pytest.param("relay", marks=pytest.mark.relay)]


def _need(mode):
    if mode == "relay":
        pytest.importorskip("nemo_relay")


class Recorder:
    """A fake Ollama transport that logs every request it receives: the ground truth for H1."""

    def __init__(self, timeouts=0):
        self.log = []
        self.timeouts = timeouts

    def __call__(self, method, url, body=None, **kwargs):
        self.log.append((url.rsplit("/api/", 1)[-1], dict(body or {})))
        if body and body.get("raw") and self.timeouts:
            self.timeouts -= 1
            raise TimeoutError("timed out")
        return {"response": CANARY + " reply", "prompt_eval_count": 9, "eval_count": 1}


def _trace_calls(tmp_path: Path, mode: str, run_id: str) -> list[dict]:
    if mode == "events":
        lines = (tmp_path / "logs" / f"{run_id}.events.jsonl").read_text(encoding="utf-8").splitlines()
        return [json.loads(x) for x in lines if "call_id" in json.loads(x)]
    calls = {}
    for line in (tmp_path / "logs" / f"{run_id}.atof.jsonl").read_text(encoding="utf-8").splitlines():
        event = json.loads(line)
        if event.get("category") == "llm":
            calls.setdefault(event["uuid"], {}).update(event.get("metadata") or {})
            calls[event["uuid"]][event["scope_category"]] = True
    return list(calls.values())


@pytest.mark.parametrize("mode", MODES)
def test_h1_every_request_the_fake_received_is_in_the_trace_once(tmp_path: Path, mode):
    _need(mode)
    fake = Recorder(timeouts=1)
    adapter = OllamaAdapter(transport=fake)
    tracer = Tracer(root=tmp_path, run_id="h1", mode=mode)
    with tracer:
        instrument({"ollama": adapter}, tracer)
        tracer.begin_slot(arm="B", index="measure:0:B")
        with pytest.raises(Exception):
            adapter.count_tokens("qwen3:8b", CANARY)
        assert adapter.count_tokens("qwen3:8b", CANARY) == 9
        adapter.transport("POST", "http://127.0.0.1:11434/api/generate", {"model": "qwen3:8b", "prompt": CANARY})
        adapter.unload("qwen3:8b")
        tracer.end_slot()
        release({"ollama": adapter})
    calls = _trace_calls(tmp_path, mode, "h1")
    assert len(calls) == len(fake.log) == 4
    assert [c["kind"] for c in sorted(calls, key=lambda c: c["call_id"])] == ["count", "count", "generate", "unload"]
    statuses = sorted(c["status"] for c in calls)
    assert statuses == ["ok", "ok", "ok", "timeout"]
    if mode == "relay":
        assert all(c.get("start") and c.get("end") for c in calls)  # no unclosed span


@pytest.mark.parametrize("mode", MODES)
def test_h3_the_trace_holds_no_prompt_host_user_or_home(tmp_path: Path, mode):
    _need(mode)
    adapter = OllamaAdapter(transport=Recorder())
    tracer = Tracer(root=tmp_path, run_id="h3", mode=mode)
    with tracer:
        instrument({"ollama": adapter}, tracer)
        adapter.transport("POST", "http://127.0.0.1:11434/api/generate", {"model": "m", "prompt": CANARY})
        tracer.mark("grant", grant="g")
    text = next((tmp_path / "logs").glob("h3.*")).read_text(encoding="utf-8")
    assert CANARY not in text
    for needle in (socket.gethostname(), os.environ.get("USERNAME") or os.environ.get("USER"), str(Path.home())):
        if needle:
            assert needle.lower() not in text.lower()


@pytest.mark.parametrize("mode", MODES)
def test_h3_an_interrupted_run_leaves_a_closed_parsable_trace(tmp_path: Path, mode):
    _need(mode)
    tracer = Tracer(root=tmp_path, run_id="stop", mode=mode)
    with pytest.raises(KeyboardInterrupt):
        with tracer:
            done = tracer.start("generate", "/api/generate", model="m", device="5090")
            tracer.end(done, "ok")
            tracer.start("generate", "/api/generate", model="m", device="5090")  # in flight at the stop
            tracer.mark("stop_file")
            raise KeyboardInterrupt
    lines = [json.loads(x) for x in next((tmp_path / "logs").glob("stop.*")).read_text(encoding="utf-8").splitlines()]
    if mode == "events":
        assert [x["status"] for x in lines if "call_id" in x] == ["ok", "abandoned"]
    else:
        llm = [x for x in lines if x.get("category") == "llm"]
        assert sum(x["scope_category"] == "start" for x in llm) == sum(x["scope_category"] == "end" for x in llm) == 2
        assert [x["scope_category"] for x in lines if x.get("category") == "agent"] == ["start", "end"]


@pytest.mark.parametrize("mode", MODES)
def test_h3_tracing_opens_no_socket(tmp_path: Path, mode, monkeypatch):
    _need(mode)
    opened = []
    real = socket.socket

    # On Windows, asyncio's event loop makes its self-pipe from a loopback socket pair (127.0.0.1, port 0). That is
    # Python's, not Relay's, and never leaves the machine. Anything else is refused.
    def loopback(address):
        return isinstance(address, tuple) and address[0] in ("127.0.0.1", "::1")

    class Guard(real):
        def connect(self, address):
            opened.append(("connect", address))
            if not loopback(address):
                raise AssertionError(f"connect to {address}")
            return super().connect(address)

        def bind(self, address):
            opened.append(("bind", address))
            if not (loopback(address) and address[1] == 0):
                raise AssertionError(f"bind to {address}")
            return super().bind(address)

    monkeypatch.setattr(socket, "socket", Guard)
    tracer = Tracer(root=tmp_path, run_id="net", mode=mode)
    with tracer:
        record = tracer.start("tags", "/api/tags", model=None, device=None)
        tracer.end(record, "ok")
        tracer.flush()
    assert all(loopback(address) for _, address in opened)
    if mode == "events":
        assert opened == []


@pytest.mark.relay
def test_the_relay_sink_refuses_layered_plugin_configs(tmp_path: Path, monkeypatch):
    pytest.importorskip("nemo_relay")
    from nemo_relay import plugin

    from interlock import relay_sink

    monkeypatch.setattr(plugin, "validate", lambda config: {"config_paths": ["elsewhere/plugins.toml"]})
    with pytest.raises(TraceError, match="plugins.toml"):
        relay_sink.RelaySink(tmp_path, "x.atof.jsonl", 0, "r")


def test_otel_refuses_before_the_sink_opens(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("OTEL_SERVICE_NAME", "x")
    with pytest.raises(TraceError):
        Tracer(root=tmp_path, run_id="o", mode="relay", relay_factory=lambda *a: pytest.fail("sink opened")).open()


@pytest.mark.parametrize("mode", ["off", *MODES])
def test_a_traced_run_writes_receipts_check_accepts(tmp_path: Path, mode):
    _need(mode if isinstance(mode, str) else "relay")
    from interlock.harness.runner import run_spec
    from interlock.receipt import check_tree, load_jsonl
    from tests.test_run_path import Fake, _arm, _bind, _result, _spec

    repo = tmp_path / "repo"
    spec_path = _bind(repo, _spec([_arm("A", "CPU")]))
    rows = run_spec(spec_path, root=repo, adapters={"fake": Fake({"A": [_result(10), _result(11), _result(12)]})},
                    date="2026-10-10", trace=mode)
    assert len(rows) == 1
    assert check_tree(repo) == []
    row = load_jsonl(repo / "receipts" / "t-2026-10-10.jsonl")[0]
    assert "call_counts" in row["artifacts"]
    if mode == "off":
        assert "trace" not in row["artifacts"]
    else:
        suffix = "atof" if mode == "relay" else "events"
        assert row["artifacts"]["trace"]["file"] == f"logs/t-2026-10-10.{suffix}.jsonl"
        assert (repo / row["artifacts"]["trace"]["file"]).is_file()


def test_trace_is_refused_where_it_is_not_wired(tmp_path: Path):
    from interlock.harness.runner import RunnerError, run_spec
    from tests.test_run_path import E5

    # The committed fill-card spec: the refusal comes before any adapter, card probe or run marker.
    with pytest.raises(RunnerError, match="interleaved specs only"):
        run_spec(E5, root=tmp_path, adapters={}, date="2026-10-10", trace="events")
    assert not (tmp_path / "receipts").exists()
```

## The evaluation, frozen before the first run: diagnose.py

```python
"""Stage 0 of the interlock-relay design: the readers and the five pre-registered questions (H4a, H4b).

Frozen before any planted case runs. Nothing here imports interlock or Relay: it reads files and receipt rows.

- `read_studio_trace(path)`: one schema-aware reader for ATOF files, with no branch on which tool wrote the file.
  It returns every scope as a normalised record. The fields H4b compares are
  `(span_id, parent_id, start_ns, end_ns, model, prompt_tokens, completion_tokens, status)`; the record also keeps
  the scope's category, name and metadata, which the questions read.
- `read_events(path)`: the native event log (`logs/<run_id>.events.jsonl`), as the same call records.
- `diagnose_from_trace(path)` and `diagnose_from_events(path)`: the five answers from an ordered log.
- `diagnose_from_receipt(row)`: the five answers from `artifacts.call_counts` alone. It answers by elimination
  wherever the counts rule out one of a question's two options, so the aggregate counter gets its best fair score.

Every answer is a string from the question's options, or CANT.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

CANT = "can't tell"
QUESTIONS = ("q1_count_growth", "q2_companion", "q3_unload_order", "q4_count_timeout", "q5_openvino_runaway")
NORMALISED = ("span_id", "parent_id", "start_ns", "end_ns", "model", "prompt_tokens", "completion_tokens", "status")


# -- readers ------------------------------------------------------------------------------------------------------


def _ns(stamp: str) -> int:
    """An ATOF timestamp (RFC 3339, with up to nine fraction digits) as integer nanoseconds since the epoch."""

    stamp = stamp.replace("Z", "+00:00")
    head, _, rest = stamp.partition(".")
    fraction, zone = (rest[:-6], rest[-6:]) if rest else ("", stamp[-6:])
    if not rest:
        head = stamp[:-6]
    whole = datetime.fromisoformat(head + zone)
    nanos = int((fraction + "000000000")[:9]) if fraction else 0
    return int(whole.timestamp()) * 1_000_000_000 + nanos


def _usage(*places) -> tuple[int | None, int | None]:
    for place in places:
        if not isinstance(place, dict):
            continue
        usage = place.get("usage") if isinstance(place.get("usage"), dict) else place
        prompt = usage.get("prompt_tokens", usage.get("input_tokens"))
        completion = usage.get("completion_tokens", usage.get("output_tokens"))
        if isinstance(prompt, int) or isinstance(completion, int):
            return (prompt if isinstance(prompt, int) else None, completion if isinstance(completion, int) else None)
    return None, None


def _status(metadata: dict, end: dict) -> str | None:
    if isinstance(metadata.get("status"), str):
        return metadata["status"]
    code = metadata.get("otel.status_code")
    if code == "OK":
        return "ok"
    if code == "ERROR":
        return "error"
    return None


def read_studio_trace(path: Path) -> list[dict]:
    """Every ATOF scope in the file, start and end paired by uuid, in start order. Marks are kept as zero-length
    records with category "mark"."""

    starts: dict[str, dict] = {}
    ends: dict[str, dict] = {}
    marks: list[dict] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        if event.get("kind") == "mark":
            marks.append(event)
        elif event.get("kind") == "scope":
            (starts if event.get("scope_category") == "start" else ends)[event["uuid"]] = event
    records = []
    for uuid, start in starts.items():
        end = ends.get(uuid, {})
        metadata = {**(start.get("metadata") or {}), **(end.get("metadata") or {})}
        prompt, completion = _usage(metadata, end.get("data"), (end.get("data") or {}).get("annotated_response")
                                    if isinstance(end.get("data"), dict) else None)
        records.append({
            "span_id": uuid,
            "parent_id": start.get("parent_uuid"),
            "start_ns": _ns(start["timestamp"]),
            "end_ns": _ns(end["timestamp"]) if end else None,
            "model": (start.get("category_profile") or {}).get("model_name"),
            "prompt_tokens": prompt,
            "completion_tokens": completion,
            "status": _status(metadata, end) if end else "open",
            "category": start.get("category"),
            "name": start.get("name"),
            "metadata": metadata,
        })
    for mark in marks:
        t = _ns(mark["timestamp"])
        records.append({"span_id": mark["uuid"], "parent_id": mark.get("parent_uuid"), "start_ns": t, "end_ns": t,
                        "model": None, "prompt_tokens": None, "completion_tokens": None, "status": None,
                        "category": "mark", "name": mark.get("name"), "metadata": mark.get("data") or {}})
    return sorted(records, key=lambda r: (r["start_ns"], r["span_id"]))


def normalised(records: list[dict]) -> list[tuple]:
    """The H4b comparison set: the eight fields of every model-call record."""

    return [tuple(r[f] for f in NORMALISED) for r in records if r["category"] == "llm"]


def _call(kind, slot, start_ns, end_ns, status, extra) -> dict:
    return {"kind": kind, "slot": slot, "endpoint": extra.get("endpoint"), "start_ns": start_ns, "end_ns": end_ns,
            "status": status,
            "ms": None if end_ns is None else (end_ns - start_ns) / 1e6,
            "worker_still_running": bool(extra.get("worker_still_running"))}


def calls_from_trace(records: list[dict]) -> list[dict]:
    return [_call(r["metadata"].get("kind"), r["metadata"].get("slot"), r["start_ns"], r["end_ns"], r["status"],
                  r["metadata"]) for r in records if r["category"] == "llm"]


def read_events(path: Path) -> list[dict]:
    calls = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        if "call_id" in event:
            calls.append(_call(event.get("kind"), event.get("slot"), event["t_ns"], event.get("end_ns"),
                               event.get("status"), event))
    return sorted(calls, key=lambda c: c["start_ns"])


# -- the five questions, from an ordered log ---------------------------------------------------------------------


def _q1(calls):
    """Did count-call latency grow monotonically across the steps of the slot?"""

    ms = [c["ms"] for c in calls if c["kind"] == "count" and c["ms"] is not None]
    if len(ms) < 2:
        return CANT
    return "grew" if all(b > a for a, b in zip(ms, ms[1:])) else "did not grow"


def _q2(calls):
    """Did the companion call overlap the generate call in wall-clock time, or finish before it started?"""

    comp = [c for c in calls if c["kind"] == "companion" and c["end_ns"] is not None]
    gen = [c for c in calls if c["kind"] == "generate" and c["end_ns"] is not None]
    if len(comp) != 1 or len(gen) != 1:
        return CANT
    a, b = comp[0], gen[0]
    if a["end_ns"] <= b["start_ns"]:
        return "finished before"
    if a["start_ns"] < b["end_ns"] and b["start_ns"] < a["end_ns"]:
        return "overlapped"
    return CANT


def _q3(calls):
    """What was the order: unload, generate, unload; or unload, companion?"""

    seq = [c["kind"] for c in calls if c["kind"] in ("unload", "generate", "companion")]
    if seq[:3] == ["unload", "generate", "unload"]:
        return "unload-generate-unload"
    if seq[:2] == ["unload", "companion"]:
        return "unload-companion"
    return CANT


def _q4(calls):
    """Was the timed-out count retried and successful before the main generate call, or did it fail after it?"""

    gen = [c for c in calls if c["kind"] == "generate"]
    counts = [c for c in calls if c["kind"] == "count"]
    timeouts = [c for c in counts if c["status"] == "timeout"]
    if not gen or not timeouts:
        return CANT
    g = gen[0]["start_ns"]
    t = timeouts[0]
    if t["end_ns"] <= g and any(c["status"] == "ok" and c["start_ns"] >= t["end_ns"] and c["end_ns"] <= g
                                for c in counts):
        return "retried and succeeded before"
    if t["start_ns"] >= gen[0]["end_ns"] and not any(c["status"] == "ok" and c["start_ns"] > t["start_ns"]
                                                     for c in counts):
        return "failed after"
    return CANT


def _q5(calls):
    """Which call in a multi-call OpenVINO slot left its worker running, and did later calls run while it was?"""

    ov = [c for c in calls if str(c.get("endpoint") or "").startswith("openvino/")]
    if len(ov) < 2:
        return CANT
    stuck = [i for i, c in enumerate(ov) if c["worker_still_running"]]
    if len(stuck) != 1:
        return CANT
    i = stuck[0]
    later = any(c["start_ns"] >= ov[i]["end_ns"] for c in ov[i + 1:])
    return f"call {i + 1}; later calls ran: {'yes' if later else 'no'}"


def diagnose_calls(calls: list[dict]) -> dict:
    return dict(zip(QUESTIONS, (_q1(calls), _q2(calls), _q3(calls), _q4(calls), _q5(calls))))


def diagnose_from_trace(path: Path) -> dict:
    return diagnose_calls(calls_from_trace(read_studio_trace(path)))


def diagnose_from_events(path: Path) -> dict:
    return diagnose_calls(read_events(path))


# -- the same questions, from the aggregate counter ---------------------------------------------------------------


def diagnose_from_receipt(row: dict) -> dict:
    counts = (row.get("artifacts") or {}).get("call_counts") or {}

    def n(kind, key="n"):
        return (counts.get(kind) or {}).get(key, 0)

    out = dict.fromkeys(QUESTIONS, CANT)
    # Q1 and Q2 need per-call times and wall-clock order: a per-kind sum has neither.
    # Q3: answer only when the counts make one of the two orders impossible.
    a = n("unload") >= 2 and n("generate") >= 1
    b = n("unload") >= 1 and n("companion") >= 1
    if a != b:
        out["q3_unload_order"] = "unload-generate-unload" if a else "unload-companion"
    # Q4: with no successful count, "retried and succeeded" is impossible.
    if n("count", "timeouts") >= 1 and n("generate") >= 1:
        succeeded = n("count") - n("count", "timeouts") - n("count", "errors")
        if succeeded == 0:
            out["q4_count_timeout"] = "failed after"
    # Q5: which of several calls, and what ran after it, is order the counter does not keep.
    return out
```

## The planted cases, key and cost measurement: cases.py

```python
"""Stage 0 of the interlock-relay design: the five planted cases, their key, and the H4b cost measurements.

Run with interlock's environment (base plus the `relay` extra) on the path:

    uv run --project <interlock checkout> python cases.py <out-dir>

Each case drives interlock's own hook points (`traced_transport` for Ollama, `_timed_call` for OpenVINO) over fakes,
once with the native event log and once with Relay. No device, no network, no model. The key below is the planted
truth, fixed before the first run, and `diagnose.py` is frozen in the same commit.
"""

from __future__ import annotations

import json
import statistics
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from diagnose import (  # noqa: E402
    CANT,
    QUESTIONS,
    diagnose_from_events,
    diagnose_from_receipt,
    diagnose_from_trace,
    normalised,
    read_studio_trace,
)

URL = "http://127.0.0.1:11434"
CANARY = "AMU_CANARY_PROMPT_7c1e"

# The planted truth: one case per question.
KEY = {
    "q1_count_growth": "grew",
    "q2_companion": "overlapped",
    "q3_unload_order": "unload-generate-unload",
    "q4_count_timeout": "retried and succeeded before",
    "q5_openvino_runaway": "call 2; later calls ran: yes",
}


def _fake(delays: dict):
    """An Ollama transport whose reply time depends on the request: a list of delays per kind, consumed in order."""

    from interlock.calltrace import classify

    lock = threading.Lock()

    def transport(method, url, body=None, **kwargs):
        kind = classify(method, url, body)
        with lock:
            delay = delays[kind].pop(0)
        if delay == "timeout":
            time.sleep(0.005)
            raise TimeoutError("timed out")
        time.sleep(delay)
        return {"response": CANARY + " reply", "prompt_eval_count": 11, "eval_count": 5}

    return transport


def _gen(prompt="go"):
    return ("POST", URL + "/api/generate", {"model": "m", "prompt": CANARY + " " + prompt})


COUNT = ("POST", URL + "/api/generate", {"model": "m", "raw": True, "prompt": CANARY})
UNLOAD = ("POST", URL + "/api/generate", {"model": "m", "keep_alive": 0, "prompt": ""})
COMPANION = ("POST", URL + "/api/generate", {"model": "c", "companion": "start"})


def case_q1(call, ov):
    for _ in range(4):
        call(*COUNT)
    call(*_gen())


def case_q2(call, ov):
    side = threading.Thread(target=lambda: call(*COMPANION), name="companion")
    side.start()
    time.sleep(0.005)
    call(*_gen())
    side.join()


def case_q3(call, ov):
    call(*UNLOAD)
    call(*_gen())
    call(*UNLOAD)


def case_q4(call, ov):
    try:
        call(*COUNT)
    except TimeoutError:
        pass
    call(*COUNT)
    call(*_gen())


def case_q5(call, ov):
    ov(lambda: time.sleep(0.002), 1.0)
    ov(lambda: time.sleep(2.0), 0.05)  # the worker outlives its bound
    ov(lambda: time.sleep(0.002), 1.0)


CASES = {
    "q1_count_growth": (case_q1, {"count": [0.002, 0.004, 0.006, 0.008], "generate": [0.003]}),
    "q2_companion": (case_q2, {"companion": [0.030], "generate": [0.010]}),
    "q3_unload_order": (case_q3, {"unload": [0.001, 0.001], "generate": [0.003]}),
    "q4_count_timeout": (case_q4, {"count": ["timeout", 0.002], "generate": [0.003]}),
    "q5_openvino_runaway": (case_q5, {}),
}


def run_case(name: str, mode: str, out: Path) -> dict:
    from interlock.adapters import openvino
    from interlock.calltrace import Tracer, traced_transport

    body, delays = CASES[name]
    run_id = f"{name}-{mode}"
    tracer = Tracer(root=out, run_id=run_id, mode=mode)
    with tracer:
        call = traced_transport(_fake({k: list(v) for k, v in delays.items()}), tracer, device="5090")
        openvino.set_tracer(tracer)
        try:
            def ov(fn, bound):
                return openvino._timed_call(fn, bound, kind="generate", model="ov-m", device="NPU")

            tracer.begin_slot(arm="A", index="measure:0:A")
            body(call, ov)
            tracer.end_slot()
        finally:
            openvino.set_tracer(None)
    row = {"id": f"T/A/{run_id}", "artifacts": tracer.artifacts("A")}
    path = out / "logs" / f"{run_id}.{'atof' if mode == 'relay' else 'events'}.jsonl"
    return {"row": row, "path": path}


def h4(out: Path) -> dict:
    result: dict = {"key": KEY, "cases": {}}
    for name in CASES:
        events = run_case(name, "events", out)
        relay = run_case(name, "relay", out)
        result["cases"][name] = {
            "from_receipt": diagnose_from_receipt(events["row"])[name],
            "from_events": diagnose_from_events(events["path"])[name],
            "from_relay": diagnose_from_trace(relay["path"])[name],
            "call_counts": events["row"]["artifacts"]["call_counts"],
        }
    for source in ("from_receipt", "from_events", "from_relay"):
        result[f"{source}_correct"] = sum(result["cases"][q][source] == KEY[q] for q in QUESTIONS)
    result["h4a_holds"] = result["from_relay_correct"] == 5 and result["from_receipt_correct"] <= 2
    result["information_parity"] = result["from_relay_correct"] >= result["from_events_correct"]
    return result


def shared_reader(out: Path) -> dict:
    """The H4b shared-reader test: one reader, interlock's trace and another Relay producer's, the same fields."""

    ours = read_studio_trace(out / "logs" / "q1_count_growth-relay.atof.jsonl")
    theirs = read_studio_trace(HERE / "fixtures" / "claude-code-wrapper.atof.jsonl")
    a, b = normalised(ours), normalised(theirs)

    def filled(rows):
        return {f: sum(r[i] is not None for r in rows) for i, f in enumerate(
            ("span_id", "parent_id", "start_ns", "end_ns", "model", "prompt_tokens", "completion_tokens", "status"))}

    return {"interlock_calls": len(a), "fixture_calls": len(b), "interlock_filled": filled(a), "fixture_filled": filled(b)}


def safety(out: Path) -> dict:
    import os
    import socket

    text = "\n".join(p.read_text(encoding="utf-8") for p in (out / "logs").glob("*.jsonl"))
    needles = {"host": socket.gethostname(), "user": os.environ.get("USERNAME") or os.environ.get("USER") or "",
               "home": str(Path.home())}
    for line in text.splitlines():
        if line.strip():  # the join puts an empty line between files
            json.loads(line)  # every line parses
    return {"canary": text.count(CANARY), **{k: (v.lower() in text.lower()) if v else None for k, v in needles.items()}}


def cost(out: Path, n: int = 2000) -> dict:
    """Bytes per call, and client time per call: bare transport, counter only (off), native log, and Relay,
    interleaved in rounds of 100."""

    from interlock.calltrace import Tracer, traced_transport

    def bare(method, url, body=None, **kwargs):
        return {"eval_count": 1, "prompt_eval_count": 1}

    times: dict[str, list[int]] = {"bare": [], "off": [], "events": [], "relay": []}
    tracers = {m: Tracer(root=out, run_id=f"cost-{m}", mode=m).open() for m in ("off", "events", "relay")}
    calls = {"bare": bare, **{m: traced_transport(bare, t, device="5090") for m, t in tracers.items()}}
    req = _gen()
    try:
        for _ in range(n // 100):
            for mode, fn in calls.items():
                for _ in range(100):
                    t0 = time.perf_counter_ns()
                    fn(*req)
                    times[mode].append(time.perf_counter_ns() - t0)
    finally:
        for t in tracers.values():
            t.close()

    def q(xs, p):
        xs = sorted(xs)
        return xs[min(len(xs) - 1, int(p * len(xs)))]

    ms = {m: {"median": statistics.median(v) / 1e6, "p99": q(v, 0.99) / 1e6} for m, v in times.items()}
    base = ms["off"]["median"]
    added = {m: {"median": ms[m]["median"] - base, "p99": ms[m]["p99"] - base} for m in ("events", "relay")}
    sizes = {m: (out / "logs" / f"cost-{m}.{'atof' if m == 'relay' else 'events'}.jsonl").stat().st_size / n
             for m in ("events", "relay")}
    return {
        "calls": n,
        "per_call_ms": ms,
        "added_over_counter_ms": added,
        "bytes_per_call": sizes,
        "relay_time_gate": added["relay"]["median"] < 0.5 and added["relay"]["p99"] < 2.0,
        "relay_vs_native_median_ms": ms["relay"]["median"] - ms["events"]["median"],
        "relay_byte_gate": sizes["relay"] <= 2048,
    }


def main() -> None:
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    result = {"h4": h4(out)}
    result["shared_reader"] = shared_reader(out)
    result["safety"] = safety(out)
    result["cost"] = cost(out)
    result["cost"]["relay_vs_native_gate"] = result["cost"]["relay_vs_native_median_ms"] < 0.25
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
```

## Run 2 output (abridged to the decision fields)

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
    "median": 0.003,
    "p99": 0.0694
   },
   "relay": {
    "median": 0.0257,
    "p99": 0.08449999999999999
   }
  },
  "bytes_per_call": {
   "events": 257.436,
   "relay": 1130.1955
  },
  "calls": 2000,
  "per_call_ms": {
   "bare": {
    "median": 0.0001,
    "p99": 0.0002
   },
   "events": {
    "median": 0.006,
    "p99": 0.0724
   },
   "off": {
    "median": 0.003,
    "p99": 0.0053
   },
   "relay": {
    "median": 0.0287,
    "p99": 0.0875
   }
  },
  "relay_byte_gate": true,
  "relay_time_gate": true,
  "relay_vs_native_gate": true,
  "relay_vs_native_median_ms": 0.022699999999999998
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
 },
 "shared_reader": {
  "fixture_calls": 7,
  "fixture_filled": {
   "completion_tokens": 0,
   "end_ns": 7,
   "model": 7,
   "parent_id": 7,
   "prompt_tokens": 0,
   "span_id": 7,
   "start_ns": 7,
   "status": 7
  },
  "interlock_calls": 5,
  "interlock_filled": {
   "completion_tokens": 5,
   "end_ns": 5,
   "model": 5,
   "parent_id": 5,
   "prompt_tokens": 5,
   "span_id": 5,
   "start_ns": 5,
   "status": 5
  }
 }
}
```
