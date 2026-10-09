"""npu-serve: the rig's Intel side as a small local service. Embeddings on the NPU, NLI on the Intel iGPU.

It answers the parts of Ollama's API an embedding client uses (`/api/embed`, `/api/tags`, `/api/version`),
so offrig, or anything that embeds through Ollama, can point its embed URL here unchanged. It adds
`/api/nli` for a cross-encoder. Loopback only.
- Devices: NPU and the Intel iGPU (GPU.0, checked by name) only. The RTX 5090 is never used: it is shared
  through the Publisher's grants, and this service needs none.
- Found by the probe (results/2026-10-09-probe.json):
  - the NPU embeds about 10× faster than the CPU, with cosine ≥ 0.99999 against it;
  - DeBERTa NLI on the NPU is no faster than the CPU, and at batch 8 it hung the device (DEVICE_LOST). So
    NLI runs on the iGPU, at batch 1, about 6× the CPU.
- The NPU needs static shapes, so each embedder is compiled at sequence lengths 128, 256 and 512 (batch 1).
  Each input goes to the smallest bucket that fits, and longer inputs are cut at 512 tokens, as Ollama does.

  E:/AI/envs/npu-openvino/Scripts/python.exe npu_serve.py [--port 11491] [--nli]
"""

import argparse
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np
import openvino as ov
from optimum.intel import OVModelForFeatureExtraction, OVModelForSequenceClassification
from transformers import AutoTokenizer

VERSION = "npu-serve 0.1.0"
EMBEDDERS = {"bge-base-en-v1.5": "BAAI/bge-base-en-v1.5", "bge-small-en-v1.5": "BAAI/bge-small-en-v1.5"}
NLI_MODEL = "cross-encoder/nli-deberta-v3-base"
BUCKETS = (128, 256, 512)


def intel_igpu(core: ov.Core) -> str:
    for d in core.available_devices:
        if d.startswith("GPU") and core.get_property(d, "FULL_DEVICE_NAME").startswith("Intel"):
            return d
    raise SystemExit("no Intel iGPU found; refusing to guess a GPU device (it could be the 5090)")


class Embedder:
    def __init__(self, repo: str, device: str):
        self.tok = AutoTokenizer.from_pretrained(repo)
        self.models = {}
        for L in BUCKETS:
            m = OVModelForFeatureExtraction.from_pretrained(repo, export=True, compile=False)
            m.reshape(1, L)
            m.to(device)
            m.compile()
            self.models[L] = m
        self.dim = None

    def embed(self, text: str) -> list[float]:
        n = len(self.tok(text, truncation=True, max_length=BUCKETS[-1])["input_ids"])
        L = next(b for b in BUCKETS if n <= b)
        enc = self.tok([text], padding="max_length", truncation=True, max_length=L, return_tensors="np")
        v = np.asarray(self.models[L](**enc).last_hidden_state[0, 0], dtype=np.float32)  # CLS, as bge specifies
        v = v / np.linalg.norm(v)
        self.dim = v.shape[0]
        return v.tolist()


class NLI:
    def __init__(self, device: str):
        self.tok = AutoTokenizer.from_pretrained(NLI_MODEL)
        self.m = OVModelForSequenceClassification.from_pretrained(NLI_MODEL, export=True, compile=False)
        self.m.reshape(1, 512)
        self.m.to(device)
        self.m.compile()
        self.labels = [self.m.config.id2label[i].lower() for i in range(len(self.m.config.id2label))]

    def score(self, premise: str, hypothesis: str) -> dict:
        enc = self.tok([premise], [hypothesis], padding="max_length", truncation=True, max_length=512,
                       return_tensors="np")
        z = np.asarray(self.m(**enc).logits[0], dtype=np.float64)
        p = np.exp(z - z.max())
        p /= p.sum()
        return {"label": self.labels[int(p.argmax())], "probs": dict(zip(self.labels, p.round(4).tolist()))}


class State:
    lock = threading.Lock()  # one inference at a time per device: OpenVINO requests here are not shared
    embedders: dict = {}
    nli: NLI | None = None
    started = time.time()


def handler_for(state: State):
    class H(BaseHTTPRequestHandler):
        def _send(self, code: int, obj: dict):
            body = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):  # quiet
            pass

        def do_GET(self):
            if self.path == "/api/tags":
                return self._send(200, {"models": [{"name": n, "model": n, "details": {"family": "bert",
                                        "format": "openvino", "device": "NPU"}} for n in state.embedders]})
            if self.path == "/api/version":
                return self._send(200, {"version": VERSION})
            if self.path == "/":
                return self._send(200, {"status": "npu-serve is running"})
            return self._send(404, {"error": "not found"})

        def do_POST(self):
            try:
                req = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            except json.JSONDecodeError:
                return self._send(400, {"error": "body is not JSON"})
            if self.path == "/api/embed":
                name = req.get("model", "")
                e = state.embedders.get(name.split(":")[0])
                if e is None:
                    return self._send(404, {"error": f"model {name!r} not found; have {sorted(state.embedders)}"})
                inputs = req.get("input", [])
                inputs = [inputs] if isinstance(inputs, str) else inputs
                t0 = time.perf_counter()
                with state.lock:
                    vecs = [e.embed(t) for t in inputs]
                return self._send(200, {"model": name, "embeddings": vecs,
                                        "total_duration": int((time.perf_counter() - t0) * 1e9)})
            if self.path == "/api/nli":
                if state.nli is None:
                    return self._send(404, {"error": "NLI is off; start with --nli"})
                pairs = req.get("pairs") or [[req.get("premise", ""), req.get("hypothesis", "")]]
                with state.lock:
                    out = [state.nli.score(p, h) for p, h in pairs]
                return self._send(200, {"model": NLI_MODEL, "results": out})
            return self._send(404, {"error": "not found"})

    return H


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=11491)
    ap.add_argument("--models", default="bge-base-en-v1.5")
    ap.add_argument("--nli", action="store_true", help="also load the NLI cross-encoder on the Intel iGPU")
    a = ap.parse_args()
    core = ov.Core()
    if "NPU" not in core.available_devices:
        raise SystemExit("no NPU visible to OpenVINO")
    state = State()
    for n in a.models.split(","):
        state.embedders[n] = Embedder(EMBEDDERS[n], "NPU")
        print(f"loaded {n} on NPU", flush=True)
    if a.nli:
        state.nli = NLI(intel_igpu(core))
        print(f"loaded {NLI_MODEL} on {intel_igpu(core)}", flush=True)
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), handler_for(state))
    print(f"npu-serve on http://127.0.0.1:{a.port}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
