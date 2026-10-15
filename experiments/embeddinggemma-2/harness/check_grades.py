"""Per-query completeness of the grade files: every pooled chunk graded once, grade 0|1|2, reason 1-15 words.

Run: E:/AI/envs/embedgemma/Scripts/python.exe check_grades.py [qid ...]   (no ids: every packet)
"""

from __future__ import annotations

import json
import sys

from common import BENCH

GRADING, GRADES = BENCH / "grading", BENCH / "grades"


def check(qid: str) -> str:
    packet = {json.loads(line)["chunk_id"] for line in open(GRADING / f"{qid}.jsonl", encoding="utf-8") if line.strip()}
    path = GRADES / f"{qid}.jsonl"
    if not path.exists():
        return f"{qid}: NO GRADES (packet {len(packet)})"
    rows = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
    ids = [int(r["chunk_id"]) for r in rows]
    bad = sum(1 for r in rows if r.get("grade") not in (0, 1, 2) or not str(r.get("reason", "")).strip()
              or len(str(r["reason"]).split()) > 15 or r.get("query_id") != qid)
    missing, extra, dupes = len(packet - set(ids)), len(set(ids) - packet), len(ids) - len(set(ids))
    counts = [sum(1 for r in rows if r.get("grade") == g) for g in (0, 1, 2)]
    ok = not (missing or extra or dupes or bad)
    return f"{qid}: {'OK ' if ok else 'BAD'} packet {len(packet)} graded {len(rows)} missing {missing} extra {extra} dupes {dupes} bad {bad} 0/1/2 {counts}"


if __name__ == "__main__":
    ids = sys.argv[1:] or sorted(p.stem for p in GRADING.glob("*.jsonl"))
    for qid in ids:
        print(check(qid))
