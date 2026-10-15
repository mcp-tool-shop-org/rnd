"""Shared pieces of the EmbeddingGemma 2 benchmark harness (design v3, experiments/embeddinggemma-2/design.md).

Everything that reproduces offrig's behaviour is copied from offrig 1.1.1's crates/offrig-core and named after its
source: fts_query (store.rs), quantize and cosine_q (index.rs), rrf with RRF_K, RANKER_DEPTH and FUSED_KEEP (index.rs).
Private text (chunks, queries' pooled passages, grades) lives under BENCH, outside the public repo. Only ids, hashes,
counts and scores are committed.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
EXPERIMENT = HERE.parent
BENCH = Path(os.environ.get("EG2_BENCH", r"E:\AI\eg2-bench"))
PROJECT = BENCH / "index"          # the offrig project: corpus/ inside it, .offrig/offrig.db holds the frozen chunks
DB = PROJECT / ".offrig" / "offrig.db"
CHUNKS = BENCH / "chunks.jsonl"
QUERIES = BENCH / "queries.jsonl"
VECTORS = BENCH / "vectors"
RUNS = BENCH / "runs"
RESULTS = EXPERIMENT / "results"   # committed: ids, hashes, counts and scores only

# offrig 1.1.1, crates/offrig-core/src/index.rs
RANKER_DEPTH = 50
FUSED_KEEP = 20
RRF_K = 60.0
BATCH = 32

# The two arms' document and query strings (design v3, section 2).
A_DOC, A_QUERY = "search_document: ", "search_query: "
B_DOC = "title: none | text: "
B_QUERY = "task: search result | query: "
B_QUERY_CODE = "task: code retrieval | query: "
EG2_REVISION = "914f7f89142e33e77833254d9c9b90c3cef7303b"
NOMIC = "nomic-embed-text"
NOMIC_DIGEST = "0a109f422b47"
EMBED_URL = "http://127.0.0.1:11490"   # offrig's CPU-only Ollama


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path: Path, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def fts_query(text: str) -> str | None:
    """offrig store.rs fts_query: split on anything but alphanumerics and _ - . :, quote each word, join with OR."""

    words, cur = [], []
    for ch in text:
        if ch.isalnum() or ch in "_-.:":
            cur.append(ch)
        elif cur:
            words.append("".join(cur))
            cur = []
    if cur:
        words.append("".join(cur))
    words = ['"' + w.replace('"', "") + '"' for w in words if w]
    return " OR ".join(words) if words else None


def quantize(v: np.ndarray) -> tuple[np.ndarray, float]:
    """offrig index.rs quantize: per-vector absmax over 127, round, clamp to [-127, 127]."""

    m = float(np.max(np.abs(v)))
    if m == 0.0:
        return np.zeros(v.shape, dtype=np.int8), 0.0
    scale = np.float32(m / 127.0)
    q = np.clip(np.round(v.astype(np.float32) / scale), -127, 127).astype(np.int8)
    return q, float(scale)


def l2n(m: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(m, axis=-1, keepdims=True)
    return m / np.where(n == 0, 1, n)


def cosine_matrix(queries: np.ndarray, docs: np.ndarray) -> np.ndarray:
    """offrig cosine: dot over the product of norms (offrig never assumes unit length)."""

    return l2n(queries.astype(np.float32)) @ l2n(docs.astype(np.float32)).T


def rrf(lists: list[list[int]], k: float = RRF_K, keep: int = FUSED_KEEP) -> list[int]:
    """offrig index.rs rrf: 1/(k + rank) summed, highest first, ties keep first-seen order."""

    scores: dict[int, float] = {}
    order: list[int] = []
    for lst in lists:
        for rank, cid in enumerate(lst, start=1):
            if cid not in scores:
                scores[cid] = 0.0
                order.append(cid)
            scores[cid] += 1.0 / (k + rank)
    first = {cid: i for i, cid in enumerate(order)}
    return sorted(order, key=lambda c: (-scores[c], first[c]))[:keep]


def ndcg_at(ranked: list[int], grades: dict[int, int], k: int = 10) -> float:
    """nDCG@k with gain 2^g - 1 over the pooled grades; an unjudged chunk counts 0."""

    dcg = sum((2 ** grades.get(c, 0) - 1) / math.log2(i + 2) for i, c in enumerate(ranked[:k]))
    ideal = sorted(grades.values(), reverse=True)[:k]
    idcg = sum((2 ** g - 1) / math.log2(i + 2) for i, g in enumerate(ideal))
    return dcg / idcg if idcg > 0 else 0.0
