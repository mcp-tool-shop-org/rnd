---
title: "5 November: the dataset labs, and udlab goes public as a prototype"
description: "Five of our public repositories make datasets, from puzzles and scenes to images and code. The newest, understanding-dataset-lab (udlab), went public this week as a v0.1.0 prototype: multi-party scenes whose answer keys come from code, never from a model. Two of its three stages were not adopted, and the third passed its development gates; there is no sealed result yet. Then the daily watch."
issue: 39
date: 2026-11-05
highlights:
  - "<strong>Five dataset labs.</strong> Puzzles, scenes, images and repositories. In the two that write test items, code makes the answer key and a model only words it."
  - "<strong>udlab is public, as a prototype.</strong> Multi-party scenes with code-made answer keys, written by a local model and checked by code. v0.1.0 is a GitHub pre-release; nothing is on PyPI."
  - "<strong>Two stages failed first.</strong> Stage 3 passed 111 of 160 renderings against 127 for the baseline, and Stage 4 89 against 120. Stage 5 passed all 7 of its development gates: 126 of 160 first drafts against a floor of 112."
---

A dataset day. The labs that make our datasets, side by side, and the newest of them, udlab, which went public this
week as a prototype. Then the daily watch.

**In this issue:**

1. [The dataset labs](#the-dataset-labs)
2. [udlab goes public, as a prototype](#udlab-goes-public-as-a-prototype)
3. [The daily watch](#the-daily-watch)

## The dataset labs

Five of our public repositories make datasets, each on different material. Three of them are built around a check in
code: reasoning-dataset-lab and udlab make every answer key in code, and dataset-desk gates image descriptions without
a model.

| Lab | What it makes | Latest release |
|---|---|---|
| [reasoning-dataset-lab](https://github.com/mcp-tool-shop-org/reasoning-dataset-lab) | Puzzles, quizzes and verification items, where code proves the answer key before any model words the item | v0.4.0 |
| [understanding-dataset-lab](https://github.com/mcp-tool-shop-org/understanding-dataset-lab) | Multi-party scenes for cognitive empathy, with code-made answer keys | v0.1.0 (pre-release) |
| [style-dataset-lab](https://github.com/mcp-tool-shop-org/style-dataset-lab) | Visual canon and image datasets: snapshots, splits, training packages and eval scorecards | v3.4.0 |
| [dataset-desk](https://github.com/mcp-tool-shop-org/dataset-desk) | Visual dataset review: duplicates, outliers, search by words or picture, and a model-free gate for image descriptions | v0.2.2 |
| [repo-dataset](https://github.com/mcp-tool-shop-org/repo-dataset) | Training datasets from code and visual repositories, checked for contamination | v1.2.1 |

The first two are a pair. reasoning-dataset-lab does it for puzzles; udlab does it for people.

## udlab goes public, as a prototype

udlab builds test scenarios for **cognitive empathy**: whether a model can keep an accurate picture of what each party
in a scene knows, believes, wants and needs. It went public this week, at
[v0.1.0](https://github.com/mcp-tool-shop-org/understanding-dataset-lab/releases/tag/v0.1.0), marked as a
pre-release because it is a prototype. It has a [landing page and handbook](https://mcp-tool-shop-org.github.io/understanding-dataset-lab/).

**Why the keys come from code.** A scene starts as a plan of events, in code: someone enters or leaves a room, moves an
object, sees something or is out of sight of it, says something or sends a message. Two rules in the code turn those
events into beliefs: what each person can see from where they stand, and that each person assumes an object stays
where they last saw it, or where a witness last said it was put. So "where does she think the ledger is?" has one right
answer, and code works it out.

A local writer model (`qwen3.6:35b`) then puts each planned scene into prose. The writer can drop an event, reorder
events or blur who saw what, so every rendering is checked by code against the plan before it counts. The key is sealed
with a private seed and never written or graded by a model.

![Process diagram showing how udlab turns a scene into a test item across 5 code steps and 1 model step in the README's words: in Step 1 (code), a scene of events (who moved where, who could see, who said what, and who heard it) is planned by code; in Step 2 (code), rules in code compute each party's beliefs (someone out of sight when an object was moved still believes it is where they last saw it, so the key is computed, not judged); in Step 3 (code), the code-made key from the plan is sealed with a private seed and is never written or graded by a model; in Step 4 (the only model step), the local writer model qwen3.6:35b receives the planned scene (never the key) and puts it into prose; in Step 5 (code), every prose rendering (with Stage 5 code swaps and speech rewrites) is checked by code against the plan; and in Step 6 (code), every rendering is checked before it counts so only renderings that pass the code check count.](/rnd/charts/issue-39-scene-to-item.svg)

**The negative results came first.** Each stage was a different way of getting the writer to produce prose the checker
accepts, measured on development banks of 160 renderings, with the decision rule written down before the run.
- **Stage 3, a list of accepted sentence forms in the writer's prompt: not adopted.** 111 of 160 renderings passed,
  against 127 of 160 with the baseline prompt. The writer didn't use the listed forms.
- **Stage 4, sentence shapes assigned by code: not adopted.** 89 of 160, against 120 of 160 for the baseline, so the
  development gate failed and there was no confirmatory run. It also turned up a defect: 16 renderings per arm (10%)
  were never generated, because the prompt plus the output budget went over the writer's context limit; they count
  as failures in both arms.
- **Stage 5, code moves and rewritten speech: passed its development gates.** The development run passed all 7
  pre-registered gates. First drafts passed 126 of 160, against a floor of 112, and 132 of 160 after the pipeline.
  Code swaps kept 2,501 of 2,501; speech rewrites kept 350 of 358; 0 renderings went over the context limit.

![Across development banks of 160 renderings in the udlab prototype, Stage 3 (accepted-forms list in the writer prompt) passed 111 of 160 renderings against 127 of 160 for the measured baseline prompt and was not adopted, and Stage 4 (sentence shapes assigned by code) passed 89 of 160 against 120 of 160 for the measured baseline and was not adopted (with 16 renderings per arm, or 10%, never generated because the prompt plus output budget went over the writer's context limit and counted inside each arm's 160), whereas Stage 5 (code moves and rewritten speech) cleared its pre-registered floor threshold of 112 of 160 with 126 of 160 on first drafts (+14 above the floor) and 132 of 160 after the pipeline (+20 above the floor), passing all 7 pre-registered development gates (2,501 of 2,501 code swaps kept, 350 of 358 speech rewrites kept or 97.8%, and 0 renderings over the context limit).](/rnd/charts/issue-39-stage-comparisons.svg)

**What "prototype" means here.** These are checks of how well udlab generates scenes, not of whether any model
understands anyone. Not yet shown:
- no sealed confirmatory run of Stage 5;
- no model trained on udlab data;
- nothing yet about whether any model understands the people in a scene.

**What stays private, and why.** The sealed test bank, the development seed banks, every sealed store and generation
log, and the run records with their plan seeds. Publishing any of them would give the answers away. None of them is in
the repository or its history; the 759 tests use synthetic seeds and invented scenes only.

**Try it without a GPU.** The default writer is a CPU mock, so the whole pipeline runs on any machine:

```bash
git clone https://github.com/mcp-tool-shop-org/understanding-dataset-lab
cd understanding-dataset-lab
uv run udlab-gen --count 3 --out-dir artifacts/demo
```

That plans three scenes, writes them with the mock, seals each key with a fresh private seed and prints a summary.
The [getting started](https://mcp-tool-shop-org.github.io/understanding-dataset-lab/handbook/getting-started/) page
goes further, including the shortcut probe that tests whether surface features of a scene give the answer away.

## The daily watch

<!-- PLACEHOLDER: the daily watch for 5 November goes here before merge. -->
