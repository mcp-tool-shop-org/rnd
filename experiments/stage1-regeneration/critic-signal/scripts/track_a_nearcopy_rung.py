"""Track A's near-duplicate rung (PLAN-ROUND4 §3): each kept re-write against the same slot's phase-4 row.

usage: python track_a_nearcopy_rung.py <phase-4 drafts jsonl> <Track A drafts jsonl> <gold record json> <calibration json> <out json>

Scores material and checker trace with the calibrated measures (char 4-gram Jaccard, bge-m3 cosine on CPU at the
calibration's revision; a trace is scored after stripping verbatim quotes of its material or statement), against the
calibration's auto thresholds (exclude at or above) and review floors (the hard negatives' 95th percentile). Writes
slot ids, scores, margins and flags only; no row text. Needs DATASET_DESK as for nearcopy_calibration.py.
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from nearcopy_calibration import char_ngrams, jaccard, parse_candidate, strip_quotes  # noqa: E402

FIELDS = {"mat_c4": "material_char4", "mat_cos": "material_cosine", "tr_c4": "trace_char4", "tr_cos": "trace_cosine"}


def load(path: Path) -> dict:
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("type") == "header" or not r.get("candidate"):
            continue
        c = parse_candidate(r["candidate"]["text"])
        out[r["slot"]["id"]] = {"material": r["material"]["text"], "statement": c.get("statement", ""),
                                "trace": c.get("checker_trace", "")}
    return out


def main() -> int:
    p4_path, ta_path, gold_path, cal_path, out_path = map(Path, sys.argv[1:6])
    p4, ta = load(p4_path), load(ta_path)
    gold = json.loads(gold_path.read_text(encoding="utf-8"))
    cal = json.loads(cal_path.read_text(encoding="utf-8"))
    slots = gold["rewrites_kept"]
    missing = [s for s in slots if s not in p4 or s not in ta]
    if missing:
        raise SystemExit(f"REFUSED: no phase-4 or Track A row for {missing}")

    sys.path.insert(0, os.environ["DATASET_DESK"])
    from dataset_desk.backends import SentenceTransformerTextEmbedder
    from dataset_desk.registry import REGISTRY
    spec = REGISTRY["bge-m3"]
    if spec.revision != cal["embedder"]["revision"]:
        raise SystemExit(f"REFUSED: bge-m3 revision {spec.revision} != calibration {cal['embedder']['revision']}")
    emb = SentenceTransformerTextEmbedder(spec, device="cpu", threads=8)

    pairs = [(p4[s], ta[s]) for s in slots]
    mats = [x for a, b in pairs for x in (a["material"], b["material"])]
    trs = [x for a, b in pairs for x in (strip_quotes(a["trace"], a["material"], a["statement"]),
                                         strip_quotes(b["trace"], b["material"], b["statement"]))]
    vm, vt = emb.texts(mats).tolist(), emb.texts(trs).tolist()

    def cos(v, i, j):
        return float(sum(x * y for x, y in zip(v[i], v[j])))

    rows = []
    for k, s in enumerate(slots):
        i, j = 2 * k, 2 * k + 1
        sc = {"mat_c4": jaccard(char_ngrams(mats[i]), char_ngrams(mats[j])), "mat_cos": cos(vm, i, j),
              "tr_c4": jaccard(char_ngrams(trs[i]), char_ngrams(trs[j])), "tr_cos": cos(vt, i, j)}
        row = {"slot": s}
        excluded, review = False, False
        for key, field in FIELDS.items():
            t_auto, t_review = cal["fields"][field]["t_auto"], cal["fields"][field]["t_review"]
            row[key] = {"score": round(sc[key], 4), "threshold": round(t_auto, 4),
                        "margin": round(t_auto - sc[key], 4), "review_floor": round(t_review, 4)}
            excluded |= sc[key] >= t_auto
            review |= t_review <= sc[key] < t_auto
        row["excluded"] = excluded
        row["in_review_band"] = review and not excluded
        rows.append(row)

    n_review = sum(r["in_review_band"] for r in rows)
    out = {"what": "Track A near-duplicate rung (PLAN-ROUND4 §3)", "rewrites_scored": len(slots),
           "excluded": [r["slot"] for r in rows if r["excluded"]],
           "in_review_band": [r["slot"] for r in rows if r["in_review_band"]],
           "publisher_stop": n_review > 2,
           "context": "every re-write has domain_changed true against phase 4, so near-copies should be rare; "
                      "several exclusions would be a signal about the thresholds, not the writer",
           "embedder": cal["embedder"], "rows": rows}
    out_path.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: out[k] for k in ("rewrites_scored", "excluded", "in_review_band", "publisher_stop")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
