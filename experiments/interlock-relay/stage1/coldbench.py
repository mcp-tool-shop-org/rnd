"""CPU-only cold-wake bench (Argon's test): a two-call slot (show + generate) behind the stage's barrier (trace flush,
gc.collect, 250 ms rest), with the stub transport blocking as the live server does (show ~2 ms, generate ~300 ms).
No device, no network. Reports the per-slot hook time, untraced and traced, as the stage's client-time gate reads it."""
import gc
import statistics as st
import sys
import tempfile
import time
from pathlib import Path

from interlock.calltrace import Tracer, traced_transport

SEED = "The switchyard counts the same cars on every pass. "
SHOW = {"model": "qwen3:8b"}
GEN = {"decode": {"model": "qwen3:8b", "prompt": "1 " + SEED * 3, "stream": False, "options": {"num_predict": 128}},
       "long": {"model": "qwen3:8b", "prompt": "1 " + SEED * 2900, "stream": False, "options": {"num_predict": 16}}}
REPLY = {"response": "x" * 400, "prompt_eval_count": 30000, "eval_count": 16, "done": True}
URL = "http://127.0.0.1:11434"


def stub(method, url, body, *a, **k):
    time.sleep(0.002 if url.endswith("/api/show") else 0.3)
    return REPLY


def slots(mode: str, pair: str, n: int, cold: bool) -> list[float]:
    tr = Tracer(root=Path(tempfile.mkdtemp()), run_id=f"cold-{mode}-{pair}", mode=mode)
    out = []
    with tr:
        t = traced_transport(stub if cold else (lambda *a, **k: REPLY), tr, device="5090")
        for i in range(n):
            if cold:
                tr.flush()
                gc.collect()
                time.sleep(0.25)
            tr.begin_slot(arm="a", index=f"s{i}")
            tr.set_emitting(mode != "off")
            t("POST", URL + "/api/show", SHOW)
            t("POST", URL + "/api/generate", GEN[pair])
            out.append(tr.end_slot()["hook_us"])
            tr.set_emitting(False)
    return out[3:]


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    for pair in ("decode", "long"):
        for cold in (False, True):
            off, relay = slots("off", pair, n, cold), slots("relay", pair, n, cold)
            diff = st.median(relay) - st.median(off)
            print(f"{pair:6s} {'cold' if cold else 'warm'}  untraced {st.median(off):7.1f} us  traced {st.median(relay):7.1f} us"
                  f"  traced-untraced {diff:7.1f} us  (p90 traced {sorted(relay)[int(0.9*len(relay))]:7.1f})")
