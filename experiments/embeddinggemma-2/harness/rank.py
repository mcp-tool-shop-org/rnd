"""Rank the corpus for every query, the way offrig would (design v3, sections 3 and 5).

For each arm (A, B, B256, and the code-prefix diagnostics on the code group) and each reading:
- dense-int8: documents quantized per vector with offrig's quantizer; the query stays float; cosine; top 20.
  This is what the decision rule reads.
- dense-float: the same, without quantization (diagnostic).
- hybrid: offrig's FTS5 BM25 top 50 from the frozen index plus dense-int8 top 50, fused by RRF (k 60), top 20 kept.
B256 is cut from B's float vectors to 256 dimensions and re-normalized in float, then quantized with its own scale.

Writes BENCH/runs/<arm>-<reading>.json as {query id: [chunk ids, best first]}.

Run: E:/AI/envs/embedgemma/Scripts/python.exe rank.py [--tag-suffix -limit512]
"""

from __future__ import annotations

import argparse
import json
import sqlite3

import numpy as np

from common import CHUNKS, DB, FUSED_KEEP, QUERIES, RANKER_DEPTH, RESULTS, RUNS, VECTORS, cosine_matrix, fts_query, l2n, quantize, read_jsonl, rrf


def quantized(docs: np.ndarray) -> np.ndarray:
    """Dequantized int8 documents, exactly as offrig scores them (dequantize then cosine)."""

    out = np.empty_like(docs)
    for i, v in enumerate(docs):
        q, scale = quantize(v)
        out[i] = q.astype(np.float32) * scale
    return out


def top(scores: np.ndarray, ids: np.ndarray, k: int) -> list[list[int]]:
    idx = np.argsort(-scores, axis=1, kind="stable")[:, :k]
    return [[int(ids[j]) for j in row] for row in idx]


def bm25(con: sqlite3.Connection, text: str) -> list[int]:
    q = fts_query(text)
    if q is None:
        return []
    rows = con.execute(
        "SELECT c.id FROM chunks_fts f JOIN chunks c ON c.id = f.rowid WHERE chunks_fts MATCH ?1 "
        "ORDER BY bm25(chunks_fts) LIMIT ?2", (q, RANKER_DEPTH)).fetchall()
    return [r[0] for r in rows]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag-suffix", default="")
    args = ap.parse_args()
    sfx = args.tag_suffix
    chunks = read_jsonl(CHUNKS)
    queries = read_jsonl(QUERIES)
    ids = np.array([c["id"] for c in chunks], dtype=np.int64)
    a_docs = np.load(VECTORS / f"A{sfx}-docs.npy")
    ids = ids[: a_docs.shape[0]]
    b_docs = np.load(VECTORS / f"B{sfx}-docs.npy")
    a_q = np.load(VECTORS / f"A{sfx}-queries.npy")
    b_q = np.load(VECTORS / f"B{sfx}-queries.npy")
    code_idx = [i for i, q in enumerate(queries) if q["group"] == "code"]
    b_qc_path = VECTORS / f"B{sfx}-queries-codeprefix.npy"
    b_qc = np.load(b_qc_path) if b_qc_path.exists() else None

    arms = {
        "A": (a_docs, a_q, list(range(len(queries)))),
        "B": (b_docs, b_q, list(range(len(queries)))),
        "B256": (l2n(b_docs[:, :256]), l2n(b_q[:, :256]), list(range(len(queries)))),
    }
    if b_qc is not None:
        arms["Bcode"] = (b_docs, b_qc, code_idx)
        arms["B256code"] = (l2n(b_docs[:, :256]), l2n(b_qc[:, :256]), code_idx)

    b256_docs, b256_q = arms["B256"][0], arms["B256"][1]
    n_d, n_q = np.linalg.norm(b256_docs, axis=1), np.linalg.norm(b256_q, axis=1)
    record = {"dim_docs": int(b256_docs.shape[1]), "dim_queries": int(b256_q.shape[1]),
              "norm_min": float(min(n_d.min(), n_q.min())), "norm_max": float(max(n_d.max(), n_q.max()))}
    if record["dim_docs"] != 256 or abs(record["norm_min"] - 1) > 1e-3 or abs(record["norm_max"] - 1) > 1e-3:
        raise SystemExit(f"STOP: B256 manipulation check failed: {record}")
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / f"embed-B256{sfx}.json").write_text(json.dumps({"arm": "B256", "manipulation": record}, indent=2) + "\n", encoding="utf-8")

    con = sqlite3.connect(DB)
    lex = {q["id"]: bm25(con, q["query"]) for q in queries}
    RUNS.mkdir(parents=True, exist_ok=True)
    for name, (docs, qv, which) in arms.items():
        qids = [queries[i]["id"] for i in which]
        dense_f = top(cosine_matrix(qv, docs), ids, max(FUSED_KEEP, RANKER_DEPTH))
        dense_q_all = top(cosine_matrix(qv, quantized(docs)), ids, RANKER_DEPTH)
        runs = {
            "dense-int8": {q: r[:FUSED_KEEP] for q, r in zip(qids, dense_q_all)},
            "dense-float": {q: r[:FUSED_KEEP] for q, r in zip(qids, dense_f)},
            "hybrid": {q: rrf([lex[q], r]) for q, r in zip(qids, dense_q_all)},
        }
        for reading, run in runs.items():
            (RUNS / f"{name}{sfx}-{reading}.json").write_text(json.dumps(run) + "\n", encoding="utf-8")
        print(name, {k: len(v) for k, v in runs.items()})


if __name__ == "__main__":
    main()
