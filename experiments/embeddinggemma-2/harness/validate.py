"""The free validation run (design v3, section 6.2). Nothing it produces is counted.

1. Tokenizer pre-check: every frozen chunk, with its arm's prefix, tokenized with nomic's WordPiece tokenizer and
   EmbeddingGemma 2's tokenizer. Stops if any exceeds 2,048 tokens.
2. Dtype gate: 50 chunks through arm B in float32 and in bfloat16. The pairwise cosine must be >= 0.999. The faster
   dtype is recorded as arm B's.
3. Throughput behind HTTP: 1,024 chunks through arm A's Ollama (as deployed), and through arm B behind a minimal
   loopback server in npu-serve's shape (/api/embed), both at batch 32.

Writes results/validation.json. The 5-query end-to-end check is embed.py and rank.py with --limit 512 on the
first five queries, run by hand after this.

Run: E:/AI/envs/embedgemma/Scripts/python.exe validate.py
"""

from __future__ import annotations

import json
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np

from common import A_DOC, B_DOC, BATCH, CHUNKS, RESULTS, read_jsonl
from embed import embed_a, embed_b, load_b

LIMIT_TOKENS = 2048
SAMPLE = 1024


def tokenizer_check(chunks: list[dict]) -> dict:
    from huggingface_hub import hf_hub_download
    from tokenizers import Tokenizer
    from transformers import AutoTokenizer

    nomic = Tokenizer.from_file(hf_hub_download("nomic-ai/nomic-embed-text-v1.5", "tokenizer.json"))
    eg2 = AutoTokenizer.from_pretrained("google/embeddinggemma-2")
    a = [len(nomic.encode(A_DOC + c["body"]).ids) for c in chunks]
    b = [len(eg2(B_DOC + c["body"])["input_ids"]) for c in chunks]
    out = {"nomic_max": max(a), "eg2_max": max(b), "nomic_p99": int(np.percentile(a, 99)), "eg2_p99": int(np.percentile(b, 99)),
           "over_limit": sum(1 for x, y in zip(a, b) if x > LIMIT_TOKENS or y > LIMIT_TOKENS)}
    if out["over_limit"]:
        raise SystemExit(f"STOP: {out['over_limit']} chunks exceed {LIMIT_TOKENS} tokens: {out}")
    return out


def dtype_gate(chunks: list[dict]) -> dict:
    texts = [B_DOC + c["body"] for c in chunks[:50]]
    res = {}
    vecs = {}
    for dtype in ("float32", "bfloat16"):
        model, _ = load_b(dtype)
        embed_b(model, texts[:4])  # warm
        t0 = time.perf_counter()
        vecs[dtype] = embed_b(model, texts)
        res[f"{dtype}_seconds"] = round(time.perf_counter() - t0, 3)
        del model
    cos = np.sum(vecs["float32"] * vecs["bfloat16"], axis=1)
    res["cosine_min"] = float(cos.min())
    res["cosine_mean"] = float(cos.mean())
    res["parity_ok"] = bool(cos.min() >= 0.999)
    res["chosen"] = ("bfloat16" if res["parity_ok"] and res["bfloat16_seconds"] < res["float32_seconds"] else "float32")
    return res


class _Handler(BaseHTTPRequestHandler):
    model = None

    def do_POST(self):  # noqa: N802
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        vecs = embed_b(self.model, body["input"]).tolist()
        data = json.dumps({"model": "embeddinggemma-2", "embeddings": vecs}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass


def wrapped_b(chunks: list[dict], dtype: str) -> float:
    _Handler.model, _ = load_b(dtype)
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_address[1]}/api/embed"
    texts = [B_DOC + c["body"] for c in chunks]
    t0 = time.perf_counter()
    for i in range(0, len(texts), BATCH):
        req = urllib.request.Request(url, data=json.dumps({"input": texts[i:i + BATCH]}).encode(),
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=600).read()
    secs = time.perf_counter() - t0
    server.shutdown()
    return secs


def main() -> None:
    chunks = read_jsonl(CHUNKS)
    out = {"tokens": tokenizer_check(chunks)}
    print("tokens", out["tokens"])
    out["dtype_gate"] = dtype_gate(chunks)
    print("dtype", out["dtype_gate"])
    rng = np.random.default_rng(3)
    sample = [chunks[i] for i in sorted(rng.choice(len(chunks), SAMPLE, replace=False))]
    embed_a([A_DOC + c["body"] for c in sample[:BATCH]])  # load and warm
    t0 = time.perf_counter()
    embed_a([A_DOC + c["body"] for c in sample])
    a_secs = time.perf_counter() - t0
    b_secs = wrapped_b(sample, out["dtype_gate"]["chosen"])
    out["http_throughput"] = {"sample": SAMPLE, "A_chunks_per_second": round(SAMPLE / a_secs, 2),
                              "B_chunks_per_second": round(SAMPLE / b_secs, 2),
                              "B_over_A": round(a_secs / b_secs, 3)}
    print("http", out["http_throughput"])
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "validation.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
