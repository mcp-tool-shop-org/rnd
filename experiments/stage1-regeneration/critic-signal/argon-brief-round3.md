[R&D → Argon] Critic-signal, round 3: a short review of the confirmation test, before anything runs.

**Project:** mcp-tool-shop-org/rnd, `experiments/stage1-regeneration/critic-signal/`. You passed v2 of the design
in rounds 1 and 2.

**What's new since round 2:**
- phases 2 and 3 ran (`PHASE-2-3.md`);
- the Director decided on a confirmation test (`DESIGN.md` §9, a draft).

Please review §9 against the phase 2–3 results summarized below.

**Severity levels:** `blocking` (fix before any window), `before the critic window` (can wait until after the
writer window), `not blocking`.

## What happened in phases 2 and 3 (the full tables are in PHASE-2-3.md)

- **Gold input:** 27 rows (12 C, 15 D), made into 66 GPU items (d 27, b 10, e 22, f 7) plus offline a, c and g.
  R&D hand-checked every b, e and g item before any run; one b was invalid, and its drop was pre-registered.
- **The critics:** Muse at seeds 0 and 1, and Lightning at seed 0, on an A100. The family rule skipped 14 items for
  Muse and 11 for Lightning.
- **Primary pool** (b, e, f and g), P2 against P0, as discordant pairs:
  - Muse 6 : 0 (p 0.031);
  - Muse P3 6 : 0 (p 0.031);
  - Lightning 7 : 0 (p 0.016).
  - Lightning P3 wasn't run: it is determined, because P0's only misses are the clean traces, which P2 already
    refuses.
  - Holm across the four gives 0.0625, so nothing is adopted under §5.
- **Every P0–P2 difference is the flaw gate.**
  - On the clean-trace items (f), both critics said "none" on every item (13 of 13). P0 ignores that, because its
    flaw check is advisory.
  - The other two P2 rules never decided an item.
- **Controls:** P2 falsely refused 1 of 44.
- **The bottleneck:** 6–7 f items per critic, because the pilot has no more gold C rows.

## §9 in brief (read the full text in DESIGN.md)

- **The one comparison:** P2 against P0 on Muse, exact McNemar, two-sided, α 0.05, with no multiplicity
  adjustment.
- **Fresh items:**
  - new kind C rows written by Gemma 4 and critiqued by Muse in the pilot path;
  - a blind gold check by R&D, with wrong, unclear and trace-leaks-label rows excluded;
  - the set sealed, then perturb.py run unchanged (role-set `47a5882`, seed 0).
- **Size:** at least 30 gold C rows, about 18 f items. With fewer than 12 f items, more rows are written before the
  critic runs. The critic window runs once.
- **Decision:** adopt P2 if p < 0.05 in P2's favour and its control refusal is at most 10%.

## Questions

1. **Validity of a confirmation.** The hypothesis came from phase 3's data. Is one pre-registered comparison on
   fresh items, with no adjustment, a sound confirmation? Or does the failed phase-3 family carry a multiplicity
   cost into it?
2. **(f)'s fixed frame.** The clean trace is a template: `The material says: "<quote>". That matches/contradicts the
   statement, so it is supported/unsupported.` The whole effect rests on the critic saying "none" to it. Does a
   fixed frame inflate the catch rate compared with a real sound trace in a checker's own style? If it does:
   - Should the confirmation use sound traces written another way, such as a writer asked for a correct trace?
   - Or is a template the right instrument, because it isolates the flaw gate?
3. **The population.** The new rows are the critic-accepted rows that pass the gold check, as in phases 1–2.
   Should rows the critic refused but that pass the gold check also enter, so the pool isn't filtered by the
   critic's own judgement?
4. **One writer.** Gemma alone writes the new rows. Is that a validity problem for the claim "the flaw gate catches
   clean traces mislabeled as flawed", given the traces in f are replaced anyway?
5. **Size and the stopping rule.** At least 12 f items, a target of about 18, and one critic run. Adequate, given
   phase 3's 13 : 0?
6. **Anything else** in §9 that would let a reader doubt the result.

Reply under `## <date> · rnd critic-signal · round 3 confirmation · <commit>`, with a verdict and then the findings.
