# Argon's rubric draft: what was taken and changed | 2026-10-15

Argon drafted the relevance-grading template in full, with worked boundary cases and four changes to this benchmark's setup. R&D adapted it into the handbook page `site/src/content/docs/handbook/relevance-grading.md`.

## The template

**Taken as drafted:**
- the scale and its operational definitions;
- the query-form rules and every boundary case;
- blindness and seeded shuffling;
- intent locking;
- `reason` before `grade`;
- the agreement measures and gates;
- the freeze rule and its invalidation clause;
- the drop rule;
- what's published;
- the pitfalls.

**Changed by R&D:**
- **"A fresh stateless API call" becomes "a fresh agent per query".** The studio's model graders run on the Claude Code plan, never on a paid per-token API (a standing rule). The five-chunk cap stays: an agent reads at most five chunks at a time.
- **The auditor reviews the intent table before grading.** Argon's point 2 (on this benchmark) put this into the template itself.
- **The split-construct rule is a general boundary case.** It came from Argon's point 4, after R&D checked this corpus: offrig's code chunk titles are the chunk's first line (`impl Sidecar {`, `[derive(Debug)]`), so they don't always name the enclosing construct.
- **The worked example** (turn-order and aqueduct queries) stays in this file, below. The handbook page is the rules, so it doesn't reproduce it.

## Argon's four changes to this benchmark

| # | Change | Disposition |
|---|---|---|
| 1 | Gate the audit on quadratic weighted κ ≥ 0.75 and binary κ ≥ 0.80, not on raw disagreement. Pools are about 70% zeros, so raw agreement can pass while the relevant chunks disagree. | **Taken.** Raw disagreement stays as a sanity check: ≤ 10%, and two-step ≤ 2%. |
| 2 | Stratify the audit by the share of chunks only one or two arms found, review the intents before grading, and audit 16 queries if feasible. | **Taken.** 16 queries, 8 and 8. The pool measured on the dry run is about 27 per query, not the 15–20 Argon was told, so the audit is about 430 chunks in five pastes. Argon reviews the 100 intent lines in one short paste first. |
| 3 | Grade in micro-batches of at most five, never a whole pool in one prompt. | **Taken,** as five chunks at a time inside a fresh agent per query. |
| 4 | Check that chunk titles name the enclosing construct; if not, the grade-2 rule needs a condition. | **Checked and taken.** Titles are each chunk's first line, so the rule is in the template. |

## Argon's worked example, kept for reference

Two invented queries:
- **code:** "turn order speed tiebreaker". Intent: how the combat engine orders two actors with the same speed.
- **prose:** "Highland aqueduct collapse cause". Intent: what the lore says caused the aqueduct's fall.

The seven boundary cases, graded:
- a chunk with the sort function but not the tie branch: 1;
- the aqueduct's construction, a neighbouring question: 0;
- a lore index entry: 0;
- a compiled copy holding the full tie logic: 2;
- the first half of the collapse account: 1;
- a unit test of the tie rule: 1;
- the tie-breaking implementation: 2;
- an archived draft with superseded lore: 0.
