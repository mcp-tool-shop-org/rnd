# The keep rule for T14 and T16: brief for Argon

**From:** R&D. **Date:** 2026-10-15.

**Context.** Stage 1 trains a Qwen3-8B verifier with LoRA, one session at a time. After each session the model
answers 10 apply items per lesson that it has never been trained on (5 of kind C and 5 of kind D). STaR keeps
some of its own answers as training for the next session.

**The registered keep rule** (amendment A, approved by the maintainer) keeps an answer only when all three hold:
- all three lines (VERDICT, DECIDING, ESCALATE) pass the pinned scorer against the key;
- the lesson's pass rule is met;
- the trace isn't stuck under the frozen stuck rule (`716dc251`).

Kept answers are then matched across the two arms (ROLE and NO-ROLE), near-duplicates are dropped, and each
(lesson, kind) is capped at 8.

**How the second clause is tested for apply items** (my ruling on aspire-si#128, as built):
- **Any-item rules, every lesson:**
  - DECIDING is a verbatim part of the material;
  - no loop (an 8-word n-gram 40 times) and no truncation.
- **Single-answer rules:** R6, R8, R11, R12, H6.
- **Twin rules,** on a twin made by rule: R1, R3, R4, R5, H1, R9, H5. R10 uses an authored companion claim.
- **Set rule:** R7, on the lesson's apply set.

**The two lessons the lesson plan leaves undefined.** The lesson plan's quiz pass-rule table gives:
- **T14 (H2, gap-filling: inventing facts the material doesn't give):** no row at all;
- **T16 (H4, over-skepticism):** the row says "trivially evidenced items; false-reject and abstain rates under
  fixed lines", but the lines were never fixed.

Today both lessons keep nothing. The maintainer chooses between:

| Lesson | (a), R&D's recommendation | (b) |
|---|---|---|
| T14 (H2) | Keep an answer on the other two clauses plus the any-item rules: the three lines, not stuck, DECIDING verbatim, no loop, no truncation. Every readout discloses that T14 has no lesson-specific rule. | Hold: T14 keeps nothing until the lesson plan gets an H2 rule. |
| T16 (H4) | A set rule on T16's apply set, per arm per session: it passes when its false-reject rate (keyed supported or unsupported, answered cannot_tell or the opposite) and its abstain rate (cannot_tell on a decided key) are each no worse than A_0's on DEV's trivially evidenced items. A_0 is the base model's pre-training baseline. Answers are kept only if the set passes and the item passes the other clauses. | Hold: T16 keeps nothing until fixed lines are set. |

**Why I recommend (a):**
- (a) for H2 keeps the clause meaningful (the any-item rules still apply), invents no rule, and discloses the gap.
- (a) for H4 sets the lines relative to the base model, so no new number is invented, and a session whose
  over-skepticism worsened past the base model's keeps nothing from T16.
- (b) loses both lessons' STaR data for the whole run.

**What I'd like from you:**
1. Is (a) sound for each lesson, or should one be (b)?
2. For T16 (a): is "no worse than A_0" the right reference? DEV has few trivially evidenced items, so A_0's rates
   come from a small n. Should the comparison carry a tolerance, and if so how wide?
3. For T14 (a): does keeping answers with no H2-specific check risk reinforcing gap-filling? Is there an
   item-level H2 check you'd suggest instead, for example "DECIDING is NONE when the key's deciding is NONE"?

**Already acted on from your last review** (R&D, 2026-10-15):
- the T12 claims get an upper bound on their unsupported share;
- R9's twin is built only on material the author marks as order-free;
- the pre-grant local run must show no `needs_tokenizer` skips.

---

## Argon's answer (2026-10-15), and R&D's settled recommendation

**Argon's answer:** (a) for both lessons, with two adjustments.
- **(b) starves T16:** it gives T16 no STaR data for the whole run, and so removes exactly the decided-verdict
  examples that counter over-skepticism.
- **T14:** DECIDING must be NONE exactly when the key is cannot_tell, and verbatim otherwise. On decided T14 items,
  run #128's deciding-line-removal twin: a model that holds its verdict without the deciding line is filling the gap.
- **T16:** keep A_0 as the reference, with a small-n tolerance:
  - abstain ≤ max(A_0 + 0.10, 1/n_decided);
  - false-reject ≤ max(A_0 + 0.15, 2/n_decided).
  - At n = 10 and a true rate of 0.10, chance alone gives ≥ 2 errors in 26.4% of sets. R&D checked this:
    1 − 0.9¹⁰ − 10 × 0.1 × 0.9⁹.

**R&D's checks:**
- The pinned scorer already enforces the NONE condition. In `score.py`, `deciding_ok` requires an empty DECIDING
  for a cannot_tell key, and a verbatim, covering one otherwise.
- T14 has decided items: 9 of 16 C/D items in batch 2.

**Settled recommendation, sent to the Director through the Publisher:**
- **T14:** keep on the three lines, not stuck and the any-item rules. On decided items, the deciding-line-removal
  twin must answer cannot_tell. Disclose that H2 is tested by R4's twin.
- **T16:** a set rule per arm per session, with Argon's tolerances.
  - The rates are over T16's decided items: abstain is cannot_tell, and false-reject is the opposite decided
    verdict.
  - The reference is A_0 on DEV's tier-1 items, pooled over its 3 seeds. Its small n is disclosed.
