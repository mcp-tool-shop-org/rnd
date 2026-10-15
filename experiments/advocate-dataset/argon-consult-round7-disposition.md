# Argon consult, round 7: the answer and the disposition | 2026-10-15

Argon read Seat C's fix-up 2 at role-set `444eb99`, with the hand-back, the code and `guards.py` inline. **Verdict: one fast third fix-up on #56 before the grant.**

| # | Finding | Disposition |
|---|---|---|
| G1 | The live pilot never calls `require_model_allowed` or `require_ollama_digest`, and `llama3.1:8b` isn't in `writers.json`. A `-cloud` tag would have run. The rig's Ollama list does carry `gemma4:31b-cloud` and `gemma4:cloud` (the Publisher). | **Taken.** Fix-up 3, step 1. |
| G2 | `render()` dropped the `Note:` label, while the procedure and the critic still say "leave out the Note lines". An unmarked `retries 0` would trip `stray_numbers` if reported. | **Taken.** Step 3. |
| G3 | `PROCEDURES["B"]` hands over the pilot slots' exact strings, so escalation becomes a lookup. The mock writer scrapes them. | **Taken.** Step 4: section 0a's categories, plus a test that no slot string appears verbatim. |
| G4 | The critic's `think` is implicit, and the test covers `qwen3:8b` only. | **Taken.** Step 2. |
| G5, G6 | The writer's and the critic's tables differ in order and vocabulary. | **Taken.** Step 5: one table, in the pack's order and the record's words, with a test that the two texts are identical. |
| A9 | gemma4 told "JSON only" often wraps the JSON in a code fence. `json.loads(raw)` would turn every judgment into "not json". | **Taken, and checked.** Nothing in role-set strips fences, and `ollama_chat` sends no `format`. Step 2 does both: an optional `format: "json"` on the critic's call, and fence stripping. |
| A10 | The procedure tempts `cannot_tell: you'd expect …`, which `check_order` refuses. It also never says that the alternative is another verdict token. | **Taken.** Step 5. |
| Probe | 0.62 equals the majority rate. Kind B has no negatives, so the 6 B texts predict positive trivially and kind A sits at exactly 0.50. | **Taken as a print:** the probe reports kind A's 20 texts beside all 26. No change to the algorithm. |

**Added by R&D, from the Director's rule on bigger turns:** step 6, the read packet (`pilot --report`). It's work that doesn't wait on a gate, it serves the live read, and it fills CI's idle minutes.

**Argon reads first in the next hand-back:**
- the writer and critic prompts for slot 1 and slot 16;
- the test results for G1, G3, G4 and A9.
