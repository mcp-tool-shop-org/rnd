"""Embed the frozen corpus and queries for arms A and B (design v3, sections 2, 3 and 6).

Arm A: nomic-embed-text on offrig's CPU-only Ollama (EMBED_URL, CUDA and Vulkan hidden), batch 32, offrig's prefixes.
Arm B: EmbeddingGemma 2 text-only on the CPU through sentence-transformers, batch 32, the card's prefixes, dtype from
the validation gate. B256 is derived at ranking time (rank.py), never stored separately.

Writes BENCH/vectors/<arm>-docs.npy and <arm>-queries.npy (float32), and results/embed-<arm>.json (public: the
manipulation records without chunk text, pins, timings).

Run: E:/AI/envs/embedgemma/Scripts/python.exe embed.py --arm A|B [--dtype float32|bfloat16] [--limit N]
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.request

import numpy as np

from common import (A_DOC, A_QUERY, B_DOC, B_QUERY, B_QUERY_CODE, BATCH, CHUNKS, EG2_REVISION, EMBED_URL, NOMIC,
                    NOMIC_DIGEST, QUERIES, RESULTS, VECTORS, read_jsonl)


def post(path: str, body: dict) -> dict:
    req = urllib.request.Request(EMBED_URL + path, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())


def get(path: str) -> dict:
    with urllib.request.urlopen(EMBED_URL + path, timeout=30) as r:
        return json.loads(r.read())


def ollama_cpu_only() -> None:
    loaded = get("/api/ps").get("models", [])
    for m in loaded:
        if m.get("size_vram", 0) > 0:
            raise SystemExit(f"STOP: {m['name']} holds {m['size_vram']} bytes of VRAM on the embed server")


def nomic_pinned() -> None:
    tags = {m["name"]: m["digest"] for m in get("/api/tags")["models"]}
    if not tags.get(NOMIC + ":latest", "").startswith(NOMIC_DIGEST):
        raise SystemExit(f"STOP: {NOMIC} digest is {tags.get(NOMIC + ':latest')}, pinned {NOMIC_DIGEST}")


def embed_a(texts: list[str]) -> np.ndarray:
    nomic_pinned()
    out = []
    for i in range(0, len(texts), BATCH):
        r = post("/api/embed", {"model": NOMIC, "input": texts[i:i + BATCH], "truncate": False,
                                "options": {"num_gpu": 0}, "keep_alive": "10m"})
        out.extend(r["embeddings"])
        if i == 0:
            ollama_cpu_only()
    return np.asarray(out, dtype=np.float32)


def load_b(dtype: str):
    import torch
    from sentence_transformers import SentenceTransformer

    if torch.cuda.is_available():
        raise SystemExit("STOP: this torch build sees CUDA; arm B runs on the CPU only")
    model = SentenceTransformer("google/embeddinggemma-2", revision=EG2_REVISION, device="cpu",
                                model_kwargs={"torch_dtype": getattr(torch, dtype)},
                                config_kwargs={"vision_config": None, "audio_config": None})
    params = sum(p.numel() for p in model.parameters())
    if params > 300e6:
        raise SystemExit(f"STOP: {params / 1e6:.0f}M parameters loaded; the text-only model is 271M")
    return model, params


def embed_b(model, texts: list[str]) -> np.ndarray:
    v = model.encode(texts, batch_size=BATCH, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)
    return np.asarray(v, dtype=np.float32)


def check(name: str, m: np.ndarray, dim: int) -> dict:
    if np.isnan(m).any():
        raise SystemExit(f"STOP: NaN in {name}")
    norms = np.linalg.norm(m, axis=1)
    if m.shape[1] != dim or abs(norms.min() - 1.0) > 1e-3 or abs(norms.max() - 1.0) > 1e-3:
        raise SystemExit(f"STOP: {name} failed the manipulation check (dim {m.shape[1]}, norms {norms.min()}..{norms.max()})")
    return {"rows": int(m.shape[0]), "dim": int(m.shape[1]), "dim_ok": m.shape[1] == dim,
            "norm_min": float(norms.min()), "norm_max": float(norms.max())}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["A", "B"], required=True)
    ap.add_argument("--dtype", default="float32", choices=["float32", "bfloat16"])
    ap.add_argument("--limit", type=int, default=0, help="first N chunks only (validation)")
    args = ap.parse_args()
    chunks = read_jsonl(CHUNKS)
    queries = read_jsonl(QUERIES)
    if args.limit:
        chunks = chunks[: args.limit]
    tag = args.arm + (f"-limit{args.limit}" if args.limit else "")
    if args.arm == "A":
        docs = [A_DOC + c["body"] for c in chunks]
        qs = [A_QUERY + q["query"] for q in queries]
        qcode = None
        t0 = time.perf_counter(); dv = embed_a(docs); t_docs = time.perf_counter() - t0
        qv = embed_a(qs)
        params, dtype = 137_000_000, "F16 GGUF (Ollama)"
    else:
        model, params = load_b(args.dtype)
        dtype = args.dtype
        docs = [B_DOC + c["body"] for c in chunks]
        qs = [B_QUERY + q["query"] for q in queries]
        t0 = time.perf_counter(); dv = embed_b(model, docs); t_docs = time.perf_counter() - t0
        qv = embed_b(model, qs)
        code = [q for q in queries if q["group"] == "code"]
        qcode = embed_b(model, [B_QUERY_CODE + q["query"] for q in code]) if code else None
    VECTORS.mkdir(parents=True, exist_ok=True)
    np.save(VECTORS / f"{tag}-docs.npy", dv)
    np.save(VECTORS / f"{tag}-queries.npy", qv)
    if qcode is not None:
        np.save(VECTORS / f"{tag}-queries-codeprefix.npy", qcode)
    record = {
        "arm": args.arm, "dtype": dtype, "params": int(params), "batch": BATCH,
        "model": NOMIC + "@" + NOMIC_DIGEST if args.arm == "A" else "google/embeddinggemma-2@" + EG2_REVISION,
        "manipulation": {
            "first_doc_prefix": docs[0][: len(A_DOC if args.arm == "A" else B_DOC)],
            "first_query_prefix": qs[0][: len(A_QUERY if args.arm == "A" else B_QUERY)],
            "first_query_sha256": __import__("hashlib").sha256(qs[0].encode()).hexdigest(),  # query text stays private
            "docs": check("docs", dv, 768), "queries": check("queries", qv, 768),
        },
        "chunks": len(chunks), "seconds_docs_in_process": round(t_docs, 2),
        "chunks_per_second": round(len(chunks) / t_docs, 2),
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / f"embed-{tag}.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=1))


if __name__ == "__main__":
    main()
