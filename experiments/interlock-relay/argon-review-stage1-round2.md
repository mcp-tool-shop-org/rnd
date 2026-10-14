# Review brief for Argon, round 2: the interlock-relay stage 1 harness and analysis

R&D, 2026-10-14. In round 1 you reviewed the stage 1 harness (interlock `4295165`) and the analysis frozen at rnd `43643bc`. You found three blocking issues (B1–B3), two important ones (I1, I2) and a minor one (M1), and confirmed the statistics.

This is the code after R&D acted on them:
- the interlock harness at `b5d9ea1`;
- the analysis re-frozen at rnd `cbaed82`.

No run has happened. Review the changes fresh, then check each round 1 finding. Your findings are advice: R&D decides what to act on and records why.

## What changed, finding by finding

| # | Finding | Disposition |
|---|---|---|
| B1 | `long.yaml` sent no canary, so H3 passed the long step vacuously | **Adopted.** The long prompt's seed carries the canary, and the stop rule says so |
| B2 | Models stay on the card after the stop step (the watcher's `os._exit` skips the unload) and after the import children, so the next preflight refuses | **Adopted, by a restructure.** Every step runs in its own process. Before each step after the first, the driver unloads every model (`keep_alive` 0), waits up to 90 s for an idle card, and runs the preflight. It unloads again at the end. (Interleaved runs already unload at their end; the stop step and the import children didn't.) |
| B3 | A 60 s sleep could outlast the whole decode run, so the stop step would exit 0, and nothing checked that it stopped | **Adopted.** The driver waits until the stop run's trace holds 10 model calls, then writes the stop file. The step passes only on exit 77, `drive()` refuses otherwise, and the analysis's H3 needs the driver's `stopped` record (S1-A5) |
| I1 | The companion arm had no `trace` key, and the plan's 21 GiB companion rule wasn't enforced anywhere | **Adopted, and widened.** `trace: false` on the companion arm. Checking the rule showed interleaved runs have no VRAM ceiling at all; the plan's "abort at 30,500 MiB" was fill-card's. The driver now watches VRAM once a second and stops the step over 30,500 MiB. The 21 GiB rule is gone: the companion step runs at small contexts, below the long step's 13,587 MiB |
| I2 | The barrier check compares spaced calls with back-to-back calls in fresh processes. With a 1% band floor it could fail stage 1 for a reason that has nothing to do with Relay | **Adopted as S1-A6.** The barrier check is reported, not gated. Both arms of every triple take the same barrier, so it can't bias Δ. The check describes the measurement protocol, and it stays in the output beside H2 |
| I3 | B alone computes the request size | **No change.** Argon agrees it's a genuine cost of tracing, charged to B's hook time |
| M1 | A step that didn't run left h2 and h3 entries missing | **Adopted.** "not run" in every section |

**The driver, after the restructure:**
- **Each step is its own process:** `relay_s1.py --child-run <step>` runs the interlock run under the request counter and writes the count.
- **The driver** supervises each step with a VRAM watch. Between steps it unloads the card, waits for it to go idle and re-runs the preflight. It refuses on a stop that didn't stop, a VRAM breach or a non-zero exit, and unloads again at the end.
- **The stop step** waits on the trace (10 model-call spans), not on a clock.

## Two rulings where R&D differed from your fix, which you should check

1. **The barrier check (I2) is now reported, not gated (S1-A6).** You suggested either matching the children's rest or living with the risk. R&D's reasoning:
   - Both arms of every in-process triple take the same barrier, so a barrier-induced shift can't bias Δ.
   - Gating on the barrier check could reject Relay for a property of the measurement protocol.
   - Is that sound, or does it weaken a check the design needs?
2. **B2's restructure is broader than your fix.** Every step is a child process, not just stop and import. Without that, a VRAM breach or a stop file would `os._exit` the driver itself. Does running the interlock run in a child process change anything H1 or H2 depends on?

## What to do

1. **Check each round 1 finding:** resolved, partly resolved or unresolved, with one line of evidence each.
2. **Review the new driver code and the analysis changes** for anything they introduced:
   - the stop timing;
   - the unload and idle wait (`wait_idle` polls `/api/ps` and `nvidia-smi` for up to 90 s);
   - the VRAM watch writing a stop file from its own thread;
   - the child-process counter.
3. **Say whether stage 1 can run.**

## How to answer

- **Rank the findings:** blocking, important, minor.
- **For each:** the file and line, a concrete failure scenario, and the fix.
- **End with a verdict:** "blocking issues remain", or "no blocking issues; stage 1 can run".

## Test results

At interlock `b5d9ea1`:
- with the `relay` extra: 774 passed, 6 skipped, coverage 93.3%;
- without it: 762 passed, 18 skipped, coverage 92.6%;
- `ruff` is clean.

The driver's tests (`tests/test_relay_s1_driver.py`, 27) now cover:
- the child run;
- the stop step waiting on spans, and a run that finished before the stop file (which doesn't pass);
- the VRAM watch writing the stop file once over the ceiling;
- unload, then the idle wait and its timeout;
- a stop that didn't stop, and a VRAM breach, each failing the run.

The analysis's tests are 13, OK, including a stop record that wasn't stopped and "not run" marking. The end-to-end fake decode run still holds H1, H2 and H3.

## The interlock diff since round 1 (4295165 to b5d9ea1)

```diff
diff --git a/experiments/relay-s1/companion.yaml b/experiments/relay-s1/companion.yaml
index 13222ae..1dfa1d7 100644
--- a/experiments/relay-s1/companion.yaml
+++ b/experiments/relay-s1/companion.yaml
@@ -111,6 +111,7 @@ arms:
     num_ctx: 4096
     batch: null
     prompt: "The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. AMU_CANARY_PROMPT_7c1e"
+    trace: false
     measure: decode_tok_s
 pairs:
   - id: companion-traced
diff --git a/experiments/relay-s1/long.yaml b/experiments/relay-s1/long.yaml
index 846fa10..3cfe0c6 100644
--- a/experiments/relay-s1/long.yaml
+++ b/experiments/relay-s1/long.yaml
@@ -29,7 +29,7 @@ needs:
   cpu_window: false
 dataset:
   name: relay-s1-long-prompt
-  seed: "The switchyard counts the same cars on every pass. "
+  seed: "The switchyard counts the same cars on every pass. AMU_CANARY_PROMPT_7c1e "
   target_tokens: 32768
   rule: >
     Repeat the seed to 32,768 tokens by the served model's count. Each call starts with its own number
@@ -40,6 +40,7 @@ metrics:
   - prompt_tok_s
   - dedicated_mib
 stop_rules:
+  - The seed carries the canary AMU_CANARY_PROMPT_7c1e. It must not appear in any trace (H3).
   - A failed step stops the sequence. A failed step is inconclusive, not a pass.
   - Order is A-B-A per round. A is untraced, B is the same arm with tracing on. Cold is once per arm and stays out
     of the comparison.
diff --git a/scripts/relay_s1.py b/scripts/relay_s1.py
index 1e875f5..c0da54c 100644
--- a/scripts/relay_s1.py
+++ b/scripts/relay_s1.py
@@ -2,19 +2,21 @@
 
     uv run --extra relay python scripts/relay_s1.py --grant <id> --prefix relay-s1-<date> [--steps ...]
 
-Steps, in order, each refusing before any model call when the preflight fails:
+Before every step the driver unloads the card, waits for it to settle at the idle baseline, and runs the full
+preflight. Any refusal stops the run before a model call. Each step runs in its own process, with a VRAM watch
+that writes the step's stop file over 30,500 MiB (interleaved runs have no VRAM ceiling of their own).
 
 - ``decode``, ``long``, ``unload``, ``companion``: ``interlock run experiments/relay-s1/<step>.yaml --trace relay``,
-  in this process, under a counter of the HTTP requests the Ollama adapter sends (below the hook: H1's ground truth).
-  Supervisor health checks aren't counted, by the design's definition. Each step writes ``logs/<id>.http.json``.
-- ``stop``: the decode spec in a child process, stopped through ``receipts/<id>.stop`` after a delay. The run's
-  watcher ends that process with ``os._exit``, so it can't run in this one. Exit 77 is the expected end.
+  under a counter of the HTTP requests the Ollama adapter sends (below the hook: H1's ground truth). Supervisor
+  health checks aren't counted, by the design's definition. Each step writes ``logs/<id>.http.json``.
+- ``stop``: the decode spec, stopped through ``receipts/<id>.stop`` once its trace holds 10 model calls. It passes
+  only on the operator-stop exit, 77.
 - ``import``: the process-level import check. There are 15 triples of child processes, in the order no import,
   idle import, no import. Each child makes 1 warm-up and 3 measured calls with the decode spec's untraced arm, and
   the idle-import child imports ``nemo_relay`` first. The output is ``logs/<prefix>-import.json``.
 
-Afterwards ``interlock check`` runs, and ``logs/<prefix>.driver.json`` records the preflight, every step's exit,
-the check, and the host, user and home strings that the analysis must not find in a trace. The analysis is
+At the end the card is unloaded, ``interlock check`` runs, and ``logs/<prefix>.driver.json`` records the preflight,
+every step, the check, and the host, user and home strings the analysis must not find in a trace. The analysis is
 ``experiments/interlock-relay/stage1/analyze.py`` in mcp-tool-shop-org/rnd, frozen before the run.
 """
 
@@ -40,7 +42,9 @@ RELAY_VERSION = "0.10.1"
 OLLAMA_VERSION = "0.35.1"
 IDLE_VRAM_MIB = 2400
 IMPORT_TRIPLES = 15
-STOP_AFTER_S = 60.0
+STOP_AFTER_SPANS = 10
+VRAM_CEILING_MIB = 30500
+STEP_TIMEOUT_S = 3600
 EXIT_OPERATOR_STOP = 77
 
 
@@ -109,6 +113,15 @@ class Seams:
         finally:
             conn.close()
 
+    def unload(self, model: str) -> None:
+        conn = http.client.HTTPConnection("127.0.0.1", 11434, timeout=60)
+        try:
+            body = json.dumps({"model": model, "prompt": "", "stream": False, "keep_alive": 0})
+            conn.request("POST", "/api/generate", body=body, headers={"Content-Type": "application/json"})
+            conn.getresponse().read()
+        finally:
+            conn.close()
+
     def gpu(self) -> dict:
         def query(args: list[str]) -> str:
             return subprocess.run(["nvidia-smi", *args], capture_output=True, text=True, check=True).stdout  # noqa: S603, S607
@@ -178,13 +191,17 @@ def preflight(root: Path, grant: str | None, seams: Seams, *, first: bool = True
 # -- the steps --------------------------------------------------------------------------------------------------------
 
 
-def run_step(step: str, prefix: str, grant: str, root: Path, main=None) -> dict:
-    """One traced interlock run in this process, under the request counter."""
+def child_run(step: str, prefix: str, grant: str, root: Path, main=None) -> int:
+    """In the step's own process: one traced interlock run under the request counter, then the count is written.
+
+    Each step is its own process so the driver survives the run watcher's os._exit (the stop step, a VRAM breach)
+    and can unload and check the card between steps (Argon stage 1 review, B2)."""
 
     if main is None:
         from interlock.cli import main
+    spec = "decode" if step == "stop" else step
     run_id = f"{prefix}-{step}"
-    argv = ["run", str(SPEC_DIR / f"{step}.yaml"), "--root", str(root), "--grant", grant, "--trace", "relay",
+    argv = ["run", str(SPEC_DIR / f"{spec}.yaml"), "--root", str(root), "--grant", grant, "--trace", "relay",
             "--run-id", run_id]
     with count_adapter_requests() as counts:
         code = main(argv)
@@ -192,23 +209,132 @@ def run_step(step: str, prefix: str, grant: str, root: Path, main=None) -> dict:
     record = {"run_id": run_id, "exit": code, "adapter_requests": sum(counts.values()), "by_path": counts}
     (root / "logs" / f"{run_id}.http.json").write_text(json.dumps(record, indent=1, sort_keys=True) + "\n",
                                                        encoding="utf-8")
-    return record
+    return code
+
+
+class VramWatch:
+    """Reads the card once a second while a step runs. Over the ceiling, it writes the step's stop file once, so the
+    run's own watcher ends it cleanly. Interleaved runs have no VRAM ceiling of their own."""
+
+    def __init__(self, seams: Seams, stop_file: Path | None, *, ceiling_mib: int = VRAM_CEILING_MIB,
+                 every_s: float = 1.0):
+        self.seams, self.stop_file, self.ceiling, self.every = seams, stop_file, ceiling_mib, every_s
+        self.peak = 0
+        self.breached = False
+        self._done = threading.Event()
+        self._thread = threading.Thread(target=self._loop, name="relay-s1-vram", daemon=True)
 
+    def _loop(self) -> None:
+        while not self._done.is_set():
+            self.read_once()
+            self._done.wait(self.every)
+
+    def read_once(self) -> None:
+        try:
+            used = int(self.seams.gpu()["used_mib"])
+        except Exception:  # a failed read is skipped; the next one counts
+            return
+        self.peak = max(self.peak, used)
+        if used > self.ceiling and not self.breached:
+            self.breached = True
+            if self.stop_file is not None:
+                self.stop_file.parent.mkdir(exist_ok=True)
+                self.stop_file.write_text(f"VRAM {used} MiB over {self.ceiling}\n", encoding="utf-8")
+
+    def __enter__(self) -> VramWatch:
+        self._thread.start()
+        return self
+
+    def __exit__(self, *exc) -> None:
+        self._done.set()
+        self._thread.join(timeout=5)
 
-def run_stop(prefix: str, grant: str, root: Path, *, after_s: float = STOP_AFTER_S, popen=subprocess.Popen,
-             sleep=time.sleep) -> dict:
-    """The decode spec in a child process, stopped through its stop file."""
+
+def _spawn(step: str, prefix: str, grant: str, root: Path, popen):
+    argv = [sys.executable, str(Path(__file__).resolve()), "--child-run", step, "--prefix", prefix, "--grant", grant,
+            "--root", str(root)]
+    return popen(argv, cwd=root)
+
+
+def run_step(step: str, prefix: str, grant: str, root: Path, *, seams: Seams, popen=subprocess.Popen,
+             watch=VramWatch) -> dict:
+    """One traced run in its own process, watched for VRAM."""
+
+    run_id = f"{prefix}-{step}"
+    proc = _spawn(step, prefix, grant, root, popen)
+    with watch(seams, root / "receipts" / f"{run_id}.stop") as card:
+        code = proc.wait(timeout=STEP_TIMEOUT_S)
+    return {"run_id": run_id, "exit": code, "vram_peak_mib": card.peak, "vram_breach": card.breached}
+
+
+def spans_started(trace: Path) -> int:
+    """How many model-call spans the trace has opened so far."""
+
+    try:
+        lines = trace.read_text(encoding="utf-8").splitlines()
+    except OSError:
+        return 0
+    count = 0
+    for line in lines:
+        try:
+            event = json.loads(line)
+        except json.JSONDecodeError:
+            continue  # a line still being written
+        count += event.get("category") == "llm" and event.get("scope_category") == "start"
+    return count
+
+
+def run_stop(prefix: str, grant: str, root: Path, *, seams: Seams, popen=subprocess.Popen, sleep=time.sleep,
+             spans: int = STOP_AFTER_SPANS, timeout_s: float = 300.0, watch=VramWatch) -> dict:
+    """The decode spec in its own process, stopped through its stop file once the trace holds ``spans`` model calls.
+
+    Waiting on the trace, not a clock, means the stop lands mid-run however fast the card is (Argon, B3). The step
+    passes only on the operator-stop exit, 77."""
 
     run_id = f"{prefix}-stop"
-    argv = [sys.executable, "-m", "interlock", "run", str(SPEC_DIR / "decode.yaml"), "--root", str(root), "--grant",
-            grant, "--trace", "relay", "--run-id", run_id]
-    proc = popen(argv, cwd=root)
-    sleep(after_s)
     stop = root / "receipts" / f"{run_id}.stop"
-    stop.parent.mkdir(exist_ok=True)
-    stop.write_text("interlock-relay stage 1: the stop-file run\n", encoding="utf-8")
-    code = proc.wait(timeout=600)
-    return {"run_id": run_id, "exit": code, "expected_exit": EXIT_OPERATOR_STOP, "stopped": code == EXIT_OPERATOR_STOP}
+    trace = root / "logs" / f"{run_id}.atof.jsonl"
+    proc = _spawn("stop", prefix, grant, root, popen)
+    with watch(seams, stop) as card:
+        waited = 0.0
+        while spans_started(trace) < spans and waited < timeout_s and proc.poll() is None:
+            sleep(0.5)
+            waited += 0.5
+        written = proc.poll() is None
+        seen = spans_started(trace)
+        if written:
+            stop.parent.mkdir(exist_ok=True)
+            stop.write_text("interlock-relay stage 1: the stop-file run\n", encoding="utf-8")
+        code = proc.wait(timeout=STEP_TIMEOUT_S)
+    return {"run_id": run_id, "exit": code, "expected_exit": EXIT_OPERATOR_STOP, "stop_written": written,
+            "spans_before_stop": seen, "stopped": written and code == EXIT_OPERATOR_STOP, "vram_peak_mib": card.peak}
+
+
+def unload_all(seams: Seams) -> list[str]:
+    """Unload every model on the card (keep_alive 0). The stop step's os._exit and the import children leave the
+    model loaded."""
+
+    names = [m.get("name") or m.get("model") for m in (seams.ollama("/api/ps") or {}).get("models") or []]
+    for name in names:
+        if name:
+            seams.unload(name)
+    return [n for n in names if n]
+
+
+def wait_idle(seams: Seams, *, sleep=time.sleep, timeout_s: float = 90.0) -> float:
+    """Wait for an empty card at the idle baseline. A card that doesn't settle refuses the next step."""
+
+    waited = 0.0
+    while True:
+        loaded = (seams.ollama("/api/ps") or {}).get("models") or []
+        used = seams.gpu()["used_mib"]
+        if not loaded and used <= IDLE_VRAM_MIB:
+            return waited
+        if waited >= timeout_s:
+            raise PreflightError(f"REFUSED: the card did not settle in {timeout_s:.0f}s ({len(loaded)} loaded, "
+                                 f"{used} MiB)")
+        sleep(1.0)
+        waited += 1.0
 
 
 CHILD = r'''
@@ -275,38 +401,55 @@ def run_import(prefix: str, root: Path, *, triples: int = IMPORT_TRIPLES, child=
 # -- the whole run ----------------------------------------------------------------------------------------------------
 
 
-def drive(root: Path, grant: str, prefix: str, steps: tuple[str, ...], *, seams: Seams | None = None, main=None,
-          stop=run_stop, imports=run_import) -> dict:
+def drive(root: Path, grant: str, prefix: str, steps: tuple[str, ...], *, seams: Seams | None = None,
+          step=run_step, stop=run_stop, imports=run_import, check=None, sleep=time.sleep) -> dict:
     seams = seams or Seams()
-    if main is None:
-        from interlock.cli import main
+    if check is None:
+        def check():
+            from interlock.cli import main
+
+            return main(["check", "--root", str(root)]) == 0
     out: dict = {"prefix": prefix, "steps": {}, "needles": {
         "host": socket.gethostname(), "user": os.environ.get("USERNAME") or os.environ.get("USER") or "",
         "home": str(Path.home())}}
     out["preflight"] = preflight(root, grant, seams)
     try:
-        for step in steps:
-            if step not in STEPS:
-                raise PreflightError(f"REFUSED: unknown step {step}")
-            if step != STEPS[0]:
+        for index, name in enumerate(steps):
+            if name not in STEPS:
+                raise PreflightError(f"REFUSED: unknown step {name}")
+            if index:
+                unload_all(seams)
+                wait_idle(seams, sleep=sleep)
                 preflight(root, grant, seams, first=False)  # the card is idle again; nothing else changed
-            if step == "stop":
-                out["steps"][step] = stop(prefix, grant, root)
-            elif step == "import":
+            if name == "stop":
+                out["steps"][name] = result = stop(prefix, grant, root, seams=seams)
+                if not result["stopped"]:
+                    raise PreflightError(f"REFUSED: the stop run ended {result['exit']}, not by its stop file (77)")
+            elif name == "import":
                 def recheck():
-                    age = seams.heartbeat_age_s()
                     from interlock.guards import HEARTBEAT_MAX_AGE_S
 
+                    age = seams.heartbeat_age_s()
                     if age > HEARTBEAT_MAX_AGE_S:
                         raise PreflightError(f"REFUSED: the watchdog heartbeat is {age:.0f}s old")
 
-                out["steps"][step] = imports(prefix, root, between=recheck)
+                with VramWatch(seams, None) as card:
+                    out["steps"][name] = imports(prefix, root, between=recheck)
+                out["steps"][name]["vram_peak_mib"] = card.peak
+                if card.breached:
+                    raise PreflightError(f"REFUSED: VRAM passed {VRAM_CEILING_MIB} MiB in the import check")
             else:
-                out["steps"][step] = run_step(step, prefix, grant, root, main=main)
-                if out["steps"][step]["exit"] != 0:
-                    raise PreflightError(f"REFUSED: step {step} exited {out['steps'][step]['exit']}; the run stops")
+                out["steps"][name] = result = step(name, prefix, grant, root, seams=seams)
+                if result.get("vram_breach"):
+                    raise PreflightError(f"REFUSED: VRAM passed {VRAM_CEILING_MIB} MiB in {name}; the run stopped")
+                if result["exit"] != 0:
+                    raise PreflightError(f"REFUSED: step {name} exited {result['exit']}; the run stops")
     finally:
-        out["check_passed"] = main(["check", "--root", str(root)]) == 0
+        try:
+            out["unloaded_at_end"] = unload_all(seams)
+        except Exception as exc:  # the record is still written
+            out["unloaded_at_end"] = f"failed: {exc}"
+        out["check_passed"] = check()
         (root / "logs").mkdir(exist_ok=True)
         (root / "logs" / f"{prefix}.driver.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n",
                                                              encoding="utf-8")
@@ -319,7 +462,11 @@ def main(argv: list[str] | None = None) -> int:
     parser.add_argument("--prefix", required=True)
     parser.add_argument("--root", type=Path, default=Path.cwd())
     parser.add_argument("--steps", default=",".join(STEPS))
+    parser.add_argument("--child-run", choices=("decode", "long", "unload", "companion", "stop"),
+                        help=argparse.SUPPRESS)
     args = parser.parse_args(argv)
+    if args.child_run:
+        return child_run(args.child_run, args.prefix, args.grant, args.root.resolve())
     try:
         drive(args.root.resolve(), args.grant, args.prefix, tuple(s for s in args.steps.split(",") if s))
     except PreflightError as exc:
```

## The driver in full at b5d9ea1: scripts/relay_s1.py

```python
"""interlock-relay, stage 1: the driver for the 5090 runs. Nothing here runs without the Publisher's grant.

    uv run --extra relay python scripts/relay_s1.py --grant <id> --prefix relay-s1-<date> [--steps ...]

Before every step the driver unloads the card, waits for it to settle at the idle baseline, and runs the full
preflight. Any refusal stops the run before a model call. Each step runs in its own process, with a VRAM watch
that writes the step's stop file over 30,500 MiB (interleaved runs have no VRAM ceiling of their own).

- ``decode``, ``long``, ``unload``, ``companion``: ``interlock run experiments/relay-s1/<step>.yaml --trace relay``,
  under a counter of the HTTP requests the Ollama adapter sends (below the hook: H1's ground truth). Supervisor
  health checks aren't counted, by the design's definition. Each step writes ``logs/<id>.http.json``.
- ``stop``: the decode spec, stopped through ``receipts/<id>.stop`` once its trace holds 10 model calls. It passes
  only on the operator-stop exit, 77.
- ``import``: the process-level import check. There are 15 triples of child processes, in the order no import,
  idle import, no import. Each child makes 1 warm-up and 3 measured calls with the decode spec's untraced arm, and
  the idle-import child imports ``nemo_relay`` first. The output is ``logs/<prefix>-import.json``.

At the end the card is unloaded, ``interlock check`` runs, and ``logs/<prefix>.driver.json`` records the preflight,
every step, the check, and the host, user and home strings the analysis must not find in a trace. The analysis is
``experiments/interlock-relay/stage1/analyze.py`` in mcp-tool-shop-org/rnd, frozen before the run.
"""

from __future__ import annotations

import argparse
import contextlib
import http.client
import importlib.metadata
import json
import os
import socket
import subprocess
import sys
import threading
import time
import traceback
from pathlib import Path

STEPS = ("decode", "long", "unload", "companion", "stop", "import")
SPEC_DIR = Path("experiments/relay-s1")
RELAY_VERSION = "0.10.1"
OLLAMA_VERSION = "0.35.1"
IDLE_VRAM_MIB = 2400
IMPORT_TRIPLES = 15
STOP_AFTER_SPANS = 10
VRAM_CEILING_MIB = 30500
STEP_TIMEOUT_S = 3600
EXIT_OPERATOR_STOP = 77


class PreflightError(RuntimeError):
    """One preflight item failed. The run stops before any model call."""


# -- the counter below the hook ---------------------------------------------------------------------------------------


_ADAPTER_FILE = os.path.join("interlock", "adapters", "ollama.py")


@contextlib.contextmanager
def count_adapter_requests():
    """Count every ``http.client`` request sent from the Ollama adapter's transport, by path. Requests from anywhere
    else (the supervisor's health checks) aren't counted."""

    counts: dict[str, int] = {}
    lock = threading.Lock()
    original = http.client.HTTPConnection.request

    def counted(self, method, url, *args, **kwargs):
        if any(_ADAPTER_FILE in frame.filename for frame in traceback.extract_stack()):
            path = url.split("?", 1)[0]
            with lock:
                counts[path] = counts.get(path, 0) + 1
        return original(self, method, url, *args, **kwargs)

    http.client.HTTPConnection.request = counted
    try:
        yield counts
    finally:
        http.client.HTTPConnection.request = original


# -- the preflight ----------------------------------------------------------------------------------------------------


class Seams:
    """Every outside read the preflight makes. The defaults are the live ones; tests pass their own."""

    def environ(self) -> dict:
        return dict(os.environ)

    def version(self, package: str) -> str | None:
        try:
            return importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            return None

    def relay_config_paths(self) -> list:
        from nemo_relay import plugin

        report = plugin.validate({"version": 1, "components": []})
        return list(report.get("config_paths") or [])

    def git(self, root: Path, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)  # noqa: S603, S607

    def ollama(self, path: str) -> dict:
        conn = http.client.HTTPConnection("127.0.0.1", 11434, timeout=5)
        try:
            conn.request("GET", path)
            return json.loads(conn.getresponse().read().decode("utf-8"))
        finally:
            conn.close()

    def unload(self, model: str) -> None:
        conn = http.client.HTTPConnection("127.0.0.1", 11434, timeout=60)
        try:
            body = json.dumps({"model": model, "prompt": "", "stream": False, "keep_alive": 0})
            conn.request("POST", "/api/generate", body=body, headers={"Content-Type": "application/json"})
            conn.getresponse().read()
        finally:
            conn.close()

    def gpu(self) -> dict:
        def query(args: list[str]) -> str:
            return subprocess.run(["nvidia-smi", *args], capture_output=True, text=True, check=True).stdout  # noqa: S603, S607

        used = query(["--query-gpu=memory.used", "--format=csv,noheader,nounits"]).strip().splitlines()
        apps = [line for line in query(["--query-compute-apps=pid", "--format=csv,noheader"]).splitlines() if line]
        return {"used_mib": int(used[0]), "compute_apps": len(apps)}

    def listeners(self, port: int) -> int:
        import psutil

        return sum(1 for c in psutil.net_connections(kind="tcp") if c.status == "LISTEN" and c.laddr.port == port)

    def heartbeat_age_s(self) -> float:
        from interlock.guards import heartbeat_age_s
        from interlock.harness.runner import heartbeat_path

        return heartbeat_age_s(heartbeat_path(None), time.time())


def preflight(root: Path, grant: str | None, seams: Seams, *, first: bool = True) -> dict:
    """Every item, in order. The first failure raises before any model call. Returns what was read.

    Before the first step the whole tree must be clean. Before a later step, everything but ``receipts/`` and
    ``table/`` must be, since the steps before it wrote their receipts there."""

    from interlock.guards import HEARTBEAT_MAX_AGE_S

    facts: dict = {}

    def need(ok: bool, message: str) -> None:
        if not ok:
            raise PreflightError(f"REFUSED: {message}")

    need(bool(grant), "no grant: the Publisher grants the 5090 for this run")
    age = seams.heartbeat_age_s()
    need(age <= HEARTBEAT_MAX_AGE_S, f"the watchdog heartbeat is {age:.0f}s old")
    facts["heartbeat_age_s"] = round(age, 1)
    otel = sorted(k for k in seams.environ() if k.startswith("OTEL_"))
    need(not otel, f"OTEL variables are set: {', '.join(otel)}")
    relay = seams.version("nemo-relay")
    need(relay == RELAY_VERSION, f"nemo-relay is {relay}, not {RELAY_VERSION} (install interlock[relay])")
    facts["nemo_relay"] = relay
    layered = seams.relay_config_paths()
    need(not layered, f"Relay would layer in {layered}")
    scope = ["--", "."] if first else ["--", ".", ":!receipts", ":!table"]
    status = seams.git(root, "status", "--porcelain", *scope).stdout.strip()
    need(not status, "the interlock tree is not clean" + ("" if first else " outside receipts/ and table/"))
    ignored = seams.git(root, "check-ignore", "-q", "logs/relay-s1-probe").returncode == 0
    need(ignored, "logs/ is not git-ignored")
    facts["git_sha"] = seams.git(root, "rev-parse", "HEAD").stdout.strip()
    version = (seams.ollama("/api/version") or {}).get("version")
    need(version == OLLAMA_VERSION, f"Ollama on 11434 is {version}, not {OLLAMA_VERSION}")
    facts["ollama_version"] = version
    loaded = (seams.ollama("/api/ps") or {}).get("models") or []
    need(not loaded, f"{len(loaded)} model(s) already on the card")
    listeners = seams.listeners(11434)
    need(listeners == 1, f"{listeners} listeners on 11434; the supervisor needs exactly one")
    gpu = seams.gpu()
    need(gpu["compute_apps"] == 0, f"{gpu['compute_apps']} other process(es) on the GPU")
    need(gpu["used_mib"] <= IDLE_VRAM_MIB,
         f"{gpu['used_mib']} MiB in use; the idle baseline is at most {IDLE_VRAM_MIB}")
    facts["idle_vram_mib"] = gpu["used_mib"]
    return facts


# -- the steps --------------------------------------------------------------------------------------------------------


def child_run(step: str, prefix: str, grant: str, root: Path, main=None) -> int:
    """In the step's own process: one traced interlock run under the request counter, then the count is written.

    Each step is its own process so the driver survives the run watcher's os._exit (the stop step, a VRAM breach)
    and can unload and check the card between steps (Argon stage 1 review, B2)."""

    if main is None:
        from interlock.cli import main
    spec = "decode" if step == "stop" else step
    run_id = f"{prefix}-{step}"
    argv = ["run", str(SPEC_DIR / f"{spec}.yaml"), "--root", str(root), "--grant", grant, "--trace", "relay",
            "--run-id", run_id]
    with count_adapter_requests() as counts:
        code = main(argv)
    (root / "logs").mkdir(exist_ok=True)
    record = {"run_id": run_id, "exit": code, "adapter_requests": sum(counts.values()), "by_path": counts}
    (root / "logs" / f"{run_id}.http.json").write_text(json.dumps(record, indent=1, sort_keys=True) + "\n",
                                                       encoding="utf-8")
    return code


class VramWatch:
    """Reads the card once a second while a step runs. Over the ceiling, it writes the step's stop file once, so the
    run's own watcher ends it cleanly. Interleaved runs have no VRAM ceiling of their own."""

    def __init__(self, seams: Seams, stop_file: Path | None, *, ceiling_mib: int = VRAM_CEILING_MIB,
                 every_s: float = 1.0):
        self.seams, self.stop_file, self.ceiling, self.every = seams, stop_file, ceiling_mib, every_s
        self.peak = 0
        self.breached = False
        self._done = threading.Event()
        self._thread = threading.Thread(target=self._loop, name="relay-s1-vram", daemon=True)

    def _loop(self) -> None:
        while not self._done.is_set():
            self.read_once()
            self._done.wait(self.every)

    def read_once(self) -> None:
        try:
            used = int(self.seams.gpu()["used_mib"])
        except Exception:  # a failed read is skipped; the next one counts
            return
        self.peak = max(self.peak, used)
        if used > self.ceiling and not self.breached:
            self.breached = True
            if self.stop_file is not None:
                self.stop_file.parent.mkdir(exist_ok=True)
                self.stop_file.write_text(f"VRAM {used} MiB over {self.ceiling}\n", encoding="utf-8")

    def __enter__(self) -> VramWatch:
        self._thread.start()
        return self

    def __exit__(self, *exc) -> None:
        self._done.set()
        self._thread.join(timeout=5)


def _spawn(step: str, prefix: str, grant: str, root: Path, popen):
    argv = [sys.executable, str(Path(__file__).resolve()), "--child-run", step, "--prefix", prefix, "--grant", grant,
            "--root", str(root)]
    return popen(argv, cwd=root)


def run_step(step: str, prefix: str, grant: str, root: Path, *, seams: Seams, popen=subprocess.Popen,
             watch=VramWatch) -> dict:
    """One traced run in its own process, watched for VRAM."""

    run_id = f"{prefix}-{step}"
    proc = _spawn(step, prefix, grant, root, popen)
    with watch(seams, root / "receipts" / f"{run_id}.stop") as card:
        code = proc.wait(timeout=STEP_TIMEOUT_S)
    return {"run_id": run_id, "exit": code, "vram_peak_mib": card.peak, "vram_breach": card.breached}


def spans_started(trace: Path) -> int:
    """How many model-call spans the trace has opened so far."""

    try:
        lines = trace.read_text(encoding="utf-8").splitlines()
    except OSError:
        return 0
    count = 0
    for line in lines:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue  # a line still being written
        count += event.get("category") == "llm" and event.get("scope_category") == "start"
    return count


def run_stop(prefix: str, grant: str, root: Path, *, seams: Seams, popen=subprocess.Popen, sleep=time.sleep,
             spans: int = STOP_AFTER_SPANS, timeout_s: float = 300.0, watch=VramWatch) -> dict:
    """The decode spec in its own process, stopped through its stop file once the trace holds ``spans`` model calls.

    Waiting on the trace, not a clock, means the stop lands mid-run however fast the card is (Argon, B3). The step
    passes only on the operator-stop exit, 77."""

    run_id = f"{prefix}-stop"
    stop = root / "receipts" / f"{run_id}.stop"
    trace = root / "logs" / f"{run_id}.atof.jsonl"
    proc = _spawn("stop", prefix, grant, root, popen)
    with watch(seams, stop) as card:
        waited = 0.0
        while spans_started(trace) < spans and waited < timeout_s and proc.poll() is None:
            sleep(0.5)
            waited += 0.5
        written = proc.poll() is None
        seen = spans_started(trace)
        if written:
            stop.parent.mkdir(exist_ok=True)
            stop.write_text("interlock-relay stage 1: the stop-file run\n", encoding="utf-8")
        code = proc.wait(timeout=STEP_TIMEOUT_S)
    return {"run_id": run_id, "exit": code, "expected_exit": EXIT_OPERATOR_STOP, "stop_written": written,
            "spans_before_stop": seen, "stopped": written and code == EXIT_OPERATOR_STOP, "vram_peak_mib": card.peak}


def unload_all(seams: Seams) -> list[str]:
    """Unload every model on the card (keep_alive 0). The stop step's os._exit and the import children leave the
    model loaded."""

    names = [m.get("name") or m.get("model") for m in (seams.ollama("/api/ps") or {}).get("models") or []]
    for name in names:
        if name:
            seams.unload(name)
    return [n for n in names if n]


def wait_idle(seams: Seams, *, sleep=time.sleep, timeout_s: float = 90.0) -> float:
    """Wait for an empty card at the idle baseline. A card that doesn't settle refuses the next step."""

    waited = 0.0
    while True:
        loaded = (seams.ollama("/api/ps") or {}).get("models") or []
        used = seams.gpu()["used_mib"]
        if not loaded and used <= IDLE_VRAM_MIB:
            return waited
        if waited >= timeout_s:
            raise PreflightError(f"REFUSED: the card did not settle in {timeout_s:.0f}s ({len(loaded)} loaded, "
                                 f"{used} MiB)")
        sleep(1.0)
        waited += 1.0


CHILD = r'''
import json, statistics, sys, time
started = time.perf_counter()
args = json.loads(sys.argv[1])
import_s = None
if args["idle_import"]:
    t = time.perf_counter()
    import nemo_relay  # noqa: F401  # idle: imported, never initialised
    import_s = time.perf_counter() - t
import yaml
from interlock.adapters.base import StepRequest
from interlock.adapters.ollama import OllamaAdapter
spec = yaml.safe_load(open(args["spec"], encoding="utf-8"))
arm = next(a for a in spec["arms"] if a["id"] == args["arm"])
keys = ("thinking_level", "num_predict", "num_ctx", "prompt", "keep_alive", "temperature")
request = StepRequest(step_id=arm["id"], task=arm["task"], model=arm["model"], device=arm["device"],
                      engine=arm["engine"], settings={k: arm.get(k) for k in keys})
adapter = OllamaAdapter(device=arm["device"])
ready_s = time.perf_counter() - started
metrics = {"latency_ms": [], "decode_tok_s": [], "prompt_tok_s": []}
for i in range(1 + args["calls"]):
    result = adapter.run(request)
    if not result.ok:
        print(json.dumps({"error": result.error}))
        sys.exit(2)
    if i == 0:
        continue  # the warm-up
    metrics["latency_ms"].append(result.latency_ms)
    metrics["decode_tok_s"].append(result.throughput)
    metrics["prompt_tok_s"].append(result.prompt_tok_s)
print(json.dumps({"metrics": metrics, "import_s": import_s, "ready_s": ready_s}))
'''


def _child(root: Path, *, idle_import: bool, calls: int = 3) -> dict:
    args = {"idle_import": idle_import, "calls": calls, "spec": str(SPEC_DIR / "decode.yaml"), "arm": "decode-off"}
    done = subprocess.run([sys.executable, "-c", CHILD, json.dumps(args)], cwd=root, capture_output=True,  # noqa: S603
                          text=True, check=False, timeout=600)
    if done.returncode != 0:
        raise RuntimeError(f"import-check child failed ({done.returncode}): {done.stdout.strip()} {done.stderr[-400:]}")
    return json.loads(done.stdout.strip().splitlines()[-1])


def run_import(prefix: str, root: Path, *, triples: int = IMPORT_TRIPLES, child=_child, between=None) -> dict:
    """15 triples of processes: no import, idle import, no import. ``between`` runs before each child (the
    heartbeat re-check in the live driver)."""

    record = {"triples": []}
    for _ in range(triples):
        triple = {}
        for side, idle in (("no_import_before", False), ("idle_import", True), ("no_import_after", False)):
            if between is not None:
                between()
            triple[side] = child(root, idle_import=idle)
        record["triples"].append(triple)
    (root / "logs").mkdir(exist_ok=True)
    (root / "logs" / f"{prefix}-import.json").write_text(json.dumps(record, indent=1, sort_keys=True) + "\n",
                                                         encoding="utf-8")
    return {"triples": len(record["triples"])}


# -- the whole run ----------------------------------------------------------------------------------------------------


def drive(root: Path, grant: str, prefix: str, steps: tuple[str, ...], *, seams: Seams | None = None,
          step=run_step, stop=run_stop, imports=run_import, check=None, sleep=time.sleep) -> dict:
    seams = seams or Seams()
    if check is None:
        def check():
            from interlock.cli import main

            return main(["check", "--root", str(root)]) == 0
    out: dict = {"prefix": prefix, "steps": {}, "needles": {
        "host": socket.gethostname(), "user": os.environ.get("USERNAME") or os.environ.get("USER") or "",
        "home": str(Path.home())}}
    out["preflight"] = preflight(root, grant, seams)
    try:
        for index, name in enumerate(steps):
            if name not in STEPS:
                raise PreflightError(f"REFUSED: unknown step {name}")
            if index:
                unload_all(seams)
                wait_idle(seams, sleep=sleep)
                preflight(root, grant, seams, first=False)  # the card is idle again; nothing else changed
            if name == "stop":
                out["steps"][name] = result = stop(prefix, grant, root, seams=seams)
                if not result["stopped"]:
                    raise PreflightError(f"REFUSED: the stop run ended {result['exit']}, not by its stop file (77)")
            elif name == "import":
                def recheck():
                    from interlock.guards import HEARTBEAT_MAX_AGE_S

                    age = seams.heartbeat_age_s()
                    if age > HEARTBEAT_MAX_AGE_S:
                        raise PreflightError(f"REFUSED: the watchdog heartbeat is {age:.0f}s old")

                with VramWatch(seams, None) as card:
                    out["steps"][name] = imports(prefix, root, between=recheck)
                out["steps"][name]["vram_peak_mib"] = card.peak
                if card.breached:
                    raise PreflightError(f"REFUSED: VRAM passed {VRAM_CEILING_MIB} MiB in the import check")
            else:
                out["steps"][name] = result = step(name, prefix, grant, root, seams=seams)
                if result.get("vram_breach"):
                    raise PreflightError(f"REFUSED: VRAM passed {VRAM_CEILING_MIB} MiB in {name}; the run stopped")
                if result["exit"] != 0:
                    raise PreflightError(f"REFUSED: step {name} exited {result['exit']}; the run stops")
    finally:
        try:
            out["unloaded_at_end"] = unload_all(seams)
        except Exception as exc:  # the record is still written
            out["unloaded_at_end"] = f"failed: {exc}"
        out["check_passed"] = check()
        (root / "logs").mkdir(exist_ok=True)
        (root / "logs" / f"{prefix}.driver.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n",
                                                             encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--grant", required=True)
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--steps", default=",".join(STEPS))
    parser.add_argument("--child-run", choices=("decode", "long", "unload", "companion", "stop"),
                        help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.child_run:
        return child_run(args.child_run, args.prefix, args.grant, args.root.resolve())
    try:
        drive(args.root.resolve(), args.grant, args.prefix, tuple(s for s in args.steps.split(",") if s))
    except PreflightError as exc:
        print(exc, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

## The analysis diff (rnd 43643bc to cbaed82, analyze.py)

```diff
diff --git a/experiments/interlock-relay/stage1/analyze.py b/experiments/interlock-relay/stage1/analyze.py
index 85b1608..615d3d1 100644
--- a/experiments/interlock-relay/stage1/analyze.py
+++ b/experiments/interlock-relay/stage1/analyze.py
@@ -24,8 +24,9 @@ The pre-registered rules, in the design's words where it has them (design v3.1,
 
 **H2, the process import check.**
 - The same Δ, band and gates, on per-process medians of the measured calls: N1, I and N2 per triple.
-- **The barrier check:** the median of the in-process decode A calls (with the barrier) and the median of the N
-  processes' calls (no barrier) differ by at most the decode band for that metric.
+- **The barrier check (reported, not gated; S1-A6):** the median of the in-process decode A calls (with the
+  barrier) against the median of the N processes' calls (no barrier), and whether they differ by at most the
+  decode band for that metric.
 
 **H1, per traced run:**
 - **Request count:** the driver's count of HTTP requests the adapter sent (below the hook) = the sum of the run's
@@ -34,7 +35,8 @@ The pre-registered rules, in the design's words where it has them (design v3.1,
 
 **H3:**
 - The trace parses, with no canary, host name, user name or home path, and the run scope opens and closes.
-- The stop run's trace parses and is closed.
+- The stop run's trace parses and is closed, and the driver recorded a real stop: the stop file was written
+  mid-run and the run exited 77 (S1-A5).
 - `interlock check` passes, as reported by the driver.
 
 **Amendments made before any run:**
@@ -57,6 +59,15 @@ The pre-registered rules, in the design's words where it has them (design v3.1,
   - with one call in twenty from a four-times-wider spread, 1.8% fail too;
   - a 1% shift passes 93% of the time;
   - a 3% shift fails 96% of the time.
+- **S1-A5 (after Argon's stage 1 review, before any run):** a stop run that finished before its stop file was written
+  would leave a normally closed trace and pass H3. H3 now also needs the driver's own record that the stop
+  landed mid-run (exit 77). The driver waits for the trace to hold 10 model calls before it writes the stop file.
+- **S1-A6 (after Argon's stage 1 review, before any run):** the barrier check is reported, not gated.
+  - Both arms of every in-process triple take the same barrier, so a barrier-induced shift in the baseline
+    can't bias Δ, and H2's verdict on Relay stands without it.
+  - What the check measures is the protocol's own effect: the card's clocks after a 250 ms rest against
+    back-to-back calls in a fresh process. Gating on it could reject Relay for a property of the measurement.
+  - It's reported beside H2, so a reader knows the conditions the equivalence was shown under.
 """
 
 from __future__ import annotations
@@ -288,9 +299,8 @@ def h2_import(record: dict, decode_rows: list[dict]) -> dict:
         else:
             barrier[name] = {"holds": None, "reason": "no data"}
     measured = {k: v for k, v in metrics.items() if v["verdict"] != "not measured"}
-    holds = bool(measured) and all(v["verdict"] == "holds" for v in measured.values()) and all(
-        b["holds"] is True for b in barrier.values())
-    return {"triples": len(trips), "metrics": metrics, "barrier": barrier, "holds": holds}
+    holds = bool(measured) and all(v["verdict"] == "holds" for v in measured.values())
+    return {"triples": len(trips), "metrics": metrics, "barrier_reported": barrier, "holds": holds}
 
 
 def h1_run(trace_path: Path, calls_path: Path, http_path: Path, rows: list[dict]) -> dict:
@@ -348,7 +358,9 @@ def analyze(root: Path, prefix: str) -> dict:
         rows = _rows(root, run_id)
         trace = root / "logs" / f"{run_id}.atof.jsonl"
         if not rows or not trace.is_file():
-            out["h1"][step] = {"holds": None, "reason": "not run"}
+            out["h1"][step] = out["h3"][step] = {"holds": None, "reason": "not run"}
+            if step in ("decode", "long"):
+                out["h2"][step] = {"holds": None, "reason": "not run"}
             continue
         out["h1"][step] = h1_run(trace, root / "logs" / f"{run_id}.calls.json", root / "logs" / f"{run_id}.http.json",
                                  rows)
@@ -356,7 +368,14 @@ def analyze(root: Path, prefix: str) -> dict:
         if step in ("decode", "long"):
             out["h2"][step] = h2_run(rows, step)
     stop_trace = root / "logs" / f"{prefix}-stop.atof.jsonl"
-    out["h3"]["stop"] = h3_trace(stop_trace, needles) if stop_trace.is_file() else {"holds": None, "reason": "not run"}
+    stopped = (driver.get("steps", {}).get("stop") or {}).get("stopped") is True
+    if stop_trace.is_file():
+        result = h3_trace(stop_trace, needles)
+        result["checks"]["stopped_mid_run"] = stopped
+        result["holds"] = all(result["checks"].values())
+        out["h3"]["stop"] = result
+    else:
+        out["h3"]["stop"] = {"holds": None, "reason": "not run"}
     out["h3"]["receipts_check"] = {"holds": driver.get("check_passed")}
     imports = root / "logs" / f"{prefix}-import.json"
     out["h2"]["import"] = (h2_import(json.loads(imports.read_text(encoding="utf-8")), _rows(root, f"{prefix}-decode"))
```

## The driver's tests at b5d9ea1

```python
"""The interlock-relay stage 1 driver (scripts/relay_s1.py), on fakes: the preflight refuses before any model call,
the request counter sees only the adapter's requests, and the steps run in order. No device, no server."""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location("relay_s1", ROOT / "scripts" / "relay_s1.py")
relay_s1 = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(relay_s1)


class Seams(relay_s1.Seams):
    """Every preflight read, healthy unless a test changes one."""

    def __init__(self, **changes):
        self.state = {
            "environ": {}, "nemo-relay": "0.10.1", "config_paths": [], "status": "", "ignored": 0, "sha": "abc",
            "/api/version": {"version": "0.35.1"}, "/api/ps": {"models": []}, "listeners": 1,
            "gpu": {"used_mib": 2008, "compute_apps": 0}, "heartbeat": 5.0,
        }
        self.state.update(changes)
        self.status_args = []
        self.unloaded = []

    def environ(self):
        return self.state["environ"]

    def version(self, package):
        return self.state[package]

    def relay_config_paths(self):
        return self.state["config_paths"]

    def git(self, root, *args):
        if args[0] == "status":
            self.status_args.append(args)
            return subprocess.CompletedProcess(args, 0, self.state["status"], "")
        if args[0] == "check-ignore":
            return subprocess.CompletedProcess(args, self.state["ignored"], "", "")
        return subprocess.CompletedProcess(args, 0, self.state["sha"] + "\n", "")

    def ollama(self, path):
        return self.state[path]

    def gpu(self):
        return self.state["gpu"]

    def unload(self, model):
        self.unloaded.append(model)
        self.state["/api/ps"] = {"models": []}
        self.state["gpu"] = {"used_mib": 2008, "compute_apps": 0}

    def listeners(self, port):
        return self.state["listeners"]

    def heartbeat_age_s(self):
        return self.state["heartbeat"]


def test_a_healthy_preflight_returns_what_it_read(tmp_path: Path):
    facts = relay_s1.preflight(tmp_path, "g-1", Seams())
    assert facts == {"heartbeat_age_s": 5.0, "nemo_relay": "0.10.1", "git_sha": "abc", "ollama_version": "0.35.1",
                     "idle_vram_mib": 2008}


@pytest.mark.parametrize(
    ("grant", "changes", "message"),
    [
        (None, {}, "no grant"),
        ("g", {"heartbeat": 10_000.0}, "heartbeat"),
        ("g", {"environ": {"OTEL_SERVICE_NAME": "x"}}, "OTEL"),
        ("g", {"nemo-relay": None}, "nemo-relay is None"),
        ("g", {"config_paths": ["user/plugins.toml"]}, "layer in"),
        ("g", {"status": " M src/x.py"}, "not clean"),
        ("g", {"ignored": 1}, "git-ignored"),
        ("g", {"/api/version": {"version": "0.36.0"}}, "0.36.0"),
        ("g", {"/api/ps": {"models": [{"name": "m"}]}}, "already on the card"),
        ("g", {"listeners": 2}, "2 listeners"),
        ("g", {"gpu": {"used_mib": 2008, "compute_apps": 1}}, "other process"),
        ("g", {"gpu": {"used_mib": 9000, "compute_apps": 0}}, "9000 MiB"),
    ],
)
def test_each_preflight_item_refuses(tmp_path: Path, grant, changes, message):
    with pytest.raises(relay_s1.PreflightError, match=message):
        relay_s1.preflight(tmp_path, grant, Seams(**changes))


def test_after_the_first_step_receipts_and_table_may_change(tmp_path: Path):
    seams = Seams()
    relay_s1.preflight(tmp_path, "g", seams, first=False)
    assert seams.status_args[-1][-2:] == (":!receipts", ":!table")


def test_the_counter_sees_only_requests_sent_from_the_adapter(tmp_path: Path, monkeypatch):
    import http.client

    sent = []
    monkeypatch.setattr(http.client.HTTPConnection, "request", lambda self, method, url, *a, **k: sent.append(url))
    # A function compiled under the adapter's file name stands in for its transport.
    adapter_like = {}
    exec(compile("def send(conn, url):\n    conn.request('POST', url)\n",  # noqa: S102
                 str(ROOT / "src" / "interlock" / "adapters" / "ollama.py"), "exec"), adapter_like)
    with relay_s1.count_adapter_requests() as counts:
        conn = http.client.HTTPConnection("127.0.0.1", 11434)
        adapter_like["send"](conn, "/api/generate")
        adapter_like["send"](conn, "/api/generate")
        conn.request("GET", "/api/version")  # a health check from elsewhere
    assert counts == {"/api/generate": 2}
    assert sent == ["/api/generate", "/api/generate", "/api/version"]  # the real request still goes out
    assert http.client.HTTPConnection.request.__name__ == "<lambda>"  # restored after the block


def test_the_child_run_runs_the_spec_traced_and_records_the_count(tmp_path: Path):
    seen = []

    def main(argv):
        seen.append(argv)
        return 0

    assert relay_s1.child_run("decode", "p", "g-1", tmp_path, main=main) == 0
    assert seen == [["run", str(Path("experiments/relay-s1/decode.yaml")), "--root", str(tmp_path), "--grant", "g-1",
                     "--trace", "relay", "--run-id", "p-decode"]]
    record = json.loads((tmp_path / "logs" / "p-decode.http.json").read_text(encoding="utf-8"))
    assert record["run_id"] == "p-decode" and record["adapter_requests"] == 0
    relay_s1.child_run("stop", "p", "g", tmp_path, main=main)
    assert seen[-1][1] == str(Path("experiments/relay-s1/decode.yaml")) and seen[-1][-1] == "p-stop"


class Proc:
    def __init__(self, code=0, *, until_stop=None):
        self.code, self.until_stop = code, until_stop

    def poll(self):
        if self.until_stop is not None and not self.until_stop.is_file():
            return None
        return self.code

    def wait(self, timeout):
        return self.code


class NoWatch:
    def __init__(self, seams, stop_file):
        self.peak, self.breached = 0, False

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return None


def test_a_step_runs_in_its_own_process_under_the_vram_watch(tmp_path: Path):
    started = []
    record = relay_s1.run_step("long", "p", "g", tmp_path, seams=Seams(),
                               popen=lambda argv, cwd: started.append(argv) or Proc(0), watch=NoWatch)
    assert record == {"run_id": "p-long", "exit": 0, "vram_peak_mib": 0, "vram_breach": False}
    assert started[0][2:4] == ["--child-run", "long"] and started[0][1].endswith("relay_s1.py")


def _spans(path: Path, n: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps({"category": "llm", "scope_category": "start", "uuid": str(i)}) for i in range(n)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_the_stop_step_waits_for_spans_then_stops_and_expects_77(tmp_path: Path):
    stop = tmp_path / "receipts" / "p-stop.stop"
    trace = tmp_path / "logs" / "p-stop.atof.jsonl"
    ticks = []

    def sleep(seconds):
        ticks.append(seconds)
        _spans(trace, 4 * len(ticks))  # the run traces 4 calls per tick

    record = relay_s1.run_stop("p", "g", tmp_path, seams=Seams(), popen=lambda argv, cwd: Proc(77, until_stop=stop),
                               sleep=sleep, watch=NoWatch)
    assert record["stopped"] is True and record["stop_written"] is True
    assert record["spans_before_stop"] >= 10 and stop.is_file()


def test_a_stop_run_that_finishes_first_does_not_pass(tmp_path: Path):
    record = relay_s1.run_stop("p", "g", tmp_path, seams=Seams(), popen=lambda argv, cwd: Proc(0),
                               sleep=lambda s: None, watch=NoWatch)
    assert record["stopped"] is False and record["stop_written"] is False
    assert not (tmp_path / "receipts" / "p-stop.stop").exists()


def test_the_vram_watch_writes_the_stop_file_once_over_the_ceiling(tmp_path: Path):
    stop = tmp_path / "receipts" / "x.stop"
    seams = Seams(gpu={"used_mib": 31_000, "compute_apps": 1})
    watch = relay_s1.VramWatch(seams, stop)
    watch.read_once()
    first = stop.read_text(encoding="utf-8")
    watch.read_once()
    assert watch.breached and watch.peak == 31_000 and "31000" in first
    calm = relay_s1.VramWatch(Seams(), tmp_path / "receipts" / "y.stop")
    calm.read_once()
    assert not calm.breached and not (tmp_path / "receipts" / "y.stop").exists()


def test_unload_all_and_wait_idle(tmp_path: Path):
    seams = Seams(**{"/api/ps": {"models": [{"name": "qwen3:8b"}]}, "gpu": {"used_mib": 15000, "compute_apps": 1}})
    assert relay_s1.unload_all(seams) == ["qwen3:8b"] and seams.unloaded == ["qwen3:8b"]
    assert relay_s1.wait_idle(seams, sleep=lambda s: None) == 0.0
    stuck = Seams(**{"/api/ps": {"models": [{"name": "m"}]}})
    with pytest.raises(relay_s1.PreflightError, match="did not settle"):
        relay_s1.wait_idle(stuck, sleep=lambda s: None, timeout_s=3)


def test_the_import_check_runs_fifteen_triples_in_order(tmp_path: Path):
    order = []

    def child(root, *, idle_import):
        order.append(idle_import)
        return {"metrics": {"latency_ms": [1.0, 1.0, 1.0]}, "import_s": 0.1 if idle_import else None}

    checks = []
    relay_s1.run_import("p", tmp_path, child=child, between=lambda: checks.append(1))
    assert order == [False, True, False] * 15
    assert len(checks) == 45
    record = json.loads((tmp_path / "logs" / "p-import.json").read_text(encoding="utf-8"))
    assert set(record["triples"][0]) == {"no_import_before", "idle_import", "no_import_after"}


def _drive(tmp_path, steps, *, seams=None, step=None, stop=None):
    checks = []
    out = relay_s1.drive(
        tmp_path, "g", "p", steps, seams=seams or Seams(),
        step=step or (lambda name, prefix, grant, root, seams: {"run_id": f"p-{name}", "exit": 0}),
        stop=stop or (lambda prefix, grant, root, seams: {"stopped": True, "exit": 77}),
        imports=lambda prefix, root, between: {"triples": 15},
        check=lambda: checks.append(1) or True, sleep=lambda s: None)
    return out, checks


def test_between_steps_the_card_is_unloaded_settled_and_preflighted(tmp_path: Path):
    seams = Seams()
    out, checks = _drive(tmp_path, ("decode", "stop", "import"), seams=seams)
    assert list(out["steps"]) == ["decode", "stop", "import"]
    assert len(seams.status_args) == 3  # the first preflight, then one before each later step
    assert checks == [1]


def test_a_stop_step_that_did_not_stop_fails_the_run(tmp_path: Path):
    with pytest.raises(relay_s1.PreflightError, match="not by its stop file"):
        _drive(tmp_path, ("stop", "import"), stop=lambda prefix, grant, root, seams: {"stopped": False, "exit": 0})
    driver = json.loads((tmp_path / "logs" / "p.driver.json").read_text(encoding="utf-8"))
    assert "import" not in driver["steps"]


def test_a_vram_breach_fails_the_run(tmp_path: Path):
    with pytest.raises(relay_s1.PreflightError, match="VRAM passed"):
        _drive(tmp_path, ("companion",),
               step=lambda name, prefix, grant, root, seams: {"exit": 77, "vram_breach": True})


def test_a_failed_step_stops_the_run_and_the_record_is_still_written(tmp_path: Path):
    ran = []

    def step(name, prefix, grant, root, seams):
        ran.append(name)
        return {"run_id": f"p-{name}", "exit": 1}

    with pytest.raises(relay_s1.PreflightError, match="decode exited 1"):
        _drive(tmp_path, ("decode", "long"), step=step)
    assert ran == ["decode"]
    driver = json.loads((tmp_path / "logs" / "p.driver.json").read_text(encoding="utf-8"))
    assert driver["check_passed"] is True and "decode" in driver["steps"] and "long" not in driver["steps"]
    assert set(driver["needles"]) == {"host", "user", "home"}


def test_a_refused_preflight_runs_nothing(tmp_path: Path):
    ran = []
    with pytest.raises(relay_s1.PreflightError):
        _drive(tmp_path, ("decode",), seams=Seams(listeners=0), step=lambda *a, **k: ran.append(1))
    assert ran == []
```
