"""The null and shifted-run behaviour of the frozen H2 gates (analyze.equivalence), by simulation. No real data.

    python simulate.py

Each run draws n triples: a per-round base, then A1, B and A2 each with independent per-call noise (normal, sd
`sigma`), with B shifted by `shift`. It reports how often equivalence() returns "holds". This is the evidence for
amendment S1-A4, and it runs on the analysis exactly as frozen.
"""

from __future__ import annotations

import json
import random

import analyze as an


def run(*, n: int, shift: float, sigma: float = 0.02, runs: int = 4000, seed: int = 11, heavy: bool = False) -> float:
    rng = random.Random(seed)

    def noise() -> float:
        if heavy and rng.random() < 0.05:
            return rng.gauss(0, 4 * sigma)  # one call in twenty from a four-times-wider spread
        return rng.gauss(0, sigma)

    holds = 0
    for _ in range(runs):
        deltas, aa = [], []
        for _ in range(n):
            base = 1 + noise()
            a1, a2 = base * (1 + noise()), base * (1 + noise())
            b = base * (1 + shift) * (1 + noise())
            m = (a1 + a2) / 2
            deltas.append((b - m) / m)
            aa.append((a2 - a1) / m)
        holds += an.equivalence(deltas, aa)["verdict"] == "holds"
    return holds / runs


def main() -> None:
    rows = []
    for n in (15, 30):
        for shift in (0.0, 0.01, 0.02, 0.03, 0.05):
            rows.append({"n": n, "shift": shift, "holds": run(n=n, shift=shift)})
    rows.append({"n": 30, "shift": 0.0, "heavy_tail": True, "holds": run(n=30, shift=0.0, heavy=True)})
    print(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
