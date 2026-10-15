"""Score the frozen keys and apply the pre-registered rule (design v3, section 5).

Per query: nDCG@10 (gain 2^g - 1), recall@5 (grade >= 1 counts relevant), MRR (first grade >= 1).
Comparisons are paired by query with 10,000 bootstrap resamples (seed fixed).

Stage 1 (B against A, dense-int8): mean delta >= +0.03, one-sided 95% lower bound > 0, neither group's mean
delta below -0.015, hybrid mean delta >= 0.00 with its one-sided 95% lower bound > -0.015.
Stage 2 (only if Stage 1 passes; B256 against B, dense-int8): one-sided 95% lower bound > -0.015 and mean
(B256 - A) >= +0.02. Otherwise B at 768.

Writes results/scores.json and results/per-query.jsonl (ids and numbers only).

Run: E:/AI/envs/embedgemma/Scripts/python.exe score.py
"""

from __future__ import annotations

import json
from collections import defaultdict

import numpy as np

from common import BENCH, QUERIES, RESULTS, RUNS, ndcg_at, read_jsonl, sha256_file, write_jsonl

SEED = 7
RESAMPLES = 10_000


def load_run(name: str) -> dict:
    return json.loads((RUNS / f"{name}.json").read_text(encoding="utf-8"))


def metrics(ranked: list[int], grades: dict[int, int]) -> dict:
    rel = {c for c, g in grades.items() if g >= 1}
    rr = next((1.0 / (i + 1) for i, c in enumerate(ranked) if c in rel), 0.0)
    return {"ndcg10": ndcg_at(ranked, grades, 10),
            "recall5": len(rel & set(ranked[:5])) / len(rel) if rel else 0.0, "mrr": rr}


def boot(delta: np.ndarray, rng: np.random.Generator) -> dict:
    n = len(delta)
    means = delta[rng.integers(0, n, size=(RESAMPLES, n))].mean(axis=1)
    return {"mean": float(delta.mean()), "lo_one_sided_95": float(np.quantile(means, 0.05)),
            "lo_95": float(np.quantile(means, 0.025)), "hi_95": float(np.quantile(means, 0.975)), "n": int(n)}


def main() -> None:
    queries = read_jsonl(QUERIES)
    group = {q["id"]: q["group"] for q in queries}
    grades: dict[str, dict[int, int]] = defaultdict(dict)
    for k in read_jsonl(BENCH / "keys.jsonl"):
        grades[k["qid"]][int(k["chunk_id"])] = int(k["grade"])
    missing = [q["id"] for q in queries if not grades.get(q["id"])]
    if missing:
        raise SystemExit(f"STOP: no grades for {missing[:5]}")
    pool_pairs = {(r["qid"], int(r["chunk_id"])) for r in read_jsonl(BENCH / "pool.jsonl")}
    graded_pairs = {(q, c) for q, d in grades.items() for c in d}
    if pool_pairs - graded_pairs:
        raise SystemExit(f"STOP: {len(pool_pairs - graded_pairs)} pooled chunks have no grade in keys.jsonl")
    # Amendment 1: a query whose pool holds nothing graded 1 or 2 carries no information about either arm.
    dropped = [q["id"] for q in queries if max(grades[q["id"]].values()) < 1]
    queries = [q for q in queries if q["id"] not in dropped]
    kept_groups = {g: sum(1 for q in queries if q["group"] == g) for g in ("prose", "code")}
    names = {p.stem for p in RUNS.glob("*.json") if "-limit" not in p.stem}
    per = defaultdict(dict)
    for name in sorted(names):
        run = load_run(name)
        for qid, ranked in run.items():
            if qid not in dropped:
                per[qid][name] = metrics(ranked, grades[qid])
    rows = [{"qid": q, "group": group[q], **{f"{n}.{m}": round(v, 5) for n, d in per[q].items() for m, v in d.items()}}
            for q in sorted(per)]
    write_jsonl(RESULTS / "per-query.jsonl", rows)

    rng = np.random.default_rng(SEED)
    qids = [q["id"] for q in queries]

    def delta(x: str, y: str, metric: str = "ndcg10", only: str | None = None) -> np.ndarray:
        return np.array([per[q][x][metric] - per[q][y][metric] for q in qids if (only is None or group[q] == only)])

    def mean_of(name: str, only: str | None = None) -> float:
        return float(np.mean([per[q][name]["ndcg10"] for q in qids if (only is None or group[q] == only)]))

    s1 = boot(delta("B-dense-int8", "A-dense-int8"), rng)
    s1_groups = {g: float(delta("B-dense-int8", "A-dense-int8", only=g).mean()) for g in ("prose", "code")}
    s1_hybrid = boot(delta("B-hybrid", "A-hybrid"), rng)
    stage1 = (s1["mean"] >= 0.03 and s1["lo_one_sided_95"] > 0 and min(s1_groups.values()) >= -0.015
              and s1_hybrid["mean"] >= 0.0 and s1_hybrid["lo_one_sided_95"] > -0.015)
    s2 = boot(delta("B256-dense-int8", "B-dense-int8"), rng)
    s2_vs_a = float(delta("B256-dense-int8", "A-dense-int8").mean())
    stage2 = stage1 and s2["lo_one_sided_95"] > -0.015 and s2_vs_a >= 0.02
    decision = "adopt B256" if stage2 else ("adopt B at 768" if stage1 else "keep nomic-embed-text")
    out = {
        "decision": decision,
        "keys_sha256": sha256_file(BENCH / "keys.jsonl"),
        "queries": {"kept": len(queries), "by_group": kept_groups, "dropped": dropped,
                    "below_40_in_a_group": any(n < 40 for n in kept_groups.values())},
        "stage1": {"dense": s1, "groups": s1_groups, "hybrid": s1_hybrid, "passed": stage1},
        "stage2": {"b256_vs_b": s2, "b256_minus_a_mean": s2_vs_a, "passed": stage2},
        "means_ndcg10": {n: {"all": mean_of(n), "prose": mean_of(n, "prose"), "code": mean_of(n, "code")}
                         for n in sorted(names) if not n.endswith("code-dense-int8") and "code-" not in n},
        "diagnostics": {
            "code_prefix_B_minus_B_on_code": float(np.mean([per[q]["Bcode-dense-int8"]["ndcg10"] - per[q]["B-dense-int8"]["ndcg10"]
                                                            for q in qids if group[q] == "code"])) if "Bcode-dense-int8" in names else None,
            "code_prefix_B256_minus_B256_on_code": float(np.mean([per[q]["B256code-dense-int8"]["ndcg10"] - per[q]["B256-dense-int8"]["ndcg10"]
                                                                  for q in qids if group[q] == "code"])) if "B256code-dense-int8" in names else None,
            "int8_minus_float_B256": float(delta("B256-dense-int8", "B256-dense-float").mean()),
            "int8_minus_float_B": float(delta("B-dense-int8", "B-dense-float").mean()),
            "recall5_B_minus_A": float(delta("B-dense-int8", "A-dense-int8", "recall5").mean()),
            "mrr_B_minus_A": float(delta("B-dense-int8", "A-dense-int8", "mrr").mean()),
        },
        "bootstrap": {"seed": SEED, "resamples": RESAMPLES},
    }
    (RESULTS / "scores.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
