"""Ladder v2, the distillation exercise's sealed test (PLAN.md, Data): math-ladder's generator at a new seed, with
knob combinations ladder v1 never tested together. Ladder v1 had only the combined ladder (every knob rising at
once) and one-knob sweeps (the rest at 0).

Cells (24, 30 claims each, 15 supported and 15 unsupported, so 720 claims):
- ladder L1..L8: the same combined levels as v1, at the new seed, so the v1 and v2 curves compare;
- cross pairs: every pair of precedence, traps, control and units, both at level 2, then both at level 3 (12);
- cross triples: every triple of those four, all at level 2 (4).
Every cross cell holds steps=4 and nearmiss=3 (the naive twin's answer, which falls back to off-by-one where no
misreading applies), and the knobs not named at 0.

Rows are math-ladder's rows with v2's own ids (`ml2-...`) and origin (`math-ladder-v2`), so no id or source path is
shared with v1. The file is written outside every working directory and only its sha256 and counts are committed.

  python -I make_ladder_v2.py --generator <math-ladder/generate.py> --out <sealed path>
"""

import argparse
import hashlib
import importlib.util
import itertools
import json
from collections import Counter
from pathlib import Path

SEED = 20261022
CROSS = ("precedence", "traps", "control", "units")


def cell_list() -> list[tuple[str, str, dict]]:
    base = {"steps": 4, "precedence": 0, "traps": 0, "control": 0, "units": 0, "nearmiss": 3}
    cells = [("ladder", f"L{lv}", GEN.ladder_knobs(lv)) for lv in range(1, 9)]
    for lvl in (2, 3):
        for a, b in itertools.combinations(CROSS, 2):
            cells.append(("cross", f"{a}{lvl}x{b}{lvl}", base | {a: lvl, b: lvl}))
    for trio in itertools.combinations(CROSS, 3):
        cells.append(("cross", "x".join(f"{k}2" for k in trio), base | {k: 2 for k in trio}))
    return cells


def main() -> None:
    global GEN
    ap = argparse.ArgumentParser()
    ap.add_argument("--generator", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    spec = importlib.util.spec_from_file_location("ml_generate", a.generator)
    GEN = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(GEN)
    cells = cell_list()
    assert len(cells) == 24 and len({c[1] for c in cells}) == 24
    rows, fallback = GEN.generate(seed=SEED, cell_list=cells, n_per_cell=30)
    for r in rows:
        r["id"] = "ml2-" + r["id"][len("ml-"):]
        r["origin"] = "math-ladder-v2"
        for c in r["context"]:
            c["source"] = c["source"].replace("math-ladder-v1/ml-", "math-ladder-v2/ml2-")
    assert len({r["id"] for r in rows}) == len(rows) == 720
    text = GEN.to_text(rows)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(text, encoding="utf-8", newline="\n")
    counts = Counter((r["ladder"]["design"], r["label"]) for r in rows)
    print(json.dumps({"seed": SEED, "cells": len(cells), "claims": len(rows),
                      "by_design_label": {f"{d}/{l}": n for (d, l), n in sorted(counts.items())},
                      "nearmiss3_fallbacks": fallback,
                      "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}, indent=1))


GEN = None

if __name__ == "__main__":
    main()
