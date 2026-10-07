---
title: Experiments
description: How rig measurements are kept so the numbers can be trusted later.
sidebar:
  order: 3
---

A `rig` source is only as good as what lets someone rerun it. Each experiment
gets a folder under `experiments/<name>/` beside the entries that cite it.

## What a folder holds

| file | purpose |
|---|---|
| `README.md` | the question, the design, pinned inputs, run commands, deviations, results |
| scripts | the harness: build the inputs, run, score |
| `results/` | receipts: the raw outputs and the scored summary the entry cites |

Large inputs (model weights, datasets) stay outside the repo. The README pins
them by checksum and source instead.

## Pinned inputs

Pin everything that could change the answer: the model file and its sha256, the
server build, helper scripts by hash, the commit the inputs came from, and the
hosted model's dated version when comparing against one.

## Deviations section

Say where the run differs from the authors' or the reference setup, and why it
might matter, before the results. For example: a different serving stack, a
quantised model, or a readout that cannot use a vendor-only parameter. A reader
should meet the caveats before the numbers.

## Results

- State the baseline a useful answer must beat (a base-rate Brier score, chance
  AUC).
- Give intervals, not just point estimates.
- Say plainly when nothing beat the baseline. A null result is a result.
- Note anything about the run itself that a rerun should change.

## Example

`experiments/openjev-vs-jev/` compares a local open model against a hosted one
on the same 124 records, scored with the consuming project's own study code. It
pins the GGUF by sha256 and the helper by hash, lists four deviations from the
authors' setup, and keeps the per-record outputs and a determinism check in
`results/`.

## GPU etiquette on the studio rig

The rig's GPU is shared between sessions. Before a run, check what is loaded.
Ask before taking the GPU, and release it as soon as the run ends.
