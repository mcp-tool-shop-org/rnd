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
- **A, brief from a record.** Material: a record in a studio format (a run record with its figures and gates, a result note, a PR thread, a cost line with its receipt). Output: the brief, with required parts: figures, gates, asks, risks, recommendation (`supported | cannot_tell`). Key: a trace table built with the material (claim ↔ line id); every figure must equal the record's, every failed gate must appear, no claim without a line, the asks list must match the record's asks. Negatives are planted and located: a brief that hides a failed gate, alters a figure, invents a claim, or drops an ask. `cannot_tell` by construction: a record whose conclusion is absent (a run that was refused, a gate not yet run).
- **B, relay.** Material: a message with its constructed list of material points, in one of two directions (team to leadership: technical to decision; leadership to team: direction to work). Output: the relayed message. Key: every point carried, none added; a planted omission, distortion or addition is located; `escalate` by construction when a point can't be relayed without a decision the relay has no authority to make.
- **C, comparative pair** (the component): two briefs of one record, written independently (two seeds; never one edited from the other); verdict `prefer_1 | prefer_2 | cannot_tell`, the deciding line, the honest case for the other side. The swap twin is made by the plan, not the writer, and the batch check refuses a verdict that doesn't map. `cannot_tell` is two briefs that both pass A's key.
- **D, two-turn.** A brief, then new material (a late receipt, a reversed gate); the brief stands or changes, and says which line changed it.
- **E, quiz** in the role's own words, as the verifier's.

**Material and privacy.** Synthetic records in the studio's own formats are the default: the generator makes a record with its figures, gates and asks, so the key is constructed with it. Real studio records (receipts, result notes, PR threads) may be material for a minority of items only when: the excerpt passes the identity scan; it carries no personal data and no name beyond role titles; it contains nothing the Director wrote verbatim (decisions described, never his words); and it is pinned to a commit on the allow-list, as the verifier's `harvest` does. The seat proposes the scrub step; R&D reads every real-material item before it nears a set.

**The plan.** Floors per trait as the verifier's, plus batch 1's: at least 25% `cannot_tell` across A and C; at least 15% `escalate` in B; planted negatives at most 50% of A and B, spread evenly across their classes (gate hidden, figure altered, claim invented, ask dropped; point omitted, distorted, added); both directions of B in equal share; both orders of every C pair; a length-ratio cap of 20% on C pairs; at least 4 real-material items per trait once the scrub step is approved.

**The checks.** The trace check (A), the point check (B), the twin check (C) and the stand-or-change check (D) are code, run on every item. The hidden-key critic sees the material and the output, not the key, and must re-derive it; its trait leg stays advisory until `critic-control` passes the bars.

**The controls script** (`role-set controls`): on a frozen batch, with no model, a cheap classifier (bag of words plus length) runs the positive marker, shuffled labels, the brief-only and message-only partial-input probes, writer identity and planter identity, with bootstrap intervals; results print and are written beside the batch.

**Variety.** Skeletons, the counterpart of T10's: A is (record kind, figure count, gate count, failed-gate count, ask count, planted class or `none`, verdict); B is (direction, point count, planted class or `none`, verdict); C is (record kind, flaw class or `none`, order); D is (record kind, the change class). Floors as the verifier's (distinct ≥ 75%, top repeat ≤ 3, none twice in a file, no stem shared), enforced in CI the way T10's are: a committed record with a hash over everything that decides a build, and an on-demand rebuild that must reproduce it.

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

- **Free pilot:** the rehearsal writer (`qwen3:8b`, local, under a grant) on one trait, kinds A and B only, 16 items. The purpose is the records: the plan, the keys, the trace tables, the refusals and the controls read correctly. Its output is marked rehearsal and is not data.
- **The critic's controls** (`critic-control` on the brief and relay legs) must pass before a critic verdict refuses anything.
- **The paid batch:** one trait at a time, the pod writer through offrig's loopback, inside a grant, at the cost the plan printed. Three traits in the first batch. The Director sees the plan and the figure first.
- **Locked seeds:** tuning seeds 1–40, locked seeds 41–60 for the verdict. The seat never runs the locked seeds before the code is frozen in a named commit.

## 6. The measurement

Per trait and per kind, on the locked seeds:
- the variety floors and the batch-1 floors (section 3);
- the controls, with intervals, and which passed;
- the critic's agreement with the key, key hidden, per kind;
- the human read: R&D and the Director read every item of the first batch before it nears a training set, as for the verifier.

**The verdict per trait:** floors met, controls passed, critic agreement at or above the verifier's bar, human read clean. Any one missed means the trait's items are held, not merged.

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
- A second writer family. Wanted for the writer-identity control, but it waits on the writer profile and the budget; the first batch uses two seeds of one writer and says so on the card.
- Tone and persuasiveness. Not keyable; the human read samples them, and they never decide a verdict.

## 10. Standards compliance

- **PIN_PER_STEP: 2.** The pack hash, the writer and critic pins, the plan seed and the code hash are in every item.
- **ANDON_AUTHORITY: 2.** A failed control or a floor miss stops the batch; a contested item is cut; a real-material item that fails the scan is dropped.
- **NAMED_COMPENSATORS: 2.** A paid batch is one pod rental through offrig, shut down by the human; an item is held, never deleted; no publish.
- **DECOMPOSE_BY_SECRETS: 2.** The pack (human), the plan (role-set), the writer (pod), the checks (code), the read (human).
- **UNCERTAINTY_GATED_HUMANS: 2.** The Director sees the three sentences, the plan and the cost before any spend; the human read covers what the checks can't.
- **EXTERNAL_VERIFIER: 2.** The Publisher's Argon consult (round 1) before the seat starts; a round-2 consult for anything it leaves open; a harness review before the free pilot.
