"""Post-hoc (2026-10-09): the most-repeated 8-word n-gram per thinking trace, for offrig's loop detector (contract v3).
Reads thinking.jsonl from the scratch run dirs (not committed: untrusted model text) and writes only counts.

  python loop_repeats_posthoc.py E:/AI/rnd-calibrate-r2
"""
import collections, json, re, sys


def max_rep(text: str, n: int = 8) -> int:
    w = re.findall(r"\S+", text)
    if len(w) < n:
        return 0
    return max(collections.Counter(tuple(w[i:i + n]) for i in range(len(w) - n + 1)).values())


root = sys.argv[1]
for ct in ("grounded", "reasoning"):
    d = f"{root}/cal-gemma4_31b-{ct}-tune/"
    status = {json.loads(l)["claim_id"]: json.loads(l)["status"] for l in open(d + "verdicts.jsonl", encoding="utf-8")}
    rows = []
    for l in open(d + "thinking.jsonl", encoding="utf-8"):
        r = json.loads(l)
        rows.append((max((max_rep(t) for t in r["thinking"] if t), default=0), r["claim_id"], status.get(r["claim_id"])))
    clean = sorted((m for m, _, s in rows if s == "ok"), reverse=True)
    bad = [(m, c, s) for m, c, s in rows if s != "ok"]
    print(f"{ct}: {len(clean)} clean replies, max 8-gram repeats {clean[0] if clean else 0}; top 5 {clean[:5]}; not ok: {bad}")
    print(f"  per-reply maxima (claim_id, max): " + json.dumps(sorted(((c, m) for m, c, s in rows), key=lambda t: -t[1])))
