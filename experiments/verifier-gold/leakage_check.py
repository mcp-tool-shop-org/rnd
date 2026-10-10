"""Leakage check for a new task set against the verifier-gold splits (R&D, 2026-10-10).

A task leaks when it repeats or closely copies a gold item. The checks are:
- the same claim after normalisation;
- a near-duplicate claim (character 5-gram Jaccard >= 0.8);
- an evidence block sharing 3 or more non-trivial lines with a gold item's evidence.

  python leakage_check.py <tasks.jsonl> [--json]

Task fields are read flexibly. The claim comes from `claim` or `statement`. The material comes from `material`,
`evidence`, `context`, or a list of {text}.

A same or near-duplicate claim **fails** (exit 1). Shared evidence lines are a **warning**: tasks built from our
repos at pinned commits will often quote the same source lines as gold, which is a leak only if that gold item
is in the training data of the model being tested. The report lists every hit with its gold id and split, so
the owner of the training data can decide.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOLD = [HERE / "grounded.jsonl", HERE / "prs" / "grounded-prs.jsonl", HERE / "diffs" / "reasoning-diffs.jsonl"]
JACCARD = 0.8
SHARED_LINES = 3


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", s.lower())).strip()


def grams(s: str, n: int = 5) -> set:
    s = norm(s)
    return {s[i:i + n] for i in range(max(1, len(s) - n + 1))}


def text_of(x) -> str:
    if x is None:
        return ""
    if isinstance(x, str):
        return x
    if isinstance(x, dict):
        return text_of(x.get("text"))
    if isinstance(x, list):
        return "\n".join(text_of(i) for i in x)
    return str(x)


def lines_of(s: str) -> set:
    return {norm(line) for line in s.splitlines() if len(norm(line)) >= 12}


def fields(row: dict) -> tuple[str, str]:
    claim = row.get("claim") or row.get("statement") or ""
    material = next((row[k] for k in ("material", "evidence", "context") if row.get(k)), "")
    return text_of(claim), text_of(material)


def load(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def check(tasks: list[dict]) -> list[dict]:
    gold = []
    for p in GOLD:
        for g in load(p):
            c, m = fields(g)
            gold.append((g["id"], g.get("split"), norm(c), grams(c), lines_of(m)))
    hits = []
    for i, t in enumerate(tasks):
        c, m = fields(t)
        tid, nc, gc, lm = t.get("id", f"#{i}"), norm(c), grams(c), lines_of(m)
        for gid, split, gnc, ggc, glm in gold:
            why = []
            if nc and nc == gnc:
                why.append("same claim")
            else:
                j = len(gc & ggc) / max(1, len(gc | ggc))
                if j >= JACCARD:
                    why.append(f"near-duplicate claim (Jaccard {j:.2f})")
            shared = len(lm & glm)
            if shared >= SHARED_LINES:
                why.append(f"{shared} shared evidence lines")
            if why:
                hits.append({"task": tid, "gold": gid, "split": split, "why": why,
                             "fail": any(w.startswith(("same claim", "near-duplicate")) for w in why)})
    return hits


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    tasks = load(Path(argv[0]))
    hits = check(tasks)
    if "--json" in argv:
        print(json.dumps({"tasks": len(tasks), "hits": hits}, indent=1))
    else:
        fails = [h for h in hits if h["fail"]]
        print(f"{len(tasks)} tasks checked against {len(GOLD)} gold files: {len(fails)} claim leak(s), "
              f"{len(hits) - len(fails)} evidence-overlap warning(s)")
        for h in hits:
            tag = "FAIL" if h["fail"] else "warn"
            print(f"  {tag} {h['task']} ~ {h['gold']} ({h['split']}): {'; '.join(h['why'])}")
    return 1 if any(h["fail"] for h in hits) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
