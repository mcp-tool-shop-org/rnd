# Phases 0 and 1: what the critic checked, and a blind gold check of what it accepted (2026-10-19)

Part of the critic-signal design (`DESIGN.md`). Item text stays out of this public repo: the blind and key files
are kept locally, and this folder holds only ids, verdicts and notes (`phase1-results.csv`).

## Phase 0: the critic's per-check record

From every critic call in windows 12f, 12h, 13b and 13l (`drafts.jsonl` in each `pilot-out.tar`, first drafts and
rewrites alike; computed by script):

| Check | Agreed | Of | Note |
|---|---|---|---|
| verdict (C, D, verdict-type E) | 28 | 30 | the critic solves blind, then is compared with the key |
| flaw (C) | 8 | 12 | advisory: `flaw_gate` is off, so a disagreement never refuses |
| trait | 24 | 39 | refuses; 10 of the 15 mismatches were on twin items |
| answer (B) | 4 | 4 | |

## Phase 1: the pool

Every accepted row of the six arms that go on (Qwen3.8, Gemma 4, Granite 4.2, Bolt, Muse, Lightning), from each
arm's final wave in W-A (window 13l) and W-B (window 13b): **51 rows.**

| Kind | Rows | Has a critic accuracy check? |
|---|---|---|
| C (verdict plus a checker's trace) | 15 | yes: verdict and flaw |
| D (verdict) | 15 | yes: verdict |
| B (puzzle) | 6 | yes: answer; and the gates' deterministic `puzzle_check` solves it |
| A (free reply) | 12 | **no** |
| E (non-verdict quiz) | 3 | **no** |

**15 of the 51 accepted rows (29%) get no accuracy check from the critic at all**, only its trait vote. That's a
coverage gap the design's protocols don't touch.

## Phase 1: R&D's blind keys

R&D keyed the 30 C and D rows blind (material, statement, and for C the trace and checker verdict), without the
writer, the critic's answer or the row's key, then compared:

- **Verdicts: 29 of 30 agree with the row's key. 1 is unclear** (P1-049, Lightning, kind C): "the internal tracking
  confirms that flexible start times increase completion rates by 25%" against a material that says the option
  "has been associated with" a 25% increase "though the tracking method was not formally audited". Unsupported and
  cannot_tell can both be argued. The key says unsupported. Under the design's rule, an unclear row counts as a
  failure.
- **Planted flaws: 15 of 15 agree**, including the 6 C items whose trace is a sound check (label `none`).
- **Deciding lines:** all agree in substance. One key carries a line that decides nothing (P1-024, Granite: "The
  specification is complete." beside the real deciding line); the rest differ only in how a multi-sentence line is
  split, or in a list dash.
- **Writers' replies:** all 30 agree with their row's verdict and ESCALATE key.
- **The B puzzles** are checked by the gates' deterministic solver and weren't re-solved.

**A new defect class: the trace gives away the answer.** In 2 C items (P1-017, Bolt pilot; P1-035, Bolt twin), the
checker's trace ends by judging itself: "That is a guess, not the source", and "That assumption is not in the
material". The key is right, but a student trained on it learns the label from the trace's last sentence. The
critic has no check that could see this. Recorded with defect-class tag `trace-leaks-label`.

## What it means

- **Under the decision rule** (wrong or unclear ≥ 3 reopens the screen): wrong 0, unclear 1, so the screen's
  choice of writers stands. With 0 wrong of 30 verdict rows, the one-sided 95% upper bound on the critic's
  false-accept rate for verdicts is about 9.5%. Counting the unclear row as wrong, 1 of 30 bounds it at about 15%.
  This is a small pool, and the bounds say so.
- **The critic isn't shown to be lenient on these rows: the rows are right.** What the pool shows instead is that
  they're **easy**:
  - every D row is a one- or two-line lookup;
  - **none of the 30 has cannot_tell as its true verdict** (18 supported, 12 unsupported), against the release
    rule's 25% minimum.
  An easy screen can't separate writers, whatever the critic does. That shifts weight from "harder critic" to
  "harder slots".
- **Two blind spots the critic can't see:** the 15 rows with no accuracy check, and traces that leak their label.

## Changes to the plan

1. **Phase 2 still runs.** The perturbations test whether the critic would catch a wrong row, which phase 1 can't
   show when every row is right. But its source pool is small: 29 confirmed rows, 30 if the unclear one is set
   aside.
2. **The T10 slot list must carry real difficulty:** cannot_tell items with no deciding line, multi-line
   deciding, and multi-turn D, as the batch-mix rule already requires. The screen's slots didn't.
3. **The gates should refuse a trace that names its own flaw.** A deterministic check, a builder item for
   aspire-si or role-set, with the two items above as its test cases.
4. **Kind A and non-verdict E need some accuracy check,** or their share of a batch should be bounded until one
   exists. That goes to the T10 design.
