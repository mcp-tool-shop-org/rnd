"""Difficulty tiers for the calibration gold, so each model's accuracy can be read as a curve: where does it
fall off? Fixed 2026-10-09 at 02:15, before any candidate's chain run, from the gold's own metadata (labels,
notes, origin), never from model results.

  T1 surface  - a false claim that differs by a value or name you could catch by comparing strings
                (changed number, swapped term/name/port/value/version/target, wrong value); supported claims
                not tagged hard.
  T2 logic    - a false claim that needs the code understood (negation, a dropped or added condition, strict vs
                inclusive bound, behaviour, outcome, order, default, scope, severity, formula, direction, step).
  T3 hard     - items built to be hard: the reasoning set's "hard:" tag (subtle change, multi-part, indirect
                effect, doc comment overclaims), and change-specific traps (a false "no behaviour change", old
                behaviour credited to the change, behaviour the hunk disclaims). Supported claims tagged hard too.
  T4 unknown  - gold cannot_tell: the deciding code isn't in the evidence.
Second axis: evidence length (total context characters), in quartiles within each check type.

A verdict is correct when: supported → supported; unsupported → unsupported; cannot_tell → unsupported or
cannot_tell (offrig#44's rule: only accepting it is wrong). Reported per model × check type × tier: n,
accuracy, false accepts (on not-supported gold), abstains (cannot_tell on decided gold). Falloff = the first
tier where accuracy drops below 0.80 or the false-accept rate exceeds 0.10. Every cell shows n and a
Wilson 95% interval, and cells under 30 claims are marked tentative. Descriptive only: the default
rule (calibration README) is unchanged.

  python difficulty.py tiers > tiers.json             # the fixed tier of every tune and held-out claim
  python difficulty.py report <run-dir>...            # per-tier table from offrig calibrate run directories
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

GOLD = Path(__file__).resolve().parent.parent
FILES = {"grounded": ["grounded.jsonl", "prs/grounded-prs.jsonl"], "reasoning": ["diffs/reasoning-diffs.jsonl"]}

SURFACE = re.compile(r"changed number|changed version|swapped (term|name|port|value|target)|wrong (new )?value"
                     r"|dropped term")
HARD = re.compile(r"hard:|false claim of no behaviour change|old behaviour credited|disclaims")


Z95 = 1.959963984540054  # offrig calibrate.rs's z
SMALL = 30  # cells under this are marked tentative (the Publisher, 2026-10-09)


def wilson(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p, z2 = k / n, Z95 * Z95
    centre = (p + z2 / (2 * n)) / (1 + z2 / n)
    margin = Z95 * ((p * (1 - p) / n + z2 / (4 * n * n)) ** 0.5) / (1 + z2 / n)
    return (max(0.0, centre - margin), min(1.0, centre + margin))


def tier(r: dict) -> str:
    notes = (r.get("notes") or "").lower()
    if r["label"] == "cannot_tell":
        return "T4"
    if HARD.search(notes):
        return "T3"
    if r["label"] == "supported":
        return "T1"
    head = notes.split("|")[0]
    return "T1" if SURFACE.search(head) else "T2"


def load() -> list[dict]:
    rows = []
    for ct, fs in FILES.items():
        for f in fs:
            for line in (GOLD / f).read_text(encoding="utf-8").splitlines():
                if line.strip():
                    r = json.loads(line)
                    r["_ct"] = ct
                    rows.append(r)
    return rows


def tiers() -> dict:
    rows = load()
    out = {}
    for ct in FILES:
        lens = sorted(sum(len(c["text"]) for c in r["context"]) for r in rows if r["_ct"] == ct)
        cut = [lens[len(lens) * q // 4] for q in (1, 2, 3)]
        for r in (r for r in rows if r["_ct"] == ct):
            n = sum(len(c["text"]) for c in r["context"])
            out[r["id"]] = {"check_type": ct, "split": r.get("split"), "label": r["label"], "tier": tier(r),
                            "length_q": 1 + sum(n > c for c in cut), "context_chars": n}
    return out


def report(dirs: list[str]) -> None:
    t = tiers()
    for d in dirs:
        lines = [json.loads(x) for x in (Path(d) / "verdicts.jsonl").read_text(encoding="utf-8").splitlines() if x]
        model = json.loads((Path(d) / "manifest.json").read_text(encoding="utf-8"))["model"]
        cells = defaultdict(lambda: [0, 0, 0, 0, 0])  # n, right, false-accept, not-supported n, abstain
        for ln in lines:
            if ln.get("status") == "unusable" or ln["claim_id"] not in t:
                continue
            info, v = t[ln["claim_id"]], ln.get("final_verdict")
            g = info["label"]
            for key in (("tier", info["tier"]), ("length_q", f"Q{info['length_q']}")):
                c = cells[(info["check_type"], *key)]
                c[0] += 1
                c[1] += (v == g) or (g == "cannot_tell" and v in ("unsupported", "cannot_tell"))
                if g != "supported":
                    c[3] += 1
                    c[2] += v == "supported"
                c[4] += v == "cannot_tell" and g != "cannot_tell"
        for (ct, axis, val), (n, right, fa, neg, ab) in sorted(cells.items()):
            alo, ahi = wilson(right, n)
            flo, fhi = wilson(fa, neg)
            mark = "  <30, tentative" if n < SMALL else ""
            print(f"{model:20} {ct:9} {axis:8} {val:3} n={n:3} acc={right / n:.2f} [{alo:.2f},{ahi:.2f}] "
                  f"FA={fa}/{neg} ({fa / neg if neg else 0:.2f} [{flo:.2f},{fhi:.2f}]) abstain={ab}{mark}")


if __name__ == "__main__":
    if sys.argv[1:2] == ["tiers"]:
        print(json.dumps(tiers(), indent=0))
    elif sys.argv[1:2] == ["report"]:
        report(sys.argv[2:])
    else:
        sys.exit(__doc__)
