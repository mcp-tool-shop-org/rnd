---
title: Where data lives
description: The five kinds of data the library handles, what may sit in the public clone, and each experiment's machine-readable record.
sidebar:
  order: 10
---

The library has to stay small enough to clone and check, while the experiments behind it produce gigabytes. So
every file has one home, decided by what it is first and by its size second. `rnd check` enforces the parts that
live in this repository.

## The five kinds

| Kind | What | Home |
|---|---|---|
| **Text** | entries, instruments, designs, write-ups, briefs, code | this repository |
| **Small data** | what a reader needs to check a result: CSVs, trimmed collected records, pre-registrations, small structured inputs | this repository, within the size limits |
| **Bulk data** | processed data a reader may want but the clone needn't carry: verdict dumps, diffs, screens | a [data pack](https://github.com/mcp-tool-shop-org/rnd#data-packs) on Hugging Face; only its manifest is here |
| **Raw data** | run outputs from the rig, Colab or RunPod: tars, generations, logs, journals, receipts, our own builds | the studio's private raw-data repository and its backups, never public |
| **Private data** | sealed keys for blind tests, item text, blind files, private notes | the private raw-data repository, never public |

**What a file is comes first.** Per-item raw generations, raw verdict dumps and raw run logs are bulk or raw data at
any size. A small structured file is small data. A published benchmark's labels (a pack's `gold.json`) are public;
only a **sealed** key, held out for a blind test that's still running, is private.

## The size rule

- A file under `experiments/` may be at most **256 KB**, and an experiment folder at most **2 MB** in total.
- **The baseline** (`docs/layout.json`) lists the files and folders that were larger when the rule began.
  - A listed file or folder may stay, but may not grow.
  - The list may shrink. Growing it (`rnd layout baseline --allow-growth`) is a reviewed change, with the reason
    given in the PR.
- **Bulk files are built in `staging/`,** which git ignores. `rnd datapack build <pack> --source
  experiments/<name>/staging` makes a data pack from there, so the bulk never enters git.

## The private-file rule

`rnd check` fails on any file in the library that:
- carries the private tag, `T5-PRIVATE-DO-NOT-PUBLISH`. Every private text file carries it, as a
  `"tier": "T5-PRIVATE-DO-NOT-PUBLISH"` field in JSON or a first-line comment elsewhere;
- has a private-looking name: `*blind*`, `*sealed*`, `*gold[-_]key*`, `*item[-_]text*`, `*itemtext*` or
  `*review[-_]items*`;
- or, where the private repository is checked out, matches a SHA-256 in its private manifest.

A published file whose name only looks private, such as a completed blind relabel pass, is listed in the
baseline's `private_allow` with its reason. No list of private files' hashes is ever published: a short label file's
hash could be matched by guessing.

## The experiment record

Every experiment folder has an `experiment.json` (schema `rnd-experiment/v1`). The folders made before the rule are
listed in the baseline's `no_record` until their record is written.

```bash
rnd new-experiment probe-x --title "Probe X" --template model-comparisons
```

That makes `README.md`, `experiment.json`, `data/`, `results/`, `scripts/` and a gitignored `staging/`.

**Written by people:**
- `name` (the folder), `status` (`designing`, `running`, `parked`, `closed`) and `design`, the design file;
- `template`: the handbook page the design follows, or null;
- `budgets`: one per cost unit, each with its `cap` and who set it. Spending is computed from the runs, never typed,
  and never added across units;
- `licences`: the licence registry ids the experiment relies on.

**Written by tools, never typed: `runs`.**
- Each run carries:
  - its `id`, `venue`, `hardware` and `date`;
  - its `cost`, with `cost_unit` and `cost_basis`;
  - its `cap`, `projected_cost`, `outcome` and `why`;
  - its `raw_manifest_id` in the raw-data repository;
  - its `pins`.
- The outcomes, cost bases, cost units and venues come from
  [`run_vocabulary.json`](https://github.com/mcp-tool-shop-org/rnd/blob/main/mcptoolshop_rnd/run_vocabulary.json).
  The Publisher's window records (`outcome.json`) use the same file, so a window's record maps onto a run one to
  one. R&D and the Publisher change it only by agreement.
- **The id rule:**
  - A run's id is the window's name (`14b`).
  - A retry adds its try (`14e-try4`).
  - A RunPod plan names its lane (`publisher-plan4`).
- `why` is required unless the outcome is `results`.

**No machine paths.** The record is public, so `rnd check` refuses a drive letter, a share or a home folder
anywhere in it.
