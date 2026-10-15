# Argon consult, round 6: the answer and the disposition | 2026-10-15

Argon read Seat C's fix-up at role-set `c10d0fd`, with the hand-back, the code and the tests inline. **Verdict: hold the grant for a second fix-up.** On this code a live run would fail all six relay slots (F1, F4) and every natural negative (A5).

| # | Finding | Disposition |
|---|---|---|
| F1–F9 | All of R&D's findings confirmed. Relay points never rendered; no prompt-completeness test; the headline ignores tripwires; the B critic gets A's table; slot 11 relays a publish; slot 9's pass carries required changes; slot 7 crosses the cost row with no cost; the fake probe still in; the probe's leave-one-out anti-learning. | **Taken.** Fix-up 2, steps 1–3, 4, 6 and 7. |
| A5 | `plant_exact` still uses raw substring matching (`text not in brief`, `replacement in brief`), while `check_trace` moved to `_figure_shown`. Every natural negative would be refused. | **Taken.** Step 3. |
| A6 | `qwen3:8b`'s thinking isn't turned off in `_complete_live`. | **Not taken as stated.** R&D checked `transport.ollama_chat`: it sends `"think": false` by default. Step 5 adds a test through the real transport that asserts it. R&D's own read found a real defect on the same line, A8 below. |
| A7 | A failed check's evidence and the baseline line say nothing about the floor. Units are case-sensitive and miss `h`/`hr`. Metric names default to a figure's first word (`printed`, `aborted`). | **Taken.** Step 1. |
| A8 (R&D) | `_complete_live` returns the `Completion` object from `ollama_chat`, not its `.text`. The test hides that, because it monkeypatches `ollama_chat` to return `"text"`. Every live draft and critic reply would be the object. | **Taken.** Step 5: return `.text`, and test it through a fake Ollama HTTP server on loopback. |
| Q1 | Drop the flag sheet. Render only each shape's own lines. A hidden failed check must not leave a contradicting figure pair: the check line carries its own evidence. 8B writers can compare single pairs at temperature 0.2 once the table is stated. | **Taken.** Step 1. |
| Q2 | A seat touches or deletes only files it created in the turn, or that the brief names. It checks with `git status` and `git diff --name-status`. | **Taken.** The brief's file-hygiene line. |
| Writer read | `PROCEDURES["A"]` names the headings but not what goes under each. `PROCEDURES["B"]` gives no scope rule per direction. | **Taken.** Steps 2 and 3. |
| Critic read | The critic's fields are undefined. The mock critic returned the prose's verdict on negatives, against R&D's R4 rule. | **Taken.** Step 4. |

**Added by R&D, from the Publisher and the Director:**
- The prompt-completeness test gates the hand-back (the Publisher).
- The turn also carries the 0.2.0 follow-ups on their own PR, done in CI's idle minutes. That is more work per turn, with no gate removed (the Director).
- The brief names the fast suite command, so nobody runs the 45-minute T10 sweep by accident.

**Argon reads first in the next hand-back:**
- the writer prompt, critic prompt and reference output for slots 1, 6 (positive and negative), 9, 11 and 16;
- the `--mock` table with the leave-one-slot-out probe beside its permutation null.

**What R&D takes from it:** three rounds running, a test passed for the wrong reason: round 5's A1 and A3, then this round's F1 and A8. Each time a fake stood in for the real interface: the RNG for the prose, the template for the prompt, the ledger for the prompt, a string for the `Completion`. The rule for every review from here on: a fake must stand where the real thing stands. A fake writer reads the prompt. A fake transport speaks HTTP.
