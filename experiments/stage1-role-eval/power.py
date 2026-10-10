"""Phase A power for the Stage 1 role evaluation (R&D, 2026-10-10).

Simulates the paired before/after comparison on the sealed task set. The setup:
- Each task has a latent baseline accuracy, drawn from Beta with mean `base` and concentration `kappa`. A low
  kappa means tasks are more often all-right or all-wrong.
- Training adds a constant logit shift, sized to give the requested mean gain.
- Each side gets 3 samples per task, at the Qwen3 card sampling settings. The real after side pools 9, so this
  is conservative.

Two tests, each at alpha = 0.05:
- the primary: a task-level paired bootstrap of the per-task mean difference, with a 95% percentile interval
  whose lower end must be above 0;
- the check: exact McNemar on the per-task majority vote.

    python power.py [--nsim 600] > results/2026-10-10-power.txt
"""
import sys
from math import comb

import numpy as np

rng = np.random.default_rng(0)


def logit(p):
    return np.log(p / (1 - p))


def expit(x):
    return 1 / (1 + np.exp(-x))


def mcnemar_p(b, c):
    n = b + c
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)


def sim(T, base, gain, kappa, S=3, nsim=600, nboot=1000):
    hit_boot = hit_mcn = 0
    for _ in range(nsim):
        p0 = rng.beta(base * kappa, (1 - base) * kappa, T).clip(1e-3, 1 - 1e-3)
        lo, hi = 0.0, 6.0
        for _ in range(40):
            mid = (lo + hi) / 2
            if expit(logit(p0) + mid).mean() - p0.mean() < gain:
                lo = mid
            else:
                hi = mid
        p1 = expit(logit(p0) + mid)
        x0, x1 = rng.binomial(S, p0) / S, rng.binomial(S, p1) / S
        d = x1 - x0
        boot = d[rng.integers(0, T, (nboot, T))].mean(1)
        hit_boot += np.quantile(boot, 0.025) > 0
        m0, m1 = x0 > 0.5, x1 > 0.5
        b, c = int((m0 & ~m1).sum()), int((~m0 & m1).sum())
        hit_mcn += mcnemar_p(b, c) < 0.05 and c > b
    return hit_boot / nsim, hit_mcn / nsim


def main(argv):
    nsim = int(argv[argv.index("--nsim") + 1]) if "--nsim" in argv else 600
    print("T\tbase\tkappa\tgain\tbootstrap_power\tmajority_mcnemar_power")
    for T, base, gains in ((120, 0.55, (0.05, 0.08, 0.10, 0.15)), (130, 0.55, (0.05, 0.08, 0.10, 0.15)),
                           (130, 0.83, (0.03, 0.05, 0.08))):
        for kappa in (1.0, 2.0, 5.0):
            for g in gains:
                pb, pm = sim(T, base, g, kappa, nsim=nsim)
                print(f"{T}\t{base}\t{kappa}\t{g:.2f}\t{pb:.2f}\t{pm:.2f}", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
