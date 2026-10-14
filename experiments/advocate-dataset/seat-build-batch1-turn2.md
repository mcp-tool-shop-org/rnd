# BUILD BRIEF | Seat C | role-set: the Advocate, batch 1, turn 2: the pack fix-up, then phase 1 | mcp-tool-shop-org/role-set | from R&D, with the Publisher | 2026-10-14

This continues the Publisher's seat brief (`seat-build-roleset-advocate-batch1.md`), which stays the spec for the whole of batch 1. Phase 0 is in at draft PR #56, head `169a51e`. R&D reviewed the pack: it passes on shape and content, with two wording defects. This turn is the fix-up, a stop for the Director, and then phase 1 on his approval.

## Where to work

- Worktree `E:/AI/role-set-advocate`, branch `feat/advocate-batch1`, draft PR #56. Normal commits, no force-push.
- The spec: rnd `experiments/advocate-dataset/brief.md` at 1.1.8.2.12 (the lean batch-1 brief, with the one verdict vocabulary). `brief-v1-hardened.md` is reference only.
- The model is the verifier: `roles/verifier/`, `src/role_set/`.

## Step 1: the pack fix-up → STOP

Two wording changes in `roles/advocate/README.md`, nothing else in the pack:

1. **Section 0a, item 5.** Replace the line that says the recommendation is marked `supported` or `cannot_tell` with:
   > **The recommendation:** one verdict from the decision table (`hold`, `cannot_tell`, `pilot_first` or `proceed`), placed before the alternative clause.
   > - **When the verdict is `hold`, `pilot_first` or `proceed`,** it names the alternative and why it wasn't chosen ("proceed: you'd expect hold; the record supports proceed because …"), and it says what was skipped.
   > - **When the record is missing a decisive figure or rule,** the verdict is `cannot_tell`, and it names what's missing.
2. **The standing rule "Local over cloud, and a paid model API".** Replace its paragraph with:
   > Default to local models on the rig, and never use a paid cloud model API: that's always `hold`. A paid pod run, meaning rented compute through offrig, is right when the local option misses a required check, a free local pilot has passed, the data is clean, and the printed cost is within the cap. That's `proceed`, or `pilot_first` if no pilot has passed yet.

   The sentence "A cloud endpoint has that same green light" goes; it contradicted the rule. The tripwire list's "paid spend or a paid model API" stays as it is: pod spend is a tripwire the green-light conditions can clear, a paid API never clears.

Then recompute the pack hash the way role-set's `pack_hash` does it, push one normal commit, and post `[Seat C → Publisher]` with the new head, the four file shas and the pack hash. **STOP.** The Director approves the pack; the build waits for him. His approval reaches you as a `[Publisher → Grok]` go on #56.

## Step 2: phase 1, the build (brief section 3), only after the go

In this order:

1. **Teach role-set the second pack.** `pack.sync` refuses any role but the verifier (`REFUSED: no sources known for role`). The advocate pack is human text committed in the repository, not synced from aspire-si, so: `pack verify --pack roles/advocate` checks the four files against a manifest and reports the pack hash; `plan --role advocate` loads the pack by that hash; `sync` keeps refusing a role it has no source for, with the message saying the advocate pack is in-repo. Every item records the pack hash.
2. **The ledger generator** for section 0a's nine record shapes (`sources.json` names them): material figures plus one or two immaterial lines, the check results, the asks, the tripwires the record touches, and the decision rule. A record is synthetic; names are role titles only.
3. **The decision table, exactly as brief section 3 orders it,** first match wins: `hold`, then `cannot_tell`, then `pilot_first`, then `proceed`. On a release record, tag the "public or irreversible act" tripwire only when the release is unapproved or fails its provenance or published-file check; a clean release waiting on the Director's go carries no tripwire and takes `proceed`.
4. **The kinds for the three traits:** A and C for `failed-gate-first` and `exact-figures`; B and D for `faithful-relay`; two quizzes (E) per trait. The lesson is what the writer gets, never "write a brief".
5. **Negatives from a separate writer prompt** whose ledger hides one failed check, hides one tripwire, or alters one figure (`behaviours.jsonl` B001–B003). Never edit a good brief into a bad one.
6. **The code checks:** the three on kind A (trace, order, length: at most 130 words and shorter than the record, with no eight-word copy; the table's verdict in section 5 before the alternative is part of the order check) and the scoped checks on B, C and D, as section 3 says; positives pass, each planted class fails.
7. **Reused, not rebuilt:** the variety skeleton floors, CI-gated from a committed record the way T10 does it; the hidden-key critic, from a different local family from the writer; the standard controls.
8. **Tests:** every row of the decision table and every 0a tripwire; the three checks with positives passing and each planted class failing; the record gate.
9. **CI at 10 minutes or less.**

Then mark the PR ready for review and post `[Seat C → Publisher]` with the head, the phase 1 list done, the test count and the suite time. **STOP.** The pilot needs the Publisher's GPU grant and its own go; don't load a model.

## Gates (every push)

- The full suite green at role-set's coverage floor (90).
- CI at 10 minutes or less.
- atlas: stage new files, `atlas map`, then `atlas check`.
- The identity scan on a git archive of HEAD: CLEAN.

## Not in scope

- The pilot (step 3 of the seat brief; it waits for the grant and the go).
- Traits 4–6; batches 2 and 3; real-record material; anything on the deferred list.
- Changes to the verifier pack or the T10 generator (if one is needed, stop and ask).
- Training, which is aspire-si's work.

## Follow-ups come through the PR

The Publisher and R&D post `[Publisher → Grok]` or `[R&D]` comments on #56. Reply `[Seat C → Publisher]`. Do nothing that isn't in the seat brief, this brief or those comments.
