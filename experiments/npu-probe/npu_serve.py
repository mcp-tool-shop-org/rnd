"""npu-serve: the rig's Intel side as a small local service. Embeddings on the NPU, NLI on the Intel iGPU.

It answers the parts of Ollama's API an embedding client uses (`/api/embed`, `/api/tags`, `/api/version`,
`/api/show`), so offrig, or anything that embeds through Ollama, can point its embed URL here unchanged. It
adds `/api/nli` for a cross-encoder, and `/health` for device status. Loopback only.
- Devices: NPU and the Intel iGPU (GPU.0, checked by name) only. The RTX 5090 is never used: it is shared
  through the Publisher's grants, and this service needs none.
- Found by the probe (results/2026-10-09-probe.json):
  - the NPU embeds about 10× faster than the CPU, with cosine ≥ 0.99999 against it;
  - DeBERTa NLI on the NPU is no faster than the CPU, and at batch 8 it hung the device (DEVICE_LOST). So
    NLI runs on the iGPU, at batch 1, about 6× the CPU.
- The NPU needs static shapes, so each embedder is compiled at a per-model ladder of sequence lengths
  (batch 1): 128/256/512 for bge, and 128/256/512/1024/2048 for nomic — the top rung covers the longest
  chunk in the benchmark corpora (1619 tokens; the CJK README translations are the tail), per
  results/2026-10-09-nomic-chunk-lengths.json. Each input goes to the smallest bucket that fits, and
  longer inputs are cut at the top rung, as Ollama does.
- Models are pinned (repo + revision) and the server never adds task prefixes: offrig adds
  "search_document: " / "search_query: " on its side, so a client of this service sees the same text twice.
- Fail loud, never silent: an inference error is a 503, and a DEVICE_LOST latches the device until restart.
  There is no CPU fallback — a slow wrong answer is worse than none.
- A per-call timeout (60 s, --call-timeout) latches the device as a hang. The timed-out call keeps running in
  a daemon thread, because a stuck device call can't be cancelled, so restart npu-serve before that device is
  used again.
- switchyard E1 (2026-10-09) measured nomic on the NPU at 2048 tokens just under the 0.999 parity guard
  (0.99861 against the CPU), and capped nomic NPU routing at 1024. The 2048 rung here predates that; check
  parity at 2048 before relying on it.

  E:/AI/envs/npu-openvino/Scripts/python.exe npu_serve.py [--port 11491] [--nli]
"""

import argparse
import hashlib
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np
import openvino as ov
from huggingface_hub import hf_hub_download
from optimum.intel import OVModelForFeatureExtraction, OVModelForSequenceClassification
from transformers import AutoTokenizer

from call_timeout import DEFAULT_CALL_TIMEOUT_S, CallTimeout, timed_call

VERSION = "npu-serve 0.2.0"
DEFAULT_BUCKETS = (128, 256, 512)  # a model's "buckets" spec overrides; nomic's top rung is
# measured, not guessed: see results/2026-10-09-nomic-chunk-lengths.json
MAX_INPUTS = 64  # texts per /api/embed call, pairs per /api/nli call
MAX_BODY = 1 << 20  # bytes per request body

# Every model: publisher, repo and revision pinned. "cls" pooling is bge's recipe; "mean" is nomic's
# (mean over the attention mask, then L2-normalize — confirmed against Ollama's GGUF in the match check).
MODELS = {
    "bge-base-en-v1.5": {"repo": "BAAI/bge-base-en-v1.5",
                         "revision": "a5beb1e3e68b9ab74eb54cfd186867f64f240e1a",
                         "format": "optimum", "pooling": "cls"},
    "bge-small-en-v1.5": {"repo": "BAAI/bge-small-en-v1.5",
                          "revision": "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a",
                          "format": "optimum", "pooling": "cls"},
    "nomic-embed-text": {"repo": "nomic-ai/nomic-embed-text-v1.5",
                         "revision": "e9b6763023c676ca8431644204f50c2b100d9aab",
                         "file": "onnx/model.onnx",
                         "format": "onnx", "pooling": "mean",
                         "buckets": (128, 256, 512, 1024, 2048)},
}
NLI_SPEC = {"name": "nli-deberta-v3-base", "repo": "cross-encoder/nli-deberta-v3-base",
            "revision": "6c749ce3425cd33b46d187e45b92bbf96ee12ec7"}


def intel_igpu(core: ov.Core) -> str:
    for d in core.available_devices:
        if d.startswith("GPU") and core.get_property(d, "FULL_DEVICE_NAME").startswith("Intel"):
            return d
    raise SystemExit("no Intel iGPU found; refusing to guess a GPU device (it could be the 5090)")


def _graph_digest(model: ov.Model) -> str:
    """A stable digest of an IR graph — op types and output shapes/types in order — for /api/tags.
    Not a file hash; for pinned ONNX files the file's sha256 is used instead."""
    h = hashlib.sha256()
    for op in model.get_ordered_ops():
        h.update(op.get_type_name().encode())
        h.update(op.get_friendly_name().encode())
        for out in op.outputs():
            h.update(str(out.get_element_type()).encode())
            h.update(str(out.get_partial_shape()).encode())
    return h.hexdigest()[:16]


class Embedder:
    """One embedder, compiled per length bucket on one device. `spec` pins repo and revision. Format
    "optimum" goes through OVModelForFeatureExtraction (bge); format "onnx" compiles the pinned ONNX file
    directly (nomic)."""
    def __init__(self, name: str, spec: dict, core: ov.Core, device: str):
        self.name, self.spec, self.device = name, spec, device
        self.buckets = tuple(sorted(spec.get("buckets", DEFAULT_BUCKETS)))
        self.tok = AutoTokenizer.from_pretrained(spec["repo"], revision=spec["revision"])
        self.models, self.dim = {}, None
        if spec["format"] == "optimum":
            for length in self.buckets:
                m = OVModelForFeatureExtraction.from_pretrained(spec["repo"], revision=spec["revision"],
                                                                export=True, compile=False)
                m.reshape(1, length)
                m.to(device)
                m.compile()
                self.models[length] = m
            base = self.models[self.buckets[-1]]
            self.dim = int(base.config.hidden_size)
            inner = getattr(base, "model", None)
            self.ir_digest = _graph_digest(inner) if inner is not None else "unknown"
        else:
            path = hf_hub_download(spec["repo"], spec["file"], revision=spec["revision"])
            with open(path, "rb") as f:
                self.ir_digest = "sha256:" + hashlib.sha256(f.read()).hexdigest()[:16]
            src = core.read_model(path)
            for length in self.buckets:
                m = src.clone()
                m.reshape({i.get_any_name(): [1, length] for i in m.inputs})
                self.models[length] = core.compile_model(m, device)
            out = next((o for o in src.outputs if "last_hidden_state" in o.get_any_name()), src.outputs[0])
            shape = out.get_partial_shape()
            if len(shape) == 3 and shape[2].is_static:
                self.dim = int(shape[2].get_length())

    def _forward(self, length: int, enc: dict) -> np.ndarray:
        m = self.models[length]
        if self.spec["format"] == "optimum":
            return np.asarray(m(**enc).last_hidden_state, dtype=np.float32)
        inputs = {}
        for k, v in enc.items():
            if k in {i.get_any_name() for i in m.inputs}:
                inputs[k] = v.astype(m.input(k).get_element_type().to_dtype())
        req = m.create_infer_request()
        out = next((o for o in m.outputs if "last_hidden_state" in o.get_any_name()), m.outputs[0])
        return np.asarray(req.infer(inputs)[out], dtype=np.float32)

    def embed(self, text: str) -> list[float]:
        n = len(self.tok(text, truncation=True, max_length=self.buckets[-1])["input_ids"])
        length = next(b for b in self.buckets if n <= b)
        enc = self.tok([text], padding="max_length", truncation=True, max_length=length, return_tensors="np")
        h = self._forward(length, enc)[0]  # [length, dim]
        if self.spec["pooling"] == "cls":
            v = h[0]
        else:  # mean pooling over the attention mask, then L2-normalize (nomic's recipe)
            mask = enc["attention_mask"][0].astype(np.float32)
            v = (h * mask[:, None]).sum(axis=0) / mask.sum()
        v = v / np.linalg.norm(v)
        self.dim = v.shape[0]
        return v.tolist()


class NLI:
    def __init__(self, core: ov.Core, device: str):
        self.device = device
        self.tok = AutoTokenizer.from_pretrained(NLI_SPEC["repo"], revision=NLI_SPEC["revision"])
        self.m = OVModelForSequenceClassification.from_pretrained(NLI_SPEC["repo"], export=True, compile=False,
                                                                  revision=NLI_SPEC["revision"])
        self.m.reshape(1, 512)
        self.m.to(device)
        self.m.compile()
        self.labels = [self.m.config.id2label[i].lower() for i in range(len(self.m.config.id2label))]
        inner = getattr(self.m, "model", None)
        self.ir_digest = _graph_digest(inner) if inner is not None else "unknown"

    def score(self, premise: str, hypothesis: str) -> dict:
        enc = self.tok([premise], [hypothesis], padding="max_length", truncation=True, max_length=512,
                       return_tensors="np")
        z = np.asarray(self.m(**enc).logits[0], dtype=np.float64)
        p = np.exp(z - z.max())
        p /= p.sum()
        return {"label": self.labels[int(p.argmax())], "probs": dict(zip(self.labels, p.round(4).tolist()))}


class State:
    def __init__(self):
        self.lock = threading.Lock()  # one inference at a time: OpenVINO requests here are not shared
        self.embedders: dict = {}
        self.nli: NLI | None = None
        self.started = time.time()
        self.device_lost: dict | None = None  # {"device", "error", "at"} on DEVICE_LOST or a call hang
        self.call_timeout_s = DEFAULT_CALL_TIMEOUT_S  # per device call; 0 disables ("hang:" error prefix)


def _model_details(e: Embedder) -> dict:
    return {"family": "bert", "format": e.spec["format"], "device": e.device,
            "repo": e.spec["repo"], "revision": e.spec["revision"], "ir_digest": e.ir_digest,
            "dim": e.dim, "pooling": e.spec["pooling"],
            "prefixes": "added by the client, not by npu-serve"}


def handler_for(state: State):
    class H(BaseHTTPRequestHandler):
        timeout = 120  # drop stalled connections: one slow reader must not hold a server thread

        def _send(self, code: int, obj: dict):
            body = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _body(self):
            """The request body as JSON, bounded, or None after answering 400/413."""
            n = int(self.headers.get("Content-Length", 0))
            if n > MAX_BODY:
                self._send(413, {"error": f"body over {MAX_BODY} bytes"})
                return None
            try:
                req = json.loads(self.rfile.read(n) or b"{}")
            except json.JSONDecodeError:
                self._send(400, {"error": "body is not JSON"})
                return None
            return req if isinstance(req, dict) else (self._send(400, {"error": "body is not a JSON object"}), None)[1]

        def _failed(self, device: str, exc: Exception):
            hang = isinstance(exc, CallTimeout)
            if hang or "DEVICE_LOST" in str(exc):
                kind = "hang" if hang else "device_lost"
                state.device_lost = {"device": device, "kind": kind,
                                     "error": ("hang: " if hang else "") + str(exc)[:200], "at": time.time()}
                print(f"{kind.upper()} on {device}, latched until restart: {exc}", flush=True)
            return self._send(503, {"error": f"inference failed on {device}: {type(exc).__name__}: "
                                             f"{str(exc)[:200]}"})

        def _latch_check(self):
            if state.device_lost:
                self._send(503, {"error": f"device {state.device_lost['device']} is off after a "
                                          f"{state.device_lost.get('kind', 'device_lost')} event; restart npu-serve",
                                 "device_lost": state.device_lost})
                return True
            return False

        def log_message(self, *a):  # quiet
            pass

        def do_GET(self):
            if self.path == "/api/tags":
                return self._send(200, {"models": [{"name": n, "model": n, "details": _model_details(e)}
                                                   for n, e in state.embedders.items()]})
            if self.path == "/api/version":
                return self._send(200, {"version": VERSION})
            if self.path == "/health":
                return self._send(200, {
                    "status": "device_lost" if state.device_lost else "ok",
                    "version": VERSION, "uptime_s": round(time.time() - state.started),
                    "device_lost": state.device_lost,
                    "models": {n: {"device": e.device, "dim": e.dim, "pooling": e.spec["pooling"]}
                               for n, e in state.embedders.items()},
                    "nli": None if state.nli is None else {"device": state.nli.device, "model": NLI_SPEC["repo"]}})
            if self.path == "/":
                return self._send(200, {"status": "npu-serve is running", "health": "/health"})
            return self._send(404, {"error": "not found"})

        def do_POST(self):
            req = self._body()
            if req is None:
                return
            if self.path == "/api/embed":
                name = req.get("model", "")
                e = state.embedders.get(name.split(":")[0])
                if e is None:
                    return self._send(404, {"error": f"model {name!r} not found; have {sorted(state.embedders)}"})
                inputs = req.get("input", [])
                inputs = [inputs] if isinstance(inputs, str) else inputs
                if not isinstance(inputs, list) or len(inputs) > MAX_INPUTS:
                    return self._send(400, {"error": f"input must be a list of at most {MAX_INPUTS} texts"})
                if not all(isinstance(t, str) for t in inputs):
                    return self._send(400, {"error": "every input must be a string"})
                if self._latch_check():
                    return
                t0 = time.perf_counter()
                print(f"embed {name} on {e.device}: {len(inputs)} text(s), timeout {state.call_timeout_s:g}s", flush=True)
                try:
                    with state.lock:
                        vecs = [timed_call(state.call_timeout_s, e.embed, t) for t in inputs]
                except Exception as exc:
                    print(f"embed {name} failed after {(time.perf_counter() - t0) * 1000:.0f} ms: {exc}", flush=True)
                    return self._failed(e.device, exc)
                print(f"embed {name} done in {(time.perf_counter() - t0) * 1000:.0f} ms", flush=True)
                return self._send(200, {"model": name, "embeddings": vecs,
                                        "total_duration": int((time.perf_counter() - t0) * 1e9)})
            if self.path == "/api/nli":
                if state.nli is None:
                    return self._send(404, {"error": "NLI is off; start with --nli"})
                pairs = req.get("pairs") or [[req.get("premise", ""), req.get("hypothesis", "")]]
                if len(pairs) > MAX_INPUTS:
                    return self._send(400, {"error": f"at most {MAX_INPUTS} pairs per call"})
                if self._latch_check():
                    return
                print(f"nli on {state.nli.device}: {len(pairs)} pair(s), timeout {state.call_timeout_s:g}s", flush=True)
                try:
                    with state.lock:
                        out = [timed_call(state.call_timeout_s, state.nli.score, p, h) for p, h in pairs]
                except Exception as exc:
                    print(f"nli failed on {state.nli.device}: {exc}", flush=True)
                    return self._failed(state.nli.device, exc)
                return self._send(200, {"model": NLI_SPEC["name"], "results": out})
            if self.path == "/api/show":
                name = (req.get("model") or req.get("name") or "").split(":")[0]
                e = state.embedders.get(name)
                if e is not None:
                    return self._send(200, {"model": name, **_model_details(e)})
                if name == NLI_SPEC["name"] and state.nli is not None:
                    return self._send(200, {"model": name, "repo": NLI_SPEC["repo"],
                                            "revision": NLI_SPEC["revision"], "device": state.nli.device,
                                            "ir_digest": state.nli.ir_digest, "labels": state.nli.labels})
                return self._send(404, {"error": f"model {name!r} not found"})
            return self._send(404, {"error": "not found"})

    return H


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=11491)
    ap.add_argument("--models", default="bge-base-en-v1.5",
                    help=f"comma-separated; known: {sorted(MODELS)}")
    ap.add_argument("--nli", action="store_true", help="also load the NLI cross-encoder on the Intel iGPU")
    ap.add_argument("--device", default="npu", choices=["npu", "cpu"],
                    help="where embedders compile; cpu is for the CPU-window baselines, never a silent NPU skip")
    ap.add_argument("--call-timeout", type=float, default=DEFAULT_CALL_TIMEOUT_S,
                    help="per device call, seconds (default 60, matches switchyard); 0 disables")
    a = ap.parse_args()
    core = ov.Core()
    device = {"npu": "NPU", "cpu": "CPU"}[a.device]
    if device == "NPU" and "NPU" not in core.available_devices:
        raise SystemExit("no NPU visible to OpenVINO")
    if device == "CPU" and a.nli:
        raise SystemExit("--nli is iGPU-pinned; a CPU-only window (the Publisher's) stays CPU-only")
    state = State()
    state.call_timeout_s = a.call_timeout
    for n in a.models.split(","):
        n = n.strip()
        state.embedders[n] = Embedder(n, MODELS[n], core, device)
        print(f"loaded {n} on {device} (dim {state.embedders[n].dim}, {state.embedders[n].spec['pooling']} pooling, "
              f"{state.embedders[n].spec['repo']}@{state.embedders[n].spec['revision'][:8]})", flush=True)
    if a.nli:
        state.nli = NLI(core, intel_igpu(core))
        print(f"loaded {NLI_SPEC['repo']} on {intel_igpu(core)}", flush=True)
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), handler_for(state))
    print(f"npu-serve on http://127.0.0.1:{a.port}", flush=True)
    srv.daemon_threads = True
    srv.serve_forever()


if __name__ == "__main__":
    main()
