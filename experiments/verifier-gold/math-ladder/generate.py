"""The math ladder: generated verifier claims about small functions, with a difficulty dial and exact answers.

Each item is evidence plus a claim, in offrig's gold format: the evidence is a short generated Python function,
the claim is "`f(x)` returns y". Supported claims carry the true result, computed by running the function.
Unsupported claims carry a near-miss. The hardest near-misses are the result of a common misreading,
computed by running a "naive" twin of the function:
- `//` read as truncation toward zero;
- `%` read as C's remainder;
- `round` read as half-up (Python rounds half to even);
- a loop bound read one past its end;
- a precedence expression read left to right.

Knobs (level 0 = base):
  steps       1 → 2 → 4 → 8 operations on the running value
  precedence  0 one op per line, parenthesised · 1 two ops per line, parenthesised · 2 two ops per line, bare
              (precedence decides) · 3 three ops per line, bare, with subtraction and floor division
  traps       0 + - * only · 1 adds // · 2 adds % with negative operands · 3 adds round() at a .5
  control     0 none · 1 an if/else on the input · 2 a for loop · 3 a for loop with an early break
  units       0 none · 1 minutes → seconds · 2 bytes → MiB by 1024² · 3 GB (10⁹) → GiB (2³⁰) with //
  nearmiss    0 far off (about 2x) · 1 about 10-20% off · 2 off by one · 3 the naive twin's answer

Designs:
  ladder  combined levels 1..8, every knob rising together
  sweep   one knob at levels 1..3, every other knob at 0 (precedence holds steps=6; nearmiss holds
          steps=2, traps=2, control=2)

n per cell: 30 claims, 15 supported and 15 unsupported, so each cell's accuracy has a usable interval (the
Publisher's rule). All items are split "tune"; the ladder is descriptive and never the default rule's gold.

  python generate.py --out ladder.jsonl   (seed 20261009; re-running gives the same file)
"""

import argparse
import hashlib
import json
import math
import random
from pathlib import Path

SEED = 20261009
N_PER_CELL = 30
KNOBS = ("steps", "precedence", "traps", "control", "units", "nearmiss")
STEPS = (1, 2, 4, 8)


def ladder_knobs(level: int) -> dict:
    """Combined ladder: level 1 is all-base, level 8 is every knob at its top."""
    up = min(3, (level - 1) // 2)
    return {"steps": STEPS[min(3, (level - 1) // 2)], "precedence": up, "traps": up, "control": up,
            "units": min(3, max(0, level - 4)), "nearmiss": up}


def sweep_knobs(knob: str, lvl: int) -> dict:
    """One knob raised, the rest held. Two sweeps hold a different base, because their knob needs something to
    act on: precedence needs several operations per line (steps=6), and the hardest near-miss (the naive
    twin's answer) needs traps and a loop in the code (traps=2, control=2, steps=2), held at every level of
    that sweep so only the near-miss distance varies."""
    k = {"steps": 1, "precedence": 0, "traps": 0, "control": 0, "units": 0, "nearmiss": 0}
    if knob == "precedence":
        k["steps"] = 6
    if knob == "nearmiss":
        k |= {"steps": 2, "traps": 2, "control": 2}
    k[knob] = STEPS[lvl] if knob == "steps" else lvl
    return k


# ---------------------------------------------------------------- building one function

def ops_for(traps: int) -> list[str]:
    return ["+", "-", "*"] + (["//"] if traps >= 1 else []) + (["%"] if traps >= 2 else [])


def const_for(op: str, rng: random.Random, traps: int) -> int:
    if op in ("//", "%"):
        c = rng.randint(3, 9)
        return -c if traps >= 2 and rng.random() < 0.5 else c
    if op == "*":
        return rng.randint(2, 7)
    return rng.randint(2, 40)


def build(k: dict, rng: random.Random) -> tuple[str, str, int]:
    """Return (source, naive_source, x). Both define f(x). The naive source reads every trap the common
    wrong way, and is used only to compute the hardest near-miss."""
    ops = ops_for(k["traps"])
    real, naive = ["def f(x):"], ["def f(x):"]

    def emit(line_real: str, line_naive: str | None = None, indent: int = 1):
        real.append("    " * indent + line_real)
        naive.append("    " * indent + (line_naive if line_naive is not None else line_real))

    def term(op: str, c: int):
        """One operation on v, real and naive forms."""
        if op == "//":
            return f"v // {c}", f"_tdiv(v, {c})"
        if op == "%":
            return f"v % {c}", f"_crem(v, {c})"
        return f"v {op} {c}", f"v {op} {c}"

    x = rng.randint(3, 40)
    emit("v = x")
    ind = 1
    if k["control"] >= 2:
        n = rng.randint(3, 6)
        limit = rng.randint(20, 400) if k["control"] == 3 else None
        emit(f"for i in range({n}):", f"for i in range({n} + 1):")  # naive: one past the end
        ind = 2
    per_line = {0: 1, 1: 2, 2: 2, 3: 3}[k["precedence"]]
    steps = k["steps"]
    done = 0
    while done < steps:
        take = min(per_line, steps - done)
        weights = [3 if op in "+-*" else 1 for op in ops]  # keep // and % from collapsing values to 0
        parts = [(rng.choices(ops, weights)[0], None) for _ in range(take)]
        parts = [(op, const_for(op, rng, k["traps"])) for op, _ in parts]
        if take == 1 or k["precedence"] <= 1:
            # one op per statement, or parenthesised: unambiguous, applied in order
            for op, c in parts:
                r, nv = term(op, c)
                emit(f"v = {r}", f"v = {nv}", ind)
        else:
            # bare: v op1 c1 op2 c2 [op3 c3], precedence decides; the naive twin reads it left to right
            expr = "v" + "".join(f" {op} {c}" for op, c in parts)
            # left-to-right reading: ((v op1 c1) op2 c2) op3 c3
            ltr = "v"
            for op, c in parts:
                ltr = f"({ltr} {op} {c})"
            emit(f"v = {expr}", f"v = {ltr}", ind)
        done += take
    if k["control"] == 3:
        emit(f"if v > {limit}:", None, ind)
        emit("break", None, ind + 1)
    if k["control"] == 1:
        c = rng.randint(2, 9)
        emit("if x % 2 == 0:")
        emit(f"v = v + {c}", None, 2)
        emit("else:")
        emit(f"v = v - {c}", None, 2)
    if k["traps"] >= 3:
        emit("v = round(v / 2)", "v = _round_half_up(v / 2)")
    u = k["units"]
    if u == 1:
        emit("v = v * 60  # minutes to seconds")
    elif u == 2:
        emit("v = (v * 1_000_000) // (1024 * 1024)  # bytes to MiB")
    elif u == 3:
        emit("v = (v * 10**9) // 2**30  # GB to GiB", "v = (v * 10**9) // 10**9  # GB to GiB")
    emit("return v")
    return "\n".join(real), "\n".join(naive), x


HELPERS = {
    "_tdiv": lambda a, b: int(a / b),  # truncation toward zero, the common misreading of //
    "_crem": lambda a, b: int(math.fmod(a, b)),  # C remainder, the common misreading of %
    "_round_half_up": lambda v: math.floor(v + 0.5),  # half-up, the common misreading of round
}


def run(src: str, x: int, naive: bool = False) -> int:
    env = {"__builtins__": {"range": range, "round": round, "int": int}} | (HELPERS if naive else {})
    exec(src, env)  # our own generated source, not external input
    v = env["f"](x)
    if not isinstance(v, int) or isinstance(v, bool):
        raise ValueError("non-int result")
    return v


def near_miss(level: int, true: int, naive: int, rng: random.Random) -> tuple[int, str]:
    if level == 3 and naive != true:
        return naive, "the naive twin's answer (a common misreading)"
    if level >= 2:
        return true + rng.choice((-1, 1)), "off by one"
    if level == 1:
        d = max(2, round(abs(true) * rng.uniform(0.1, 0.2)))
        return true + rng.choice((-1, 1)) * d, "10-20% off"
    return true * 2 + rng.randint(5, 40) if true >= 0 else true * 2 - rng.randint(5, 40), "far off"


def cells() -> list[tuple[str, str, dict]]:
    out = [("ladder", f"L{lv}", ladder_knobs(lv)) for lv in range(1, 9)]
    for knob in KNOBS:
        for lvl in (1, 2, 3):
            out.append(("sweep", f"{knob}={lvl}", sweep_knobs(knob, lvl)))
    return out


def generate(seed: int = SEED, cell_list=None, n_per_cell: int = N_PER_CELL) -> tuple[list[dict], int]:
    """All rows for `seed` (and the count of naive-twin fallbacks). Pure: same seed, same rows. The property
    tests call this with other seeds and cells; main() calls it with the pre-registered SEED."""
    rows, fallback = [], 0
    for design, cell, k in (cell_list if cell_list is not None else cells()):
        rng = random.Random(f"{seed}:{design}:{cell}")
        made = 0
        while made < n_per_cell:
            src, naive_src, x = build(k, rng)
            try:
                true = run(src, x)
                naive = run(naive_src, x, naive=True)
            except (ZeroDivisionError, ValueError):
                continue
            if abs(true) > 10**12:
                continue
            supported = made % 2 == 0
            if supported:
                value, why = true, "the true result"
            else:
                value, why = near_miss(k["nearmiss"], true, naive, rng)
                if k["nearmiss"] == 3 and naive == true:
                    fallback += 1
                if value == true:
                    continue
            rid = f"ml-{design}-{cell.replace('=', '')}-{made:02d}"
            rows.append({
                "id": rid, "check_type": "grounded",
                "claim": f"`f({x})` returns {value}.",
                "context": [{"source": f"generated:math-ladder-v1/{rid}", "text": src}],
                "label": "supported" if supported else "unsupported", "subtle": not supported,
                "split": "tune", "origin": "math-ladder-v1",
                "notes": f"{design} {cell} | " + " ".join(f"{n}={k[n]}" for n in KNOBS) + f" | claim: {why}",
                "ladder": {"design": design, "cell": cell, **k, "true": true},
            })
            made += 1
    return rows, fallback


def to_text(rows: list[dict]) -> str:
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    rows, fallback = generate()
    text = to_text(rows)
    a.out.write_text(text, encoding="utf-8", newline="\n")
    print(f"{len(rows)} claims in {len(cells())} cells; sha256 {hashlib.sha256(text.encode()).hexdigest()[:16]}; "
          f"nearmiss=3 fell back to off-by-one {fallback} times (naive twin agreed with the truth)")


if __name__ == "__main__":
    main()
