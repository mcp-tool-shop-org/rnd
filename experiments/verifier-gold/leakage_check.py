"""Leakage check for a new task set against the verifier-gold splits (R&D, 2026-10-10).

A task leaks when it repeats or closely copies a gold item. The checks are:
- the same claim after normalisation;
- a near-duplicate claim (character 5-gram Jaccard >= 0.8);
- an evidence block sharing 3 or more non-trivial lines with a gold item's evidence.

  python leakage_check.py <tasks.jsonl> [--json]
  python leakage_check.py <training.jsonl> --against <sealed.jsonl> --against <pilot.jsonl> --against <interview.md> ...

With `--against`, the file is also checked against each named set. These are held-out sets that training
data must never touch: the sealed task set, the pilot, and the pre-interview. Against them the bar is
stricter than against gold:
- a near-duplicate claim (5-gram Jaccard >= 0.8) still **fails**;
- a looser match (Jaccard >= 0.5) is a **warning**, so a person can check it for paraphrase;
- **2 or more** shared non-trivial material lines **fail**, because the held-out sets' sources are
  excluded from training outright.

An `.md` file is read as one item per numbered line ("1. ..."), which is how the pre-interview lists its
questions.

Task fields are read flexibly. The claim comes from `claim` or `statement`, or, for a training item, from
its user turns (`turns[].user`), compared sentence by sentence. The material comes from `material`,
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
HELD_OUT_WARN = 0.5
HELD_OUT_LINES = 2


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
    if not claim and isinstance(row.get("turns"), list):  # training items: the text lives in the user turns
        claim = "\n".join(t.get("user", "") for t in row["turns"] if isinstance(t, dict))
    return text_of(claim), text_of(material)


def sentences(s: str) -> list[str]:
    """A long text (a training item's user turns) is compared sentence by sentence, so a copied question
    inside a longer prompt is still caught."""
    parts = [x for x in re.split(r"(?<=[.?!])\s+|\n", s) if len(norm(x)) >= 20]
    return parts if len(norm(s)) > 300 else [s]


def best_jaccard(text: str, ref_grams: set) -> float:
    return max((len(grams(x) & ref_grams) / max(1, len(grams(x) | ref_grams)) for x in sentences(text)),
               default=0.0)


def load(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".md":
        q = re.search(r"^## Questions\s*$(.*?)(?=^## |\Z)", text, flags=re.M | re.S)
        text = q.group(1) if q else text
        items = re.findall(r"^\s*(\d+)\.\s+(.+(?:\n\s{2,}\S.*)*)", text, flags=re.M)
        return [{"id": f"{path.stem}#{n}", "claim": re.sub(r"\s+", " ", q).strip()} for n, q in items]
    return [json.loads(x) for x in text.splitlines() if x.strip()]


def check_against(tasks: list[dict], ref_path: Path) -> list[dict]:
    """Held-out check: training items against a set they must never touch."""
    refs = [(r.get("id", f"#{i}"), *fields(r)) for i, r in enumerate(load(ref_path))]
    refs = [(rid, norm(c), grams(c), lines_of(m)) for rid, c, m in refs]
    hits = []
    for i, t in enumerate(tasks):
        c, m = fields(t)
        tid, nc, gc, lm = t.get("id", f"#{i}"), norm(c), grams(c), lines_of(m)
        for rid, rnc, rgc, rlm in refs:
            why, fail = [], False
            if nc and nc == rnc:
                why.append("same claim")
                fail = True
            else:
                j = best_jaccard(c, rgc)
                if j >= JACCARD:
                    why.append(f"near-duplicate claim (Jaccard {j:.2f})")
                    fail = True
                elif j >= HELD_OUT_WARN:
                    why.append(f"similar claim (Jaccard {j:.2f}), check for paraphrase")
            shared = len(lm & rlm)
            if shared >= HELD_OUT_LINES:
                why.append(f"{shared} shared material lines")
                fail = True
            if why:
                hits.append({"task": tid, "gold": rid, "split": ref_path.name, "why": why, "fail": fail})
    return hits


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
                j = best_jaccard(c, ggc)
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
    against = [Path(argv[i + 1]) for i, a in enumerate(argv[:-1]) if a == "--against"]
    for ref in against:
        hits += check_against(tasks, ref)
    if "--json" in argv:
        print(json.dumps({"tasks": len(tasks), "hits": hits}, indent=1))
    else:
        fails = [h for h in hits if h["fail"]]
        print(f"{len(tasks)} tasks checked against {len(GOLD)} gold files and {len(against)} held-out set(s): "
              f"{len(fails)} failure(s), {len(hits) - len(fails)} warning(s)")
        for h in hits:
            tag = "FAIL" if h["fail"] else "warn"
            print(f"  {tag} {h['task']} ~ {h['gold']} ({h['split']}): {'; '.join(h['why'])}")
    return 1 if any(h["fail"] for h in hits) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
