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
  and never added across units. A budget can also say two more things, each naming recorded runs in its unit, a run
  at most once:
  - `excludes`, with an `excludes_why`: runs that fall outside the cap, such as runs made before the budget began.
    The ledger shows them on their own line.
  - `reconciled`: groups of overlapping runs whose own estimates overcount, each with the total that was actually
    `measured` (a provider balance) and `why`. The ledger counts the measured total, and shows the estimates beside
    it.
    - stage1-regeneration's night one is the example: 29 windows whose estimates sum to 136.90 units, against a
      measured 129.48.
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
- `why` is required unless the outcome is `results`. A `no-capacity` run costs nothing, so its `cost` is 0. An
  older word listed under `aliases` (`not-assigned`) is mapped by the recorder and never stored.

**No machine paths.** The record is public, so `rnd check` refuses a drive letter, a share or a home folder
anywhere in it.

## Recording runs, and asking where things are

Every run reaches its experiment record through one command, from the window's own record:

```bash
rnd runs record --experiment stage1-regeneration --from <window>/outcome.json --venue colab --cost-unit colab_units
```

- **A `run` object is read as written.** The Publisher's `publisher outcome write` puts one in each new
  `outcome.json`, in exactly the run fields, and it's recorded with no mapping.
- **The mapping, for older files.** An older file without a `run` object maps one to one: `window` to `id`, `card` to `hardware`, `spent` to `cost`,
  `basis` to `cost_basis`, and `cap`, `outcome` and `why` to themselves. A `commit` becomes a pin.
- **What the options do.** They fill only what `outcome.json` lacks. A value given both ways must agree; nothing is
  silently overridden.
- **Checked before writing.** The whole record is validated first, and nothing is written if any check fails.
- **No silent overwrites.** A run already recorded is replaced only with `--replace`.

The index (`rnd.db`) is rebuilt from the records, the data-pack manifests and, where it's checked out, rnd-data's
manifests:

| Command | What it answers |
|---|---|
| `rnd runs [--experiment] [--venue] [--outcome] [--cost-unit] [--pin TEXT]` | which runs match, across every experiment |
| `rnd ledger <experiment>` | spending per cost unit against each budget, computed from the runs and split by cost basis |
| `rnd where <sha256 or path>` | every name a file goes by and every copy: in git, on Hugging Face, in rnd-data |

The index also has the tables `experiments`, `runs`, `budgets`, `files`, `manifest_files` and `copies`, for
`rnd sql`. The schema's hash is part of the index's change detector, so an rnd upgrade rebuilds it.

## rnd-data's manifests

The private raw-data repository describes each run in `runs/<id>/manifest.json`, and its private files in
`private/manifest.json`:

```json
{"schema": "rnd-data-run/v1", "id": "14b",
 "files": [{"path": "out/pilot-out.tar", "sha256": "…", "bytes": 123, "tier": "T4", "licence": "…"}],
 "copies": [{"sha256": "…", "store": "d", "location": "…"}]}
```

- **The private manifest** uses the schema `rnd-data-private/v1`, and its files have no tier field.
- **Locations stay out of public files.** A location may be a machine path. It lives only in the private manifest and
  the local `rnd.db`, never in a public file.
- **A bad manifest is skipped.** An unreadable manifest, or one with the wrong schema, is skipped with a warning,
  since rnd-data is a separate checkout.
