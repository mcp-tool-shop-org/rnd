"""Per-cell table for the math ladder: each model's accuracy and false accepts by ladder level and by knob, with
Wilson 95% intervals. The falloff is the first cell where accuracy drops below 0.80 or false accepts exceed
0.10, read along the combined ladder (L1..L8) and along each knob's sweep (level 1..3).

  python report.py <offrig-calibrate-run-dir>...
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
Z = 1.959963984540054


def wilson(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p, z2 = k / n, Z * Z
    c = (p + z2 / (2 * n)) / (1 + z2 / n)
    m = Z * ((p * (1 - p) / n + z2 / (4 * n * n)) ** 0.5) / (1 + z2 / n)
    # Exact at the edges: float rounding left wilson(0, n)'s lower bound at ~1e-17, above the observed 0,
    # which would read as "the interval excludes 0" for a cell with no events.
    lo = 0.0 if k == 0 else max(0.0, c - m)
    hi = 1.0 if k == n else min(1.0, c + m)
    return (lo, hi)


def tally(gold: dict, verdicts: list[dict]) -> dict:
    """Per-cell counts [n, right, false accepts, unsupported n, abstain, unusable] from verdict lines.
    Lines whose claim isn't in the gold are ignored; an unusable line counts only as unusable."""
    cells = defaultdict(lambda: [0, 0, 0, 0, 0, 0])
    for ln in verdicts:
        g = gold.get(ln["claim_id"])
        if g is None:
            continue
        c = cells[g["ladder"]["cell"]]
        if ln.get("status") == "unusable":
            c[5] += 1
            continue
        v = ln.get("final_verdict")
        c[0] += 1
        c[1] += v == g["label"]
        if g["label"] == "unsupported":
            c[3] += 1
            c[2] += v == "supported"
        c[4] += v == "cannot_tell"
    return cells


def main(dirs: list[str]) -> None:
    gold = {}
    for line in (HERE / "ladder.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        gold[r["id"]] = r
    order = [f"L{i}" for i in range(1, 9)] + [f"{k}={v}" for k in
             ("steps", "precedence", "traps", "control", "units", "nearmiss") for v in (1, 2, 3)]
    for d in dirs:
        model = json.loads((Path(d) / "manifest.json").read_text(encoding="utf-8"))["model"]
        verdicts = [json.loads(x) for x in (Path(d) / "verdicts.jsonl").read_text(encoding="utf-8").splitlines()]
        cells = tally(gold, verdicts)
        falloff = {"ladder": None}
        print(f"\n{model}")
        for cell in order:
            n, right, fa, neg, ab, bad = cells.get(cell, [0] * 6)
            if not n:
                continue
            acc, (alo, ahi) = right / n, wilson(right, n)
            far, (flo, fhi) = (fa / neg if neg else 0.0), wilson(fa, neg)
            design = "ladder" if cell.startswith("L") else cell.split("=")[0]
            if falloff.get(design) is None and (acc < 0.80 or far > 0.10):
                falloff[design] = cell
            print(f"  {cell:13} n={n:2} acc={acc:.2f} [{alo:.2f},{ahi:.2f}] FA={fa}/{neg} ({far:.2f} "
                  f"[{flo:.2f},{fhi:.2f}]) abstain={ab}" + (f" unusable={bad}" if bad else "")
                  + ("  <30, tentative" if n < 30 else ""))
        print("  falloff: " + ", ".join(f"{k} at {v}" for k, v in falloff.items() if v) or "  falloff: none")


if __name__ == "__main__":
    main(sys.argv[1:])
