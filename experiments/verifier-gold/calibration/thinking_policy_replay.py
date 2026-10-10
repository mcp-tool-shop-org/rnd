"""Post hoc (2026-10-10): replay thinking policies over existing think-off and think-on verdicts on the same tune
claims, with no new runs. A policy picks, per claim, the off verdict or the on verdict. Wall seconds are summed for
the calls it would make.

  python thinking_policy_replay.py [model_tag]   (default gemma4_31b)
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent / "results"
Z = 1.959963984540054
ON = {"gemma4_31b": "2026-10-09-gemma-r2", "qwen3_8b": "2026-10-09-chain", "qwen3_14b": "2026-10-09-chain"}


def upper(k, n):
    if n == 0:
        return 1.0
    p, z2 = k / n, Z * Z
    c = (p + z2 / (2 * n)) / (1 + z2 / n)
    m = Z * ((p * (1 - p) / n + z2 / (4 * n * n)) ** 0.5) / (1 + z2 / n)
    return 1.0 if k == n else min(1.0, c + m)


def load(path):
    return {r["claim_id"]: r for r in (json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x)}


def think_before_accepting(off, on):
    """Off's 'unsupported' stands; otherwise ask with thinking; an unusable thinking call falls back to cannot_tell."""
    if off["status"] == "ok" and off["final_verdict"] == "unsupported":
        return off, False
    if on["status"] == "ok":
        return on, True
    return ({**off, "status": "ok", "final_verdict": "cannot_tell"}, True)


POLICIES = {
    "always off": lambda off, on: (off, False),
    "always on": lambda off, on: (on, True),
    "escalate on abstain or quote failure": lambda off, on: (
        (on, True) if off["status"] != "ok" or off["final_verdict"] == "cannot_tell" else (off, False)),
    "think before accepting": think_before_accepting,
}


def score(rows):
    ok = [r for r in rows if r["status"] == "ok"]
    neg = [r for r in ok if r["gold_label"] in ("unsupported", "cannot_tell")]
    fa = sum(r["final_verdict"] == "supported" for r in neg)
    dec = [r for r in ok if r["gold_label"] in ("supported", "unsupported")]
    ab = sum(r["final_verdict"] == "cannot_tell" for r in dec)
    d2 = [r for r in dec if r["final_verdict"] != "cannot_tell"]
    sp = [r for r in d2 if r["gold_label"] == "supported"]
    un = [r for r in d2 if r["gold_label"] == "unsupported"]
    ba = (sum(r["final_verdict"] == "supported" for r in sp) / len(sp)
          + sum(r["final_verdict"] == "unsupported" for r in un) / len(un)) / 2
    return f"FA {fa}/{len(neg)} upper {upper(fa, len(neg)):.3f}  abstain {ab / len(dec):.3f}  BA {ba:.3f}  missing {len(rows) - len(ok)}"


def main(tag="gemma4_31b"):
    for ct in ("grounded", "reasoning"):
        on = load(HERE / ON[tag] / f"cal-{tag}-{ct}-tune" / "verdicts.jsonl")
        off = load(HERE / "2026-10-09-thinking-off" / f"cal-{tag}-{ct}-tune" / "verdicts.jsonl")
        ids = sorted(set(on) & set(off))
        on_secs = sum(on[i]["wall_seconds"] or 0 for i in ids)
        for name, policy in POLICIES.items():
            rows, secs, thought = [], 0.0, 0
            for i in ids:
                r, think = policy(off[i], on[i])
                rows.append(r)
                thought += think
                secs += (0 if name == "always on" else off[i]["wall_seconds"] or 0) + (on[i]["wall_seconds"] or 0 if think else 0)
            print(f"{ct:9} {name:38} {score(rows)}  thinking {thought}/{len(ids)}  time {secs / on_secs:.0%} of always-on")


if __name__ == "__main__":
    main(*sys.argv[1:])
