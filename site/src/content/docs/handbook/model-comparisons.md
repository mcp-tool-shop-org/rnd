---
title: Model comparisons
description: A design template for ranking several models on a kind of job, and the checks a design passes before anything runs.
sidebar:
  order: 5
---

A model comparison runs several models on the same tasks and decides which one gets a kind of job. It differs from an [A/B experiment](../ab-experiments/) in three ways:
- **there are many arms,** so a winner can be crowned by chance;
- **each model has its own runtime and settings,** which can favour one model over another;
- **some models won't fit the hardware at all.**

Fill in every section below, have an outside model review the design, and get the Director's approval. Then build. The A/B template's sections 3, 6 and 7 apply here too. This page adds what many arms need.

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

1. **The job kinds,** and the decision each one feeds, for example "which local model writes apply items".
2. **The candidates and the incumbent,** with how each is run.
3. **Why the ranking measure answers the decision.**

If sentence 3 is hard to write, the measure is wrong.

## 2. Candidates and pins

For each model, record before any run:
- **the model digest** (or the Hugging Face revision), the quant and the licence, with its registry id and verdict for this use (section 0);
- **the context length, sampling and a stop cap,** the same for every model in a job kind, or each model's documented production values. Say which.
- **Effort:** the raw parameter actually sent, and whether the model supports graded levels. A level the model can't take is a label, not a setting. Record it as unsupported, and don't count it as a level.

**A pin holds for the whole confirmatory run.** A model that can't run at its pins on the target hardware is recorded as **doesn't fit at this card.** It is never quietly downgraded to a shorter context, a smaller quant or offload. A step-down profile is a different arm, measured in its own sub-study (section 6).

## 3. Each model in its native runtime

- **Run each model where it would really be deployed:** its own tool format, chat template and system prompt, through a harness built for open models, such as Aider or the model family's own CLI.
- **A model inside a runtime built for another family is a guest.** Its score measures the fit to that runtime, not the model. Such an arm may only answer "how well does that runtime drive these models", and it never ranks them.
- **Hold the harness version, the tool set and the turn and time caps equal across models.** A cap one model hits first censors it, so report capped runs apart.
- **Containment:** an arm that could reach a paid account or a cloud model fails closed. Use an empty config directory, a loopback-only endpoint, and a check that refuses any other route.

## 4. Tasks and keys

- **One task bank per job kind,** drawn from the real work, with the A/B template's section 4 rules: count distinct templates rather than tasks, mix difficulty, and fix and audit the keys before any run.
- **Grade blind to the model.** A grader who sees which model wrote an output isn't blind. Where the job makes items (data, code), the reviewer keys them without the source, beside a control set from the incumbent.
- **Public benchmarks are probably in pretraining.** Use them only as a change detector, or say plainly that a high score may be recall.
- **Leakage:** no task, key or near-duplicate may be in any candidate's prompt, tools or retrieval, or in a dataset it will later be trained on.

## 5. The ranking and the decision rule

- **One ranking measure per job kind,** pre-registered. Report the others, but don't decide on them.
- **The unit is the task,** never the seed or the sample. Average a task's repeats first.
- **The ranking:** report each model's score with an interval, and P(best) by bootstrap over tasks. A "best" model whose P(best) is low is a tie, and the report says so.
- **Pairwise tests only on pairs named in advance,** usually each challenger against the incumbent. Use an exact paired test (McNemar for pass/fail), with Holm across the job kinds and pairs. Testing every pair after seeing the results finds false winners.
- **Size it before running.** From a pilot, estimate the discordance, then the smallest difference the task count can detect with 80% power. State it in the design. A study that can only see 20 points says so, and a smaller difference reads as "not shown", not "equal".
- **Cost is part of the decision:** the wall time, memory and energy at the card size the decision is for. A model that wins by 2 points at three times the time may lose the job.
- **The decision rule** is written in full before any run: what each outcome assigns, including "keep the incumbent" and "no decision at this sample size".

## 6. Hardware and the card sub-study

- **Main runs use one machine line** (GPU, driver, runtime and versions), recorded with every run.
- **"What runs on smaller hardware" is its own sub-study,** where the profile (card size, context, quant, offload) is the treatment.
  - A simulated card via a memory reservation reproduces what fits. It doesn't reproduce a smaller card's bandwidth, compute or spill behaviour. Say so beside the table.
- **Preemption:** a run stopped by the safety governor (or by the host for another job) isn't scored against the model, and is rerun. A run that blew its stated time or memory budget is scored as a failure at that card size.

## 7. Receipts

Each run records:
- the task id, model digest, harness and version, and every pin;
- the effort's raw parameter and graded-or-not;
- thinking and output tokens, truncation, wall time and peak memory;
- the grade, and the machine line.

Records go to the study's own store with a shared schema, never into another study's frozen store. Shape them so a later study can reuse them: for example, effort against difficulty for each model.

**The generation record (provenance evidence).** Every model call that produces text the experiment keeps
(writer, critic, judge or candidate) is also logged in the [dataminer](/rnd/handbook/ab-dataminer/)'s record format,
`generations.jsonl`, with:
- one `result` row per call: `arm` (the model's registry name), `prompt` (the call id), `tokens`, and the top-K
  log-probabilities per step (`top`, K = 5 by default);
- the run's pins (the model file's sha256, the server binary and its libraries) and the record's own sha256 on the
  receipt.

**Why:** the record fingerprints the model. Replaying a kept output through the pinned model on the pinned stack
must reproduce its per-token log-probabilities, within the tolerance the replay check sets. A different model, or
an edited text, can't. A sample of every release is replayed by `rnd abmine` (its replay today drives Ollama; a llama-server path is being added for the pinned stacks) and the result goes on the
recipe card or the report. A call made with sampling still records the log-probabilities of the tokens it chose;
the replay checks those.

## 8. Before the first counted run

The A/B template's section 6 applies. In addition:
1. **A fit preflight per model and pins,** recorded, with "doesn't fit" decided here and not mid-run.
2. **The safety governor has passed its fault-injection tests,** and its watchdog heartbeat is fresh.
3. **One free validation run per harness** shows that the records are right, and that the native-runtime and containment checks read correctly.
