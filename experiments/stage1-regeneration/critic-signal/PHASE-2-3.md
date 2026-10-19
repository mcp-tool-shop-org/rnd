# Phases 2 and 3: perturbed copies, and the protocols P0, P2 and P3 (2026-10-19)

Part of the critic-signal design (`DESIGN.md`). Item text stays out of this public repo: the input, the perturbed
items and the critics' replies are kept locally. This file holds ids, counts and results only.

## Tooling and the dry runs

- **Tooling:** role-set #96 (`critic-eval`, `critic-rescore-offline`, `scripts/critic_signal/perturb.py`,
  `PIN_ROLE=critic-eval`), merged at role-set `47a5882` after two R&D review rounds.
- **Gold input:** 27 rows from Phase 1's agreed rows: 12 C and 15 D, 6 of them two-turn.
  - Left out: P1-049 (unclear key), and P1-017 and P1-035, whose traces name their own flaw (defect class
    trace-leaks-label).
- **perturb.py, seed 0:** 66 GPU items (d 27, b 10, e 22, f 7) and key-only files (a 27, c 12, g 22). The items
  file's sha256 starts `cdce4a8a`.
- **R&D hand-checked every b, e and g item before any run.**
  - b: 9 of 10 valid. P1-046:b doesn't flip the verdict. perturb.py misses numbers with a unit attached ("16px"), so
    it changed the wrong number. The item stayed in the sealed file, and its drop was recorded before the run.
  - e: 22 of 22 valid.
  - g: 22 of 22 valid.
- **The ladder, all before the paid windows:**
  - a `--mock` CPU check (P0, P2 and P3 behave as specified; a resume replays 149 calls with no model call);
  - a CPU stub rung (13v-a/b/c: a deadline cut, a resume, a replay with zero calls, token_clean).

## The runs (A100 on Colab, critic at its card values)

| Window | Critic, seed | Scored | Family skips | Calls | Seed time | Units |
|---|---|---|---|---|---|---|
| 13w | Muse, 0 | 52 of 66 | 14 (Muse-written rows) | 89 | 1,695 s | 3.10 (+0.24 for a launch fault, try 1) |
| 13x | Muse, 1 | 52 of 66 | 14 | 89 | 1,642 s | 3.17 |
| 13y | Lightning, 0 | 55 of 66 | 11 (Nemotron-family rows) | 94 (1 VOID retry) | 1,716 s | 4.52 |

- **Per call:** Muse's median was 14–16 s, against the design's projection of 120 s an item, which was taken from
  Lightning's earlier traited runs.
- **One empty reply,** from Lightning on P1-014:e. It hit the length cap, so it was VOID and retried; the retry's
  quote wasn't verbatim, so the item ends VOID, which counts as refused.
- **Thinking:** the role-set field is null on every call, because llama-server doesn't report it. The rnd proxy's
  `generations.jsonl` holds the count of record.

## Results

A perturbed item should be refused; a control should be accepted. The primary pool is b, e and f plus the offline
g, with P1-046:b dropped as pre-registered.

| Type | Muse P0 | Muse P2 | Lightning P0 | Lightning P2 |
|---|---|---|---|---|
| d, controls: refused | 0 of 22 | 1 of 22 | 0 of 22 | 0 of 22 |
| b, material flip: refused | 5 of 6 | 5 of 6 | 9 of 9 | 9 of 9 |
| e, cannot_tell trap: refused | 17 of 17 | 17 of 17 | 17 of 17 | 17 of 17 |
| f, clean trace: refused | 0 of 6 | 6 of 6 | 0 of 7 | 7 of 7 |
| g, decoy deciding (offline): refused | 17 of 17 | 17 of 17 | 17 of 17 | 17 of 17 |
| a, verdict flip (deterministic, reported apart) | 22 of 22 | 22 of 22 | 22 of 22 | 22 of 22 |
| c, flaw relabel (deterministic, reported apart) | 0 of 10 | 10 of 10 | 0 of 11 | 11 of 11 |

- **P3** (Muse at seeds 0 and 1, refusing if either refuses) is identical to P2 on every type. Seed 1 refused nothing
  that seed 0 didn't.
- **Every difference between P0 and P2 is the flaw gate.**
  - On the clean traces (f), both critics said the trace has no flaw on every item: 13 of 13. P0 ignores that,
    because its flaw check is advisory.
  - The two other P2 rules (an empty deciding on cannot_tell, the quote-length cap) never decided an item.
- **The one control P2 refused** is Muse on P1-014:d: it said "guess" where the key has "none".
- **The critics' flaw agreement on the C controls:** Muse 9 of 10.
- **The only miss under every protocol** is Muse on P1-033:b: an end time changed from 5:00 PM to 7:00 PM, which
  Muse read as supported. Lightning caught it.

## The pre-registered test, and why nothing was adopted

- **The comparisons:** exact McNemar on the primary pool, with Holm across the two pairs (P2 and P3 against P0) for
  each critic run.

| Comparison | Discordant pairs (P2 or P3 right, P0 wrong : the reverse) | p |
|---|---|---|
| Muse P2 against P0 | 6 : 0 | 0.031 |
| Muse P3 against P0 | 6 : 0 | 0.031 |
| Lightning P2 against P0 | 7 : 0 | 0.016 |

- **Lightning's P3 was not run.** P0's only misses on Lightning are the 7 clean traces, which P2 already refuses, so
  P3 could only reproduce 7 : 0 at p = 0.016. That saved about 4.5 units on a result already known.
- **Holm over the four comparisons:** 0.016 × 4 = **0.0625, above 0.05. Under the decision rule, no protocol is
  adopted.**
- **What the data show, plainly:**
  - P2 beats P0 13 : 0 across the two critics, with 1 false refusal in 44 controls.
  - The test is short of significance because the pool holds only 6–7 clean-trace items per critic. That's the
    number of gold kind C rows with a planted flaw.
- **The Director's decision (2026-10-19):** a confirmation test on fresh items, pre-registered as one comparison
  (`DESIGN.md` §9).

## Cost

- 10.79 units across 13w (both tries), 13x and 13y, plus 0.05 for the stub rung.
- The study ledger stands at 176.96 of 300.
