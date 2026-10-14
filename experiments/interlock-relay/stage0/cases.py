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
