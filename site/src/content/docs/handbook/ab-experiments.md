---
title: A/B experiments
description: A design template for comparing two setups of an agent or a model, and the checks a design passes before anything runs.
sidebar:
  order: 4
---

An A/B experiment compares two setups that differ in one thing, on the same tasks, and decides something. Most of its value is settled before the first run: a design that measures the wrong thing produces a clean, confident, useless answer. Fill in every section below, have an outside model review the design, and get the Director's approval. Then build.

For agent experiments, the [agent-ab-harness instrument](https://github.com/mcp-tool-shop-org/rnd/blob/main/instruments/agent-ab-harness.md) runs the arms.

For runs that compare backends, builds or settings of one model, [`rnd abmine`](/rnd/handbook/ab-dataminer/) mines the record: where the arms fork, Δz per step, drift and tie-breaks.

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

1. **The question,** in the words of the person who will act on the answer.
2. **What each arm gets,** concretely: the model, tools, prompt and environment.
3. **Why the difference between the arms answers the question.**

If sentence 3 is hard to write, the design is wrong.

## 2. The treatment is actually taken

- **The arm must receive the thing being tested.** If the question is "is X faster with tool T", the T arm is set up to use T: either told to, or told what T is for, the way real use would be. Making T merely available measures whether a model happens to pick it.
- **Use a manipulation check.** Each run's record must show the treatment was used, for example a count of tool calls. A run that didn't take it is reported as untreated and doesn't count, and a pattern of untreated runs stops the experiment early.
- **Use the treatment where it's meant to help.** Classify the tasks before any run: those the treatment is designed for, and those it isn't. Measure the two groups separately.

## 3. The arms differ only by the treatment

Check each of these, and write down how each is held equal:

- **Leakage.** Can either arm read the answer? Look in the working tree, and also in git history (`git log -p`, `git show`), generated files, caches and earlier runs' records. Delete from history, not just the checkout.
- **Settings parity.** Effort, temperature, turn caps, timeouts and context size must match across arms, or be set to each arm's real production values. Say which.
- **Turn and time caps.** A cap that a slower or chattier setup hits first censors that arm. Size caps so neither arm is cut off by the cap rather than by its ability, or report capped runs apart.
- **Runtime fit.** If one arm runs inside a runtime built for the other (its system prompt, tool formats, conventions), the comparison is of the runtime, not the model. Compare setups as each would really be deployed.
- **Order and time.** Interleave arms task by task, in a seeded order. Don't run one arm's whole block and then the other's: service latency and throttling change by the hour.
- **Caching and warmness.** Run every task's first rep before any second rep, so a repeat doesn't start from a warm cache. State what caches each arm can hit.
- **Concurrency.** If the decision is about real use with many agents at once, measure at that concurrency. One-at-a-time timings overstate a shared GPU.

## 4. The tasks represent the decision

- **Draw tasks from the real work** the decision affects, such as recent agent logs and real questions. A bank built to test something else measures that something else.
- **Count distinct task templates, not tasks.** Five questions with the same stem are closer to one task than to five. Remove near-duplicates.
- **Mix difficulty.** Include multi-step reasoning, not only one-call lookups.
- **Keys:** fixed and audited before any run, by someone who didn't write them. Grade partial answers, with recall and precision for sets, so a near miss and a wild guess don't score the same.

## 5. Measures, sample size and the decision rule

- **The primary measure** is the one the decision turns on. Name it once. Report the others, but don't decide on them.
- **The unit of analysis is the task.** Repeats of one task aren't independent: average a task's reps, then compare arms across tasks. Use a paired test or bootstrap over tasks.
- **Size it before running.** From a pilot or past runs, estimate the share of tasks where the arms disagree. Work out the interval's half-width at your number of tasks. If that half-width is wider than the margin, the test can't pass even when the arms are equal, so add tasks or change the question.
- **The margin is a cost, not a habit.** Say what a given loss costs downstream. A 10-point drop in correctness can cost more than the saving.
- **Stratify by the classification from section 2.** An average can hide a collapse in one kind of task.
- **The decision rule** is written in full before any run, and says what each outcome changes.

## 6. Before the first counted run

1. **The harness has been reviewed** by an outside model, and every finding was checked against the code.
2. **A containment probe passes** for the exact pins and tools in use.
3. **One free validation run** (a local model, or a recorded-stream replay) shows that the records are right: tokens match the CLI's own totals, wall time covers the task alone, and the manipulation check reads correctly.
4. **The design has been reviewed by an outside model,** and the Director has approved it.
5. **Plan or paid runs** wait for the Director's go.

## 7. While running and after

- **Pre-registered stop rules** halt everything on a defect: leakage, writes, a start that doesn't match its arm, or untreated runs.
- **A change to the design after any run** is a dated amendment that says why, and it never touches what the decision rule counts.
- **Report the results with intervals,** by task group, with the manipulation check and every dropped run. A null result is a result.
