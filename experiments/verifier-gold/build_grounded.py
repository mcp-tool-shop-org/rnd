"""Build the grounded gold set for offrig's verifier from role-os source at a pinned commit.

Each fact names a file, an anchor string that must occur in it, and how many lines of context to take
around the anchor. The evidence is those exact lines, read with `git show <sha>:<path>`, so nothing is
paraphrased. Each fact yields up to three claims:
  supported    the evidence states it;
  unsupported  a planted near-miss the evidence contradicts (a changed number, a flipped condition, a
               swapped term). These are the `subtle` items;
  cannot_tell  (optional) a plausible claim the evidence neither states nor contradicts.

Labels are R&D's (Claude), written against the code. A second blind pass checks a sample before the set
counts (see README). Output: grounded.jsonl in the verifier gold format agreed with the Publisher.

  python build_grounded.py --batch facts_roleos:E:/AI/role-os:ce91be8 \n      --batch facts_offrig:E:/AI/offrig:a45fe53 --out grounded.jsonl
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import importlib


def evidence(repo: Path, sha: str, path: str, anchor: str, before: int, after: int) -> tuple[str, int, int]:
    text = subprocess.run(
        ["git", "-C", str(repo), "show", f"{sha}:{path}"], capture_output=True, text=True, encoding="utf-8", check=True
    ).stdout.splitlines()
    hits = [i for i, line in enumerate(text) if anchor in line]
    if len(hits) != 1:
        raise SystemExit(f"{path}: anchor {anchor!r} matched {len(hits)} lines, need exactly 1")
    lo = max(0, hits[0] - before)
    hi = min(len(text), hits[0] + after + 1)
    return "\n".join(text[lo:hi]), lo + 1, hi


def build(repo: Path, sha: str, facts: list[dict], name: str) -> list[dict]:
    rows = []
    for f in facts:
        text, lo, hi = evidence(repo, sha, f["file"], f["anchor"], f.get("before", 6), f.get("after", 6))
        for must in f.get("must", []):
            if must not in text:
                raise SystemExit(f"{f['id']}: evidence lacks {must!r}; the fact no longer matches the code")
        ctx = [{"source": f"{name}@{sha}:{f['file']}#L{lo}-L{hi}", "text": text}]
        base = {"check_type": "grounded", "context": ctx, "origin": f"{name}-{sha}", "split": None}
        rows.append({**base, "id": f"{f['id']}-t", "claim": f["true"], "label": "supported", "subtle": False,
                     "notes": ""})
        rows.append({**base, "id": f"{f['id']}-f", "claim": f["false"], "label": "unsupported", "subtle": True,
                     "notes": f"near-miss: {f['kind']}"})
        if f.get("silent"):
            rows.append({**base, "id": f"{f['id']}-s", "claim": f["silent"], "label": "cannot_tell", "subtle": False,
                         "notes": "evidence is silent on this"})
    return rows


def assign_splits(rows: list[dict], salt: str = "20261008") -> None:
    """Split by FACT, never by claim, so a fact's true and false forms land on the same side. The side is a
    stable hash of the fact id, so adding a batch never moves an existing fact between tune and held-out."""
    for r in rows:
        fact = r["id"].rsplit("-", 1)[0]
        h = int(hashlib.sha256(f"{salt}:{fact}".encode()).hexdigest(), 16)
        r["split"] = "heldout" if h % 2 else "tune"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", action="append", required=True,
                    help="facts_module:repo_path:sha, e.g. facts_roleos:E:/AI/role-os:ce91be8 (repeatable)")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    rows, nfacts = [], 0
    for spec in a.batch:
        module, rest = spec.split(":", 1)
        repo, sha = rest.rsplit(":", 1)
        mod = importlib.import_module(module)
        rows += build(Path(repo), sha, mod.FACTS, mod.NAME)
        nfacts += len(mod.FACTS)
    assign_splits(rows)
    with a.out.open("w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    digest = hashlib.sha256(a.out.read_bytes()).hexdigest()[:16]
    counts = {}
    for r in rows:
        counts[(r["split"], r["label"])] = counts.get((r["split"], r["label"]), 0) + 1
    print(f"{len(rows)} claims from {nfacts} facts, sha256 {digest}")
    for k in sorted(counts):
        print(" ", k, counts[k])


if __name__ == "__main__":
    main()
