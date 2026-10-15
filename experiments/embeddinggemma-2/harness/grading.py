"""Grading packets, the audit sample, the key merge and the audit agreement (relevance-grading template).

  packets  Split BENCH/pool.jsonl into one private packet per query, BENCH/grading/<qid>.jsonl, in the pool's shuffled
           order. A fresh Sonnet agent grades one packet, reading at most five chunks at a time, and writes
           BENCH/grades/<qid>.jsonl with rows {"query_id", "chunk_id", "reason", "grade"}.
  audit    Choose 16 audit queries (8 code, 8 prose) with the highest share of pooled chunks that only one or two of
           the six decision runs found, and write the auditor's private paste files, BENCH/audit/packet-N.md.
  merge    Validate every grade file (0|1|2, reason <= 15 words, every pooled chunk present) and write BENCH/keys.jsonl,
           sorted by query and chunk.
  agree    Read the auditor's grades (BENCH/audit/auditor.jsonl) and compute quadratic weighted kappa, binary kappa
           (0 against 1-2), raw and two-step disagreement against the merged key, with the template's gates.

Run: E:/AI/envs/embedgemma/Scripts/python.exe grading.py packets|audit|merge|agree
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict

import numpy as np

from common import BENCH, RESULTS, RUNS, read_jsonl, sha256_file, write_jsonl

import os

# Round 2 (design amendment 4) regrades the whole pool under grader-brief-v2.md. Its grades, key and audit go to new
# folders, so round 1's are kept as the record and never overwritten. Its audit is drawn from the queries round 1 did
# not audit, by the same criterion.
ROUND = int(os.environ.get("EG2_ROUND", "1"))
SUFFIX = "" if ROUND == 1 else f"-r{ROUND}"
GRADING, GRADES, AUDIT = BENCH / "grading", BENCH / f"grades{SUFFIX}", BENCH / f"audit{SUFFIX}"
KEYS = BENCH / f"keys{SUFFIX}.jsonl"
EXCLUDE_FROM_AUDIT = set() if ROUND == 1 else set(json.loads((BENCH / "audit" / "chosen.json").read_text(encoding="utf-8"))["queries"])
DECISION_RUNS = [f"{a}-{r}" for a in ("A", "B", "B256") for r in ("dense-int8", "hybrid")]
AUDIT_PER_GROUP = 8
PER_PACKET = 4  # queries per auditor paste


def packets() -> None:
    by_q = defaultdict(list)
    for row in read_jsonl(BENCH / "pool.jsonl"):
        by_q[row["qid"]].append({k: row[k] for k in ("qid", "group", "query", "intent", "note", "n", "chunk_id", "text")})
    for qid, rows in by_q.items():
        write_jsonl(GRADING / f"{qid}.jsonl", rows)
    print(f"{len(by_q)} packets, {sum(len(v) for v in by_q.values())} chunks")


def audit() -> None:
    runs = {n: json.loads((RUNS / f"{n}.json").read_text(encoding="utf-8")) for n in DECISION_RUNS}
    pool = defaultdict(list)
    for row in read_jsonl(BENCH / "pool.jsonl"):
        pool[row["qid"]].append(row)
    share = {}
    for qid, rows in pool.items():
        found = defaultdict(int)
        for run in runs.values():
            for cid in run.get(qid, [])[:10]:
                found[cid] += 1
        share[qid] = sum(1 for r in rows if found.get(int(r["chunk_id"]), 0) <= 2) / len(rows)
    chosen = []
    for group in ("code", "prose"):
        qs = sorted({r["qid"] for rows in pool.values() for r in rows if r["group"] == group and r["qid"] not in EXCLUDE_FROM_AUDIT}, key=lambda q: (-share[q], q))
        chosen += qs[:AUDIT_PER_GROUP]
    AUDIT.mkdir(parents=True, exist_ok=True)
    (AUDIT / "chosen.json").write_text(json.dumps({"queries": chosen, "unique_share": {q: share[q] for q in chosen}}, indent=1), encoding="utf-8")
    for i in range(0, len(chosen), PER_PACKET):
        part = chosen[i:i + PER_PACKET]
        lines = [f"# Audit packet {i // PER_PACKET + 1} of {-(-len(chosen) // PER_PACKET)}: grade every chunk blind\n",
                 "Private. Use the relevance-grading rubric (0/1/2), judging each chunk against the query's locked intent "
                 "and note only, never against the other chunks. Reply with JSON Lines only, one row per chunk, in the "
                 "order given: {\"query_id\": ..., \"chunk_id\": ..., \"reason\": \"<=15 words\", \"grade\": 0|1|2}.\n"]
        for qid in part:
            rows = sorted(pool[qid], key=lambda r: r["n"])
            lines.append(f"\n## {qid} ({rows[0]['group']})\n\n**Query:** {rows[0]['query']}\n\n**Intent:** {rows[0]['intent']}\n")
            if rows[0].get("note"):
                lines.append(f"\n**Note:** {rows[0]['note']}\n")
            for r in rows:
                lines.append(f"\n### chunk {r['chunk_id']}\n\n~~~~\n{r['text']}\n~~~~\n")
        (AUDIT / f"packet-{i // PER_PACKET + 1}.md").write_text("".join(lines), encoding="utf-8", newline="\n")
    print("audit queries", chosen)


def merge() -> None:
    pool = {(r["qid"], int(r["chunk_id"])) for r in read_jsonl(BENCH / "pool.jsonl")}
    keys, problems = {}, []
    for path in sorted(GRADES.glob("*.jsonl")):
        for r in read_jsonl(path):
            key = (r["query_id"], int(r["chunk_id"]))
            if r.get("grade") not in (0, 1, 2):
                problems.append(f"{key}: grade {r.get('grade')!r}")
            if len(str(r.get("reason", "")).split()) > 15 or not str(r.get("reason", "")).strip():
                problems.append(f"{key}: reason missing or over 15 words")
            if key not in pool:
                problems.append(f"{key}: not in the pool")
            if key in keys:
                problems.append(f"{key}: graded twice")
            keys[key] = r
    missing = pool - set(keys)
    if missing:
        problems.append(f"{len(missing)} pooled chunks ungraded, e.g. {sorted(missing)[:3]}")
    if problems:
        raise SystemExit("STOP:\n" + "\n".join(problems[:40]))
    rows = [{"qid": q, "chunk_id": c, "grade": keys[(q, c)]["grade"], "grader": "sonnet"} for q, c in sorted(keys)]
    write_jsonl(KEYS, rows)
    print(f"keys: {len(rows)} grades, sha256 {sha256_file(KEYS)}")


def kappa(a: list[int], b: list[int], levels: list[int], weights: str | None) -> float:
    k = len(levels)
    idx = {v: i for i, v in enumerate(levels)}
    obs = np.zeros((k, k))
    for x, y in zip(a, b):
        obs[idx[x], idx[y]] += 1
    obs /= obs.sum()
    exp = np.outer(obs.sum(axis=1), obs.sum(axis=0))
    i, j = np.indices((k, k))
    w = ((i - j) ** 2) / (k - 1) ** 2 if weights == "quadratic" else (i != j).astype(float)
    return float(1 - (w * obs).sum() / (w * exp).sum())


def agree() -> None:
    key = {(r["qid"], int(r["chunk_id"])): r["grade"] for r in read_jsonl(KEYS)}
    aud = {(r["query_id"], int(r["chunk_id"])): int(r["grade"]) for r in read_jsonl(AUDIT / "auditor.jsonl")}
    chosen = json.loads((AUDIT / "chosen.json").read_text(encoding="utf-8"))["queries"]
    expected = {k for k in key if k[0] in chosen}
    if set(aud) != expected:
        raise SystemExit(f"STOP: the auditor graded {len(aud)} chunks, the sample has {len(expected)}")
    pairs = sorted(expected)
    s, a = [key[p] for p in pairs], [aud[p] for p in pairs]
    out = {
        "chunks": len(pairs), "queries": len(chosen),
        "kappa_weighted_quadratic": kappa(s, a, [0, 1, 2], "quadratic"),
        "kappa_binary": kappa([int(x >= 1) for x in s], [int(x >= 1) for x in a], [0, 1], None),
        "raw_disagreement": float(np.mean([x != y for x, y in zip(s, a)])),
        "two_step_disagreement": float(np.mean([abs(x - y) == 2 for x, y in zip(s, a)])),
        "keys_sha256": sha256_file(KEYS),
    }
    out["passed"] = (out["kappa_weighted_quadratic"] >= 0.75 and out["kappa_binary"] >= 0.80
                     and out["raw_disagreement"] <= 0.10 and out["two_step_disagreement"] <= 0.02)
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "audit-agreement.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    {"packets": packets, "audit": audit, "merge": merge, "agree": agree}[sys.argv[1]]()
