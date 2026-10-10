"""Phase A power from the measured sealed baseline (R&D, 2026-10-10).

`power.py` assumed a 55% baseline. The sealed baseline came in far lower on the pinned score, so this re-runs
the same simulation with each task's baseline accuracy taken from its measured k-of-3 correct. Each task is
smoothed to (k + 0.5) / 4 so no task sits at exactly 0 or 1. Training is again a constant logit shift sized
to the requested mean gain. The test is the same task-level paired bootstrap: 3 samples per side, 1,000
resamples, alpha 0.05.

The input is only the per-task k-of-3 counts: 130 integers, no task text.

    python power_empirical.py results/2026-10-10-sealed-baseline-k.json > results/2026-10-10-power-empirical.txt
"""
import json
import sys

import numpy as np

rng = np.random.default_rng(0)


def expit(x):
    return 1 / (1 + np.exp(-x))


def run(k, gain, nsim=600, nboot=1000, S=3):
    p0 = (np.array(k) + 0.5) / 4
    lo, hi = 0.0, 8.0
    for _ in range(50):
        mid = (lo + hi) / 2
        if expit(np.log(p0 / (1 - p0)) + mid).mean() - p0.mean() < gain:
            lo = mid
        else:
            hi = mid
    p1 = expit(np.log(p0 / (1 - p0)) + mid)
    T = len(p0)
    hits = 0
    for _ in range(nsim):
        d = rng.binomial(S, p1) / S - rng.binomial(S, p0) / S
        boot = d[rng.integers(0, T, (nboot, T))].mean(1)
        hits += np.quantile(boot, 0.025) > 0
    return hits / nsim


def main(path):
    data = json.load(open(path, encoding="utf-8"))
    print("score\tbaseline_mean\tgain\tbootstrap_power")
    for score, k in data.items():
        for g in (0.03, 0.05, 0.08, 0.10):
            print(f"{score}\t{np.mean(k) / 3:.3f}\t{g:.2f}\t{run(k, g):.2f}", flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
