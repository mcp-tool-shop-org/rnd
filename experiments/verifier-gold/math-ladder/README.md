# The math ladder

Generated verifier claims about small functions, with a difficulty dial and exact answers. The idea is the
Director's (2026-10-09): math can be made harder one step at a time, so each model's falloff shows as a
curve, and the knobs show *what* breaks a model, not just *where*.

Pre-registered 2026-10-09 at about 02:25, before any model sees an item. The calibration chain was running
on other gold at the time.

## The items (`generate.py`, `ladder.jsonl`)

- **Format:** offrig's gold, so `offrig verify calibrate` scores it directly. The evidence is a short
  generated Python function; the claim is "`f(x)` returns y". Check type `grounded`, split `tune`, origin
  `math-ladder-v1`.
- **Truth:** every function is executed to get its true result. An independent re-run of all 780 functions
  confirms every label (0 mislabelled).
- **Near-misses** (the unsupported claims) come at four distances:
  - far off (about 2×);
  - 10–20% off;
  - off by one;
  - **the answer from a common misreading,** computed by running a "naive" twin of the function: `//` read as
    truncation toward zero, `%` read as C's remainder, `round` read as half-up (Python rounds half to even),
    a loop bound read one past its end, and bare arithmetic read left to right instead of by precedence.
- **Knobs** (level 0 = base): steps 1 → 2 → 4 → 8; precedence (one op per line … three ops per line, bare);
  traps (adds `//`, then `%` with negative divisors, then `round` at a .5); control flow (if/else, loop, loop
  with early break); units (minutes → seconds, bytes → MiB, GB → GiB); near-miss distance.
- **Designs:**
  - **ladder** L1..L8, every knob rising together;
  - **sweep**: one knob at levels 1..3, the rest held. The precedence sweep holds steps = 6, so there is
    precedence to get wrong. The near-miss sweep holds steps = 2, traps = 2 and control = 2, so the naive
    twin has traps to misread.
- **Size:** 26 cells × 30 claims (15 supported, 15 unsupported) = **780 claims**.
  - Seed 20261009; a re-run gives the identical file (sha256 `a1062f61554d99ad…`).
  - In the near-miss sweep's top level, 14 of 15 false claims are the naive twin's answer. The other one
    falls back to off by one, because the twin agreed with the truth there.

## How it runs and is read

- **Where:** locally on the 5090, after the overnight calibration chain's "card free" and a 15-minute rest,
  under its own grant from the Publisher. That's the Director's choice; the pod path comes later.
- **What:** all six candidates, smallest first, with the settings their smoke settled
  (`../calibration/candidates.txt`), using `offrig verify calibrate ladder.jsonl --split tune` per model. Rest
  15 minutes between models.
- **Read:** `report.py` gives, per model and cell, accuracy and false accepts with Wilson 95% intervals.
  - **Falloff** is the first cell where accuracy drops below 0.80 or false accepts exceed 0.10. It's read
    along L1..L8 and along each knob's levels 1..3.
  - Every cell has n = 30, the Publisher's minimum for a falloff call.
- **Descriptive only.** It never feeds the default rule: there are no cannot_tell items, and it's one generated
  domain. It shows what each model can and can't compute when checking a claim. A finding such as "fails at
  traps=2 (negative modulo)" is a concrete limit to put in the verifier's documentation.

## Not in v1

- cannot_tell items (a call to a function whose body isn't shown);
- other languages' semantics (Rust's wrapping arithmetic, JS's number type);
- claims about offrig's real budget code.

These are candidates for v2, generated the same way.
