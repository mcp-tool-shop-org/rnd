# CONSULT | Argon | offrig embed-serve: resource safety before the next run | from R&D | 2026-10-15

**Status:** a CPU run went wrong today, and nothing runs again until this is settled.

**Record note:** Argon read the first version of this brief. The affinity-mask proposal and the measured core map in question 1, and the affinity line in the rerun plan, were added after it had been sent, so Argon didn't see them. The disposition says how they were ruled.

`embed-serve` is a small loopback server that runs EmbeddingGemma 2 (text only, 271M parameters, float32, CPU) behind Ollama's embedding API. offrig's project index calls it. It ships in offrig 1.2.0, after the benchmark that chose the model.

**What went wrong:**
- An end-to-end index rebuild (202 chunks) ran the server with torch's default thread count: all 24 logical cores of a Core Ultra 9 285K, with 63.4 GB RAM.
- The CPU went to 100%, and the Director had to kill it. R&D had already measured that torch takes every core, and ran it without a cap.
- No hardware was harmed, but the run took the shared machine from everything else on it, without warning. Other Claude sessions and the Director's own work run on the same rig.

**What R&D changed since:**
- `default_threads()` is half the logical cores (12 of 24). `--threads N` overrides it.
- `torch.set_num_threads` is always called.

**Measured (all on this rig, 2026-10-15):**
- 1.7 GiB resident once the model is loaded.
- Peak working set 3.1 GiB at sub-batch 8, which included a batch of the 32 longest chunks (about 1,500 tokens each). At batch 32 the peak was 6.8 GiB, with 8.5 GiB commit.
- At 24 threads: 96 chunks in about 35 s. At 12 threads: not measured.
- The parity check against the benchmark's vectors passed: cosine ≥ 0.9999999 on 96 chunks and 100 queries.

## Asked of you

1. **Is `torch.set_num_threads` enough to cap the CPU?** Name every other place this stack can start threads:
   - torch's inter-op pool;
   - OpenMP or MKL from the environment;
   - the Rust `tokenizers` library (RAYON / `TOKENIZERS_PARALLELISM`);
   - `ThreadingHTTPServer` itself.

   For each, say what must be set, and where (environment before import, or a call), so the process can't use more than N cores.

   **A proposal to judge (from the Publisher):** make the hard ceiling an OS one, not a thread count.
   - Launch the process with a CPU affinity mask (E-cores only, see the map below) at `BELOW_NORMAL` priority. Every thread and child process inherits both, however many threads torch, Rayon or OpenMP start.
   - `set_num_threads` then tunes performance only, matched to the mask.
   - The same would apply to a build: an 8-processor mask plus `-j 8`.

   **The core map, measured on this rig** (the Publisher read `GetSystemCpuSetInformation`). The CPU is 8 P-cores and 16 E-cores, with no hyper-threading.

   | Cores | Logical processors | Mask |
   |---|---|---|
   | The 8 P-cores (EfficiencyClass 1) | 0, 1, 10–13, 22, 23 | `0xC03C03` |
   | All 16 E-cores (EfficiencyClass 0) | 2–9, 14–21 | `0x3FC3FC` |
   | 12 E-cores | 2–9, 14–17 | `0x3C3FC` |
   | 8 E-cores (for a build at `-j 8`) | 2–9 | `0x3FC` |
   | 4 E-cores | 2–5 | `0x3C` |

   A naive `0xFFF` would take 4 P-cores and 8 E-cores.

   **The proposal:** background jobs are pinned to E-cores, so the P-cores stay free for the Director and the interactive sessions. Any timing taken under a mask names the cores it ran on, because E-core throughput is below the all-core benchmark figure.

   Is that sound on Windows, and how many E-cores should the server and a build each get? Should the server set its own affinity at start (for example through `psutil` or `SetProcessAffinityMask`), or should the launch line set it?
2. **Is half the cores the right default on a shared workstation?** Or should it be a fixed small number? Or should a lower OS process priority (Windows `BELOW_NORMAL`) be used instead or as well? Say which, and why.
3. **Memory.** Is there any input that can take RAM well past the 3.1 GiB measured? Consider:
   - a 32 MiB body;
   - many short texts in one request;
   - one text over the model's sequence length;
   - concurrent requests, which queue on one lock but each hold their parsed body.

   Name the bound the server should enforce (per-request text count, total characters, truncation length), with a value.
4. **Anything else in the code below that could put the machine at risk,** or that a security reviewer would flag. It binds 127.0.0.1 only and has no authentication, the same as Ollama.
5. **The rerun plan.** R&D proposes one rebuild of the 202-chunk test store at the new default (12 threads):
   - it's estimated at about 2–3 minutes, an inference that hasn't been measured;
   - the process runs on the 12 E-cores (`0x3C3FC`) at below-normal priority, with 12 threads, if you approve that; its time is reported as an E-core figure;
   - CPU utilisation is logged every 5 s from outside (`typeperf`), with a stop if total CPU holds above 60% for 10 s;
   - the peak working set is reported;
   - the Director is told before it starts.

   Is that plan sound, or what would you change?
6. **Verdict:** "approve as written", or the exact changes.

## The code (offrig `tools/embed-serve/embed_serve.py`, as it stands now)

```python
"""embed-serve: EmbeddingGemma 2 for offrig's project index, on the CPU, behind Ollama's embedding API.

Ollama on Windows cannot run EmbeddingGemma 2 (its library builds need MLX), so this small loopback server
answers the parts of Ollama's API that offrig's embed client calls: `/api/embed`, `/api/ps`, `/api/tags` and
`/api/version`. offrig points `embed_url` here unchanged (default http://127.0.0.1:11490).

- The model is google/embeddinggemma-2 at a pinned revision, text only (271M parameters), float32 on the CPU,
  run through sentence-transformers exactly as the benchmark that chose it ran it (rnd
  `experiments/embeddinggemma-2/`). Vectors are L2-normalized. offrig adds the task prefixes; the model adds none.
- It serves one name, `embeddinggemma-2:f32`, and answers 404 for any other. That matters: a server that
  embedded a `nomic-embed-text` request with this model would return 768-dimension vectors that pass every
  check offrig makes, and a store would silently mix two models.
- It never touches a GPU: it refuses to start when torch can see CUDA, and `/api/ps` reports `size_vram: 0`.
- Requests are encoded in sub-batches (default 8), which bounds the attention memory of long chunks.
- It uses half the machine's logical cores by default (`--threads N` sets another cap), because the rig is shared: with
  every core, a rebuild takes the whole CPU from everything else running.

    python embed_serve.py [--port 11490] [--sub-batch 8] [--threads N]
"""

from __future__ import annotations

import argparse
import os
import json
import math
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Protocol

VERSION = "embed-serve 1.0.0"
MODEL_NAME = "embeddinggemma-2:f32"
REPO = "google/embeddinggemma-2"
REVISION = "914f7f89142e33e77833254d9c9b90c3cef7303b"
DEFAULT_PORT = 11490
SHARED_OLLAMA_PORT = 11434
DEFAULT_SUB_BATCH = 8


def default_threads() -> int:
    """Half the logical cores, at least one: the rig is shared, so a rebuild never takes the whole CPU by default."""
    return max(1, (os.cpu_count() or 2) // 2)
MAX_TEXT_PARAMS = 300_000_000  # the text-only model is 271M; more means the vision or audio encoder loaded
MAX_BODY_BYTES = 32 * 1024 * 1024


class Encoder(Protocol):
    dim: int
    size_bytes: int

    def encode(self, texts: list[str]) -> list[list[float]]: ...


def refuse_if_cuda(torch) -> None:
    """Stop when this torch build can see a CUDA device: the server must never take the card."""
    if torch.cuda.is_available():
        raise SystemExit(
            "REFUSED: this torch build sees CUDA. embed-serve runs on the CPU only; install the CPU build "
            "(requirements.txt) or start it with CUDA_VISIBLE_DEVICES=-1"
        )


class SentenceTransformerEncoder:
    """The model, encoded in sub-batches of `sub_batch` texts."""

    def __init__(self, model, sub_batch: int, size_bytes: int):
        if sub_batch < 1:
            raise ValueError("sub_batch must be at least 1")
        self.model = model
        self.sub_batch = sub_batch
        self.size_bytes = size_bytes
        self.dim = int(model.get_embedding_dimension())

    def encode(self, texts: list[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for i in range(0, len(texts), self.sub_batch):
            part = texts[i : i + self.sub_batch]
            vecs = self.model.encode(
                part,
                batch_size=len(part),
                normalize_embeddings=True,
                convert_to_numpy=True,
                show_progress_bar=False,
            )
            out.extend(v.tolist() for v in vecs)
        return out


def load_encoder(sub_batch: int, threads: int) -> SentenceTransformerEncoder:
    import torch
    from sentence_transformers import SentenceTransformer

    refuse_if_cuda(torch)
    if threads < 1:
        raise SystemExit("REFUSED: --threads must be at least 1")
    torch.set_num_threads(threads)
    model = SentenceTransformer(
        REPO,
        revision=REVISION,
        device="cpu",
        model_kwargs={"torch_dtype": torch.float32},
        config_kwargs={"vision_config": None, "audio_config": None},
    )
    params = sum(p.numel() for p in model.parameters())
    if params > MAX_TEXT_PARAMS:
        raise SystemExit(f"REFUSED: {params / 1e6:.0f}M parameters loaded; the text-only model is 271M")
    return SentenceTransformerEncoder(model, sub_batch, size_bytes=params * 4)


class State:
    def __init__(self, encoder: Encoder):
        self.encoder = encoder
        self.lock = threading.Lock()  # one encode at a time: each encode already uses all the threads it is given
        self.started = time.time()


def _inputs(req: dict) -> list[str] | str:
    """The request's texts, or an error message."""
    raw = req.get("input", [])
    texts = [raw] if isinstance(raw, str) else raw
    if not isinstance(texts, list) or not all(isinstance(t, str) for t in texts):
        return "input must be a string or a list of strings"
    return texts


def handler_for(state: State):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, code: int, obj: dict) -> None:
            body = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args) -> None:  # quiet
            pass

        def do_GET(self) -> None:
            if self.path == "/api/version":
                return self._send(200, {"version": VERSION})
            if self.path == "/api/tags":
                return self._send(200, {"models": [{
                    "name": MODEL_NAME, "model": MODEL_NAME, "size": state.encoder.size_bytes,
                    "details": {"family": "gemma", "format": "safetensors", "parameter_size": "271M",
                                "quantization_level": "F32", "revision": REVISION}}]})
            if self.path == "/api/ps":
                return self._send(200, {"models": [{
                    "name": MODEL_NAME, "model": MODEL_NAME, "size": state.encoder.size_bytes, "size_vram": 0}]})
            if self.path == "/":
                return self._send(200, {"status": "embed-serve is running", "model": MODEL_NAME})
            return self._send(404, {"error": "not found"})

        def do_POST(self) -> None:
            if self.path != "/api/embed":
                return self._send(404, {"error": "not found"})
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_BODY_BYTES:
                return self._send(413, {"error": f"request body over {MAX_BODY_BYTES} bytes"})
            try:
                req = json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError:
                return self._send(400, {"error": "body is not JSON"})
            if not isinstance(req, dict):
                return self._send(400, {"error": "body must be a JSON object"})
            name = req.get("model", "")
            if name != MODEL_NAME:
                return self._send(404, {"error": f"model {name!r} not found; this server serves only {MODEL_NAME}"})
            texts = _inputs(req)
            if isinstance(texts, str):
                return self._send(400, {"error": texts})
            t0 = time.perf_counter()
            with state.lock:
                vecs = state.encoder.encode(texts)
            if len(vecs) != len(texts) or any(not all(math.isfinite(x) for x in v) for v in vecs):
                return self._send(500, {"error": "the model returned a missing or non-finite vector"})
            return self._send(200, {"model": MODEL_NAME, "embeddings": vecs,
                                    "total_duration": int((time.perf_counter() - t0) * 1e9)})

    return Handler


def make_server(encoder: Encoder, port: int) -> ThreadingHTTPServer:
    """A loopback server for `encoder`. Port 0 picks a free port (tests)."""
    if port == SHARED_OLLAMA_PORT:
        raise SystemExit(f"REFUSED: {SHARED_OLLAMA_PORT} is the shared Ollama's port")
    return ThreadingHTTPServer(("127.0.0.1", port), handler_for(State(encoder)))


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="EmbeddingGemma 2 on the CPU behind Ollama's embedding API")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--sub-batch", type=int, default=DEFAULT_SUB_BATCH)
    ap.add_argument("--threads", type=int, default=default_threads(), help="torch's CPU threads (default: half the logical cores)")
    a = ap.parse_args(argv)
    encoder = load_encoder(a.sub_batch, a.threads)
    srv = make_server(encoder, a.port)
    print(f"embed-serve: {MODEL_NAME} ({REPO}@{REVISION[:7]}, {encoder.dim}d, CPU) on "
          f"http://127.0.0.1:{a.port}, sub-batch {a.sub_batch}, threads {a.threads} of {os.cpu_count()}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
```

## The pinned requirements (`tools/embed-serve/requirements.txt`)

```text
# embed-serve's exact dependencies: Python 3.12, Windows or Linux on x86-64.
# torch is the CPU build from the PyTorch CPU index; the +cpu pin refuses any CUDA build.
# pillow and torchvision are needed although only text is embedded: the model's processor imports both on load.
#   python -m venv .venv && .venv/Scripts/python -m pip install -r requirements.txt   (Linux: .venv/bin/python)
# Locked from a fresh environment on 2026-10-15; these are the versions the benchmark that chose the model ran.
--extra-index-url https://download.pytorch.org/whl/cpu
annotated-doc==0.0.5
anyio==4.15.1
certifi==2026.7.22
click==8.5.0
cloudpickle==3.1.2
colorama==0.4.6 ; sys_platform == "win32"
filelock==4.2.0
fsspec==2026.9.0
h11==0.16.0
hf-xet==1.7.0
httpcore==1.0.9
httpx==0.28.1
huggingface-hub==1.33.0
idna==3.20
jinja2==3.1.6
joblib==1.6.0
markdown-it-py==4.2.0
markupsafe==3.0.4
mdurl==0.1.2
mpmath==1.3.0
narwhals==2.27.1
networkx==3.7
numpy==2.5.4
packaging==26.3
pillow==12.3.0
pygments==2.21.0
pyyaml==6.0.3
regex==2026.9.29
rich==15.0.0
safetensors==0.8.0
scikit-learn==1.9.1
scipy==1.18.1
sentence-transformers==6.1.0
setuptools==84.0.0
shellingham==1.5.4
sympy==1.14.0
threadpoolctl==3.7.0
tokenizers==0.23.3
torch==2.14.1+cpu
torchvision==0.29.1+cpu
tqdm==4.70.1
transformers==5.19.0
typer==0.27.3
typing-extensions==4.16.0
```
