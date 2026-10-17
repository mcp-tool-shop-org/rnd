---
title: Dataset builds
description: A design template for a generated training set that teaches a role, with variety floors and fingerprint controls as the gates, and the checks a design passes before anything is written or paid for.
sidebar:
  order: 6
---

A dataset build makes items that teach a role one quality at a time, through a generator that enforces the method in code. Its value is settled before the first paid call: a set that passes every gate and teaches the generator's habits instead of the role is clean, confident and useless. Fill in every section, have an outside model review the design, and get the Director's approval. Then build.

For role-shaping sets, the [role-set instrument](https://github.com/mcp-tool-shop-org/rnd/blob/main/instruments/role-set.md) is the generator. The evidence behind the controls is in the library entry on dataset recipes for critic roles.

## 0. Licences first

Before section 1 is written, every model, service, data source and tool the design puts to work is checked against
the studio's licence registry ([`licences/registry.json`](https://github.com/mcp-tool-shop-org/rnd/blob/main/licences/registry.json))
**for the use this design makes of it.** That covers writers, critics, judges, graders, embedders, generators of
images or audio, datasets, and the code tools that build it.

- **A use is allowed unless the provider's contract or licence restricts it.** The search is recorded in the
  registry: the page, the clause, its date. Uses that providers commonly ban (training on outputs, distillation,
  competing models) need the explicit clause check, and the registry entry must say which way it reads.
- **A missing entry blocks the design.** Read the terms at the source, add the entry, then go on. A model's summary
  of the terms is never the check.
- **The design lists each item with its registry id and verdict,** for example "writer: Muse-Glimmer-30B
  (`muse-glimmer-30b-card`, training: proven)".
- **The reviewer's verdict carries a licence line.** A pass without one doesn't count.

Why this comes first: Stage 1's training data was built by three services whose terms turned out to bar training on
their outputs, and it had to be regenerated. Checking afterwards costs the work; checking first costs an hour.

## 1. The check in three sentences

Write these first. Nothing else proceeds until the Director has read them.

1. **What the set teaches, and to which role,** in the words of the person who will train on it.
2. **How an item is known to be right** without a model's opinion: by construction, or from a source.
3. **How we would know it taught the role and not the generator's fingerprint.**

If sentence 3 is hard to write, the recipe is missing its controls.

## 2. The role pack comes first

- **Humans write the role.** The lessons, the traits with their counterweights, the kinds and the rules are text the generator serves and never changes. The pack is versioned and hashed, and every item records the hash.
- **The generator teaches qualities, not the task.** A writer gets a lesson and a slot, never "write an item of kind X".
- **A new role is a new pack,** reviewed before a slot is planned. Reuse the method, not the lessons.

## 3. Every answer is known

- **Keys are derivable:** by construction (a solver checks the model, a proof shows the trap works) or from a pinned source with its excerpt recorded.
- **Refusals are structural.** A check in code, or a known-answer mismatch. The generator never scores an item by a model's taste.
- **A contested item is cut,** not argued for. A slot that fails twice is dropped and reported.

## 4. The plan before the spend

- **A plan is a quota table** that meets every floor by construction, produced with no model call and reproduced by its seed. Each slot fixes what the writer must not be free to repeat.
- **Cost is printed before anything runs:** slots, expected attempts, tokens, hours and dollars at the profile's rate.
- **The Director sees the plan and the figure** before a paid batch starts, and the batch runs only inside a grant.

## 5. Variety floors are gates

- **Name the skeleton:** the structural description of an item with its wording removed, so two items can be compared.
- **Set the floors per stratum and in advance,** for example: distinct skeletons at least 75%, no skeleton more than 3 times, none twice in one file, and no prompt stem shared.
- **Tune on tuning seeds; judge on locked seeds** that nobody tunes against. A floor miss on the locked seeds stops the batch; it is not re-rolled.
- **Cells, not luck:** when a stratum has few structures, allocate builds across cells with a cap on the barest, and gate the capacity so growth fails loudly.
- **Enforce the floors in CI** from a committed record with a hash over everything that decides a build, with an on-demand exhaustive rebuild that must reproduce it.

## 6. Fingerprint controls, read before any training

Cheapest first. Say which are gates and which are reports.

1. **Positive control:** a learnable marker must be learned. Proves the probe can see.
2. **Graded marker** at the edit or decision position: tells "the features can't see it" from "the item is hard".
3. **Shuffled labels sit at chance.** A failure here stops every reading.
4. **Partial-input baseline:** one side alone, or the edit span alone, must not predict the label.
5. **Generator-identity probe:** can a cheap classifier tell the writers, planters or seeds apart? If it can, say what it reads.
6. **Clean edits read as clean:** the same planter's edits with no error carry no label.
7. **A held-out generator family** is the headline transfer number.
8. **A natural set** of real, unplanted cases, however small.

Pairs built by editing one side from the other carry the edit as a label. Prefer sides written independently; where planting is used, record the planter and hold one family out.

## 7. Splits that are locked

Train, validation, a frozen exam, a never-tuned final set, the held-out family, the natural set. The split is a file, committed before the batch, and an item moves between splits only by a dated amendment that says why.

## 8. The recipe card ships with the set

| field | contents |
|---|---|
| role and target | the quality taught, the failure it guards, out-of-scope uses |
| sources | prompts, strong answers, licences, provenance |
| construction | writers and planters (family, revision), the edit request, error taxonomy, size stats, seed, code hash |
| filtering | difficulty, solvability, cartography |
| format | pointwise or pairwise (one per run), order randomisation, swap augmentation, reference answer |
| mixture | counts per kind, trait, planter |
| splits | as in section 7 |
| controls | the list in section 6, with each result |
| results | per stratum, against chance and the best single reference, with intervals |
| pins | every model, prompt and tool version |

## 9. Before the first paid batch

1. **One free pilot** on a local writer shows the records are right: the plan, the keys, the refusals and the floors read correctly.
2. **The critic's own controls pass** before its verdicts refuse anything. Until then they are advisory and the human read is the check.
3. **The harness and the design have been reviewed by an outside model,** and the Director has approved the design.
4. **A paid batch waits for the Director's go** and the Publisher's grant, and costs what the plan said.

## 10. Verdicts and what changes

- **Verdicts are per stratum,** on the locked seeds, with the baseline beside them.
- **A floor miss or a failed control stops the batch.** The fix is a dated amendment with its own re-run on fresh locked seeds; the missed run stays in the record.
- **Report what was dropped and why.** A set that teaches less than planned, honestly counted, beats one padded to the quota.
