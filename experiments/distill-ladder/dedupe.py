"""Dedupe and seal for the distillation exercise (PLAN.md, "Data").

- A training item is dropped when its function source matches any item in a test set. "Matches" means the
  same normalised-source hash: line endings unified, trailing whitespace and blank lines removed, runs of
  spaces and tabs inside a line collapsed. It is a textual identity, so two functions that differ only in a
  constant are different items.
- The seal of a set is the sha256 of its canonical jsonl: one row per line, keys sorted, compact separators,
  UTF-8, "\\n" line ends, in the set's own order. Changing, adding, removing or reordering any item changes it.

  python dedupe.py train.jsonl test1.jsonl [test2.jsonl ...] > kept.jsonl   # dropped count to stderr
  python dedupe.py --seal set.jsonl                                         # prints the sha256
"""

import hashlib
import json
import re
import sys
from pathlib import Path

_SPACES = re.compile(r"[ \t]+")


def normalise_source(text: str) -> str:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    kept = []
    for line in lines:
        stripped = line.rstrip()
        if not stripped:
            continue
        indent = len(stripped) - len(stripped.lstrip())
        kept.append(stripped[:indent] + _SPACES.sub(" ", stripped[indent:]))
    return "\n".join(kept)


def source_of(row: dict) -> str:
    """The function source an item is about: its context texts, in order."""
    return "\n".join(c["text"] for c in row.get("context", []))


def source_hash(row: dict) -> str:
    return hashlib.sha256(normalise_source(source_of(row)).encode("utf-8")).hexdigest()


def dedupe(train: list[dict], *tests: list[dict]) -> tuple[list[dict], list[str]]:
    """Training rows whose source hash is in no test set (order kept), and the ids dropped."""
    seen = {source_hash(r) for t in tests for r in t}
    kept, dropped = [], []
    for r in train:
        if source_hash(r) in seen:
            dropped.append(r.get("id"))
        else:
            kept.append(r)
    return kept, dropped


def canonical_jsonl(rows: list[dict]) -> str:
    return "".join(json.dumps(r, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n" for r in rows)


def seal(rows: list[dict]) -> str:
    return hashlib.sha256(canonical_jsonl(rows).encode("utf-8")).hexdigest()


def _read(path: str) -> list[dict]:
    return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["--seal"] and len(args) == 2:
        print(seal(_read(args[1])))
    elif len(args) >= 2:
        kept, dropped = dedupe(_read(args[0]), *(_read(a) for a in args[1:]))
        sys.stdout.write(canonical_jsonl(kept))
        print(f"kept {len(kept)}, dropped {len(dropped)}", file=sys.stderr)
    else:
        sys.exit(__doc__)
