"""Read every seed's scores and apply the pre-registered rule.

    python summarise.py            # prints a Markdown table, writes results/summary.json

The rule (README, written before the run): on the confirmation set, hard-choice
accuracy >= 0.85 with option A chosen 40-60% of the time, and order-averaged
accuracy not below the untrained Kev-4B's 0.973. Three seeds must all pass. The
judge set is reported beside it as the transfer check.
"""

import json
import re
from pathlib import Path

RESULTS = Path(__file__).parent / "results"
FROZEN_ORDER_AVERAGED = 0.973      # Kev-4B v1.0 on the same 149 pairs (aspire-si PR #36)
SEEDS_NEEDED = 3


def passes(confirm: dict) -> bool:
    return (confirm["accuracy"] >= 0.85 and 0.40 <= confirm["a_rate"] <= 0.60
            and confirm["order_averaged"]["accuracy"] >= FROZEN_ORDER_AVERAGED)


def main() -> None:
    seeds = sorted({int(m.group(1)) for f in RESULTS.glob("judge-4b-full-s*-confirm.json")
                    if (m := re.search(r"-s(\d+)-confirm", f.name))})
    rows = []
    for s in seeds:
        c = json.loads((RESULTS / f"judge-4b-full-s{s}-confirm.json").read_text(encoding="utf-8"))
        j = json.loads((RESULTS / f"judge-4b-full-s{s}-judge.json").read_text(encoding="utf-8"))
        rows.append({"seed": s, "confirm_hard": c["accuracy"], "confirm_a_rate": c["a_rate"],
                     "confirm_order_averaged": c["order_averaged"]["accuracy"],
                     "confirm_order_averaged_ci": c["order_averaged"]["ci"],
                     "judge_hard": j["accuracy"], "judge_a_rate": j["a_rate"],
                     "judge_order_averaged": j["order_averaged"]["accuracy"], "passes": passes(c)})
    verdict = ("helps" if len(rows) >= SEEDS_NEEDED and all(r["passes"] for r in rows)
               else "fails" if any(not r["passes"] for r in rows) else "pending")
    (RESULTS / "summary.json").write_text(json.dumps({"rule_frozen_order_averaged": FROZEN_ORDER_AVERAGED,
                                                      "seeds": rows, "verdict": verdict}, indent=1), encoding="utf-8")
    print("| seed | confirm hard | A-rate | confirm order-averaged [95% CI] | judge hard | judge A-rate | judge order-averaged | rule |")
    print("|---|---|---|---|---|---|---|---|")
    for r in rows:
        lo, hi = r["confirm_order_averaged_ci"]
        print(f"| {r['seed']} | {r['confirm_hard']:.3f} | {r['confirm_a_rate']:.0%} | "
              f"{r['confirm_order_averaged']:.3f} [{lo:.3f}, {hi:.3f}] | {r['judge_hard']:.3f} | "
              f"{r['judge_a_rate']:.0%} | {r['judge_order_averaged']:.3f} | {'pass' if r['passes'] else 'FAIL'} |")
    print(f"\nverdict: {verdict} ({len(rows)} of {SEEDS_NEEDED} seeds)")


if __name__ == "__main__":
    main()
