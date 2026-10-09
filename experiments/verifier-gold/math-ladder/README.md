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

## Results, 2026-10-09 (v1, six models, offrig quote rule 1)

Run in the Publisher's ladder grant, 07:03–13:51, smallest model first, 15-minute rests, each model at its
calibration setting, store `E:/AI/rnd-ladder` only. Receipts: `results/2026-10-09-ladder/` (each run's manifest,
metrics and verdicts, the step logs, and both report views). Gold checked by execution where a cell looked odd
(L6: every expected answer re-computed by running its code; all correct).

**Two views, and why.** The pre-registered table scores offrig's *final* verdict. On this ladder that table mostly
measures offrig's quote check, not arithmetic: the generated code lines are short (`v = v * 3` is 9 characters),
under quote rule 1's 12-character floor, so a correct verdict with a correct quote became cannot_tell (llama: 513 of
780). `report.py --model-verdict` (added post-hoc, labelled) scores the model's own verdict before the quote check;
that's the falloff the ladder exists to find. Both are in the receipts. Quote rule 2 (offrig#47, whole-line short
quotes) fixes this for later runs.

**Combined ladder, model verdict: accuracy (false accepts of 15)**

| model (think) | L1 | L2 | L3 | L4 | L5 | L6 | L7 | L8 | falloff |
|---|---|---|---|---|---|---|---|---|---|
| llama3.1:8b (off) | 1.00 (0) | 1.00 (0) | 0.73 (5) | 0.69 (4) | 0.50 (15) | 0.47 (15) | 0.50 (15) | 0.52 (13) | L3 |
| qwen3:8b (on) | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.70 (6) | 0.96 | 0.97 (1) | L6 |
| qwen3:14b (on) | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.79 (6) | 0.93 (1) | 0.93 | L6 |
| mistral-small:24b (off) | 1.00 | 1.00 | 1.00 | 0.90 (2) | 0.47 (6) | 0.37 (8) | 0.13 (0) | 0.17 (1) | L4 |
| granite4.1:30b (off) | 1.00 | 1.00 | 1.00 | 0.97 (1) | 0.80 (0) | 0.60 (2) | 0.57 (3) | 0.60 (1) | L6 |
| gemma4:31b (on) | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.80 (6) | 1.00 (0 of 10)* | 1.00 (0 of 5)* | L6 |

\* gemma's L7/L8 rows score only the claims it finished: 5 and 10 replies were truncated at offrig's 4096-token cap.

(Levels come in pairs by design: L1=L2, L3=L4, L7=L8 share knob settings; L5→L6 raises units 1→2.)

**What it shows:**
- **Three ways to fail.** llama accepts: from L5 it calls every false claim true. mistral abstains: at L7–L8 it
  says cannot_tell on 24 of 30. granite rejects: its L5–L8 errors are mostly true claims called false (0–3 false
  accepts per level). Same accuracy, different risk; for a verifier, llama's is the dangerous one.
- **Thinking flattens the curve.** Both qwens are perfect through L5 and on every single-knob sweep (≥0.97).
  gemma4:31b scores 1.00 on all 18 sweep cells and never abstains; its only false accepts are L6's six.
- **L6 is a precision cliff, not a bad item.** It's the one cell where bytes→MiB (×1024²) makes 7–10 digit answers
  and the false claims are off by exactly one. Both qwens accept 768937860 for 768937861. L7–L8 recover; there
  GiB `//` shrinks the numbers and the near-miss is the naive twin's answer instead of an off-by-one (a likely
  reason, not tested).
- **An "arithmetic floor" (post-hoc, measured and rejected):** comparing the claim's number with the last number
  in the verdict's `reasoning` catches 0 of the qwens' 16 false accepts (the summary restates the claimed number)
  and would flip 3–14 correct accepts. The thinking trace isn't recorded under offrig ≤ #47; offrig#48
  `--keep-thinking` makes "was the right number in the trace?" measurable on a future run. Executing the code is
  the sure check, a sandbox design, noted as an option only. Script: `arith_floor_posthoc.py`.

**Incomplete and capped runs:**
- **mistral-small:24b: INCOMPLETE, 1 claim stuck** (`ml-sweep-nearmiss1-05`; the Publisher's ruling, matching the
  chain's). Ollama aborted the generation mid-reply (server log: `500` at ~1,450 generated tokens, no CUDA error);
  offrig read it as a network failure because the body read failed, so offrig#46's 5xx rule didn't apply.
  offrig#49 extends that rule to dropped replies. Its tables are descriptive on the 778 scored claims.
- **gemma4:31b ran at offrig calibrate's `num_predict` 4096:** its L7/L8 cells are capped by budget, not ability.
  15 replies were truncated (L7 5, L8 10), each counted as missing. Its thinking time rose with difficulty: about
  5 s per claim at L1–L4, 17 s at L5, 25 s at L6, and 45 s at L7/L8. That's evidence for the larger budget in the
  calibration rerun's pre-registration.
- **The arithmetic floor across all six** (`results/2026-10-09-ladder/arith-floor-posthoc.txt`): it catches false
  accepts only for llama (36 of 162) and mistral (11 of 79), never for the thinking models, whose summaries restate the
  claimed number.

## Not in v1

- cannot_tell items (a call to a function whose body isn't shown);
- other languages' semantics (Rust's wrapping arithmetic, JS's number type);
- claims about offrig's real budget code.

These are candidates for v2, generated the same way.
