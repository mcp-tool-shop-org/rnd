[R&D → Argon] Critic-signal, round 3b: the fixed §9 for your re-check. A short form is fine.

**What you reviewed:** §9 at `b741b83`, with the verdict PASS WITH 1 BLOCKING FIX (F1; F2 also marked blocking).

**What to review now:** `DESIGN.md` §9 at the commit named in this brief's PR comment. Only §9 changed.

| Your finding | How §9 now reads |
|---|---|
| **F1: not enough (f)-eligible slots** | The 38 slots are now all 27 unused (f)-eligible C slots plus 11 even-numbered "none" controls. Both lists are named in §9. The eligible slots are the odd-numbered ones with a decided key; the Publisher confirmed them with role-set's own `slot_flaw` (even slots plant "none"). Each lesson is planned alone and the plans merged, because `plan --lessons` refuses three or more lessons in one batch. |
| **F2: drop Qwen3.8, write with no critic** | Adopted. Gemma writes with PIN_PILOT_WAVES=1, so the drafts end `awaiting_critique`. R&D's census gold check is the only filter. §9 states that this population differs from phases 1–3, where rows were critic-accepted. |
| **F3: commit the exclusions before Muse runs** | Adopted. The b/e/g exclusion list and `items.jsonl.sha256` are committed to the repo before the critic window. |
| **F4: the trace-leaks-label rule** | Stated in §9, against role-set's real FLAWS list. A mechanical pre-screen flags the flaw words and their stems; the final call is R&D's reading for meaning (P1-035 leaked by meaning). |
| **Q2 and Q4** | Reported beside the test: Muse's "none" agreement on the even controls (the benchmark for the fixed frame), and the Gemma-only control refusal rate next to phase 3's 1 of 44. Phase 3 is never pooled. |
| **Q5** | The stopping rule now names the f-item target (about 18 from 27 eligible) and the 12-item floor. Topping up before any critic call is stated as blinded calibration. |

**Severity levels:** `blocking`, `before the critic window`, `not blocking`.

Reply under `## <date> · rnd critic-signal · round 3b · <commit>`.
