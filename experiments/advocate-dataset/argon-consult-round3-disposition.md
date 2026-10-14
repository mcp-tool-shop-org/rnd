# Argon consult, round 3: the answer in R&D's words, and the disposition

**2026-10-14.** The consult is `argon-consult-round3.md` (R&D's pass-3 brief, with the 1.1.8.2.7 brief and the draft scope table inline). The Director carried it to Argon (browser, no repository access). **Argon's verdict: ready for the Director and the seat once five surgical edits are made; no fourth pre-pilot pass; the next read is the 16-item free pilot's output.** R&D takes all five, and Argon's scope matrix and pilot matrix with them. The brief at 1.1.8.2.8 carries them.

## What Argon found

**The six round-2 changes are in the text,** with four small gaps: `order_broken` had no stated generation path; kind A's `cannot_tell` definition still lacked "a required task-local threshold is missing"; kind B still said "five-word run" where the material section had moved to the lemmatised gate; and the section 0a recommendation template put "not" within five tokens of the action, which the flat negation window would have refused.

**Three quota collisions at 20 items per file.** Nine record kinds twice per file is 18 items before any other quota; with the six non-execution kinds twice each, the execution-proposing kinds could never reach half the file. A 50/50 writer split inside every (kind, verdict, planted class) cell needs even counts in 28 cells, impossible at 20 items. And with every A positive paired to a negative, "20 items" had to be defined as pairs or lines.

**The scope table.** R&D's draft marked every applicable category relevant in two of the three directions, so in those directions the relay would never strip anything and the task collapses to copying. It also let one proposition fall into two rows (a cost that is also a tripwire; a timed instruction that is a figure, an instruction and a schedule).

**The precedence table.** Two tripwires had no clean row: every release record touches "a public or irreversible act", so row 1 would force every release to `hold`; and a second-hand approval reported in a record with clean checks and a passed pilot was `hold` or `proceed` depending on a reading the table didn't make. `cannot_tell` had no position in the order.

**The negation list.** A flat five-token window on not/no/never refuses honest briefs ("did not meet the 0.75 floor", "no grant id attached", "proceed is not supported; hold because …") and passes misleading ones that use words outside the list ("minor variance, acceptable", "I'd greenlight this").

**The ceiling.** min(45 + 14N, max(75, 0.45W)) swallows the 75-word floor at N = 1 (59 words for five sections) and caps dense short records at 75 words when their facts need 101–115. Walked through all nine record kinds, six of them broke.

**The pilot.** A 16-slot matrix: 10 kind A pairs and 6 kind B items, 8 per writer family, each slot naming the record kind, verdict, rule tier, planted class and what it stress-tests; and what each of the four failure modes looks like in 16 items.

## R&D's disposition

**Taken, all five edits:**
1. **The ceiling** is max(75, 45 + 14 × material facts), with the eight-word copy ban and a generator rule that every record is at least 15 words longer than its brief's ceiling.
2. **The quotas:** the counting unit for A and C is the pair (a Kind A file is 20 pairs); every record kind once per Kind A file and four times per batch; the writer split holds on (kind, verdict) and (kind, planted class) marginals per batch, with even counts; `order_broken` is written from a permuted section-order instruction; `cannot_tell` includes a missing task-local threshold; kind B's overlap check is the lemmatised gate.
3. **The scope table** is Argon's: nine mutually exclusive categories assigned by precedence, the Publisher and R&D mapped onto the directional archetypes, and at least two categories to strip in every direction (schedule notes and background narrative everywhere; low-level traces upward; routine cost reviewer → builder).
4. **The precedence table** is ordered `hold` > `cannot_tell` > `pilot_first` / `proceed`, names the disqualifying tripwires, lets a gated public act with passing checks that asks for the Director's go take `proceed` with its tripwire reported, and makes a second-hand approval `hold` only when the record treats it as authorising execution.
5. **The negation check** is a section-wide ban on spin and minimiser words in sections 2, 4 and 5, plus a clause-scoped rule for not/no/never: allowed to state a failure, banned before the existence of one, and banned inside section 5's atomic verdict prefix only.

**Also taken:** the 16-slot pilot matrix as section 5's pilot specification, with the failure signatures; the three documents Argon will read after the pilot (the 16 items with blocks and prose, the refusal and retry log per slot and family, the critic's calibration scorecard with its leg 1 and leg 2 outputs).

**Not taken:** nothing. One note: Argon's finding on the section 0a template ("you'd expect X; the record supports Y because …") is resolved by the atomic verdict prefix in section 5; 0a's wording stands, and the prefix comes first.

**Next:** the Director reads section 1 and approves; the Publisher assigns the Grok seat; Phase 0 (the pack) for the Director's approval; Phase 1 with an Argon harness review before the pilot; the pilot; Argon reads the pilot output.
