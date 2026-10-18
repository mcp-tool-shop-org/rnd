"""Every figure issue 13 quotes from the window data, computed from data/windows.csv and data/windows/*/gate.jsonl.

Run: python experiments/colab-golden-path/figures.py  (writes figures.json beside this file and prints it)
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"


def f(x: str) -> float | None:
    return float(x) if x not in ("", None) else None


def main() -> None:
    rows = list(csv.DictReader((DATA / "windows.csv").open(encoding="utf-8")))
    windows = [r for r in rows if r["window"].startswith("window")]
    out: dict = {"windows": len(windows)}

    def spent(rs):
        return round(sum(f(r["spent_units"]) or 0 for r in rs), 2)

    by_class: dict = {}
    for r in windows:
        c = r["outcome_class"] or "unclassified"
        e = by_class.setdefault(c, {"windows": 0, "units": 0.0})
        e["windows"] += 1
        e["units"] = round(e["units"] + (f(r["spent_units"]) or 0), 2)
    out["by_class"] = dict(sorted(by_class.items()))
    out["units_all_windows"] = spent(windows)

    for day in ("2026-10-16", "2026-10-17", "2026-10-18"):
        d = [r for r in windows if r["date"] == day]
        out[day] = {"windows": len(d), "units": spent(d),
                    "by_class": {c: spent([r for r in d if r["outcome_class"] == c])
                                 for c in sorted({r["outcome_class"] or "unclassified" for r in d})}}

    paid = [r for r in windows if r["outcome_class"] != "test" and (f(r["spent_units"]) or 0) > 0]
    got = [r for r in paid if r["outcome_class"] == "results"]
    out["paid_windows"] = len(paid)
    out["paid_units"] = spent(paid)
    out["results_units"] = spent(got)
    out["results_share"] = round(spent(got) / spent(paid), 3) if paid else None
    lost = [r for r in paid if r["outcome_class"] in ("lost-vm", "cap-stop", "tooling-fault")]
    out["lost_units"] = spent(lost)

    tests = [r for r in windows if r["outcome_class"] == "test"]
    out["test_windows"] = len(tests)
    out["test_units"] = spent(tests)

    tries, rejected, reasons = 0, 0, []
    # Only real windows: cpu-measure's rows were readings taken at the first, wrong floor (129), not windows.
    for g in sorted((DATA / "windows").glob("window*/gate.jsonl")):
        for line in g.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            tries += 1
            gate = row.get("gate") or {}
            if not gate.get("ok"):
                rejected += 1
                reasons.append({"window": g.parent.name, "try": row.get("try"), "why": gate.get("why")})
    out["gate"] = {"tries": tries, "rejected": rejected, "rejections": reasons}

    (HERE / "figures.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
