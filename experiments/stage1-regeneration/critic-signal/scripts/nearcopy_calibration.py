"""Calibrate Track A's near-duplicate rung on prose rows (PLAN-ROUND4 §3), per Argon's consult of 2026-10-21.

usage: python nearcopy_calibration.py <gold-input.jsonl> <private-out-dir> <public-receipt.json>

Needs torch (CPU is enough) and sentence-transformers, and a dataset-desk checkout on DATASET_DESK (default: a
sibling of this repo).

- Positives, built deterministically from each phase-4 kind C draft:
  - P-close: a surface near-copy (two lines swapped for unordered kinds, days and numbers nudged, bullets toggled;
    the trace's clauses and connectors reworded);
  - P-template: the same layout and trace skeleton with domain nouns swapped through a fixed table.
- Negatives: all 496 off-diagonal pairs of the 32 drafts, with the hard strata Argon named
  (material: same content kind or same lesson; trace: same planted flaw or same lesson).
- Measures, per field: bge-m3 cosine through dataset-desk's text embedder on CPU (float32), character 4-gram Jaccard,
  and for material a digit-masked line-set Jaccard. Verbatim quotes of the material or statement are stripped from a
  trace before scoring.
- Thresholds: T_auto = max(hard negatives) + 0.005 (cosine) or + 0.02 (lexical); the midpoint if the lowest P-close
  clears the hardest negative. A review band starts at the hard negatives' 95th percentile.

The rows are private. The private dir gets the positives and every pair score; the public receipt carries only slot
ids, pool sizes, order statistics, thresholds and confidence bounds.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import re
import sys
from pathlib import Path

ORDERED_KINDS = {"changelog", "timetable"}
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
CONNECTORS = [
    ("the material states", "according to the text"),
    ("The material states", "According to the text"),
    ("therefore", "so"),
    ("Therefore", "So"),
    ("because", "since"),
    ("Because", "Since"),
    ("clearly", "plainly"),
    ("I'll mark", "I will mark"),
    ("isn't", "is not"),
    ("doesn't", "does not"),
]
# A fixed domain-noun table: each frequent domain noun moves to a noun from another domain, keeping the layout.
NOUNS = {
    "Yoga": "Pottery", "yoga": "pottery", "Choir": "Chess", "Hall": "Annex", "Station": "Depot", "Community": "Harbor",
    "community": "harbor", "Center": "Office", "center": "office", "Class": "Workshop", "classes": "workshops",
    "Book": "Film", "Club": "Circle", "dashboard": "console", "settings": "preferences", "elevators": "escalators",
    "lobby": "foyer", "water": "power", "taps": "outlets", "portal": "kiosk", "menu": "toolbar", "shipping": "billing",
    "department": "division", "project": "campaign", "search": "filter", "archive": "ledger", "interface": "panel",
    "mobile": "tablet", "devices": "terminals", "synchronization": "indexing", "button": "toggle", "maintenance":
    "inspection", "Maintenance": "Inspection", "service": "shuttle", "reports": "invoices", "user": "member",
    "order": "booking", "amount": "balance", "portal's": "kiosk's", "North": "East", "morning": "evening",
    "October": "March", "June": "April", "speed": "range", "crash": "freeze", "loading": "rendering",
}
STOP = set("""the a an and or of to in on at for from with by this that will must should be is are was were has have
been not no it its as if when where during before after every between""".split())


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower()).strip()


def char_ngrams(s: str, n: int = 4) -> set[str]:
    t = norm(s)
    return {t[i:i + n] for i in range(max(0, len(t) - n + 1))}


def jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if (a or b) else 0.0


def line_set(s: str) -> set[str]:
    return {re.sub(r"\d+", "<NUM>", norm(x)) for x in s.splitlines() if x.strip()}


def strip_quotes(trace: str, material: str, statement: str) -> str:
    src = norm(material + " " + statement)
    def keep(m):
        inner = m.group(2)
        return "" if len(inner) >= 4 and norm(inner) in src else m.group(0)
    return re.sub(r"(['\"])(.+?)\1", keep, trace)


def parse_candidate(text: str) -> dict:
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*", "", t)
    t = re.sub(r"\s*```$", "", t)
    return json.loads(t)


def rng_for(slot_id: str, tag: str) -> int:
    return int(hashlib.sha256(f"{slot_id}:{tag}".encode()).hexdigest(), 16)


def p_close(row: dict) -> tuple[str, str]:
    sid, kind = row["slot_id"], row["content_kind"]
    lines = row["material"].splitlines()
    idx = [i for i, x in enumerate(lines) if x.strip() and i > 0]
    if kind not in ORDERED_KINDS and len(idx) >= 2:
        h = rng_for(sid, "swap")
        i, j = idx[h % len(idx)], idx[(h // 7) % len(idx)]
        if i == j:
            j = idx[(idx.index(i) + 1) % len(idx)]
        lines[i], lines[j] = lines[j], lines[i]
    mat = "\n".join(lines)
    # Nudge days and numbers.
    for d_i, d in enumerate(DAYS):
        mat = re.sub(rf"\b{d}\b", f"@@{d_i}@@", mat)
    mat = re.sub(r"@@(\d)@@", lambda m: DAYS[(int(m.group(1)) + 1) % 7], mat)
    mat = re.sub(r"\b(\d{1,3})\b", lambda m: str(int(m.group(1)) + 5), mat)
    # Toggle bullets.
    mat = "\n".join(("* " + x[2:]) if x.startswith("- ") else (("- " + x[2:]) if x.startswith("* ") else x)
                    for x in mat.splitlines())
    tr = row["trace"]
    for d_i, d in enumerate(DAYS):
        tr = re.sub(rf"\b{d}\b", f"@@{d_i}@@", tr)
    tr = re.sub(r"@@(\d)@@", lambda m: DAYS[(int(m.group(1)) + 1) % 7], tr)
    tr = re.sub(r"\b(\d{1,3})\b", lambda m: str(int(m.group(1)) + 5), tr)
    for a, b in CONNECTORS:
        tr = tr.replace(a, f"§{b}§") if a in tr else tr.replace(b, f"§{a}§")
    tr = tr.replace("§", "")
    # Invert the clause order of a two-sentence trace.
    parts = re.split(r"(?<=[.!?])\s+", tr.strip())
    if len(parts) == 2:
        tr = parts[1] + " " + parts[0]
    return mat, tr


def p_template(row: dict) -> tuple[str, str]:
    def swap(s: str) -> str:
        return re.sub(r"[A-Za-z][A-Za-z']+", lambda m: NOUNS.get(m.group(0), m.group(0)), s)
    return swap(row["material"]), swap(row["trace"])


def quantile(xs: list[float], q: float) -> float:
    s = sorted(xs)
    if not s:
        return float("nan")
    k = (len(s) - 1) * q
    lo, hi = math.floor(k), math.ceil(k)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def cp_upper_zero(n: int) -> float:
    """One-sided 95% Clopper-Pearson upper bound when 0 of n events occur."""
    return 1 - 0.05 ** (1 / n) if n else float("nan")


def cp_lower_all(n: int) -> float:
    """One-sided 95% lower bound when n of n succeed."""
    return 0.05 ** (1 / n) if n else float("nan")


def main() -> int:
    src, priv_dir, receipt = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    raw = [json.loads(l) for l in src.read_text(encoding="utf-8").splitlines() if l.strip()][1:]
    rows = []
    for r in raw:
        cand = parse_candidate(r["candidate"]["text"])
        rows.append({
            "slot_id": r["slot"]["id"], "lesson": r["slot"]["lesson"], "content_kind": r["slot"].get("content_kind"),
            "flaw": r["key"].get("planted_flaw"), "material": r["material"]["text"],
            "statement": cand.get("statement", ""), "trace": cand.get("checker_trace", ""),
        })

    import os
    sys.path.insert(0, os.environ.get("DATASET_DESK", str(Path(__file__).resolve().parents[5] / "dataset-desk")))
    from dataset_desk.backends import SentenceTransformerTextEmbedder
    from dataset_desk.registry import REGISTRY
    spec = REGISTRY["bge-m3"]
    emb = SentenceTransformerTextEmbedder(spec, device="cpu", threads=8)

    pos = []
    for r in rows:
        for tier, fn in (("close", p_close), ("template", p_template)):
            m, t = fn(r)
            pos.append({"slot_id": r["slot_id"], "tier": tier, "material": m, "trace": t,
                        "statement": r["statement"]})

    texts_m = [r["material"] for r in rows] + [p["material"] for p in pos]
    texts_t = [strip_quotes(r["trace"], r["material"], r["statement"]) for r in rows] + \
              [strip_quotes(p["trace"], p["material"], p["statement"]) for p in pos]
    vm = emb.texts(texts_m).tolist()
    vt = emb.texts(texts_t).tolist()
    n = len(rows)

    def cos(v, i, j):
        return float(sum(a * b for a, b in zip(v[i], v[j])))

    def score(i, j):
        return {
            "mat_cos": cos(vm, i, j), "mat_c4": jaccard(char_ngrams(texts_m[i]), char_ngrams(texts_m[j])),
            "mat_lines": jaccard(line_set(texts_m[i]), line_set(texts_m[j])),
            "tr_cos": cos(vt, i, j), "tr_c4": jaccard(char_ngrams(texts_t[i]), char_ngrams(texts_t[j])),
        }

    pos_scores = []
    for k, p in enumerate(pos):
        i = next(ix for ix, r in enumerate(rows) if r["slot_id"] == p["slot_id"])
        pos_scores.append({"slot_id": p["slot_id"], "tier": p["tier"], **score(i, n + k)})
    neg_scores = []
    for i, j in itertools.combinations(range(n), 2):
        a, b = rows[i], rows[j]
        neg_scores.append({
            "a": a["slot_id"], "b": b["slot_id"],
            "hard_material": a["lesson"] == b["lesson"] or a["content_kind"] == b["content_kind"],
            "hard_trace": a["lesson"] == b["lesson"] or a["flaw"] == b["flaw"],
            **score(i, j),
        })

    priv_dir.mkdir(parents=True, exist_ok=True)
    (priv_dir / "positives.jsonl").write_text("".join(json.dumps(p, ensure_ascii=False) + "\n" for p in pos),
                                              encoding="utf-8", newline="\n")
    (priv_dir / "scores.json").write_text(json.dumps({"positives": pos_scores, "negatives": neg_scores}, indent=1),
                                          encoding="utf-8", newline="\n")

    def summary(field: str, hard_key: str, margin: float) -> dict:
        hard = [x[field] for x in neg_scores if x[hard_key]]
        allneg = [x[field] for x in neg_scores]
        close = [x[field] for x in pos_scores if x["tier"] == "close"]
        templ = [x[field] for x in pos_scores if x["tier"] == "template"]
        max_hard = max(hard)
        t_auto = max_hard + margin
        if min(close) > max_hard:
            t_auto = (min(close) + max_hard) / 2
        caught_close = sum(v >= t_auto for v in close)
        caught_templ = sum(v >= t_auto for v in templ)
        return {
            "n_hard": len(hard), "n_all_negatives": len(allneg), "n_close": len(close), "n_template": len(templ),
            "hard_neg": {"p50": quantile(hard, .5), "p95": quantile(hard, .95), "p99": quantile(hard, .99),
                         "max": max_hard},
            "all_neg": {"p50": quantile(allneg, .5), "p95": quantile(allneg, .95), "max": max(allneg)},
            "close": {"min": min(close), "p05": quantile(close, .05), "p50": quantile(close, .5)},
            "template": {"min": min(templ), "p05": quantile(templ, .05), "p50": quantile(templ, .5)},
            "gap_close_minus_hard": min(close) - max_hard,
            "t_auto": t_auto, "t_review": quantile(hard, .95),
            "recall_close": f"{caught_close}/{len(close)}", "recall_template": f"{caught_templ}/{len(templ)}",
            "fp_hard": f"{sum(v >= t_auto for v in hard)}/{len(hard)}",
            "fp_all": f"{sum(v >= t_auto for v in allneg)}/{len(allneg)}",
            "fp_hard_upper95_if_zero": cp_upper_zero(len(hard)),
            "fp_all_upper95_if_zero": cp_upper_zero(len(allneg)),
        }

    out = {
        "source": "PLAN-ROUND4 §3 near-duplicate rung; design from Argon's consult, 2026-10-21",
        "pool": {"drafts": n, "slot_ids": [r["slot_id"] for r in rows], "positives_per_tier": n,
                 "negative_pairs": len(neg_scores)},
        "embedder": {"name": spec.name, "repo": spec.repo, "revision": spec.revision, "device": "cpu",
                     "dtype": "float32"},
        "fields": {
            "material_cosine": summary("mat_cos", "hard_material", 0.005),
            "material_char4": summary("mat_c4", "hard_material", 0.02),
            "material_lines": summary("mat_lines", "hard_material", 0.02),
            "trace_cosine": summary("tr_cos", "hard_trace", 0.005),
            "trace_char4": summary("tr_c4", "hard_trace", 0.02),
        },
    }
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    for k, v in out["fields"].items():
        print(k, json.dumps({x: v[x] for x in ("t_auto", "gap_close_minus_hard", "recall_close", "recall_template",
                                                "fp_hard", "fp_all")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
