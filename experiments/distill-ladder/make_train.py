"""The distillation exercise's training items (PLAN.md, Data): math-ladder's generator at seed 70010, over ladder
v1's 26 cells (the combined ladder and the one-knob sweeps), 78 claims a cell (39 supported, 39 unsupported), so
2,028 before dedupe. Ids become `mlt-...` and the origin `math-ladder-train`, so nothing is shared with v1 or v2.

Then dedupe.py drops any item whose normalised function source matches an item in ladder v1 or the sealed ladder
v2. v2 is read here only to hash its sources; nothing about its items is printed. Only the output's seal and counts
are committed.

  python -I make_train.py --generator <math-ladder/generate.py> --v1 <ladder.jsonl> --v2 <sealed ladder-v2.jsonl> --out <train.jsonl>
"""

import argparse
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dedupe  # noqa: E402

SEED = 70010
N_PER_CELL = 78


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--generator", type=Path, required=True)
    ap.add_argument("--v1", type=Path, required=True)
    ap.add_argument("--v2", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    spec = importlib.util.spec_from_file_location("ml_generate", a.generator)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    rows, fallback = gen.generate(seed=SEED, n_per_cell=N_PER_CELL)
    for r in rows:
        r["id"] = "mlt-" + r["id"][len("ml-"):]
        r["origin"] = "math-ladder-train"
        for c in r["context"]:
            c["source"] = c["source"].replace("math-ladder-v1/ml-", "math-ladder-train/mlt-")
    assert len({r["id"] for r in rows}) == len(rows)
    read = lambda p: [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
    kept, dropped = dedupe.dedupe(rows, read(a.v1), read(a.v2))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in kept), encoding="utf-8", newline="\n")
    labels = Counter(r["label"] for r in kept)
    print(json.dumps({"seed": SEED, "cells": len(gen.cells()), "generated": len(rows), "dropped_as_test_overlap": len(dropped),
                      "kept": len(kept), "by_label": dict(sorted(labels.items())), "nearmiss3_fallbacks": fallback,
                      "seal": dedupe.seal(kept)}, indent=1))


if __name__ == "__main__":
    main()
