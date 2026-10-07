"""Score every decision model run on the 124 phrases side by side.

    <sense-si venv python> compare_all.py openjev kev4b kev9b kev4b-knowledge kev9b-knowledge

Each name reads $OPENJEV_WORK/<name>.jsonl (field <name>_p_yes); hosted Jev's
p_yes comes from the same rows. For every model it reports:
  - raw Brier and pooled AUC with bootstrap 95% intervals, and the within-mix AUC mean;
  - sense-si's own study (run_study: inner/outer split, temperature fit), as in compare.py;
  - leave-one-mix-out (LOMO) calibration: a temperature is fitted on six mixes and
    applied to the seventh, so no mix calibrates itself. Two baselines match it:
    the LOMO base rate (the clean rate of the other six mixes) and a constant 0.5.
    A very large fitted temperature flattens a model towards 0.5, so a LOMO Brier
    near 0.25 means "no usable signal", not "beats the base rate".
Writes $OPENJEV_WORK/compare-all.json.
"""

import json
import math
import os
import sys
from pathlib import Path

from compare import auc, boot, brier, pc, pearson, within_mix_auc  # noqa: F401  (pc: sense-si study code)

WORK = Path(os.environ.get("OPENJEV_WORK", "E:/AI-Models/openjev/work"))
EPS = 1e-6


def mix_of(pid):
    return pid.rsplit("/", 1)[0]


def logit(p):
    p = min(max(p, EPS), 1 - EPS)
    return math.log(p / (1 - p))


def sig(x):
    return 1 / (1 + math.exp(-x))


def fit_temperature(p, y):
    """Scalar T minimising log loss of sigmoid(logit(p) / T); grid search, stdlib only."""
    best = (float("inf"), 1.0)
    for i in range(-60, 61):
        t = 10 ** (i / 30)  # 0.01 .. 100
        ll = -sum(math.log(max(EPS, sig(logit(a) / t) if b else 1 - sig(logit(a) / t))) for a, b in zip(p, y))
        best = min(best, (ll, t))
    return best[1]


def lomo(rows, key):
    mixes = sorted({mix_of(r["id"]) for r in rows})
    cal, base, temps = {}, {}, {}
    for m in mixes:
        train = [r for r in rows if mix_of(r["id"]) != m]
        t = fit_temperature([r[key] for r in train], [r["label"] for r in train])
        rate = sum(r["label"] for r in train) / len(train)
        temps[m] = round(t, 3)
        for r in rows:
            if mix_of(r["id"]) == m:
                cal[r["id"]] = sig(logit(r[key]) / t)
                base[r["id"]] = rate
    y = [r["label"] for r in rows]
    pc_ = [cal[r["id"]] for r in rows]
    return {"brier_lomo_temperature": round(brier(pc_, y), 4),
            "brier_lomo_temperature_ci": boot(brier, pc_, y),
            "brier_lomo_base_rate": round(brier([base[r["id"]] for r in rows], y), 4),
            "temperature_by_held_out_mix": temps}


def main():
    names = sys.argv[1:] or ["openjev"]
    req = {json.loads(l)["id"]: json.loads(l) for l in (WORK / "requests.jsonl").read_text(encoding="utf-8").splitlines()}
    rows = [{"id": i, "label": r["label"], "jev_p_yes": r["jev_p_yes"]} for i, r in req.items()]
    by_id = {r["id"]: r for r in rows}
    latency = {}
    for n in names:
        for line in (WORK / f"{n}.jsonl").read_text(encoding="utf-8").splitlines():
            rec = json.loads(line)
            by_id[rec["id"]][n] = rec[f"{n}_p_yes"]
            latency.setdefault(n, []).append(rec["seconds"])
    y = [r["label"] for r in rows]
    base = sum(y) / len(y)
    report = {"n": len(y), "n_clean": sum(y), "base_rate_brier": round(brier([base] * len(y), y), 4),
              "constant_half_brier": round(brier([0.5] * len(y), y), 4), "models": {}}
    jp = [r["jev_p_yes"] for r in rows]
    for n, key in [("jev_hosted", "jev_p_yes")] + [(n, n) for n in names]:
        p = [r[key] for r in rows]
        study = pc.run_study(p, y)
        mix_mean, mix_each = within_mix_auc(rows, key)
        m = {"brier_raw": round(brier(p, y), 4), "brier_raw_ci": boot(brier, p, y),
             "auc": round(auc(p, y), 4), "auc_ci": boot(auc, p, y),
             "auc_within_mix_mean": mix_mean, "auc_within_mix": mix_each,
             "mean_p": round(sum(p) / len(p), 4), "distinct_values": len(set(p)),
             "sense_si_brier_temperature": round(study["brier_temperature"], 4),
             "sense_si_decision_adopted": study["decision"]["adopted"],
             **lomo(rows, key)}
        if key != "jev_p_yes":
            m["pearson_vs_jev"] = round(pearson(jp, p), 4)
            s = sorted(latency[n])
            m["latency_s"] = {"median": s[len(s) // 2], "p90": s[int(0.9 * len(s))]}
        report["models"][n] = m
    (WORK / "compare-all.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    hdr = f"{'model':<18}{'Brier raw':>10}{'sense-si T':>11}{'LOMO T':>8}{'LOMO base':>10}{'AUC':>7}{'AUC in-mix':>11}"
    print(f"n={report['n']} clean={report['n_clean']} base-rate Brier={report['base_rate_brier']} "
          f"(in-sample; a constant 0.5 scores {report['constant_half_brier']})")
    print(hdr)
    for n, m in report["models"].items():
        print(f"{n:<18}{m['brier_raw']:>10}{m['sense_si_brier_temperature']:>11}{m['brier_lomo_temperature']:>8}"
              f"{m['brier_lomo_base_rate']:>10}{m['auc']:>7}{m['auc_within_mix_mean']:>11}")


if __name__ == "__main__":
    main()
