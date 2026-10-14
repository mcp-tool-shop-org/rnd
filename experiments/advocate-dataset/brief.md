# Brief: the Advocate, role-set's second role (its pack, recipe and first batch), for the Grok seat

**Status:** written 2026-10-14 on the Director's request for the next role-set dataset after the verifier, with the choice of role left to R&D. Goes to the Publisher for review and seat assignment. Template: [Dataset builds](https://mcp-tool-shop-org.github.io/rnd/handbook/dataset-builds/). Nothing is written or paid for until the Director has read section 1 and approved the design after an outside review.

## 0. Why the Advocate, and not the Auditor

- **The jury needs members whose errors differ.** The verifier reads one answer and asks whether it stands. The Auditor does the same job as a critic head (pointwise "is there an error"), so its errors would overlap the verifier's. The Advocate's task is comparative: two answers, or an answer and a located change, and the honest case for each side. Pairwise and pointwise skills interfere when trained together and separate cleanly when trained apart (Prometheus 2), and juries gain only from members that fail differently (Kim 2025, Ladha 1992).
- **The critic route is stalled on data.** aspire-si's Auditor and Advocate heads (PR #45) got no role reading: the shuffled-label control failed in every feature source, and the heads separate a pair (0.89–0.97) while barely flagging a lone flawed answer (AUC 0.53–0.57). They learned "which version was edited". That is the generator fingerprint the Director named on 2026-10-08, and designed data with controls is the fix.
- **aspire-si already has the slot.** The Advocate is a named role in its plan, with a defined task (pairwise preference; judging a located change). What it lacks is a role pack and a set built to teach it rather than to leak an edit.

## 1. The check, in three sentences (for the Director)

1. **The set teaches the Advocate:** given two answers to one question, or one answer and a change to it, make the strongest honest case for each side, name the line that decides between them, and prefer one only when the material decides; concede when it doesn't.
2. **Every item's key is known without a model's opinion:** the preferred side is fixed by construction (a planted, located flaw with a proof that the other side has none; a solver-checked puzzle answer; a pinned source line) or is `cannot_tell` by construction, and the hidden-key critic must re-derive it from the material alone.
3. **We would know it taught the role and not the fingerprint** because the two sides of every pair are written independently (never one edited from the other), each pair appears in both orders with one verdict, a partial-input probe on either side alone sits at chance, a classifier can't tell the writers apart above chance, shuffled labels sit at chance, and one planter family is held out for the headline transfer number.

## 2. Phase 0: the role pack (drafted by the seat, approved by the maintainer)

The pack is human text. The seat drafts it in the verifier pack's form, from aspire-si's Advocate plan and the maintainer's method, and the maintainer approves or rewrites it before any slot is planned.

- `role.md`: lessons 1–3 (the role, how it thinks, what is expected). The Advocate argues *for* a position to find its best form, and the counterweight is in the role: advocacy is not loyalty. An advocate concedes the point it can't defend, and says `cannot_tell` when the material doesn't decide.
- `traits/`: the seat proposes **8–12 traits** with counterweights, each a lesson, drawn from where comparative judgement goes wrong. Candidates for the maintainer to keep or cut: the strongest case for the weaker side; the deciding line, quoted; preferring the longer answer; preferring the first answer; preferring the confident answer; a located change that helps against one that only differs; two right answers (`cannot_tell`); two wrong answers; conceding under pressure (the verifier's T13 pattern, comparative); a change that fixes one thing and breaks another; honest praise with the flaw still named.
- `kinds.md`: the kinds, with required parts:
  - **A** pair (question, side 1, side 2): verdict `prefer_1 | prefer_2 | cannot_tell`, the deciding line, the honest case for the other side;
  - **B** located change (answer, change): `helps | hurts | does_not_decide`, with the line it touches;
  - **C** swap twins: every A item has its twin with the sides exchanged and the verdict mapped; both are items, both are checked, and the pair id links them;
  - **D** two-turn: the advocate states a case, new material arrives, the case stands or changes;
  - **E** quiz in the role's own words.
- `rules.md`, `amendments/`, `exclusions.txt`: as the verifier's, with the sealed-set and DEV exclusions carried over.
- The pack is hashed; every item records the hash. Nothing the generator writes enters the pack.

## 3. Phase 1: role-set's second role

role-set's design said the gates package moves when a second role exists. This phase is that.

- `pack sync` takes a role name; the Advocate pack syncs from aspire-si at a commit like the verifier's.
- **Pair construction without an edit artefact:** the two sides of an A item come from **two independent writes** (two seeds, or two writers when a second is available), each against the same question and the same slot, never one rewritten from the other. Where a flaw is planted, it is planted into an independent write, the planter and its family are recorded, and the clean side is proven clean by the same check.
- **Swap augmentation is mechanical:** the C twin is generated from the A item by the plan, not by the writer, and the batch check refuses a verdict that doesn't map.
- **Keys by construction:** a planted flaw carries its proof (what the flaw changes, checked in code where the kind allows: a puzzle answer by the solver, a source line by the pinned excerpt, a number by recomputation); `cannot_tell` pairs are two sides that pass the same checks with no planted flaw.
- **The critic for pairs:** the hidden-key critic sees the question and both sides, not the verdict, and must name the side and the deciding line. Its trait leg (which trait the item teaches, from the closed list) stays advisory until `critic-control` passes the bars.
- **The plan:** floors per trait as the verifier's, plus the pair floors: at least 25% `cannot_tell`, both orders of every pair, at most one in four pairs with a length difference above 20%, no side-1 preference above 60% in a file, and at least 4 real-source items per trait.
- **The controls script** (`role-set controls`): on a frozen batch, with no model, a cheap classifier (bag of words plus length) run for the positive marker, shuffled labels, partial input per side, writer identity and planter identity, with bootstrap intervals; the results print and are written beside the batch.
- **Variety:** the skeleton of an A item is (kind, trait, the flaw class or `none`, the material kind, the order); floors as the verifier's, enforced in CI the way T10's are (a committed record with a hash, an on-demand rebuild).

## 4. Symptom-to-fix table, fixed in advance

| Symptom at the controls or the floors | Fix | Not the fix |
|---|---|---|
| Partial-input probe above chance on one side | The planted flaw is visible without the comparison; move the flaw class to one that only shows against the other side, or raise the share of `cannot_tell` | Lowering the probe's bar |
| Writer-identity probe above chance | Rotate writers or seeds per side; strip the avoid-list phrases; re-check | Dropping the probe |
| Shuffled labels off chance | Stop the batch; find the leak (an id, a position, a length) | Any reading |
| Side-1 preference above 60% | The plan's order quota; check the twins | Telling the writer to balance |
| Length difference predicts the verdict | Cap the length ratio in the plan | Trimming the winner by hand |
| A trait's items read as another trait's (the critic's trait leg) | Exclude the item from exemplars; fix the lesson's counterweight | Editing the item |
| Floor miss on locked seeds | A dated amendment and a fresh locked run | Re-rolling the seed |

## 5. Phase 2: the free pilot, then the paid batch

- **Free pilot:** the rehearsal writer (`qwen3:8b`, local, under a grant) on one trait, kinds A and C only, 16 items. The purpose is the records: the plan, the keys, the twins, the refusals and the controls read correctly. Its output is marked rehearsal and is not data.
- **The critic's controls** (`critic-control` on the pair leg) must pass before a critic verdict refuses anything.
- **The paid batch:** one trait at a time, the pod writer through offrig's loopback, inside a grant, at the cost the plan printed. Three traits in the first batch. The Director sees the plan and the figure first.
- **Locked seeds:** tuning seeds 1–40, locked seeds 41–60 for the verdict. The seat never runs the locked seeds before the code is frozen in a named commit.

## 6. The measurement

Per trait and per kind, on the locked seeds:
- the variety floors (distinct skeletons ≥ 75%, top repeat ≤ 3, none twice in a file, no stem shared);
- the pair floors (section 3);
- the eight controls, with intervals, and which passed;
- the critic's pair-leg agreement with the key, with the key hidden;
- the human read: R&D and the maintainer read every item of the first batch before it nears a training set, as for the verifier.

**The verdict per trait:** floors met, controls passed, critic agreement at or above the verifier's bar, human read clean. Any one missed means the trait's items are held, not merged.

## 7. Attribution

If the batch passes, what made it pass is the construction, not the writer: the twins, the independent sides and the planted-flaw proofs. The seat reports, for the first batch, how many items each check refused and why, so the next batch's plan can lower the attempt count.

## 8. What the PR reports

- The pack as approved (its hash), the recipe card (section 8 of the template), the plan and its cost, the split file.
- Per trait: the floors, the controls, the critic agreement and the human-read count.
- Lines of code added to role-set, the suite time, and the CI budget held (10 minutes, as T10's).
- No change to the verifier pack, the gates package's verifier rules, or the T10 generator. If one is needed, stop and ask.

## 9. Not in scope

- Training the adapter. That is aspire-si's, on the maintainer's go, after R&D's key-check and the second read.
- A second writer family. Wanted for the writer-identity control, but it waits on the writer profile and the budget; the first batch uses two seeds of one writer and says so on the card.
- The Auditor's pack. It follows the Advocate's if the jury wants it, with the same method.

## 10. Standards compliance

- **PIN_PER_STEP: 2.** The pack hash, the writer and critic pins, the plan seed and the code hash are in every item.
- **ANDON_AUTHORITY: 2.** A failed control or a floor miss stops the batch; a contested item is cut.
- **NAMED_COMPENSATORS: 2.** A paid batch is one pod rental through offrig, shut down by the human; an item is held, never deleted; no publish.
- **DECOMPOSE_BY_SECRETS: 2.** The pack (human), the plan (role-set), the writer (pod), the checks (code), the read (human).
- **UNCERTAINTY_GATED_HUMANS: 2.** The Director sees the three sentences, the plan and the cost before any spend; the human read covers what the checks can't.
- **EXTERNAL_VERIFIER: 2.** An outside-model review of the design and the harness before the free pilot, as for T10 and interlock-relay.
