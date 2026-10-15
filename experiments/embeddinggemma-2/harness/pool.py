"""Build the blind grading pool (design v3, section 4, keys steps 2 and 3).

Union of each query's top 10 across every run in BENCH/runs (A, B, B256, both readings and the code-prefix
diagnostics), deduplicated, with model identities and ranks dropped and the order shuffled by a fixed seed.

Writes BENCH/pool.jsonl (private: chunk text for the graders) and results/pool-manifest.json (public: sizes).
Grades go in BENCH/keys.jsonl as {"qid", "chunk_id", "grade": 0|1|2, "grader"}.

Run: E:/AI/envs/embedgemma/Scripts/python.exe pool.py [--tag-suffix S]
"""

from __future__ import annotations

import argparse
import json
import random
from statistics import mean

from common import BENCH, CHUNKS, QUERIES, RESULTS, RUNS, read_jsonl, write_jsonl

SEED = 20261015
DEPTH = 10


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag-suffix", default="")
    args = ap.parse_args()
    body = {c["id"]: c for c in read_jsonl(CHUNKS)}
    queries = read_jsonl(QUERIES)
    # The decision readings of A, B and B256, plus the code-prefix diagnostic's dense reading (design v3, keys
    # step 2). The float readings and the code-prefix hybrids are diagnostics read against these grades; a chunk
    # only they surface counts 0, which is stated beside those diagnostics.
    names = [f"{arm}{args.tag_suffix}-{reading}" for arm in ("A", "B", "B256") for reading in ("dense-int8", "hybrid")]
    names += [f"Bcode{args.tag_suffix}-dense-int8", f"B256code{args.tag_suffix}-dense-int8"]
    runs = [json.loads((RUNS / f"{n}.json").read_text(encoding="utf-8")) for n in names]
    rng = random.Random(SEED)
    rows, sizes = [], []
    for q in queries:
        pool: list[int] = []
        for run in runs:
            for cid in run.get(q["id"], [])[:DEPTH]:
                if cid not in pool:
                    pool.append(cid)
        rng.shuffle(pool)
        sizes.append(len(pool))
        for n, cid in enumerate(pool, start=1):
            c = body[cid]
            rows.append({"qid": q["id"], "group": q["group"], "query": q["query"], "n": n, "chunk_id": cid,
                         "source": c["source"], "text": c["body"]})
    write_jsonl(BENCH / f"pool{args.tag_suffix}.jsonl", rows)
    manifest = {"seed": SEED, "depth": DEPTH, "runs": len(runs), "queries": len(queries), "pooled": len(rows),
                "per_query_mean": round(mean(sizes), 2), "per_query_max": max(sizes)}
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / f"pool-manifest{args.tag_suffix}.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(manifest)


if __name__ == "__main__":
    main()
