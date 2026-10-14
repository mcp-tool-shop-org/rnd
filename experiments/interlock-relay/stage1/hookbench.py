"""CPU-only bench of the traced transport's hook time, by component. Stub transport, no device, no network."""
import cProfile
import io
import json
import pstats
import statistics as st
import sys
import tempfile
import time
from pathlib import Path

from interlock.calltrace import Tracer, traced_transport

SEED = "The switchyard counts the same cars on every pass. "
BODIES = {
    "show": {"model": "qwen3:8b"},
    "decode-gen": {"model": "qwen3:8b", "prompt": "1 " + SEED * 3, "stream": False, "options": {"num_predict": 128}},
    "long-gen": {"model": "qwen3:8b", "prompt": "1 " + SEED * 2900, "stream": False, "options": {"num_predict": 16}},
}
PATH = {"show": "/api/show", "decode-gen": "/api/generate", "long-gen": "/api/generate"}
REPLY = {"response": "x" * 400, "prompt_eval_count": 30000, "eval_count": 16, "done": True}


def stub(method, url, body, *a, **k):
    return REPLY


def run(mode, name, n=300):
    root = Path(tempfile.mkdtemp())
    tr = Tracer(root=root, run_id=f"bench-{mode}-{name}", mode=mode)
    hooks = []
    with tr:
        t = traced_transport(stub, tr, device="5090")
        tr.set_emitting(mode != "off")
        for i in range(n):
            tr.begin_slot(arm="a", index=f"s{i}")
            t("POST", "http://127.0.0.1:11434" + PATH[name], BODIES[name])
            hooks.append(tr.end_slot()["hook_us"])
    return st.median(hooks[20:])


if __name__ == "__main__":
    for name in BODIES:
        size = len(json.dumps(BODIES[name]))
        t0 = time.perf_counter_ns()
        for _ in range(200):
            json.dumps(BODIES[name])
        dumps_us = (time.perf_counter_ns() - t0) / 200 / 1000
        off, relay = run("off", name), run("relay", name)
        print(f"{name:11s} body {size:7d} B  off {off:7.1f} us  relay {relay:7.1f} us  extra {relay-off:7.1f} us  json.dumps {dumps_us:6.1f} us")
    pr = cProfile.Profile()
    pr.enable()
    run("relay", "long-gen", 200)
    pr.disable()
    s = io.StringIO()
    pstats.Stats(pr, stream=s).sort_stats("tottime").print_stats(18)
    print(s.getvalue()[:4000])
