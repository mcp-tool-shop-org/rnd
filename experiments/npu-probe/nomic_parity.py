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
  A-fresh:  the Ollama GGUF at --ollama (default http://127.0.0.1:11490, offrig's CPU-only server),
            with truncate=false on every request so a too-long input is a server error, never a
            silent cut; the five longest chunks go singly so their served prompt_eval_count is
            asserted against this tokenizer (BOS/EOS allowance 2), and once more exactly as offrig
            sends them (no truncate flag, no num_ctx) to show whether today's index truncates them;
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
import sys
import importlib.util
import json
import math
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from call_timeout import DEFAULT_CALL_TIMEOUT_S, CallTimeout, timed_call

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


def _embed_body(model: str, inputs: list, truncate, cpu_only: bool = True) -> dict:
    """offrig's own request shape (ollama.rs embed @ a45fe53): model + input, options.num_gpu 0 when
    cpu_only. The parity check sends truncate=false so a too-long input is an error, never a silent
    cut; the offrig probe (truncate=None) omits the key entirely, exactly what offrig sends today."""
    body = {"model": model, "input": inputs}
    if truncate is not None:
        body["truncate"] = truncate
    if cpu_only:
        body["options"] = {"num_gpu": 0}
    return body


def _post_embed(base: str, body: dict) -> dict:
    url = base.rstrip("/") + "/api/embed"
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace").strip()
        raise SystemExit(f"{url} answered {e.code}: {detail} (with truncate=false a too-long input "
                         "lands here, which is the point) ; aborting") from e
    except urllib.error.URLError as e:
        raise SystemExit(f"no Ollama answers at {url}: {e}; A-fresh needs offrig's CPU-only server")             from e


def embed_ollama(base: str, model: str, texts: list, task: str) -> tuple:
    """A-fresh: embed through the Ollama copy offrig uses, with offrig's own prefix rule and request
    shape plus truncate=false. Batches of OLLAMA_BATCH. Returns (embeddings, per-response
    prompt_eval_counts); any server error aborts the run."""
    prefix = task_prefix(model, task)
    out, counts = [], []
    for i in range(0, len(texts), OLLAMA_BATCH):
        batch = [prefix + t for t in texts[i:i + OLLAMA_BATCH]]
        got = _post_embed(base, _embed_body(model, batch, False))
        embs = got.get("embeddings")
        if not embs or len(embs) != len(batch):
            raise SystemExit(f"{base}/api/embed carried {len(embs or [])} vectors for "
                             f"{len(batch)} inputs; aborting")
        out.extend(embs)
        counts.append({"inputs": len(batch), "prompt_eval_count": got.get("prompt_eval_count")})
    return out, counts


def embed_one(base: str, model: str, text: str, task: str, truncate=False) -> tuple:
    """A single A-fresh call, so its prompt_eval_count is per-item. truncate=None sends offrig's
    exact request (the offrig probe)."""
    got = _post_embed(base, _embed_body(model, [task_prefix(model, task) + text], truncate))
    embs = got.get("embeddings")
    if not embs:
        raise SystemExit(f"{base}/api/embed carried no embeddings for a single call; aborting")
    return embs[0], got.get("prompt_eval_count")


def top_k_longest(toks: list, k: int = 5) -> list:
    """Indices of the k longest items, longest first, ties by index. Deterministic."""
    return sorted(range(len(toks)), key=lambda i: (-toks[i], i))[:k]


def check_token_counts(rows: list, allowance: int = 2) -> list:
    """Each row gains diff and ok; returns the rows whose served prompt_eval_count differs from this
    tokenizer's count by more than the BOS/EOS allowance."""
    bad = []
    for r in rows:
        pec = r["prompt_eval_count"]
        r["diff"] = None if pec is None else pec - r["my_tokens"]
        r["ok"] = r["diff"] is not None and abs(r["diff"]) <= allowance
        if not r["ok"]:
            bad.append(r)
    return bad


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
                             {**NOMIC_ONNX, "format": "onnx", "pooling": "mean",
                              # npu_serve's measured ladder for nomic — the corpus tops out at 1619
                              # (results/2026-10-09-nomic-chunk-lengths.json); without this the
                              # default 512-cap silently truncates every long body
                              "buckets": (128, 256, 512, 1024, 2048)}, core, device)


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
    ap.add_argument("--call-timeout", type=float, default=DEFAULT_CALL_TIMEOUT_S,
                    help="per ONNX call, seconds (default 60, matches switchyard); 0 disables")
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

    # The reference must be whole. /api/show's advertised window is recorded as context; the check
    # itself is a measurement: every A-fresh request carries truncate=false (a too-long input is a
    # server error, never a silent cut), and the five longest chunks are embedded singly so their
    # served prompt_eval_count is asserted against this tokenizer's count.
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

    top5 = top_k_longest(doc_toks)
    top5set = set(top5)
    kept = [i for i in range(len(all_chunks)) if i not in top5set]
    a_fresh_bulk, batch_counts = embed_ollama(
        a.ollama, model, [all_chunks[i]["body"] for i in kept], "document")
    a_fresh_docs = [None] * len(all_chunks)
    for i, v in zip(kept, a_fresh_bulk):
        a_fresh_docs[i] = v
    longest_rows = []
    for i in top5:
        v, pec = embed_one(a.ollama, model, all_chunks[i]["body"], "document", truncate=False)
        a_fresh_docs[i] = v
        longest_rows.append({"item": f"{all_chunks[i]['store']}:{all_chunks[i]['source']}"
                                     f"#chunk{all_chunks[i]['chunk_id']}",
                             "my_tokens": doc_toks[i], "prompt_eval_count": pec})
    bad = check_token_counts(longest_rows)
    if bad:
        raise SystemExit("Ollama's served token counts differ from the nomic tokenizer's by more "
                         "than the BOS/EOS allowance (2); the tokenizers disagree and parity would "
                         "be meaningless: " + chr(10) + json.dumps(bad, indent=1))
    # Descriptive: the same five chunks embedded exactly as offrig's index sends them today (no
    # truncate flag, no num_ctx, num_gpu 0). prompt_eval_count below my_tokens means the real
    # reference index cuts these chunks now — a finding for the Publisher whatever option C shows.
    probe_rows = []
    for i, row in zip(top5, longest_rows):
        _, pec = embed_one(a.ollama, model, all_chunks[i]["body"], "document", truncate=None)
        probe_rows.append({"item": row["item"], "my_tokens": doc_toks[i],
                           "prompt_eval_count": pec,
                           "would_truncate_today": (pec is not None and pec < doc_toks[i])})
    a_fresh_queries, query_counts = embed_ollama(a.ollama, model, [t for _, t in queries], "query")
    print(f"A-fresh embedded: {len(all_chunks)} chunks (5 singly for the count check, 5 probed as "
          f"offrig sends them), {len(queries)} queries via {a.ollama}", flush=True)

    def c_embed(text: str) -> list:
        return timed_call(a.call_timeout, onnx.embed, text)

    def _marker(item: str, kind: str, outcome: str, error: str = "") -> dict:
        return {"item": item, "kind": kind, "outcome": outcome, "error": error[:200]}

    cap = onnx.buckets[-1]
    chunk_rows = []
    over512_docs = truncated_docs = 0
    hang = None  # a CallTimeout: record the hang, stop this device, fill the rest "not run"
    for i, (c, prefixed, toks) in enumerate(zip(all_chunks, doc_prefixed, doc_toks)):
        item = f"{c['store']}:{c['source']}#chunk{c['chunk_id']}"
        over512_docs += toks > 512
        over = toks > cap
        truncated_docs += over
        if hang is not None:
            chunk_rows.append(_marker(item, "chunk", "not run"))
            continue
        t0 = time.perf_counter()
        try:
            cf = c_embed(prefixed)
        except CallTimeout as exc:
            hang = {"item": item, "error": str(exc)}
            chunk_rows.append(_marker(item, "chunk", "hang", str(exc)))
            print(f"hang at {item}: {exc} - device off for the rest of the run; remaining rows not run", flush=True)
            continue
        row = {"item": item, "kind": "chunk",
               "chars": len(prefixed), "tokens": toks, "truncated": over,
               "cos": {"c_vs_a_fresh": cosine(cf, a_fresh_docs[i]),
                       "c_vs_a_stored": cosine(cf, c["stored"]),
                       "a_fresh_vs_a_stored": cosine(a_fresh_docs[i], c["stored"])}}
        chunk_rows.append(row)
        ms = (time.perf_counter() - t0) * 1000
        if (i + 1) % 25 == 0:
            print(f"C: {i + 1}/{len(all_chunks)} chunks (last {ms:.0f} ms)", flush=True)
    query_rows = []
    over512_queries = truncated_queries = 0
    for i, ((qid, _text), prefixed, toks) in enumerate(zip(queries, q_prefixed, q_toks)):
        over512_queries += toks > 512
        over = toks > cap
        truncated_queries += over
        if hang is not None:
            query_rows.append(_marker(qid, "query", "not run"))
            continue
        try:
            cf = c_embed(prefixed)
        except CallTimeout as exc:
            hang = {"item": qid, "error": str(exc)}
            query_rows.append(_marker(qid, "query", "hang", str(exc)))
            print(f"hang at {qid}: {exc} - remaining rows not run", flush=True)
            continue
        query_rows.append({"item": qid, "kind": "query", "chars": len(prefixed), "tokens": toks,
                           "truncated": over,
                           "cos": {"c_vs_a_fresh": cosine(cf, a_fresh_queries[i])}})

    measured_docs = [r for r in chunk_rows if "cos" in r]
    measured_queries = [r for r in query_rows if "cos" in r]
    bound_min = min([r["cos"]["c_vs_a_fresh"] for r in measured_docs + measured_queries] or [1.0])
    receipt = {
        "date": time.strftime("%Y-%m-%d"), "kind": "nomic parity: the option-C match check",
        "prereg": "experiments/npu-probe/retrieval-benchmark.md",
        "smoke": a.limit is not None, "limit": a.limit,
        "device": a.device.upper(), "ollama": a.ollama, "ollama_model": model,
        "stores": stores,
        "reference_check": {"ollama_show": ctx,
                            "note": "show reports the advertised window; the guard is the "
                                    "measurement here, not that number",
                            "truncate_false": "every A-fresh request; a too-long input is an error",
                            "observed_max_tokens": observed_max,
                            "batch_prompt_eval_counts": {"n_responses": len(batch_counts)
                                                         + len(query_counts),
                                                         "per_response": batch_counts
                                                         + query_counts},
                            "longest5_single_calls": longest_rows,
                            "specials_allowance": 2,
                            "offrig_probe": probe_rows,
                            "offrig_probe_note": "sent exactly as offrig's index sends them: no "
                                                 "truncate flag, no num_ctx, num_gpu 0"},
        "onnx": {**NOMIC_ONNX, "ir_digest": onnx.ir_digest, "dim": onnx.dim},
        "counts": {"chunks": len(chunk_rows), "queries": len(query_rows),
                   "measured_chunks": len(measured_docs), "measured_queries": len(measured_queries)},
        "call_timeout_s": a.call_timeout,
        "hang": hang,
        "truncation": {"bucket_top": cap,
                       "documents_over_bucket_tokens": truncated_docs,
                       "queries_over_bucket_tokens": truncated_queries,
                       "documents_over_512_tokens": over512_docs,
                       "queries_over_512_tokens": over512_queries},
        "cosines": {"chunks": {"c_vs_a_fresh": compare(measured_docs, "c_vs_a_fresh"),
                               "c_vs_a_stored": compare(measured_docs, "c_vs_a_stored"),
                               "a_fresh_vs_a_stored": compare(measured_docs, "a_fresh_vs_a_stored")},
                    "queries": {"c_vs_a_fresh": compare(measured_queries, "c_vs_a_fresh")}},
        "worst5_c_vs_a_fresh": worst_k(measured_docs + measured_queries),
        "bound": {"minimum_cosine": bound_min, "bound": BOUND, "passes": bound_min >= BOUND,
                  "note": "minimum over every chunk and query, C vs A-fresh, as pre-registered"},
        "wall_seconds": round(time.time() - started, 1)}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    if hang is not None:
        receipt["bound"]["passes"] = False
        receipt["bound"]["note"] += "; run ended in a hang before all items were measured"
    a.out.write_text(json.dumps(receipt, indent=1) + "\n", encoding="utf-8")
    print(f"\nwrote {a.out}")
    print(f"minimum cosine (C vs A-fresh): {bound_min:.5f} vs bound {BOUND}: "
          f"{'MATCHES' if receipt['bound']['passes'] else 'DOES NOT MATCH'}")
    if hang is not None:
        raise SystemExit(f"hang recorded at {hang['item']}: the receipt is written; the device stays off until restart")


if __name__ == "__main__":
    main()
