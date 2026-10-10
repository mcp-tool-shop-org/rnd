#!/usr/bin/env python3
"""The pre-registered retrieval benchmark (retrieval-benchmark.md): does offrig's index get worse if
its embedder moves to the NPU?

Options (names as pre-registered): a = nomic via Ollama 11490 over the store's own int8 vectors
(today); b = bge-base via npu-serve; c = nomic via npu-serve from the pinned ONNX (option C; its
decision line depends on the phase-2 match check); b-small = bge-small via npu-serve (reported only).
bge variants run twice: without the query instruction (what offrig would send unchanged — the score
that counts) and with "Represent this sentence for searching relevant passages: ".

Corpus: the scratch stores of role-os @ ce91be8 and offrig @ a45fe53 (offrig's own chunking and int8
storage). Retrieval is over the UNION of both stores; a query hits when a top-k chunk is from the
fact's own corpus and a target file. Queries: the 60 grounded facts, true and near-miss forms (120),
targets each fact's `file` or `spans[].file`.

Scoring is embedding-only, as pre-registered: cosine top-k over dequantized int8 chunk vectors with
float queries — offrig's exact query path (index.rs cosine_q). Fresh option vectors are quantized with
the pinned port of index.rs's quantize, so every option pays the same storage cost. Metrics:
recall@1/5/10 by file and MRR, plus the per-option truncated share (its own tokenizer, its own
window; amendment 2026-10-09). A paired bootstrap over facts (true+false resampled together, 2000
resamples, seed 20261009) gives 95% CIs per variant and per (variant − a) recall@5 difference.

Decision (the prereg's, unchanged): b (no-instruction) or c may replace a only if the lower 95% CI on
(variant − a) recall@5 >= -0.05 AND the separate scale leg (full offrig@a45fe53 index, 3 repeats,
wall-clock on each endpoint) is >= 2x faster; c additionally needs the phase-2 match (min cosine
>= 0.995). This runner computes the CI half; the scale leg is its own timed command (README).

Runs inside the CPU window (queries against 11490) with npu-serve up (NPU ledger). The 5090 is never
touched — embeddings come only from offrig's CPU Ollama and npu-serve (NPU, no GPU device allowed).

  retrieval_bench.py --store role-os=.../role-os/.offrig/offrig.db --store offrig=.../offrig/.offrig/offrig.db \
      --serve http://127.0.0.1:11491 --ollama http://127.0.0.1:11490 --out results/2026-10-09-retrieval.json


Per-call timeouts (R&D, 2026-10-09): this runner is a client; its device calls go through
npu-serve, which holds the 60 s timed_call latch. The HTTP read timeout here stays 600 s -
the defense against a wedged device is the serve-side hang latch, not a shorter client timeout.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import random
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import nomic_parity as np_

BGE_INSTRUCTION = "Represent this sentence for searching relevant passages: "
# Model windows: bge's hard max; nomic's is the top of its measured bucket ladder.
WINDOWS = {"bge-base-en-v1.5": 512, "bge-small-en-v1.5": 512, "nomic-embed-text": 2048}
EMBED_BATCH = 32  # npu-serve bounds to 64; keep the same batch as the parity check's Ollama side
BOOT_RESAMPLES = 2000
BOOT_SEED = 20261009

# The variants, as pre-registered. embed_chunks: "stored" reads the index's own int8; otherwise the
# named model via npu-serve. queries: (endpoint, model, query fix) where fix is "task" (offrig's
# task_prefix rule), "bge_instr", or "none".
VARIANTS = {
    "a":            {"chunks": "stored",            "queries": ("ollama", "nomic-embed-text", "task")},
    "b":            {"chunks": "bge-base-en-v1.5",  "queries": ("serve", "bge-base-en-v1.5", "none")},
    "b-instr":      {"chunks": "bge-base-en-v1.5",  "queries": ("serve", "bge-base-en-v1.5", "bge_instr")},
    "b-small":      {"chunks": "bge-small-en-v1.5", "queries": ("serve", "bge-small-en-v1.5", "none")},
    "b-small-instr": {"chunks": "bge-small-en-v1.5", "queries": ("serve", "bge-small-en-v1.5", "bge_instr")},
    "c":            {"chunks": "nomic-embed-text",  "queries": ("serve", "nomic-embed-text", "task")},
}
# The decision is on these two; the rest are reported.
DECISION_VARIANTS = ("b", "c")


def bench_queries(facts_dir: Path = np_.FACTS_DIR) -> list:
    """120 queries with their fact, form ("true"/"false"), and target (corpus, file) pairs."""
    out = []
    for name in np_.FACTS_FILES:
        spec = importlib.util.spec_from_file_location(name[:-3], facts_dir / name)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        corpus = mod.NAME
        for fact in mod.FACTS:
            targets = ({(corpus, s["file"]) for s in fact["spans"]} if "spans" in fact
                       else {(corpus, fact["file"])})
            out.append({"fact": fact["id"], "form": "true", "text": fact["true"],
                        "targets": sorted(targets)})
            out.append({"fact": fact["id"], "form": "false", "text": fact["false"],
                        "targets": sorted(targets)})
    return out


def load_corpus(stores: list) -> list:
    """Union of the scratch stores' chunks with their stored int8 vectors, store name attached.
    Reuses the parity check's reader (schema v6, mixed-model refusal)."""
    corpus = []
    for spec in stores:
        name, _, path = spec.partition("=")
        if not name or not path:
            raise SystemExit(f"--store wants NAME=PATH, got {spec!r}")
        model, dim, chunks, stored = np_.read_store(Path(path))
        if model != "nomic-embed-text":
            raise SystemExit(f"{path}: today's index embeds with {model!r}, expected nomic-embed-text")
        for c in chunks:
            corpus.append({"store": name, "chunk_id": c["chunk_id"], "source": c["source"],
                           "body": c["body"], "stored": stored[c["chunk_id"]]})
    return corpus


def apply_fix(fix: str, model: str, task: str, texts: list) -> list:
    """The query/document fix of a variant: offrig's task_prefix for nomic, bge's instruction when
    asked, or nothing."""
    if fix == "task":
        p = np_.task_prefix(model, task)
        return [p + t for t in texts]
    if fix == "bge_instr":
        return [BGE_INSTRUCTION + t for t in texts]
    return list(texts)


def embed_serve(base: str, model: str, texts: list) -> list:
    """Embeddings from npu-serve (loopback only). A 503 (device error or latched DEVICE_LOST)
    aborts the benchmark — never a silent retry on another device."""
    out = []
    for i in range(0, len(texts), EMBED_BATCH):
        batch = texts[i:i + EMBED_BATCH]
        body = json.dumps({"model": model, "input": batch}).encode()
        req = urllib.request.Request(base.rstrip("/") + "/api/embed", data=body,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                embs = json.loads(r.read())["embeddings"]
        except urllib.error.HTTPError as e:
            raise SystemExit(f"npu-serve answered {e.code} for {model}: "
                             f"{e.read().decode('utf-8', 'replace').strip()}; aborting") from e
        except urllib.error.URLError as e:
            raise SystemExit(f"npu-serve is not answering at {base}: {e}; start it first") from e
        if len(embs) != len(batch):
            raise SystemExit(f"npu-serve returned {len(embs)} vectors for {len(batch)} inputs")
        out.extend(embs)
    return out


def prepare_docs(corpus: list, variant: dict, serve: str) -> list:
    """Dequantized int8 chunk vectors for a variant: the store's own for a; freshly embedded and
    quantized with the pinned port for the others, so every option pays the same storage cost."""
    if variant["chunks"] == "stored":
        return [c["stored"] for c in corpus]
    fresh = embed_serve(serve, variant["chunks"],
                        apply_fix("task", variant["chunks"], "document",
                                  [c["body"] for c in corpus]))
    docs = []
    for v in fresh:
        q, scale = np_.quantize(v)
        docs.append(np_.dequantize(q, scale))
    return docs


def score_variant(corpus: list, queries: list, docs: list, qvecs: list,
                  ks=(1, 5, 10), use_numpy: bool = True) -> list:
    """Per-query rows: hits at k and the first-hit rank. The metric counts a hit when a top-k chunk
    is from the fact's own corpus and a target file. numpy (float64) ranks when available and is
    what the full corpus runs on; the pure reference loop is the fallback. Both follow cosine's
    zero-vector -> 0.0 rule; tests check the two paths agree."""
    dmat = dn = np = None
    if use_numpy:
        try:
            import numpy as np
        except ImportError:
            np = None
        if np is not None:
            dmat = np.asarray(docs, dtype=np.float64)
            norms = np.sqrt((dmat * dmat).sum(axis=1))
            dn = np.where(norms == 0.0, 1.0, norms)  # a zero chunk: sims come out 0.0, not nan
    rows = []
    kmax = max(ks)
    for q, qv in zip(queries, qvecs):
        if dmat is not None:
            qv_a = np.asarray(qv, dtype=np.float64)
            qn = math.sqrt(float((qv_a * qv_a).sum()))
            sims = (np.arange(dmat.shape[0]) if qn == 0.0
                    else np.argsort(-(dmat @ qv_a) / (dn * qn), kind="stable"))[:kmax].tolist()
        else:
            sims = sorted(range(len(docs)), key=lambda i: -np_.cosine(qv, docs[i]))[:kmax]
        hit_at = {}
        first_rank = None
        for rank, i in enumerate(sims, start=1):
            m = corpus[i]
            if (m["store"], m["source"]) in {(t[0], t[1]) for t in q["targets"]}:
                if first_rank is None:
                    first_rank = rank
                for k in ks:
                    if rank <= k:
                        hit_at[k] = True
        rows.append({"query": q["fact"] + ":" + q["form"], "fact": q["fact"],
                     "hit_at": {k: hit_at.get(k, False) for k in ks},
                     "rr": 0.0 if first_rank is None else 1.0 / first_rank})
    return rows


def summarize(rows: list, ks=(1, 5, 10)) -> dict:
    n = len(rows)
    out = {f"recall@{k}": sum(1 for r in rows if r["hit_at"][k]) / n for k in ks}
    out["mrr"] = sum(r["rr"] for r in rows) / n
    return out


def resample_sets(n_facts: int, resamples: int = BOOT_RESAMPLES, seed: int = BOOT_SEED) -> list:
    """One list of fact-index draws, shared by every variant (paired bootstrap over facts)."""
    rng = random.Random(seed)
    return [[rng.randrange(n_facts) for _ in range(n_facts)] for _ in range(resamples)]


def bootstrap_recall(rows: list, draws: list, k: int = 5) -> list:
    """recall@k for each draw, fact-level: a draw picks facts (both forms together)."""
    facts = sorted({r["fact"] for r in rows})
    pos = {f: i for i, f in enumerate(facts)}
    by_fact = {}
    for r in rows:
        by_fact.setdefault(pos[r["fact"]], []).append(r["hit_at"][k])
    out = []
    for d in draws:
        hits = tot = 0
        for i in d:
            for h in by_fact[i]:
                hits += h
                tot += 1
        out.append(hits / tot)
    return out


def ci(values: list, lo=0.025, hi=0.975) -> tuple:
    s = sorted(values)
    n = len(s)
    return (s[int(lo * n)], s[min(n - 1, int(hi * n))])


def truncated_share(corpus: list, model: str) -> dict:
    """The amendment's column: share of chunks over the model's window under its own tokenizer."""
    spec = importlib.util.spec_from_file_location("npu_serve", HERE / "npu_serve.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    from transformers import AutoTokenizer
    mspec = mod.MODELS[model]
    tok = AutoTokenizer.from_pretrained(mspec["repo"], revision=mspec["revision"])
    window = WINDOWS[model]
    over = sum(1 for c in corpus
               if len(tok(np_.task_prefix(model, "document") + c["body"])["input_ids"]) > window)
    return {"model": model, "window": window, "over_window": over, "of": len(corpus),
            "share": over / len(corpus) if corpus else None}


def embed_queries(queries: list, variant: dict, serve: str, ollama: str) -> list:
    """Query vectors for a variant. The Ollama path (option a) embeds through offrig's own server
    with its prefix rule and the parity check's truncate=false guard; npu-serve paths apply the
    variant's query fix. Any server error aborts the run: no silent degradation mid-benchmark."""
    endpoint, model, fix = variant["queries"]
    texts = [q["text"] for q in queries]
    if endpoint == "ollama":
        if fix != "task":
            raise SystemExit(f"Ollama-side variants embed with offrig's task_prefix rule; got {fix!r}")
        vecs, _counts = np_.embed_ollama(ollama, model, texts, "query")
        return vecs
    return embed_serve(serve, model, apply_fix(fix, model, "query", texts))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--store", action="append", required=True,
                    help="NAME=PATH to a scratch store's offrig.db; repeat for role-os and offrig")
    ap.add_argument("--serve", default=None, help="npu-serve base URL (loopback); every variant "
                    "except a needs it")
    ap.add_argument("--options", default=None, help="comma subset of variants to run (default all); "
                    "the CPU window runs the a arm alone — b/c ride on the NPU serve")
    ap.add_argument("--ollama", required=True, help="offrig's Ollama base URL (11490, CPU only)")
    ap.add_argument("--out", required=True, type=Path, help="the receipt JSON")
    a = ap.parse_args()
    started = time.perf_counter()
    active = [n for n in VARIANTS
              if a.options is None or n in {s.strip() for s in a.options.split(",")}]
    if not active or "a" not in active:
        raise SystemExit("the a arm is the reference; it must always run")
    need_serve = [n for n in active
                  if VARIANTS[n]["queries"][0] == "serve" or VARIANTS[n]["chunks"] != "stored"]
    if need_serve and not a.serve:
        raise SystemExit(f"variants {need_serve} need --serve")

    corpus = load_corpus(a.store)
    queries = bench_queries()
    facts = sorted({q["fact"] for q in queries})
    # The prereg pins the denominators; check them before the first embedding call.
    if len(queries) != 120 or len(facts) != 60:
        raise SystemExit(f"the prereg pins 120 queries over 60 facts; got "
                         f"{len(queries)}/{len(facts)}; refusing to run off-prereg")
    stores = {}
    for c in corpus:
        stores[c["store"]] = stores.get(c["store"], 0) + 1
    if len(stores) != 2:
        raise SystemExit(f"expected the two scratch stores; got {sorted(stores)}")

    shares = {}

    def share(name):
        model = ("nomic-embed-text" if VARIANTS[name]["chunks"] == "stored"
                 else VARIANTS[name]["chunks"])
        if model not in shares:
            shares[model] = truncated_share(corpus, model)
        return shares[model]

    docs_cache = {}
    per = {}
    for name in active:
        v = VARIANTS[name]
        key = v["chunks"]
        if key not in docs_cache:
            t0 = time.perf_counter()
            docs = prepare_docs(corpus, v, a.serve)
            docs_cache[key] = {"docs": docs, "seconds": round(time.perf_counter() - t0, 1),
                               "owner": name}
        entry = docs_cache[key]
        t0 = time.perf_counter()
        qvecs = embed_queries(queries, v, a.serve, a.ollama)
        qsec = round(time.perf_counter() - t0, 1)
        rows = score_variant(corpus, queries, entry["docs"], qvecs)
        per[name] = {"rows": rows,
                     "embed_seconds": {"docs": entry["seconds"], "queries": qsec,
                                       "docs_shared_with": (None if entry["owner"] == name
                                                            else entry["owner"])}}
        line = summarize(rows)
        print(f"{name:13s} recall@1 {line['recall@1']:.3f}  recall@5 {line['recall@5']:.3f}"
              f"  recall@10 {line['recall@10']:.3f}  mrr {line['mrr']:.3f}"
              f"  (docs {entry['seconds']}s, queries {qsec}s)", flush=True)

    draws = resample_sets(len(facts))
    boot = {n: bootstrap_recall(per[n]["rows"], draws) for n in active}
    diffs = {}
    for n in active:
        if n == "a":
            continue
        lo, hi = ci([bv - ba for bv, ba in zip(boot[n], boot["a"])])
        diffs[n] = {"point": round(summarize(per[n]["rows"])["recall@5"]
                                   - summarize(per["a"]["rows"])["recall@5"], 4),
                    "ci95": [round(lo, 4), round(hi, 4)]}

    options = {}
    for n in active:
        lo5, hi5 = ci(boot[n])
        options[n] = {"chunks": VARIANTS[n]["chunks"],
                      "queries": dict(zip(("endpoint", "model", "fix"), VARIANTS[n]["queries"])),
                      "metrics": {k: round(x, 4) for k, x in summarize(per[n]["rows"]).items()},
                      "recall@5_ci95": [round(lo5, 4), round(hi5, 4)],
                      "truncated_share": share(n),
                      "embed_seconds": per[n]["embed_seconds"]}
        if n != "a":
            options[n]["vs_a_recall@5"] = diffs[n]

    challengers = {}
    for n in [n for n in DECISION_VARIANTS if n in active]:
        lo = diffs[n]["ci95"][0]
        challengers[n] = {"lower_ci_recall@5_vs_a": lo, "ci_half_passes": lo >= -0.05}
    decision = {"rule": ("a challenger replaces a iff lower 95% CI on (challenger - a) recall@5 "
                         ">= -0.05 AND the scale leg (full offrig@a45fe53 index, 3 timed repeats "
                         "per endpoint) is >= 2x faster; c also needs the phase-2 min cosine "
                         ">= 0.995"),
                "scale_leg": "separate timed command (README); this receipt is the CI half",
                "challengers": challengers,
                "c_phase2_match": ("reads the phase-2 nomic parity receipt before the "
                                   "decision table is filled"),
                **({"note": "b/c held for the NPU serve; this run is the CPU-window a arm, "
                             "no replacement is decided from it"}
                   if not challengers else {})}

    receipt = {"date": time.strftime("%Y-%m-%d"),
               "kind": "npu-probe: pre-registered retrieval benchmark (CI half)",
               "prereg": "experiments/npu-probe/retrieval-benchmark.md",
               "seed": BOOT_SEED, "resamples": BOOT_RESAMPLES,
               "corpus": {"stores": stores, "chunks": len(corpus)},
               "queries": {"facts": len(facts), "queries": len(queries),
                           "k": [1, 5, 10], "scoring": "embedding-only top-k, offrig's exact path"},
               "options_run": active, "options": options, "decision": decision,
               "wall_seconds_total": round(time.perf_counter() - started, 1)}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(receipt, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
