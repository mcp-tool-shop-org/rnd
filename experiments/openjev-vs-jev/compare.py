"""Score local OpenJev against hosted Jev on the same 124 phrases and labels.

Uses sense-si's own study code (run_study: inner/outer split, temperature fit,
bootstrap) so both models are judged by the identical protocol.

    <sense-si venv python> compare.py

Writes $OPENJEV_WORK/compare.json and prints a summary.
"""

import json
import math
import os
import random
import sys
from pathlib import Path

WORK = Path(os.environ.get("OPENJEV_WORK", "E:/AI-Models/openjev/work"))
SENSE = WORK / "sense-si-main"
for pkg in ("ears", "decisions", "eyes"):
    src = SENSE / "packages" / pkg / "src"
    if src.is_dir():
        sys.path.insert(0, str(src))
sys.path.insert(0, str(SENSE / "tools"))

import phrase_calibration as pc  # noqa: E402


def brier(p, y):
    return sum((a - b) ** 2 for a, b in zip(p, y)) / len(y)


def auc(p, y):
    pos = [a for a, b in zip(p, y) if b == 1]
    neg = [a for a, b in zip(p, y) if b == 0]
    wins = sum(1.0 if a > b else 0.5 if a == b else 0.0 for a in pos for b in neg)
    return wins / (len(pos) * len(neg))


def boot(fn, p, y, n=2000, seed=7):
    rng = random.Random(seed)
    idx = list(range(len(y)))
    vals = sorted(fn([p[i] for i in s], [y[i] for i in s])
                  for s in ([rng.choice(idx) for _ in idx] for _ in range(n)))
    return [round(vals[int(0.025 * n)], 4), round(vals[int(0.975 * n)], 4)]


def within_mix_auc(rows, key):
    """Mean AUC inside each mix (song/mix), skipping mixes with only one class.
    Pooled AUC on this set largely measures which mix a phrase came from
    (ai-jam-sessions PR #88), so both views are reported."""
    groups = {}
    for r in rows:
        groups.setdefault(r["id"].rsplit("/", 1)[0], []).append(r)
    per = {}
    for mix, rs in groups.items():
        y = [r["label"] for r in rs]
        if 0 < sum(y) < len(y):
            per[mix] = round(auc([r[key] for r in rs], y), 4)
    return round(sum(per.values()) / len(per), 4), per


def pearson(a, b):
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    return num / math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))


def main():
    rows = [json.loads(l) for l in (WORK / "openjev.jsonl").read_text(encoding="utf-8").splitlines()]
    y = [r["label"] for r in rows]
    base = sum(y) / len(y)
    report = {"n": len(y), "n_clean": sum(y), "base_rate_brier": round(brier([base] * len(y), y), 4)}
    for name, key in (("jev_hosted", "jev_p_yes"), ("openjev_local", "openjev_p_yes")):
        p = [r[key] for r in rows]
        study = pc.run_study(p, y)
        mix_mean, mix_each = within_mix_auc(rows, key)
        report[name] = {
            "brier_raw": round(brier(p, y), 4), "brier_raw_ci": boot(brier, p, y),
            "auc": round(auc(p, y), 4), "auc_ci": boot(auc, p, y),
            "auc_within_mix_mean": mix_mean, "auc_within_mix": mix_each,
            "mean_p": round(sum(p) / len(p), 4), "distinct_values": len(set(p)),
            "sense_si_study": {k: study[k] for k in study if k.startswith("brier") or k in ("decision",)},
        }
    jp, op = [r["jev_p_yes"] for r in rows], [r["openjev_p_yes"] for r in rows]
    report["agreement"] = {"pearson_p": round(pearson(jp, op), 4),
                           "same_side_of_0.5": round(sum((a >= .5) == (b >= .5) for a, b in zip(jp, op)) / len(y), 4)}
    secs = sorted(r["seconds"] for r in rows)
    report["latency_s"] = {"median": secs[len(secs) // 2], "p90": secs[int(0.9 * len(secs))]}
    (WORK / "compare.json").write_text(json.dumps(report, indent=1, default=str), encoding="utf-8")
    print(json.dumps(report, indent=1, default=str))


if __name__ == "__main__":
    main()
