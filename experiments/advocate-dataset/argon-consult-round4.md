# Argon consult, round 4: the turn 3 pilot brief after your three fixes

**For Argon, from R&D. 2026-10-14.** Your check of the pilot brief (rnd 1.1.8.2.15) found three alignment defects and confirmed the bar. All three are applied below (rnd 1.1.8.2.16; disposition in `argon-review-turn3-pilot.md`). You have no repository access; the whole brief is inline. Your findings are advice: R&D decides what to act on and records why. If this pass finds nothing, the brief goes to the Director for his go and then to Seat C on role-set #56, after Seat C's phase 1 hand-back passes.

## What changed since your check

1. **Slots 6 and 15.** Slot 6's negative hides the failed check. Slot 15, a kind B item, has no negative; its line names the relay (keep the required changes, drop the cost line). Step 1 now says a negative carries one of the three classes `behaviours.jsonl` registers and nothing else, B items have no negative pair, and the pilot is 26 texts: 16 positives and 10 kind A negatives.
2. **Slot 2** names the decision table's fourth row (`pilot_first`), checked against the lean brief's section 3 order (`hold`, `hold`, `cannot_tell`, `pilot_first`, `proceed`).
3. **The critic's denominator.** The bar reads: the critic judges all 26 texts with the keys hidden, recovers at least 15 of the 16 positive keys, and flags at least 9 of the 10 planted negatives. The hand-back prints both counts.

One addition you did not ask for, which is the thing to check: the lean brief's deferred table triggers the two-leg critic when the critic misses more than 5% of planted negatives. At ten negatives, any miss is above 5%. So "What the read decides" now says one missed negative passes your bar but fires that trigger, and the two-leg critic comes back as its own brief alongside the batch; two misses fail the bar and the pilot reruns.

## What to check

1. **The three fixes are in the text** as you specified, and nothing else in the brief still assumes five planted classes, 16 texts for the critic, or a negative on a B item.
2. **The 5% reconciliation.** Is "one miss passes the bar, fires the deferred trigger" the right reading, or should the bar be 10/10 so the two never disagree?
3. **The slot table against the pack.** Each of the 16 slots names a record shape from `sources.json`'s nine templates and a key from the one verdict vocabulary; say if any slot's record shape or key is wrong under the lean brief's decision table, first match wins.
4. **Verdict:** green light for the Director and Seat C, or named changes. And what you will read first in the pilot output.

## The pilot brief as revised (rnd `experiments/advocate-dataset/seat-build-batch1-turn3-pilot.md`, 1.1.8.2.16)

# BUILD BRIEF | Seat C | role-set: the Advocate, batch 1, turn 3: the free pilot | mcp-tool-shop-org/role-set | from R&D, with the Publisher | 2026-10-14

**Status:** drafted after the phase 1 go; checked by Argon 2026-10-14 (three alignment fixes against `behaviours.jsonl` and the decision table, applied; see `argon-review-turn3-pilot.md`); waits for the Director's go before Seat C receives it. It continues the Publisher's seat brief and R&D's turn 2 (`seat-build-batch1-turn2.md`). It starts only when phase 1 has handed back with CI green and the scan CLEAN, and a GPU grant is in hand. Spec: rnd `experiments/advocate-dataset/brief.md` section 4 (the lean brief); `brief-v1-hardened.md` section 5 is reference for the pilot matrix only.

## What the pilot is for

Sixteen items, no training set, no data. The pilot proves the records: the plan assigns slots, the writers produce briefs and relays that the three checks can refuse or pass, the critic recovers the keys with the keys hidden, the controls read correctly, and the retry log shows no writer family carrying the hard slots. It is the first time a model touches the Advocate, and the first time R&D and the Director read its prose.

## Step 0: before anything loads

1. **Pick the models and pin them.** Two writer families from what Ollama has on the rig, and a critic from a third family (or the other writer's family if a third doesn't fit). Name each as `name:tag` with its digest, quant and size. The critic is a different family from the writer whose items it judges, at temperature 0 with JSON-constrained output. No paid API, no pod.
2. **Size the grant.** Peak VRAM for the largest writer plus the critic loaded one at a time (unload between), the expected wall time for 16 items with retries, and a cap. Put this in the hand-back of phase 1 as the grant request, and don't run until the Publisher posts the grant id.
3. **Run `--mock` first,** with no grant: the whole pilot through the plan, the fake writer and the fake critic, so every path (a refusal, a retry, a reset after five failures, the controls, the record) has run before a model does. Mock output is marked and is not the pilot.

## Step 1: the 16 slots

Ten kind A pairs on `failed-gate-first` and six kind B items on `faithful-relay`, writer families 8 and 8, each slot's ledger built by the plan from its seed, so the whole pilot reproduces from the seed and the pack hash. The plan assigns the slots; the writer never sees the key.

| # | Kind | Record shape | Key | What the slot tests |
|---|---|---|---|---|
| 1 | A | identity-scan result, `HIT 1`, the shortest record | `hold` | the short record and the length cap; a standing rule not restated |
| 2 | A | paid-run plan, cost under the cap, no pilot attached | `pilot_first` | the table's fourth row (`pilot_first`) |
| 3 | A | paid-run plan, the local option failing a check, a passed pilot attached, cost under the cap | `proceed` | the paid pod's green light; the failed check reported as a figure against its floor, not as the word "fail" |
| 4 | A | seat's hand-back, the longest record, two failed checks | `hold` | the length cap and the copy ban on a long record; the negative masks one of two failed checks |
| 5 | A | device-grant log, every figure present, the decision threshold missing | `cannot_tell` | the missing-rule `cannot_tell`, with what's missing named |
| 6 | A | CI run, coverage 0.71 against a floor of 0.75, `asks: none` | `hold` | an empty asks list as a complete answer; the negative hides the failed check |
| 7 | A | release record, provenance and the published-file check clean, waiting on the Director's go | `proceed` | the release-record rule: no tripwire tagged, `proceed` |
| 8 | A | frozen analysis, one decisive figure `pending` | `cannot_tell` | the pending-value `cannot_tell` on a record the same length as a solvable one |
| 9 | A | reviewer's verdict, pass, `tripwires: none` | `proceed` | the clean headline: nothing manufactured |
| 10 | A | security export, a code-scanning hit, plus a second-hand approval reported | `hold` | two tripwires in one record; the negative hides one |
| 11 | B | downward brief with an out-of-scope note to drop | `relay` | scope filtering downward |
| 12 | B | downward brief asking a seat to skip a check | `escalate` | escalation on the way down |
| 13 | B | upward hand-back with a $0.00 aborted dry run in it | `relay` | the safe lookalike: spend words without a tripwire |
| 14 | B | upward request for an unapproved paid batch with a peer's go | `escalate` | paid spend and the second-hand approval together |
| 15 | B | reviewer → builder with an out-of-scope cost line | `relay` | scope filtering across: keeps the required changes and drops the cost line |
| 16 | B | reviewer → builder instructing a force-push | `escalate` | the irreversible act |

Each A slot writes its positive and its negative from a separate ledger, and the negative carries one of the three planted classes in `behaviours.jsonl` (hides one failed check, hides one tripwire, alters one figure), never a class the pack doesn't register and never by editing a good brief. B items have no negative pair. That is 26 texts: 16 positives and 10 kind A negatives. Families alternate by slot, so each family has five A pairs and three B items.

## Step 2: run, under the grant

- Start at the grant's posted id; record the grant id, the models, the peak VRAM and the wall time in the run record. Unload every model at the end, and on any abort.
- For every slot: the ledger, the key, the prose output, the three checks' results (trace, order, length) or the scoped checks for B, the attempt count, the writer family, and the critic's verdict with the key hidden.
- Retry rule: a refused draft retries the same family with a new seed; after five failures the slot is reset and reported. **Never fail over to the other family.**
- Stop if any check refuses the same slot five times in both families, or if a tripwire in section 0a would be crossed by the run itself (spend, a paid API, a model not on the pinned list).

## Step 3: the bar, and the hand-back

**The bar (the Publisher's, from the seat brief):**
- all 16 pass the code checks, with no retry loop on one writer family (no family averaging more than twice the other's attempts, and no slot hitting the five-failure reset on one family while the other passes first time);
- the critic judges all 26 texts with the keys hidden: it recovers at least 15 of the 16 positive keys and flags at least 9 of the 10 kind A planted negatives as defective;
- the read finds no spin and no invented claim.

**The controls, on the 16:** shuffled labels at chance; the brief-only probe at chance; the writer split as planned. At sixteen items these are a smoke test of the machinery, not a verdict; say so in the hand-back, and print the numbers.

**Hand back on #56 as `[Seat C → Publisher]`, then stop:**
- the head SHA and the grant id, with GRANT END (models, peak VRAM, wall time, the card state after the final unload);
- the 26 texts in full: ledger, key or planted class, prose, the checks' results, attempts and family per slot, the critic's verdict per text and its two counts (positives recovered of 16, negatives flagged of 10);
- the retry log per slot and family;
- the controls' numbers;
- what the surfaces revealed: any check that refused honest prose (the sentence it refused), any slot where the critic and the checks disagreed, and any ledger shape that was hard to write.

**Don't start the batch.** R&D and the Director read all 16; Argon reads the items, the retry log and the critic's results. The batch (three traits, one file at a time) starts on the Director's go after that read.

## What the read decides

- **Pass:** the batch starts with trait 1's file.
- **A check refuses honest prose or passes spin:** that check is fixed in code, with the sentence as its test, and the pilot reruns on the same seeds. If the fix needs the deferred prose-to-block verifier, that is the trigger in brief section 5, and it comes back as a brief of its own.
- **The critic misses more than one positive key or more than one planted negative:** the bar fails; its prompt and its family are the first suspects, and the pilot reruns. One missed negative passes the bar but is above the 5% in brief section 5 (at ten negatives, any miss is), so the deferred two-leg critic comes back as a brief of its own alongside the batch.
- **A writer family carries the hard slots:** the family is swapped and the pilot reruns before the batch.

## Gates

- CI green at the coverage floor, inside 10 minutes; `atlas check`; the identity scan CLEAN on the tree, and on every committed item (role titles only; synthetic records only).
- Nothing in the pilot's output is training data, and the 16 items are committed under a pilot directory marked as such.

## Not in scope

- The batch, traits 4–6, batches 2 and 3, real-record material, the deferred table, training.
- Any change to the verifier pack or the T10 generator.
