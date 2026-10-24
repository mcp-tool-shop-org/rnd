"""Compare a fresh window's call journal with reference journals by request key (colab-drift DESIGN v2).

Usage: python compare.py --fresh <calls.jsonl> --ref <name>=<calls.jsonl> [--ref ...] [--only-fresh-calls]

Keys are matched as a multiset: a key that appears more than once is paired in journal order. Each matched pair is
scored as exact (byte-identical completion text) or drift. A drifted pair is parsed the way role-set (8b55129a) parses
that check's reply, so a change role-set can't see (case, a trailing period, bold, an earlier ANSWER line) isn't
counted, and a change it does see is:
- `verdict` and `twin_verdict`: VERDICT as aspire_si_gates' parse_answer reads it, and DECIDING split on " | " and
  normalised as the gates' norm (critic._lines);
- `trait`: TRAIT as critic.trait_named reads it; CONTRASTED (scaffolding role-set never parses) is reported only;
- `answer`: the last ANSWER line (critic.compare_answer), whitespace collapsed and a final period dropped;
- `flaw`: the reply's first word (critic.compare_flaw).
A reply role-set would void parses as "void", so two unreadable replies don't count as a change.

Counts: every changed field in `field_changes`. `decision_drift`: a closed decision label changed (VERDICT, TRAIT,
ANSWER or a flaw LABEL). `verdict_drift`: VERDICT alone. `evidence_drift`: DECIDING changed on a `verdict` call, where
role-set acts on it (a quote not verbatim in the material voids the call and asks again; on supported and unsupported
keys, critic_mismatch refuses evidence that doesn't cover the key's). A DECIDING change doesn't always change the
outcome, so evidence_drift counts the calls where it could. (2026-10-23: the G4 write-up counted every labelled line as
a decision and said 65 of 65 drifts changed a decision; 3 changed a verdict. 2026-10-24: DECIDING had then been left
out entirely, though role-set acts on it on verdict calls; evidence_drift now counts it.)

Known limits (Argon's review round 2, 2026-10-24; none occurs in the T10 drift journals):
- `answer`: role-set reads the last ANSWER line through closed_answer and same_answer, which void an answer with
  "because" or "since" and treat a reordered map or a leading article as the same answer. This reads the text only, so
  it can count those as decision drift. Port closed_answer before comparing kind B journals.
- `verdict`: role-set repairs a DECIDING quote against the material (backticks, link marks, trailing punctuation)
  before checking it; without the material this can't, so `evidence_drift` can count a quote role-set would accept
  unchanged. It is an upper bound.
- With no `check` recorded, a bare trait id ("T03") isn't read as a trait.

Keys in the fresh journal that are in no reference are reported as unmatched, which voids an arm until explained, and
reference rows no fresh row consumed are counted per reference (`ref_unconsumed`), so a fresh run that stopped early
shows. A key in two named references is refused: compare against replicate references one at a time. Prints one JSON
summary; exits 0 once it has compared (the reading is the result), and refuses bad input with an error.
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


# role-set's own rules at 8b55129a: assemble.FLAWS and VERDICTS, critic.TRAIT_LINE and critic.ANSWER_LINE.
FLAWS = ("rubber_stamp", "guess", "loop", "nitpick", "fix", "obeyed_material", "caved", "reject_by_default")
VERDICTS = ("supported", "unsupported", "cannot_tell")
TRAIT_LINE = re.compile(r"^\s*\**\s*TRAIT\s*\**\s*:\s*\**\s*(T\d\d)\b", re.I | re.M)
ANSWER_LINE = re.compile(r"^\s*\**\s*ANSWER\s*\**\s*:\s*(.+?)\s*$", re.I | re.M)


def _line(t: str, tag: str) -> str | None:
    """A tagged line's value as aspire_si_gates' parse_answer finds it (first match, any case)."""
    m = re.search(rf"^\s*{tag}\s*:\s*(.*)$", t, re.M | re.I)
    return m.group(1).strip() if m else None


def _norm(x: str) -> str:
    """The gates' norm: ** and __ dropped, whitespace collapsed."""
    return re.sub(r"\s+", " ", x.replace("**", "").replace("__", "")).strip()


def _verdict(t: str) -> str:
    v = (_line(t, "VERDICT") or "").lower().strip(" .*`")
    return v if v in VERDICTS else "void"


def _deciding(t: str) -> tuple:
    d = _line(t, "DECIDING")
    if not d or d.strip().upper() == "NONE":
        return ()
    return tuple(_norm(x) for x in d.split(" | ") if x.strip())


def _trait(t: str) -> str:
    m = TRAIT_LINE.search(t)
    if m:
        return m.group(1).upper()
    word = t.strip().split()[0].strip(".,:;'\"*").upper() if t.strip() else ""
    return word if re.fullmatch(r"T\d\d", word) else "void"


def _answer(t: str) -> str:
    lines = ANSWER_LINE.findall(t)
    return " ".join(lines[-1].split()).strip().rstrip(".").lower() if lines else "void"


def _flaw(t: str) -> str:
    word = t.strip().split()[0].strip(".,:;'\"").lower() if t.strip() else ""
    return word if word in FLAWS + ("none",) else "void"


def fields(t: str, check: str | None = None) -> dict:
    """The fields of one reply, read as role-set reads that check's reply."""
    if check in ("verdict", "twin_verdict"):
        return {"VERDICT": _verdict(t), "DECIDING": _deciding(t)}
    if check == "trait":
        out = {"TRAIT": _trait(t)}
        c = _line(t, "CONTRASTED")
        if c is not None:
            out["CONTRASTED"] = c
        return out
    if check == "answer":
        return {"ANSWER": _answer(t)}
    if check == "flaw":
        return {"LABEL": _flaw(t)}
    # No check recorded: read every field a reply could carry, by the same rules.
    out = {}
    if _line(t, "VERDICT") is not None:
        out["VERDICT"], out["DECIDING"] = _verdict(t), _deciding(t)
    if TRAIT_LINE.search(t):
        out["TRAIT"] = _trait(t)
    if _line(t, "CONTRASTED") is not None:
        out["CONTRASTED"] = _line(t, "CONTRASTED")
    if ANSWER_LINE.search(t):
        out["ANSWER"] = _answer(t)
    if not out:
        out["LABEL"] = _flaw(t)
    return out


DECISION_FIELDS = ("VERDICT", "TRAIT", "ANSWER", "LABEL")


def score(fresh: list[dict], refs: dict) -> dict:
    per = defaultdict(lambda: {"matched": 0, "exact": 0, "drift": 0, "decision_drift": 0, "verdict_drift": 0,
                               "evidence_drift": 0, "ref_unconsumed": 0, "field_changes": defaultdict(int)})
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
        check = r.get("check")
        fa, fb = fields(ref_text, check), fields(got, check)
        changed = sorted(k for k in set(fa) | set(fb) if fa.get(k) != fb.get(k))
        for k in changed:
            s["field_changes"][k] += 1
        if any(k in DECISION_FIELDS for k in changed):
            s["decision_drift"] += 1
        if "VERDICT" in changed:
            s["verdict_drift"] += 1
        if "DECIDING" in changed and check in ("verdict", None):
            s["evidence_drift"] += 1
        drifts.append({"ref": name, "key": r["key"][:16], "role": r.get("role"), "check": r.get("check"),
                       "fields_changed": changed, **ident(r)})
    for q in refs.values():
        for name, _ in q:
            per[name]["ref_unconsumed"] += 1
    keys = ("matched", "exact", "drift", "decision_drift", "verdict_drift", "evidence_drift", "ref_unconsumed")
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
    owner: dict[str, str] = {}
    for spec in a.ref:
        name, path = spec.split("=", 1)
        for r in load(path, only_fresh=True):  # a replayed row is a copy of another window's reply, not this VM's
            if owner.setdefault(r["key"], name) != name:
                # Pooling is for disjoint waves. Replicates share keys, and one queue would pair each fresh call with
                # only one of them: compare against each replicate in its own run.
                raise SystemExit(f"REFUSED: key {r['key'][:16]} is in both {owner[r['key']]!r} and {name!r}; "
                                 "compare against replicate references one at a time")
            refs[r["key"]].append((name, text(r)))

    out = score(fresh, refs)
    per, pooled, unmatched, drifts = out["per"], out["pooled"], out["unmatched"], out["drifts"]
    reused = 0 if a.only_fresh_calls else sum(1 for r in fresh if r.get("reused"))
    print(json.dumps({"fresh_scored": len(fresh), "fresh_reused_scored": reused,
                      "unmatched_keys": len(unmatched), "unmatched_sample": unmatched[:10],
                      "per_ref": per, "pooled": pooled, "drifts": drifts[:200]}, indent=1))


if __name__ == "__main__":
    main()
