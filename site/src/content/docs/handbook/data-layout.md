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
| **Raw data** | run outputs from the rig, Colab or RunPod: tars, generations, logs, journals, receipts, our own builds | [rnd-data](https://github.com/mcp-tool-shop-org/rnd-data), public: manifests and small files in git, larger files once by content in a blob store (public on Hugging Face from the next phase) |
| **Private data** | only the named exceptions: sealed or held-out keys, blind files, item text, unapproved plans, private projects, files the identity scan flags | rnd-data-private, the private companion |

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

## rnd-data and its private companion

The studio's research is open by default, so its raw data is public: [rnd-data](https://github.com/mcp-tool-shop-org/rnd-data)
holds every run's manifest and small files. Its companion, rnd-data-private, holds only the files with a named reason.

```bash
rnd raw ingest <folder> --prefix receipts --reasons reasons.json   # runs into rnd-data, exceptions into rnd-data-private
rnd raw private <folder> --as rnd-local --reasons reasons.json     # a private source's exceptions
rnd raw verify [--run ID] [--deep]                                 # re-hash every git copy; check (or re-hash) every blob
rnd raw verify --public-only                                       # what a public clone can check (rnd-data's CI)
rnd raw relicense --rules <rules.json> --prefix receipts          # reapply a rules file's licences to its manifests
```

- **Runs.** A run is the nearest folder holding an `outcome.json`, so each retry is its own run. Its id is the folder
  path with `/` written as `--`.
- **Files.**
  - Files of 256 KB or less go into git.
  - Larger ones go once, by content, into the blob store (`blobs/<sha[:2]>/<sha>`). They're copied and hash-checked,
    and every blob is read-only.
  - **`--link` hard-links instead.** It's only for a read-only snapshot, such as the backup, on the store's volume. The
    blob is then the same bytes under a second name, never counted as a second copy. A live tree is always copied:
    an append to a linked working file would change the stored blob.
- **Reasons.**
  - A reasons file maps paths or `folder/` prefixes to a reason: `sealed`, `blind`, `item-text`, `unapproved`,
    `private-project` or `identity`.
  - A file whose name looks private is held back even if the reasons file misses it.
- **What a public manifest says about a private file:**
  - A file private only for `identity` is listed by path and size, with no hash.
  - A file private for its content is left out, and counted by reason in `private_files`.
  - No private file's hash is ever published, since a short label file's hash could be matched by guessing.
- **The public check.** `--public-only` is what rnd-data's CI runs, with no blob store or companion to hand. It
  re-hashes every git copy, counts the copies it skips per store, and fails on:
  - under `runs/`: a file no manifest names, a git file over 256 KB, or a content marker (`CALL_CHECKPOINT`);
  - anywhere: the private tag (except the four pages that explain it), a private-looking name, or a home-directory
    path in any OS's form (Windows, macOS, Linux or WSL);
  - in manifests, `store.json`, the docs and the workflows: a drive or machine path;
  - in a public manifest: a private entry with a hash, or a copy naming the private companion, a hash that isn't a
    public file's, or a private entry's path.

  Raw run files may show drive and WSL mount paths (`/mnt/e/...`): a folder layout, not a person. A problem names the
  file and line, never the text it matched. The markers and patterns live inside the package, so a bare
  `pip install` checks the same rules as the rig.
- **Licences.** rnd-data is licensed like rnd: the data is CC BY 4.0, scripts (`*.sh`, `*.py`) are MIT, and a
  third-party file keeps the licence its manifest names. A rules file's `licences` set each public file's
  `licence` at ingest, first match wins. `rnd raw relicense` reapplies them to manifests already written, and
  changes nothing but that field.
- **Tagging.** A note-type private text file (`.md`, `.txt`, `.py`, `.sh`) gets the private tag as its first line,
  unless its hash is pinned anywhere in the library. Data files stay byte-exact.
- **Both repositories store every file byte-exact** (`* -text`), since manifests pin each file by SHA-256.
- **Where rnd finds them.** `rnd check` and the index read them beside the library (`../rnd-data`,
  `../rnd-data-private`), or through `$RND_DATA` and `$RND_DATA_PRIVATE`. A bad manifest is skipped with a warning.
- **The pre-push hook.** `scripts/hooks/pre-push` runs `rnd check` before every push, including the exact private
  match CI can't run. Install it once per clone with `git config core.hooksPath scripts/hooks`.
