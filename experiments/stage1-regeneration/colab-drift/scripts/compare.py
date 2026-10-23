"""Compare a fresh window's call journal with reference journals by request key (colab-drift DESIGN v2).

Usage: python compare.py --fresh <calls.jsonl> --ref <name>=<calls.jsonl> [--ref ...] [--only-fresh-calls]

Keys are matched as a multiset: a key that appears more than once is paired in journal order. Each matched pair is
scored as exact (byte-identical completion text) or drift. For drift, every labelled line is compared and counted per
field in `field_changes`. Only lines the pipeline acts on count as decisions: `decision_drift` is a change in VERDICT,
TRAIT, ANSWER or a bare flaw LABEL, and `verdict_drift` is a change in VERDICT alone. DECIDING (the quoted span) and
CONTRASTED (scaffolding role-set never parses) are reported but are not decisions (2026-10-23: the G4 write-up counted
them as decisions and said 65 of 65 drifts changed a decision; 3 changed a verdict). Keys in the fresh journal that are in no reference are reported as
unmatched, which voids an arm until explained. Prints one JSON summary; exits 0 always (the reading is the result).
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict, deque


def load(path: str, only_fresh: bool = False) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            if only_fresh and r.get("reused"):
                continue
            rows.append(r)
    return rows


def text(r: dict) -> str:
    c = r.get("completion")
    return c.get("text", "") if isinstance(c, dict) else str(c or "")


def ident(r: dict) -> dict:
    """Where a call came from, when the journal records it (DESIGN v3 acceptance item 2): slot, attempt, messages sha256."""
    return {k: r.get(k) for k in ("slot", "attempt", "messages_sha256") if r.get(k) is not None}


def fields(t: str) -> dict:
    out = {}
    for name in ("VERDICT", "DECIDING", "TRAIT", "CONTRASTED", "ANSWER"):
        m = re.search(rf"(?m)^\s*{name}\s*:\s*(.*)$", t)
        if m:
            out[name] = m.group(1).strip()
    # A critic-eval flaw reply is the bare label ("guess", "none", "rubber_stamp"; reasoning is stripped), so the
    # reply is the decision: without this, every changed label counted as drift but never as decision drift (stub 16e).
    if not out and t.strip() and "\n" not in t.strip() and len(t.strip()) <= 40:
        out["LABEL"] = t.strip()
    return out


DECISION_FIELDS = ("VERDICT", "TRAIT", "ANSWER", "LABEL")


def score(fresh: list[dict], refs: dict) -> dict:
    per = defaultdict(lambda: {"matched": 0, "exact": 0, "drift": 0, "decision_drift": 0, "verdict_drift": 0,
                               "field_changes": defaultdict(int)})
    unmatched, drifts = [], []
    for r in fresh:
        q = refs.get(r["key"])
        if not q:
            unmatched.append({"key": r["key"][:16], "role": r.get("role"), **ident(r)})
            continue
        name, ref_text = q.popleft()
        got = text(r)
        s = per[name]
        s["matched"] += 1
        if got == ref_text:
            s["exact"] += 1
            continue
        s["drift"] += 1
        fa, fb = fields(ref_text), fields(got)
        changed = sorted(k for k in set(fa) | set(fb) if fa.get(k) != fb.get(k))
        for k in changed:
            s["field_changes"][k] += 1
        if any(k in DECISION_FIELDS for k in changed):
            s["decision_drift"] += 1
        if "VERDICT" in changed:
            s["verdict_drift"] += 1
        drifts.append({"ref": name, "key": r["key"][:16], "role": r.get("role"), "check": r.get("check"),
                       "fields_changed": changed, **ident(r)})
    keys = ("matched", "exact", "drift", "decision_drift", "verdict_drift")
    pooled = {k: sum(v[k] for v in per.values()) for k in keys}
    return {"per": per, "pooled": pooled, "unmatched": unmatched, "drifts": drifts}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fresh", required=True)
    ap.add_argument("--ref", action="append", required=True, help="name=path")
    ap.add_argument("--only-fresh-calls", action="store_true", help="score only fresh lines that weren't replayed")
    a = ap.parse_args()

    fresh = load(a.fresh, a.only_fresh_calls)
    refs: dict[str, deque] = defaultdict(deque)  # key -> deque of (ref name, text), in journal order
    for spec in a.ref:
        name, path = spec.split("=", 1)
        for r in load(path, only_fresh=True):  # a replayed row is a copy of another window's reply, not this VM's
            refs[r["key"]].append((name, text(r)))

    out = score(fresh, refs)
    per, pooled, unmatched, drifts = out["per"], out["pooled"], out["unmatched"], out["drifts"]
    print(json.dumps({"fresh_scored": len(fresh), "unmatched_keys": len(unmatched), "unmatched_sample": unmatched[:10],
                      "per_ref": per, "pooled": pooled, "drifts": drifts[:200]}, indent=1))


if __name__ == "__main__":
    main()
