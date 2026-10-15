# BUILD BRIEF | Seat C | role-set: the Advocate, batch 1, the phase 1 fix-up | mcp-tool-shop-org/role-set | from R&D, with the Publisher | 2026-10-14

**Status:** R&D's verdict on phase 1 (#56 at `3141e2d`), settled with Argon's round 5 answer (`argon-consult-round5.md` and its disposition). Phase 1 is well tested and CI is green, but it can't carry the pilot yet. This turn fixes it. It comes **before** the turn 3 pilot. The amendments to turn 3 are at the end. The Publisher holds the GPU grant until R&D passes this turn. Load no model.

## Where to work

The same worktree and branch, `feat/advocate-batch1`, on #56. Normal commits, no force-push. Don't touch the pack: the pilot runs on the approved hash `975cf5e1…950b` (see step 7).

## The fix-up, in this order

**1. Records in their shapes, one rendering (findings R1, R2; Q1).**
- Replace `_make` with a builder per shape for the nine shapes in `sources.json`. Each record carries what its shape carries, with two to four material figures that have units (`0.71`, `19 GB`, `41 min`, `$0.00`, `HIT 1`), and one or two immaterial lines.
- The threshold or cap a figure is judged against is itself a figure on the record (`floor 0.75`, `cap $40.00`). A decisive figure that is missing is shown as `pending`.
- Delete `PAD` and `render_record`. A ledger has **one** rendering, in its shape's studio format. The writer reads that rendering, the critic reads it, and the length and copy checks compare against it.
- Tripwires get one fixed display phrase each, from section 0a's wording: paid spend, a public or irreversible act, personal data, the Director's own words in a file, device use without a grant, a merge without review, a floor missed, a frozen analysis changed, a second-hand approval. The record shows the phrase, and trace checks the phrase in section 4, ignoring case. The `B004`–`B012` ids stay internal.

**2. Kind B in the studio's directions (R5).** A point carries a direction (the Director to a seat, a seat to the Director, a reviewer to a builder), a category (figure, instruction, ask, cost or act), and whether it's in scope for that direction. Escalation text comes from the point's own tripwire class, never "a paid step". The `$0.00` aborted dry run is a cost point with spend words and no tripwire, and it relays.

**3. Verdict-changing plants (C1).** Drop the `decide(hidden) == decide(ledger)` filter. A negative's order check runs against the hidden ledger's verdict. `plant_exact` lets the headline and the verdict follow the hidden ledger, and still refuses any other dropped or altered item.

**4. The writer's prompt, and the checks (R3, A2, A3, A4, Q3).**
- `PROCEDURES["A"]` names the five headings exactly as `sections()` reads them, the four verdict tokens, and the section 5 form ("`<verdict>`: you'd expect `<alternative>`; the record supports `<verdict>` because …", or "cannot_tell: the record is missing …"). `PROCEDURES["B"]` names `relay:` and `escalate:`.
- **Order:** match the four verdict tokens on word boundaries in the body of section 5. The first one must equal the key, and it must come before "you'd expect" when that clause is there.
- **Trace:** each material figure's number and unit token appears verbatim, and its metric name appears in the same line or sentence. A verb between them is allowed. No other number appears.
- **Numbers:** a digit inside an alphanumeric token (a SHA, a grant id, `B004`) is not a number. `plant_exact` compares sets of numbers, not lists.
- **Length:** at most 130 words, and at most `max(65, record words − 1)`. The 8-word copy ban against the record stays.

**5. The critic, the probe and the hash (R4, A1, R6).**
- The critic prompt carries the record as the writer saw it, the prose, the decision table and the four verdict tokens. It never carries the key or the plant. Kind A returns `{"verdict", "faithful", "diff_item"}`, and kind B returns `{"action", "faithful", "diff_item"}`. **Recovered** means its verdict or action equals the key and it judged the text faithful. **Flagged** means it judged the text unfaithful.
- The brief-only probe reads the prose alone, without the record, and predicts positive or negative from surface features (length, and a leave-one-out bag of words). It prints its accuracy beside chance. The lean brief said "reused", but role-set has no such probe to reuse, so it's built here. On 26 texts it is a smoke test. Say so when it prints.
- `RECORD_HASH_FILES` is closed over everything the Advocate's planner imports (`kinds.py`, `role_set.pack`, any new module). Port T10's import-closure test.

**6. The pilot planner and runner (Q5).**
- `plan --role advocate --pilot` builds turn 3's sixteen slots exactly as its table describes, from a seed, with the pack hash on every slot. That's 26 texts with the negative split below.
- `pilot --role advocate` runs it: the writer, the three checks (or B's scoped checks), and the critic. The retry rule: the same family with a new seed; reset the slot after five refusals and report it; never fail over to the other family. Then the controls. It writes one run record (items, ledgers, prompts, prose, checks, attempts, critic payloads, controls) and unloads every model at the end and on any abort.
- `--mock` uses a fake writer and a fake critic, and loads nothing. A live run refuses without `--grant` and a fresh heartbeat file, the way `write` does.
- A test runs `pilot --mock` end to end over all 26 texts in CI. It must cover at least one refusal, one retry, one five-refusal reset, one verdict-changing negative and one verdict-stable negative.

**7. The pack stays as approved (Q4).** Leave `behaviours.jsonl` at `handled: none`. The pack is revised once after the pilot read, with the `handled` fields and anything the read changes, for the Director's re-approval with the batch go. Say so in the CHANGELOG.

## Hand-back, then stop

Post `[Seat C → Publisher]` on #56 with:
- the head SHA, the suite count and time, coverage, and CI inside 10 minutes;
- `pack verify` showing the hash unchanged;
- **the reviewers' first read:** `writer_prompt` and `critic_prompt` rendered in full, with the record, for slots 1 (`HIT 1`), 3 (the pod green light with the baseline's failure), 6 (the hidden sole failed check, positive and negative) and 13 (the `$0.00` relay);
- **the `--mock` run's output** on all 26 texts: each check's result, the attempts, which negatives change the verdict and which don't, the critic's two counts, and the probe's accuracy beside chance;
- the grant request, restated or revised.

**Stop.** R&D reviews, Argon reads the two items above, and the Publisher posts the grant only after R&D passes this turn. Then turn 3 runs, as amended below.

## Turn 3, amended by this round

These replace the matching lines in `seat-build-batch1-turn3-pilot.md` (rnd 1.1.8.2.18):
- **Step 0's `--mock` run** is the runner from step 6 above. It already exists when turn 3 starts.
- **The ten negatives:** five change the verdict and five don't. Slots 1 and 6 change it. Slots 4 and 10 keep it. The planner assigns the other six so that each plant class (B001, B002, B003) appears at least twice, and the run record says which slots changed the verdict. A figure plant that crosses a threshold or cap counts as verdict-changing.
- **The critic** reads the record and the prose, with the table, never the key (step 5 above). The bar is unchanged: at least 15 of 16 positives recovered, at least 9 of 10 negatives flagged.
- **Length:** at most 130 words, and at most `max(65, record words − 1)`.

## Gates (every push)

- The full suite green at the coverage floor (90). CI at 10 minutes or less.
- atlas: stage new files, then `atlas map`, then `atlas check`.
- The identity scan on a git archive of HEAD: CLEAN.
- The variety record regenerated and its hash check green, with the closure test.

## Not in scope

- Loading any model. The grant comes after R&D passes this turn.
- The pack's text, traits 4–6, batches 2 and 3, and real-record material.
- The T10 generator and the verifier pack.
