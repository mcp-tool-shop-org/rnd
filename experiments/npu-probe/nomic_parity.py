#!/usr/bin/env python3
"""The retrieval benchmark's option-C match check (retrieval-benchmark.md, pre-registered 2026-10-09):
does the pinned ONNX nomic, run through OpenVINO, produce the same vectors as the Ollama GGUF copy
offrig indexes with today?

Reads scratch offrig stores (schema v6 @ a45fe53: chunks(id, source, kind, title, ordinal, body) and
embeddings(chunk_id, model, dim, vec int8 BLOB, scale)). A stored chunk's body is exactly what offrig
embedded (its header line is written into body, index.rs @ a45fe53); prefixes are offrig's own
task_prefix rule: "search_document: " / "search_query: " when the model starts with nomic-embed-text,
else none.

Every chunk and each query (the benchmark's grounded facts, true and near-miss forms, from
facts_roleos.py / facts_offrig.py / facts_roleos_docs.py in experiments/verifier-gold) is embedded:
  A-fresh:  the Ollama GGUF at --ollama (default http://127.0.0.1:11490, offrig's CPU-only server);
  C:        nomic-ai/nomic-embed-text-v1.5 @ e9b6763023c676ca8431644204f50c2b100d9aab onnx/model.onnx
            through npu_serve's Embedder (mean pooling over the attention mask, L2), on --device;
  A-stored: the index's own int8 vectors, dequantized x ~ q * scale (index.rs quantize/dequantize).

Pre-registered bound: C counts as the same model as A iff the MINIMUM cosine over every chunk and query
(C vs A-fresh) is >= 0.995. The receipt reports min / mean / p1 for C vs A-fresh, C vs A-stored, and
A-fresh vs A-stored (what int8 storage alone costs), the worst 5 items with lengths and truncation, and
how many documents overflow the 512-token mark, and how many overflow the top bucket (the latter should be zero:
the ladder is measured to cover the corpus, results/2026-10-09-nomic-chunk-lengths.json).

The --device npu leg needs a Publisher-logged NPU window (one exclusive device). The cpu leg loads the
CPU through Ollama, so it waits for the Publisher's card-free like the rest of the lane. The 5090 is
never used: the only device strings here are OpenVINO's "CPU" and "NPU".

  nomic_parity.py --store role-os=E:/AI/rnd-npu-index/role-os/<store>.db \
                  --store offrig=E:/AI/rnd-npu-index/offrig/<store>.db \
                  --device cpu --out results/2026-XX-nomic-parity-cpu.json
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
NPU_SERVE = HERE / "npu_serve.py"
FACTS_DIR = REPO_ROOT / "experiments" / "verifier-gold"
FACTS_FILES = ["facts_roleos.py", "facts_offrig.py", "facts_roleos_docs.py"]

BOUND = 0.995  # the pre-registered match bound on the minimum cosine
NOMIC_ONNX = {"repo": "nomic-ai/nomic-embed-text-v1.5",
              "revision": "e9b6763023c676ca8431644204f50c2b100d9aab", "file": "onnx/model.onnx"}
OLLAMA_BATCH = 32  # texts per /api/embed call


def task_prefix(model: str, task: str) -> str:
    """offrig's task_prefix (index.rs @ a45fe53), mirrored: nomic-embed-text* gets its trained
    prefixes, every other model gets none. task is "document" or "query"."""
    if not model.startswith("nomic-embed-text"):
        return ""
    return "search_document: " if task == "document" else "search_query: "


def dequantize(q: bytes, scale: float) -> list:
    """Stored int8 -> float: x ~ q * scale (index.rs dequantize). The blob is raw signed bytes."""
    return [int.from_bytes(bytes([b]), "big", signed=True) * scale for b in q]


def quantize(v: list) -> tuple:
    """The Rust quantize, mirrored for round-trip tests: scale = max|x| / 127, q = round(x/scale)
    clamped to [-127, 127]."""
    m = max(abs(x) for x in v)
    if m == 0.0:
        return bytes(len(v)), 0.0
    scale = m / 127.0
    q = bytes((max(-127, min(127, round(x / scale))) & 0xFF) for x in v)
    return q, scale


def cosine(a: list, b: list) -> float:
    """Cosine with a float64 accumulator; a zero vector gives 0.0, as in index.rs's test."""
    dot = math.fsum(x * y for x, y in zip(a, b))
    na = math.sqrt(math.fsum(x * x for x in a))
    nb = math.sqrt(math.fsum(x * x for x in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


def p1(values: list) -> float:
    """The 1st percentile, nearest-rank: the bound cares about the tail, and this is pinned so the
    receipt's p1 means one exact thing."""
    s = sorted(values)
    return s[max(0, math.ceil(0.01 * len(s)) - 1)]


def stats(values: list) -> dict:
    return {"n": len(values), "min": min(values), "mean": math.fsum(values) / len(values),
            "p1": p1(values)}


def read_store(path: Path) -> tuple:
    """One scratch store: (embed_model, dim, chunks, stored). chunks is a list of {chunk_id, source,
    body}; stored maps chunk_id -> dequantized vector. Refuses a store whose rows mix models or dims:
    that is exactly the mixed-vector case the index's check_model/check_dim guards."""
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        model = con.execute("SELECT value FROM settings WHERE key='embed_model'").fetchone()
        dim = con.execute("SELECT value FROM settings WHERE key='embed_dim'").fetchone()
        if model is None or dim is None:
            raise SystemExit(f"{path}: no embed_model/embed_dim in settings; index the project first")
        model, dim = model[0], int(dim[0])
        chunks = [{"chunk_id": cid, "source": src, "body": body} for cid, src, body in
                  con.execute("SELECT id, source, body FROM chunks ORDER BY id")]
        models = {r[0] for r in con.execute("SELECT DISTINCT model FROM embeddings")}
        dims = {r[0] for r in con.execute("SELECT DISTINCT dim FROM embeddings")}
        if models != {model} or dims != {dim}:
            raise SystemExit(f"{path}: embeddings mix {models}/{dims} against settings {model}/{dim}")
        stored = {}
        for cid, vec, scale in con.execute("SELECT chunk_id, vec, scale FROM embeddings"):
            v = dequantize(vec, scale)
            if len(v) != dim:
                raise SystemExit(f"{path}: chunk {cid} vector is {len(v)}-d, settings say {dim}")
            stored[cid] = v
        if {c["chunk_id"] for c in chunks} != set(stored):
            raise SystemExit(f"{path}: chunks and embeddings disagree on which chunks exist")
        return model, dim, chunks, stored
    finally:
        con.close()


def queries_from_facts(facts_dir: Path = FACTS_DIR) -> list:
    """The benchmark's queries: each fact's true and near-miss forms, id-tagged, in file order.
    Returns [(query_id, text)]."""
    queries = []
    for name in FACTS_FILES:
        spec = importlib.util.spec_from_file_location(name[:-3], facts_dir / name)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for fact in mod.FACTS:
            queries.append((fact["id"] + ":true", fact["true"]))
            queries.append((fact["id"] + ":false", fact["false"]))
    return queries


def embed_ollama(base: str, model: str, texts: list, task: str) -> list:
    """A-fresh: embed through the Ollama copy offrig uses, with offrig's own prefix rule. Batches of
    OLLAMA_BATCH; a non-200 aborts the run."""
    prefix = task_prefix(model, task)
    out = []
    for i in range(0, len(texts), OLLAMA_BATCH):
        batch = [prefix + t for t in texts[i:i + OLLAMA_BATCH]]
        body = json.dumps({"model": model, "input": batch}).encode()
        req = urllib.request.Request(base.rstrip("/") + "/api/embed", data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=600) as r:
            if r.status != 200:
                raise SystemExit(f"{base}/api/embed answered {r.status}; aborting")
            out.extend(json.loads(r.read())["embeddings"])
    return out


def parse_show(payload: dict) -> dict:
    """Ollama /api/show -> the effective context window for this model: num_ctx from the Modelfile
    parameters when set, otherwise the architecture's context_length (Ollama's default since mid-2025
    is the model's own length). If neither is readable we refuse to run: a reference that might
    silently truncate is worse than none."""
    num_ctx = None
    for line in str(payload.get("parameters") or "").splitlines():
        parts = line.split()
        if parts[:1] == ["num_ctx"] and len(parts) > 1:
            try:
                num_ctx = int(parts[1])
            except ValueError:
                pass
    lengths = {v for k, v in (payload.get("model_info") or {}).items()
               if isinstance(k, str) and k.endswith(".context_length")}
    context_length = lengths.pop() if len(lengths) == 1 else None
    effective = num_ctx if num_ctx is not None else context_length
    if effective is None:
        raise SystemExit("could not establish the reference model's context window from /api/show; "
                         "refusing to run a reference that might silently truncate")
    return {"num_ctx": num_ctx, "context_length": context_length, "effective": effective}


def ollama_context(base: str, model: str) -> dict:
    """/api/show for the reference model on offrig's CPU-only server, before anything is embedded."""
    url = base.rstrip("/") + "/api/show"
    req = urllib.request.Request(url, data=json.dumps({"model": model}).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            if r.status != 200:
                raise SystemExit(f"{url} answered {r.status} for {model}; aborting")
            payload = json.loads(r.read())
    except urllib.error.URLError as e:
        raise SystemExit(f"no Ollama answers at {url}: {e}; A-fresh needs offrig's CPU-only server") from e
    return parse_show(payload)


def load_onnx_nomic(device: str):
    """C: the pinned ONNX nomic through npu_serve's Embedder. device is exactly 'CPU' or 'NPU';
    nothing else is allowed in this lane."""
    if device not in ("CPU", "NPU"):
        raise SystemExit(f"--device must be cpu or npu (got {device!r}); this lane never guesses a GPU")
    spec = importlib.util.spec_from_file_location("npu_serve", NPU_SERVE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    import openvino as ov
    core = ov.Core()
    return mod, mod.Embedder("nomic-embed-text",
                             {**NOMIC_ONNX, "format": "onnx", "pooling": "mean"}, core, device)


def worst_k(items: list, k: int = 5) -> list:
    return sorted(items, key=lambda r: r["cos"]["c_vs_a_fresh"])[:k]


def compare(items: list, key: str) -> dict:
    return stats([r["cos"][key] for r in items])


def main() -> None:
    ap = argparse.ArgumentParser(description="The option-C match check (retrieval-benchmark.md).")
    ap.add_argument("--store", action="append", required=True, metavar="NAME=PATH",
                    help="a scratch-project offrig store; repeat per corpus")
    ap.add_argument("--device", default="cpu", choices=["cpu", "npu"],
                    help="where the pinned ONNX runs; npu legs need a Publisher-logged window")
    ap.add_argument("--ollama", default="http://127.0.0.1:11490",
                    help="offrig's CPU-only Ollama (A-fresh)")
    ap.add_argument("--out", required=True, type=Path, help="the receipt JSON")
    ap.add_argument("--limit", type=int, default=None,
                    help="first N chunks and queries (smoke; the receipt is marked)")
    a = ap.parse_args()

    stores = {}
    all_chunks = []
    for spec in a.store:
        name, _, path = spec.partition("=")
        if not name or not path:
            raise SystemExit(f"--store wants NAME=PATH, got {spec!r}")
        model, dim, chunks, stored = read_store(Path(path))
        stores[name] = {"path": path, "embed_model": model, "dim": dim, "chunks": len(chunks)}
        for c in chunks:
            c["store"] = name
        for c in chunks:
            c["stored"] = stored[c["chunk_id"]]
        all_chunks.extend(chunks)
    models = {s["embed_model"] for s in stores.values()}
    if len(models) != 1:
        raise SystemExit(f"stores disagree on the embedder: {sorted(models)}")
    model = models.pop()
    queries = queries_from_facts()
    if a.limit:
        all_chunks, queries = all_chunks[:a.limit], queries[:a.limit * 2]

    # The reference must be whole: establish Ollama's effective context for this model before
    # embedding anything. A truncated A-fresh would measure truncation, not model difference.
    ctx = ollama_context(a.ollama, model)
    mod, onnx = load_onnx_nomic(a.device.upper())
    started = time.time()
    doc_prefix = task_prefix(model, "document")
    q_prefix = task_prefix(model, "query")
    doc_prefixed = [doc_prefix + c["body"] for c in all_chunks]
    q_prefixed = [q_prefix + t for _, t in queries]
    doc_toks = [len(ids) for ids in onnx.tok(doc_prefixed)["input_ids"]]
    q_toks = [len(ids) for ids in onnx.tok(q_prefixed)["input_ids"]]
    observed_max = max(doc_toks + q_toks, default=0)
    if observed_max > ctx["effective"]:
        raise SystemExit(
            f"Ollama at {a.ollama} would truncate A-fresh: its effective context for {model} is "
            f"{ctx['effective']} tokens (num_ctx={ctx['num_ctx']}, context_length="
            f"{ctx['context_length']}), but the longest benchmark item is {observed_max}. "
            "A truncated reference makes parity meaningless; fix the reference and rerun.")
    a_fresh_docs = embed_ollama(a.ollama, model, [c["body"] for c in all_chunks], "document")
    a_fresh_queries = embed_ollama(a.ollama, model, [t for _, t in queries], "query")
    print(f"A-fresh embedded: {len(all_chunks)} chunks, {len(queries)} queries via {a.ollama}",
          flush=True)

    def c_embed(text: str) -> list:
        return onnx.embed(text)

    cap = onnx.buckets[-1]
    chunk_rows = []
    over512_docs = truncated_docs = 0
    for i, (c, prefixed, toks) in enumerate(zip(all_chunks, doc_prefixed, doc_toks)):
        over512_docs += toks > 512
        over = toks > cap
        truncated_docs += over
        cf = c_embed(prefixed)
        row = {"item": f"{c['store']}:{c['source']}#chunk{c['chunk_id']}", "kind": "chunk",
               "chars": len(prefixed), "tokens": toks, "truncated": over,
               "cos": {"c_vs_a_fresh": cosine(cf, a_fresh_docs[i]),
                       "c_vs_a_stored": cosine(cf, c["stored"]),
                       "a_fresh_vs_a_stored": cosine(a_fresh_docs[i], c["stored"])}}
        chunk_rows.append(row)
        if (i + 1) % 100 == 0:
            print(f"C: {i + 1}/{len(all_chunks)} chunks", flush=True)
    query_rows = []
    over512_queries = truncated_queries = 0
    for i, ((qid, _text), prefixed, toks) in enumerate(zip(queries, q_prefixed, q_toks)):
        over512_queries += toks > 512
        over = toks > cap
        truncated_queries += over
        cf = c_embed(prefixed)
        query_rows.append({"item": qid, "kind": "query", "chars": len(prefixed), "tokens": toks,
                           "truncated": over,
                           "cos": {"c_vs_a_fresh": cosine(cf, a_fresh_queries[i])}})

    bound_min = min([r["cos"]["c_vs_a_fresh"] for r in chunk_rows + query_rows] or [1.0])
    receipt = {
        "date": time.strftime("%Y-%m-%d"), "kind": "nomic parity: the option-C match check",
        "prereg": "experiments/npu-probe/retrieval-benchmark.md",
        "smoke": a.limit is not None, "limit": a.limit,
        "device": a.device.upper(), "ollama": a.ollama, "ollama_model": model,
        "stores": stores,
        "ollama_context": ctx,
        "reference_check": {"observed_max_tokens": observed_max,
                            "assertion": "Ollama's effective context covers the longest item"},
        "onnx": {**NOMIC_ONNX, "ir_digest": onnx.ir_digest, "dim": onnx.dim},
        "counts": {"chunks": len(chunk_rows), "queries": len(query_rows)},
        "truncation": {"bucket_top": cap,
                       "documents_over_bucket_tokens": truncated_docs,
                       "queries_over_bucket_tokens": truncated_queries,
                       "documents_over_512_tokens": over512_docs,
                       "queries_over_512_tokens": over512_queries},
        "cosines": {"chunks": {"c_vs_a_fresh": compare(chunk_rows, "c_vs_a_fresh"),
                               "c_vs_a_stored": compare(chunk_rows, "c_vs_a_stored"),
                               "a_fresh_vs_a_stored": compare(chunk_rows, "a_fresh_vs_a_stored")},
                    "queries": {"c_vs_a_fresh": compare(query_rows, "c_vs_a_fresh")}},
        "worst5_c_vs_a_fresh": worst_k(chunk_rows + query_rows),
        "bound": {"minimum_cosine": bound_min, "bound": BOUND, "passes": bound_min >= BOUND,
                  "note": "minimum over every chunk and query, C vs A-fresh, as pre-registered"},
        "wall_seconds": round(time.time() - started, 1)}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(receipt, indent=1) + "\n", encoding="utf-8")
    print(f"\nwrote {a.out}")
    print(f"minimum cosine (C vs A-fresh): {bound_min:.5f} vs bound {BOUND}: "
          f"{'MATCHES' if receipt['bound']['passes'] else 'DOES NOT MATCH'}")


if __name__ == "__main__":
    main()
