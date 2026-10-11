---
title: How is the verifier's training data checked?
description: Every Stage 1 item is read by hand against its key, every puzzle is solved by a program, and every defect found is named, so the checks can move from people into tools.
date: 2026-10-11
status: interim
shelf: not yet (the training run hasn't happened)
---

## The question

ASPIRE (aspire-si) is teaching Qwen3-8B the role of a verifier before any domain training. That Stage 1 data
is a few hundred short items per batch: teaching passages, logic puzzles, flawed checker traces to catch,
two-turn pushback, and written quizzes. A model learns whatever the data teaches, including its mistakes. How
do we keep a wrong key, a puzzle with two answers, or a lazy habit out of it?

## What we found

- **Generated items need a reader.** In pilot 2, a 235B writer produced 49 candidates. Read by hand against their keys, 15 passed, 15 needed a mechanical fix and 19 failed. Three of the
  five logic puzzles had more than one answer.
- **Hand-built batches need one too.** Of batch 5's 120 items, 91 passed as written, 6 needed a relabel, 1 a
  small edit and 22 a rewrite. The commonest fault (11 items) was a claim about something the material never
  names, which makes "can't tell" the answer for the wrong reason.
- **A program now solves every logic puzzle.** role-set's `puzzle-check` reads a small model of each puzzle (the
  people or things, the values, and one rule per numbered line). It refuses a puzzle unless:
  - there is exactly one answer;
  - every clue is needed;
  - no single clue gives the answer away.
- **Passing the solver isn't the same as being a good item.** In one fix round, about 30 of 51 rewritten
  puzzles passed the solver only because they had been bent to fit it: invented yes-or-no attributes, the answer
  stated as "not the other value", made-up counts. The solver was tightened the same day, and now refuses 22 of
  those 51.
- **The same puzzle came back under new names.** Comparing the puzzles' logic with names and values renamed in
  order of first use found six copies of two shapes in one round, then one more pair the next. The check is now
  part of `puzzle-check`: it compares every file together, ignores names, line order, the direction of an order
  clue and the order of a symmetric pair, and refuses the later copy. Its first run found one more copy that both
  human readers had missed.
- **A check can push the data wrong.** A duplicate-phrase check counted the required closing lines (verdict,
  deciding quote, escalate) as prose. To get past it, one item split those lines, which would have taught a
  broken format. The check was fixed, with tests, and the item put back.
- **Every defect now gets a class name.** About 30 classes so far, from `skeleton_repeat` to
  `reject_by_default_as_unsupported`. Each one records whether a tool catches it or only a written brief does.
  Over time, classes move from the brief into a gate.

| Where the item came from | Read | Passed as written | Fixable | Failed or rewritten |
|---|---|---|---|---|
| Pilot 2, 235B writer | 49 | 15 | 15 | 19 |
| Batch 5, hand-built | 120 | 91 | 7 | 22 |

## Caveats

- **None of this data has trained a model yet.** Whether careful data beats rough data at this size is the
  experiment, not a finding.
- The counts are from R&D's key-check, a single reader backed by the solver and the gates, plus a second read by
  the Dataset Specialist. They aren't an inter-rater study.
- The held-out evaluation set is sealed. Nothing on this page comes from it beyond aggregate counts.

## Receipts

`mcp-tool-shop-org/rnd`:
- `experiments/stage1-role-eval/README.md`, one row per review, with the commit reviewed;
- `instruments/role-set.md`, for the solver, puzzle-check and the reviews of each tool change.

`mcp-tool-shop-org/role-set`: `src/role_set/puzzle.py`, the solver; `docs/runs/`, the pilot records.

`mcp-tool-shop-org/aspire-si`: the batch and fix-round pull requests (#92 and #95), and the gates package.

## Shelf status

Not promoted. The method becomes a knowledge-base candidate once Stage 1 has trained and been scored.
