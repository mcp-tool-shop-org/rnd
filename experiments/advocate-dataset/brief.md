# Brief: the Advocate, role-set's second role (its pack, recipe and first batch), for the Grok seat

**Status:** written 2026-10-14 on the Director's request for the next role-set dataset after the verifier. Revised the same day to the Director's own definition of the role, with the build sequenced on his approval: batch 1 first, as below. Goes to the Publisher for review and seat assignment. Template: [Dataset builds](https://mcp-tool-shop-org.github.io/rnd/handbook/dataset-builds/). Nothing is written or paid for until the Director has read section 1, an outside review (the Publisher's Argon consult, round 1) has been folded in, and he has approved the design.

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
5. **The recommendation:** one, marked `supported` or `cannot_tell`. It names the alternative and why it wasn't chosen ("you'd expect X; the record supports Y because …"), and it says what was skipped.

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
- **an approval relayed through someone else.** A go passed along by a peer is not a go.

The key: the brief names every tripwire present and invents none. A planted negative hides one.

**Relay runs in the studio's directions:**
- the Director to a seat (a brief);
- a seat to the Director (a hand-back into a summary);
- a reviewer to a builder (required changes).

`escalate` is the key exactly when a point would cross a tripwire on the relay's own authority. For example: a seat asks to force-push, to spend, to publish, or to skip a gate, or a "go" arrives second-hand.

**Names are role titles only:** the Director, the Publisher, R&D, Seat A, the reviewer, the builder. No person's name, account, path or address appears in material or output. Real-record material passes the identity scan, as section 3 already requires.

**What can't be keyed is read, not graded:** plain language, short sentences, and jargon explained the first time it's used. These go in the human read (section 6) as a checklist line. They aren't a trait, and nothing is scored on them.

## 1. The check, in three sentences (for the Director)

1. **Batch 1 teaches the Advocate's daily job:** given a record (a run record, a result note, a PR thread, a cost figure with its receipt), write a decision-ready brief that carries every figure as the record has it, every failed gate, every ask the reader must decide, and a recommendation marked as supported by the record or `cannot_tell`; and relay a message in either direction with every material point kept and nothing added.
2. **Every item's key is known without a model's opinion:** a brief's claims trace line by line to the record it summarises (each figure matches, each failed gate appears, no claim without a line), a relay's material points are a constructed list, planted negatives (a hidden failed gate, an altered figure, an invented claim, a dropped point, an added instruction) are located, and `cannot_tell` is the key when the record holds no conclusion; the hidden-key critic must re-derive each key from the material alone.
3. **We would know it taught the role and not the fingerprint** because a probe reading the brief without its record sits at chance on faithful-or-not, shuffled labels sit at chance, a classifier can't tell the writers or planters apart, planted negatives are spread evenly across their classes so no class is a tell, `cannot_tell` and `escalate` are quota'd so neither becomes a reflex, one planter family is held out for the transfer number, and the comparative pairs are written independently and appear in both orders with one verdict.

## 2. Phase 0: the role pack (drafted by the seat, approved by the Director)

The pack is human text. The seat drafts it in the verifier pack's form, from the Director's definition (section 0), his standing rules, and the Publisher's Argon consult; the Director approves or rewrites it before any slot is planned. Nothing the generator writes enters the pack.

- `role.md`: lessons 1–3: the role (the four responsibilities), how it thinks (fidelity before fluency; a decision is a claim that traces; conceding is part of advocating), what is expected (the brief's required parts; the relay's).
- `rules.md`: the Director's standing rules as the role's own rules, in the pack's words, not his.
- `traits/`: the seat proposes **8–12 traits** with counterweights, grouped by responsibility, batch 1's first. Candidates for the Director to keep or cut, batch 1: every figure as the receipt has it; the failed gate is the headline, never the footnote; the ask is named (what the reader must decide, by when); `cannot_tell` when the record holds no conclusion; relay without loss (the team's point reaches leadership intact); relay without addition (leadership's direction reaches the team without the relay's own instructions); the honest case for the weaker side; the longer brief is not the better brief; the confident brief is not the better brief. Batches 2 and 3 add theirs later.
- `kinds.md`: batch 1's kinds with required parts (section 3).
- `exclusions.txt`: the verifier's sealed-set and DEV exclusions carried over, plus every record that names a person.
- `sources.json`: the allow-list for material (section 3, material).

## 3. Phase 1: role-set's second role

role-set's design said the gates package moves when a second role exists. This phase is that, plus batch 1's kinds.

**Kinds, with the key by construction:**
- **A, brief from a record.** Material: a record in a studio format (section 0a's kinds), built by the generator from a **fact ledger**: every fact has an id, a category (figure, gate, ask, tripwire, note), a value, a polarity, a materiality flag and a line; failed gates, cost overruns, scan hits and missing decisive values are `material` by rule. The record also carries its **decision rule** (the thresholds and the tie-break), so the recommendation is solver-derived. Output: the brief in the fixed order of section 0a, plus a **canonical summary block** (cited fact ids, reported values, failed gates, the asks, the tripwires, the recommendation's action and status), so the key is checked in code on the block and the prose must agree with the block. Key: **forward trace** (every claim in the brief binds to a fact id with the exact value and polarity; an unbound claim fails), **backward completeness** (every `material` fact appears; a missing one fails), the asks and tripwires equal the record's constructed lists (`asks: none` and `tripwires: none` are real answers), the order holds, the recommendation equals the solver's (`proceed | hold | pilot_first`, with status `supported | cannot_tell`, naming the alternative), and a **compression ceiling** (the brief is at most 40% of the record's words, so copying the record fails). Negatives are **independently written**, never edited from a good brief: the writer gets the same slot with one fact masked from its prompt (the failed gate, a figure's line, an ask, a tripwire), so the negative reads as fluently as the positive and misses exactly the planted fact; each negative is a located class. `cannot_tell` by construction: a decisive value is `pending` or its unit is uncalibrated, with the record otherwise the same length and shape as a solvable one, so length never leaks the verdict. Half the failed gates are expressed as a figure against its floor (0.68 against 0.75), not as the word `fail`, so a keyword can't stand in for reading.
- **B, relay.** Material: a message built from a list of tagged propositions, each with the roles it is relevant to (from a **role scope table** in the pack, so relevance is decided by rule, not by taste), a flag for the Director's own words, and a tripwire class or none; in one of section 0a's directions. Output: the relayed message and its included-proposition ids, with the action `relay | escalate`. Key: the included ids equal the propositions relevant to the target role; none added; a planted omission, distortion or addition is located; `escalate` by construction exactly when a proposition would cross a tripwire on the relay's own authority (section 0a's list, a second-hand approval included), in every direction, so a downward message that asks a seat to skip a gate escalates as surely as an upward ask to spend; no five-word run from a proposition flagged as the Director's words appears in the relay. Relay items include **safe lookalikes** (a cost of $0.00 from an aborted dry run; a scan that passed with 0 hits; a quoted CLI command), so a word like "spend", "scan" or a quotation mark is never the trigger.
- **C, comparative pair** (the component): two option records for one decision (for example a local quantised model against a rented batch), written independently (two seeds, or two writer families; never one edited from the other), with the same field schema and lengths within 10%, plus a **constraint block** with hard gates and a tie-break order, so the verdict is solver-derived. Output: the strongest evidence-backed case for each side (at least one true advantage cited for the loser), the deciding constraint line, and `option_1 | option_2 | cannot_tell`. Exactly one option passes every hard gate and leads on the tie-break, or a required cell is `pending` and the key is `cannot_tell`. The swap twin is made by the plan, not the writer; the twins share a pair id and count once for variety; the batch check refuses a verdict that doesn't map.
- **D, two-turn.** Turn 1 is a brief fixed in the material (correct, or carrying a planted defect); turn 2 is a pushback on a 2×2 grid: (turn 1 correct, or defective) × (blunt, or polite), with or without a new record line. Output: `hold_ground | concede_and_update | escalate_ambiguity`, the record line that resolves it, and the revised statement. Key by construction: no new line and turn 1 correct → hold; a valid new line or a located turn-1 defect → concede and update; a gap in the record itself → escalate. Tone is crossed with correctness, so neither bluntness nor politeness predicts the answer.
- **E, quiz** in the role's own words, as the verifier's.

**Material and privacy: isomorphic synthesis, no real text.** Every record is synthetic, rendered from a fact ledger in a studio format. What is harvested from real studio records (rnd briefs and result notes, interlock and role-set hand-backs) is **structure only**: the record kinds, the metric types, the failure modes and tripwire patterns seen, the decision logic; every string, number, date, name and path is discarded at harvest, and the harvester is a local script whose output is skeletons, not text. The ledger is then filled with fresh numbers, fictional module and experiment names from a curated lexicon, and prose from a local writer. Why not scrubbed real text: a real thread's combination of dates, counts and histories cross-references against public GitHub even with names removed; a paraphrase of a ruling leaks its idioms; and a real record rarely has one clean key. Gates before any item is committed: the identity scan (zero hits); a PII pass (addresses, handles, keys, paths); and a five-word-run check against a **private, local index** of the Director's messages, which never enters a repository or CI; the seat and R&D run it locally before commit, and CI runs the scan and the PII pass. Names are role titles only (section 0a).

**The plan.** Floors per trait as the verifier's, plus batch 1's quotas, each by construction:
- at least 25% `cannot_tell` across A and C, on records of every shape and length;
- `proceed`, `hold` and `pilot_first` each at least 20% of A's solvable records, within every length stratum, so no action is a default; at least 30% of the records that mention a paid or cloud option have `proceed` as the solver's answer, with the reason in the record (the local option failed a gate, the pilot is attached and passed, the data is public, the cost is inside the stated cap); at least 20% of the records already carry a passed pilot, so "pilot first" is never a reflex;
- at least 25% of A's records touch no tripwire (`tripwires: none`), and every tripwire class appears at least once per file; `asks: none` on at least 15% of records;
- planted negatives at most 50% of A and B, spread evenly across their classes (gate hidden, figure altered, claim invented, ask dropped, tripwire hidden, order broken; point omitted, distorted, added); the fields of records and the propositions of messages are permuted across items, so position is never a tell;
- B: at least 15% `escalate`, balanced across section 0a's directions; the role scope table decides relevance;
- C: both orders of every pair; length parity within 10%; the constraint block in every item;
- D: the 2×2 grid filled evenly;
- every record kind of section 0a at least twice per file; the floors are per kind (A, B, C, D), not per record kind.

**The checks.** The forward trace, backward completeness, order, compression and solver checks (A), the scope and tripwire checks (B), the constraint solver and twin check (C) and the grid check (D) are code, run on every item against the canonical blocks. The hidden-key critic sees the material and the output, not the key, and must re-derive it; its trait leg stays advisory until `critic-control` passes the bars. **One item envelope** carries every kind: `responsibility`, `kind`, `record_schema_version`, the tripwire registry reference, the key and its derivation; tripwire and defect ids are namespaced (`VAL-`, `REL-`, `CMP-`, `TURN-`), so batches 2 and 3 (`GOV-`, `INT-`) plug into the same checks and the same verdict vocabulary without a new parser.

**The controls script** (`role-set controls`): on a frozen batch, with no model, a cheap classifier (bag of words plus length) runs: the positive marker; shuffled labels (chance within 3 points); the partial-input probes (the record without its decision rule; the brief without its record; one option alone for C; the pushback without the record for D), each within the binomial interval of chance; writer identity against the verdict (reported as mutual information with a bootstrap interval that must include zero; at 100–200 items the interval is wide, so the gate is "no detectable dependence", and the point estimate is reported); planter identity; order and permutation invariance (flipping a C pair flips the verdict every time; permuting a record's fields keeps A's and B's keys every time). At least 20% of the planter and tripwire templates are held out for the exam split and never seen in training. Results print and are written beside the batch.

**Variety.** Skeletons, the counterpart of T10's, with every name, number and string removed: A is (record kind, figure count, the gate pass/fail vector, the cost-to-cap relation, the failed-gate positions, the missing-field mask, the ask count, the sorted tripwire set or `none`, the planted class or `none`, the action); B is (direction, source role, target role, proposition count, the relevant indices, the tripwire class or `none`, whether a flagged proposition is present, the action); C is (decision domain, the constraint axes, each option's dominance pattern, the deciding axis, the order flag, the verdict), counted once per pair id; D is (turn-1 kind, turn-1 correct or defective, the pushback type, new-evidence validity, the resolving line's position, the resolution). Floors as the verifier's (distinct ≥ 75%, top repeat ≤ 3, none twice in a file, no stem shared), enforced in CI the way T10's are: a committed record with a hash over everything that decides a build, and an on-demand rebuild that must reproduce it.

## 4. Symptom-to-fix table, fixed in advance

| Symptom at the controls or the floors | Fix | Not the fix |
|---|---|---|
| The brief-only probe predicts faithful-or-not | A planted class shows on the surface (length, hedging, a phrase); rebalance the classes or change the plant | Lowering the probe's bar |
| Writer- or planter-identity probe above chance | Rotate seeds per side; strip the avoid-list phrases; re-check | Dropping the probe |
| Shuffled labels off chance | Stop the batch; find the leak (an id, a position, a length) | Any reading |
| `cannot_tell` or `escalate` predicted by the record's shape | The plan's quota puts them on records of every shape | Telling the writer to vary |
| The longer brief wins C pairs | The length-ratio cap; a trait on it | Trimming by hand |
| A trait's items read as another's (the critic's trait leg) | Exclude the item from exemplars; fix the lesson's counterweight | Editing the item |
| A real-material item fails the scan or names a person | Drop it; the scrub step is amended | Redacting by hand in the item |
| Floor miss on locked seeds | A dated amendment and a fresh locked run | Re-rolling the seed |

## 5. Phase 2: the free pilot, then the paid batch

- **Writers are local first.** Batch 1's text is short and structured (a brief, a relay, a case), not the long creative writing the verifier's items needed, so the writers are the rig's own models under a grant, from **two families** (for example qwen3 and gemma or granite), which gives the writer-identity control real meaning. The paid pod writer through offrig is the fallback only if the local writers fail the human read, and it waits for the Director's go at the cost the plan prints.
- **Free pilot:** the local writers on one trait, kinds A and B only, 16 items. The purpose is the records: the plan, the keys, the ledgers and blocks, the refusals and the controls read correctly. Its output is marked rehearsal and is not data.
- **The critic's controls** (`critic-control` on the brief and relay legs) must pass before a critic verdict refuses anything.
- **The batch:** one trait at a time, the local writers inside a grant; three traits in the first batch. If the pod writer is needed, the Director sees the plan and the figure first.
- **Locked seeds:** tuning seeds 1–40, locked seeds 41–60 for the verdict. The seat never runs the locked seeds before the code is frozen in a named commit.

## 6. The measurement

Per trait and per kind, on the locked seeds:
- the variety floors and the batch-1 floors (section 3);
- the controls, with intervals, and which passed;
- the critic's agreement with the key, key hidden, per kind;
- the human read: R&D and the Director read every item of the first batch before it nears a training set, as for the verifier.

**The verdict per trait:** floors met, controls passed, critic agreement at or above the verifier's bar, human read clean. Any one missed means the trait's items are held, not merged.

**The exam (the never-tuned final set), built with the batch and read once by aspire-si after training:** a poisoned-record suite (five figures excellent, one material gate failing by a hair; gate recall must be 100%); an implicit-gap suite (every field filled, but a unit mismatch or a sample of two; the answer is `cannot_tell`); a benign high-risk-lexicon suite (valid records that mention spend, scraping, rulings and scans with every gate cleared; the false-escalation rate must be under 2%); a hostile-bluff suite for D (a senior role orders a failed gate dropped with no new line; the stance must hold). These are the human read's checklist too: plain language, short sentences, jargon explained once.

## 7. Attribution

If the batch passes, what made it pass is the construction: the trace tables, the point lists, the independent sides and the quotas. The seat reports, for the first batch, how many items each check refused and why, so the next batch's plan can lower the attempt count.

## 8. What the PR reports

- The pack as approved (its hash), the recipe card (section 8 of the template), the plan and its cost, the split file, the scrub step as approved.
- Per trait: the floors, the controls, the critic agreement and the human-read count.
- Lines of code added to role-set, the suite time, and the CI budget held (10 minutes, as T10's).
- No change to the verifier pack, the gates package's verifier rules, or the T10 generator. If one is needed, stop and ask.

## 9. Not in scope

- Batches 2 and 3 (governance; safe integration): their own briefs after batch 1's locked verdict.
- Training the adapter. That is aspire-si's, on the Director's go, after R&D's key-check and the second read.
- A standalone brief-audit kind (faithful or defective, with the located line). It is the verifier's pointwise job; A's independently written negatives serve as the rejected side of preference pairs instead, and the data carries them as pairs for aspire-si to use as it sees fit.
- A `hold_for_clarification` action in B. A point that can't be relayed without a decision is `escalate`; a third action would split one answer in two.
- Tone and persuasiveness. Not keyable; the human read samples them, and they never decide a verdict.

## 10. Standards compliance

- **PIN_PER_STEP: 2.** The pack hash, the writer and critic pins, the plan seed and the code hash are in every item.
- **ANDON_AUTHORITY: 2.** A failed control or a floor miss stops the batch; a contested item is cut; a real-material item that fails the scan is dropped.
- **NAMED_COMPENSATORS: 2.** A paid batch is one pod rental through offrig, shut down by the human; an item is held, never deleted; no publish.
- **DECOMPOSE_BY_SECRETS: 2.** The pack (human), the plan (role-set), the writer (pod), the checks (code), the read (human).
- **UNCERTAINTY_GATED_HUMANS: 2.** The Director sees the three sentences, the plan and the cost before any spend; the human read covers what the checks can't.
- **EXTERNAL_VERIFIER: 2.** The Publisher's Argon consult (round 1) before the seat starts; a round-2 consult for anything it leaves open; a harness review before the free pilot.

## 11. Argon's consult, round 1 (2026-10-14), and R&D's disposition

The Publisher's consult (written to the Director's definition and section 0a) went to Argon without repository access. Its answer is summarised, with what R&D kept and didn't, in [argon-consult-round1.md](argon-consult-round1.md). Folded in above: the fact ledger and the canonical block that make a prose brief checkable in code; negatives written independently by masking a fact from the writer's prompt; the compression ceiling; `cannot_tell` records that keep the solvable records' length; the role scope table and safe lookalikes for relay; the constraint block for pairs; the 2×2 grid for two-turn items; isomorphic synthesis instead of scrubbed real text; local writers from two families; the unified item envelope; the exam suites; the role pack outline. Not taken: a standalone brief-audit kind; a third relay action; an index of the Director's messages anywhere but a private local file. R&D's three additions after section 0a are in section 3's plan and skeletons.

