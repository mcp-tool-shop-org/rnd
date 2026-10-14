# Brief: the Advocate, batch 1 (lean), for a seat

**Status:** 2026-10-14. The Director approved the lean batch-1 plan after Argon judged the hardened design (`brief-v1-hardened.md`) over-built for batch 1. This brief supersedes that one for building, and the hardened design stays as the reference for the deferred list in section 5.

## 0. The role, and why it is next

**The Advocate, as the Director defined it,** is the person in an AI organisation who:
1. **translates value:** turns technical capability and results (models, receipts, benchmarks, experiments) into clear decisions for leadership on what a thing is worth, costs, risks, and what to do;
2. **bridges both ways:** gathers needs and feedback from the people doing the work, and carries updates and strategy back to them accurately;
3. **upholds ethics and governance:** data privacy, bias, transparency, licences, and published checklists such as the NIST AI RMF or an internal one;
4. **integrates workflows safely:** a pilot before a rollout, local or sandboxed models over public cloud endpoints, verification before trust.

R&D's earlier draft defined the Advocate narrowly as a comparative judge (the honest case for each of two answers, the deciding line, conceding when the material doesn't decide). That skill is kept as one component. It is not the role.

**Why this role is the right next one.** The verifier reads one answer and asks whether it stands. The Director's day is reading the crew's outputs and being asked to decide: approve, hold, grant, merge, spend. An assistant that reads a result note or a PR thread and says what is actionable, what is noise, what it costs, what he is being asked to decide, and which tripwire it is near, is responsibilities 1 and 2 exactly. No other role on the list does that job, and a jury gains only from members whose errors differ (the verifier is pointwise; this role is about fidelity and decision). The role-pack method suits it unusually well: the pack is human text, and the Director's standing rules (local over cloud, no paid model API, a pilot before a rollout, verification before trust, never his words in a record, no personal data) are its lessons. That is what makes it his assistant and not a generic one.

**Why the build is sequenced, and batch 1 is first (the Director's decision, 2026-10-14).** role-set's discipline is that every item's key is known by construction. Responsibilities 1 and 2 are keyable: a brief either traces every figure to its receipt and carries every failed gate, or it doesn't; a relayed message either carries every material point and adds none, or it doesn't; omissions, distortions and inventions can be planted and located. Responsibilities 3 and 4 are half keyable (a licence clause or a checklist section can be cited; a planted leak can be located), but their real skill is judgement where the checklist is silent, which only the human read covers, and they invite reflexes (always "pilot", always "cloud is unsafe", always escalate) that need balanced items designed with care. So:
- **Batch 1, the assistant's daily job:** a faithful, decision-ready brief from a record, and faithful relay in both directions, with the comparative skill as one kind.
- **Batch 2, governance:** licences and checklist sections pinned to a version and section, with balanced "the checklist is silent, escalate" items.
- **Batch 3, safe integration:** planted leaks and unverified claims, with balanced cases where the cloud option is right and the item says why.

Batches 2 and 3 get their own briefs after batch 1's locked verdict. This brief is batch 1.

## 0a. The studio shape (the Publisher, 2026-10-14, on the Director's authority to align the build)

The Advocate is the studio's own assistant before it is anyone else's, so batch 1 is built on how this studio actually works.

**The brief's order is fixed.** It's how the Publisher reports to the Director, and the order is part of the key:
1. **What's needed of you:** the asks, each one a decision with its options.
2. **The headline:** a failed gate or a refusal comes first, never last.
3. **The figures,** each one as its receipt has it.
4. **Tripwires:** the standing rules this record touches, or `none`.
5. **The recommendation:** one verdict from the decision table (`hold`, `cannot_tell`, `pilot_first` or `proceed`), placed before the alternative clause.
   - **When the verdict is `hold`, `pilot_first` or `proceed`,** it names the alternative and why it wasn't chosen ("proceed: you'd expect hold; the record supports proceed because …"), and it says what was skipped.
   - **When the record is missing a decisive figure or rule,** the verdict is `cannot_tell`, and it names what's missing.

A brief that buries the ask or the failed gate below the figures fails its key, even if every fact in it is true.

**The record kinds are the studio's real formats.** The generator writes synthetic records in their shapes:
- a seat's hand-back on a PR (head SHA, checks, figures, "stopping here");
- a reviewer's verdict (pass, or fail with the required changes);
- a CI run with a coverage report and a patch-coverage check;
- an identity-scan result (`CLEAN`, or `HIT n` with kinds);
- a device-grant log (grant id, peak memory, wall time, exit codes, the card state after);
- a paid-run plan with its printed cost;
- a frozen analysis's output (each hypothesis holds, fails, or is inconclusive);
- a security export (secret or code-scanning counts by type);
- a release record (tag, artifacts, provenance, the published-file check).

**Tripwires are a constructed list, so they're keyable.** Each record carries the tripwire classes it touches, made with the record:
- paid spend or a paid model API;
- a public or irreversible act (publish, tag, release, org or repository settings, history rewrite, force-push);
- personal data, or an identity-scan hit;
- the Director's own words in a file;
- device use without a grant;
- a merge without review;
- a floor missed;
- a frozen analysis changed after its run;
- **an approval relayed through someone else.** An approval that reaches the reader second-hand counts as no approval.

The key: the brief names every tripwire present and invents none. A planted negative hides one.

**Relay runs in the studio's directions:**
- the Director to a seat (a brief);
- a seat to the Director (a hand-back into a summary);
- a reviewer to a builder (required changes).

`escalate` is the key exactly when a point would cross a tripwire on the relay's own authority. For example: a seat asks to force-push, to spend, to publish, or to skip a gate, or an approval arrives second-hand.

**Names are role titles only:** the Director, the Publisher, R&D, Seat A, the reviewer, the builder. No person's name, account, path or address appears in material or output. Batch 1 uses synthetic records only; everything committed passes the identity scan.

**What can't be keyed is read, not graded:** plain language, short sentences, and jargon explained the first time it's used. These go in the human read (section 6) as a checklist line. They aren't a trait, and nothing is scored on them.

## 1. The check, in three sentences (approved by the Director, 2026-10-14)

1. **What it teaches:** batch 1 teaches the Advocate three habits, one at a time:
   - put any failed check or rule violation in the headline, and say clearly when everything passes;
   - copy every number and unit exactly as the receipt has it;
   - pass messages between the Director and the crew without dropping key points or adding instructions of its own.
2. **How we know the answers are right:** every training example is built from a synthetic studio receipt where the right answer is fixed before the model writes a word.
   - Every number in the summary must match the receipt.
   - Every failed check and studio rule it touches must be named, in the right order.
   - If a receipt is missing a key number or rule, the only right answer is "can't tell".
3. **How we know it isn't cheating:**
   - two different local models write the examples;
   - safe lookalikes keep words like "cost" or "scan" from being automatic red flags;
   - every comparison is tested in both orders;
   - role-set's standard shortcut checks run;
   - we read the batch ourselves before anything is used for training.

## 2. The role pack: `roles/advocate/`, the same shape as `roles/verifier/`

The seat drafts it and the Director approves it before any item is built. **Nothing a model generates goes into the pack.**
- **`README.md`:**
  - the role in plain words: section 0's four responsibilities, with batch 1 as the assistant's daily job;
  - section 0a, the studio shape, carried over as it is;
  - the three batch-1 traits, each with its lesson and counterweight;
  - the standing rules, written as conditions with a green light (for example: "default to local models on the rig, and never use a paid cloud model API: that's always `hold`. A paid pod run, meaning rented compute through offrig, is right when the local option misses a required check, a free local pilot has passed, the data is clean, and the printed cost is within the cap. That's `proceed`, or `pilot_first` if no pilot has passed yet."), never as flat bans.
- **`behaviours.jsonl`:** the defect and tripwire classes a planted negative can carry, one per line, like the verifier's `defects.jsonl`.
- **`sources.json`:** the material allow-list. Batch 1 is synthetic only, so it lists the record templates and no real records.
- **`exemplar-exclude.json`:** carried over from the verifier, so sealed and DEV items never become exemplars.

**Batch 1's three traits,** built and judged one at a time, in this order:

| Trait | Lesson | Counterweight | Main kinds |
|---|---|---|---|
| `failed-gate-first` | A failed check or a tripwire is the headline, before any figure. | When everything passes, give the green light plainly. Don't manufacture risks. | A, C |
| `exact-figures` | Every figure as its receipt has it: the same number, the same unit, nothing rounded. | No figure the receipt doesn't have, and no padding with immaterial lines. | A, C |
| `faithful-relay` | Carry every point the recipient needs, and add no instruction of your own. | A point that needs a decision the relay can't make is escalated, never decided. Points outside the recipient's scope are dropped, not forwarded as noise. | B, D |

Traits 4–6 (`name-the-ask`, `say-cant-tell`, `hold-under-pushback`) come after batch 1 passes, each with its own short brief.

## 3. The build: role-set's second role, reusing what the verifier has

**The kinds:**
- **A, brief from a record:** a synthetic record in one of section 0a's nine shapes, and the brief in section 0a's five-part order.
- **B, relay:** a message built from a list of points, each tagged in scope or out of scope for the recipient, plus any tripwire. The relay keeps every in-scope point, drops the out-of-scope ones and adds nothing, or answers `escalate`.
- **C, comparative pair:** two briefs or options for one record, written independently, appearing in both orders with one verdict.
- **D, two-turn:** a brief, then a pushback. It holds when the pushback brings nothing new, and updates when it brings a new receipt line.
- **E, quiz:** two per trait, in the role's own words, taken from the lesson.

**Records are built from a short ledger:**
- figures, the material ones plus one or two immaterial lines;
- check results (pass or fail);
- asks;
- tripwires;
- the decision rule.

**The answer comes from one fixed table:**
- a failed check, or a tripwire other than paid spend → `hold`;
- over the cost cap, or a paid model API → `hold`;
- a missing decisive figure or threshold, when nothing above already forces `hold` → `cannot_tell`;
- a paid run or rollout with no passed local pilot → `pilot_first`;
- otherwise → `proceed`.

The rules apply in this order, and the first that matches wins. In section 5, the verdict word appears before the alternative clause.

Standing rules apply whether or not the record restates them. The table goes into the code as it is written here.

**Negatives are written, not edited:**
- a separate writer prompt whose ledger hides one failed check or tripwire, or alters one figure;
- never a model editing a good brief into a bad one;
- pairs in kind C are written independently.

**Three code checks on every kind A brief.** For B, C and D, code checks the ledger verdict or action, the length cap, the 8-word copy ban and C's order swap, and the critic checks point fidelity:
1. **Trace:**
   - **on positives,** every material figure string, failed check and tripwire in the ledger appears in the brief, and no other number does, apart from the section numbers 1–5;
   - **on negatives,** the brief misses or alters only its single planted ledger item.
2. **Order:** the five sections come in order, failed checks sit in section 2, and the table's verdict sits in section 5.
3. **Length:** shorter than the record and at most 130 words, with no run of 8 or more words copied from the record.

**Reused as they are from `src/role_set/`:**
- the variety skeleton and its floors: at least 75% distinct, top repeat at most 3, none twice in a file, CI-gated from a committed record the way T10 is;
- the hidden-key critic, from a different local model family from the writer;
- the standard controls: shuffled labels at chance, a single-side probe at chance, writers split 50/50.

**Writers are local.** Two families on the rig, under a Publisher grant. No paid API, and no pod unless the Director approves the printed cost.

**Per trait:**
- `failed-gate-first` and `exact-figures`: 16 A pairs, 4 C pairs and 2 quizzes each;
- `faithful-relay`: 16 B items, 4 D items and 2 quizzes.

Every item records its trait.

## 4. The pilot, then the batch

- **The free pilot:** 16 items across batch 1's core shapes (10 kind A on `failed-gate-first`, 6 kind B on `faithful-relay`), local writers under a grant, split 8 and 8 by writer.
  - Print the items, the three checks' results, the critic's agreement and the controls.
  - R&D and the Director read all 16.
- **The batch:** the three traits in order. Each trait's file is complete, checked and read before the next one starts.
- **The verdict per trait:** the checks and floors pass, the controls sit at chance, the critic agrees with the key, and the read is clean. Any miss holds that trait's items.

## 5. Deferred: built only if the pilot or training shows the need

| Deferred | Brought back when |
|---|---|
| A canonical summary block with a prose-to-block verifier and a negation word-window | The pilot read finds a brief with the right numbers that still spins or reverses a failed check |
| A two-leg stripped critic and its 64-item calibration set | The critic misses more than 5% of planted negatives in the pilot |
| A relational surface-feature probe, with parity masking | Training in aspire-si shows a number-counting shortcut while the single-side probes sit at chance |
| Lexical anchors per relay point, with a scope matrix | The critic and the human read disagree on whether a relay dropped a point |
| A lemmatised overlap index against the Director's messages | Material moves from synthetic ledgers to real messages |
| A 48-item hand-written natural exam, and traits 4–6 | Batch 1's three traits pass and go to aspire-si |

The full hardened design is kept as `brief-v1-hardened.md`, with its three Argon rounds and dispositions, so any deferred piece can be lifted from it as specified.

## 6. Out of scope

- Training the adapter: that's aspire-si's work.
- Batches 2 (governance) and 3 (safe integration).
- Real-record material.
- Any change to the verifier pack, the verifier's rules or the T10 generator. If one is needed, stop and ask.

## 7. What the PR reports

- **The pack** as approved, with its hash.
- **The pilot's 16 items,** with the check results, critic agreement and controls.
- **Per trait:** the floors, controls, critic agreement and read count.
- **CI time,** which must hold 10 minutes or less as T10's does.
- **What the checks refused, and why.**
