# rnd at scale: where each kind of data lives, and the databases that find it (plan v1, 2026-10-19)

**Status: draft for Argon's review.**
- **Kept private** until the Director approves it (brainstorms stay out of public rnd).
- **Nothing here has been done.** Creating a repository or uploading data needs the Director's go.
- **The ask:** the Director wants rnd built up so it scales without becoming a mess, with databases, and possibly
  another repository, outside readouts, for raw and bulk data.

## Standards compliance (workflow standards, 0–3)

- **PIN_PER_STEP — 2.**
  - Every move is made by a script at a pinned rnd commit, and every byte moved carries its SHA-256 in a manifest.
  - The datapack format already does this (`rnd-datapack/v1`).
- **ANDON_AUTHORITY — 2.**
  - `rnd check` gains the size and tier rules (§4) and exits 1 on a breach, so CI stops a bad commit.
  - A migration stops on the first hash mismatch.
- **NAMED_COMPENSATORS — 2.** See the table in §8. Owner: R&D for the rnd side, the Publisher for uploads and repo
  settings.
- **DECOMPOSE_BY_SECRETS — 2.** Four parts change for different reasons, and each gets its own home:
  - text (entries, designs);
  - small public data;
  - bulk public data;
  - private data.
- **UNCERTAINTY_GATED_HUMANS — 2.** The irreversible steps each wait on the Director's go: a new repository, a public
  upload, deleting a local copy. Each is asked contrastively in §9.
- **EXTERNAL_VERIFIER — n/a.** No specialized claims. Argon reviews the design as normal practice.

## 1. What's there now (measured 2026-10-19)

**rnd** (`mcp-tool-shop-org/rnd`, main `c04ab4e`):

| Part | Files | Size | Notes |
|---|---|---|---|
| `experiments/` | 697 | 33.7 MB | 24.4 MB of it is `verifier-gold/` (197 files) |
| `site/` | 78 | 1.9 MB | the newsletter and handbook |
| `tests/` | 51 | 0.65 MB | |
| `entries/` | 67 | 0.36 MB | the library's source of truth |
| the rest | | about 1.5 MB | code, catalogues, instruments, licences, data-pack manifests |

- **The git pack is 8.8 MB.** History is small, and no rewrite is needed.
- **Largest tracked files:** model verdict JSONL files of 0.9–1.3 MB each, mostly under
  `verifier-gold/math-ladder/results/` and `verifier-gold/diffs/`, and `ollama-cuda-backend/diag-record-v6.jsonl`
  at 1.3 MB.
- **By type:** 312 JSON, 309 Markdown, 126 Python, 78 JSONL, 43 SVG and 33 log files.
- **Nothing limits what goes in.** Any size, any file in any folder. There's no rule on raw against processed data.

**Outside rnd, on this rig:**

| Store | Size | Files | What | Copies |
|---|---|---|---|---|
| `E:/AI/rnd-local` | 22 MB | 363 | private: blind and gold keys, item text, sealed items, project notes | **one; none found on D:** |
| `E:/AI/Publisher/receipts` | 20 GB | 1,474 | Colab and RunPod window receipts: tars, generations, logs; 19.9 GB of it is `colab/` | **one; none found on D:** |
| `E:/AI/rnd-watch` | 43 MB | 998 | the weekly watch's runs and reports | one |
| `E:/AI/readouts` (readouts-internal) | 12 GB on disk, 102 MB git | 12,749 | the shelf; 10.8 GB is `model-knowledge/generated/`, untracked | the git part on GitHub |

- **The receipts' one copy is on E:, the USB workspace drive** (the Publisher measured this on 2026-10-19). D:
  (AI-BACKUP) holds none.
  - 58 receipt files are tracked in the Publisher's git repo, but that repo has no remote, so they aren't off the
    drive either.
  - The bulk isn't in git at all: GGUF parts, llama-server builds, pod logs.
- **The data packs** (`natural-errors`, `hymn-arrangements`) are on Hugging Face as **`mcp-tool-shop/rnd-*`**, the
  personal namespace, with manifests in rnd.
- **In the receipts:** the same 122 MB `llama-server.gz` build is uploaded in four windows (10, 10b, 10c, 10d). A
  159 MB build sits in window 1. Single generation logs reach 112 MB.

**The index (`rnd.db`):**
- A generated SQLite file, not in git, rebuilt from the text.
- It covers entries, fields, tags, sources, claims, links and catalogues, with two FTS5 tables (`store.py`).
- **It knows nothing about experiments, runs, costs, data packs or where bytes live.**
- Costs and ledgers ("195.17 of 300 units") are prose in each experiment's README.

## 2. The problems this solves

1. **Bulk data in the clone grows without bound.** Every run adds megabytes of verdict JSONL to git, forever.
2. **Single copies.** The private gold keys and 20 GB of window receipts exist only on E:, a USB drive. A fault on
   that one drive loses the studio's evidence for results already published.
3. **No map of where bytes live.** Finding a run's raw output means knowing which disk, folder and tar it's in.
4. **No machine-readable record of experiments.** A question like "which runs used Muse at Q8_0, and what did they
   cost?" means reading prose READMEs.
5. **Duplicated binaries** in the receipts, re-uploaded per window.
6. **The data packs sit in the personal namespace,** while the org rule puts tool data under the org.

## 3. The design: five tiers, each with one home

Every file belongs to exactly one tier. The tier decides where it lives, how it's backed up, and who may see it.

| Tier | What | Home | Public? | Backed up by |
|---|---|---|---|---|
| **T1 text** | entries, instruments, designs, results write-ups, briefs, code | rnd git | yes | GitHub |
| **T2 small data** | per-experiment data a reader needs to check a result: CSVs, trimmed records, prereg files; each file at most 256 KB, at most 2 MB per experiment | rnd git | yes | GitHub |
| **T3 bulk data** | processed data too big for T2: verdict JSONL, diffs, screens | data packs on Hugging Face, manifest in rnd | private until a publish go | HF + D: |
| **T4 raw** | window outputs: tars, generations, logs, journals, pod receipts | **new repo `rnd-data`** (manifests, small raw files) + D: (the bytes) | never public | D: + an off-site copy (§6) |
| **T5 private** | gold keys, item text, sealed items, blind files | **new private repo `rnd-private`**, or a private folder of `rnd-data` (§9 Q2) | never | GitHub (private) + D: |

- **Not stored at all:** anything rebuilt from a pin. Binaries built from a pinned source (llama-server), and model
  weights already hosted. Their pins and SHA-256s go in the manifest; one copy of each build stays in T4, not one per
  window.
- **readouts is unchanged.** It stays the shelf of verified knowledge bases. Its 10.8 GB of generated media is
  readouts' own matter, listed here only so nobody puts it in rnd-data by accident.

## 4. rnd itself: conventions that `rnd check` enforces

**The size rule (T2).**
- A tracked file over 256 KB under `experiments/` fails `rnd check`, unless it's listed in a short allow-list with a
  reason.
- An experiment over 2 MB in total fails the same way.
- **Existing files are grandfathered** by a list generated once, so nothing turns red on day one.
- **The ratchet:** the allow-list may shrink, never grow, without an R&D review line.

**The experiment layout.** Every new experiment folder gets:
- `README.md`: the design, result and promotion line, as now;
- `experiment.json`: its machine-readable record (below);
- `data/`: T2 only;
- `scripts/`;
- no raw output. A raw file is referenced by its manifest id in rnd-data.

`rnd new-experiment <name>` scaffolds it from the handbook template.

**`experiment.json`** (schema `rnd-experiment/v1`), written by people and checked by `rnd check`:
- **The basics:** name, status (`designing`, `running`, `parked`, `closed`), the design doc, the template used.
- **Runs:** one row per window or session.
  - Its id (13w, 14b, …), where it ran (rig, Colab, RunPod), the hardware, the date.
  - Its pins: tool commits, model and quant with SHA-256, seed.
  - Its cost: units or dollars, measured, with the projection beside it.
  - Its outcome: ok, cut or failed, with the reason.
  - Its raw manifest id in rnd-data.
- **Ledgers:** the budget, its cap and who set it. The total spent is computed from the runs, never typed.
- **Data:** the T2 files, the data packs (T3) and the raw manifests (T4) it uses.
- **Licences:** the registry ids it relies on.

## 5. The databases

The text stays the source of truth, and every database is rebuilt from it. That's how `rnd.db` works today, and it
works.

**`rnd.db` gains five tables,** built from `experiment.json` files and data-pack manifests:
- `experiments` (name, status, template, design path);
- `runs` (experiment, id, venue, hardware, date, cost, projected cost, outcome, pins as JSON);
- `ledgers` (experiment, budget, cap, spent: computed);
- `artifacts` (id, tier, sha256, bytes, licence, location: `git:<path>`, `hf:<repo>@<rev>/<path>`,
  `data:<manifest>/<path>`, `d:<path>`);
- `uses` (experiment, artifact).

It gains these commands:
- `rnd runs [--model …] [--venue …]`;
- `rnd ledger <experiment>`;
- `rnd where <artifact or path>`: where the bytes are, and every copy.

`rnd sql` already gives read-only SQL.

**rnd-data keeps its own manifest index** (`rnd-data.db`, generated, not in git): every raw file's SHA-256, size,
the window it came from, and each copy's location (D:, off-site).
- `rnd where` reads both databases.

**What doesn't change:** readouts' knowledge-base databases.

## 6. rnd-data, the new repository

- **Name and owner:** `mcp-tool-shop-org/rnd-data`, private.
- **What's in git:**
  - one manifest per window (`windows/<id>/manifest.json`: every file's path, SHA-256, size, tier, licence and
    copies);
  - raw files under 256 KB that matter: logs, journals, receipts JSON, `outcome.json`;
  - a README.
- **What's not in git:**
  - the tars, generations and binaries. They live on D: under `D:/rnd-data/windows/<id>/`, with an off-site copy.
  - **The off-site copy is an open choice** (§9 Q3): a private Hugging Face dataset repo, or another store. Its
    cost and limits are read from the vendor's page before choosing (rung 0). This plan doesn't assume either.
- **Tooling:** `rnd raw ingest <receipts-dir> --window <id>`. It hashes every file and writes the manifest. It copies
  to D: and verifies by hash. It drops a file whose SHA-256 is already stored, and records a pointer to it instead.
  - It never deletes the source. Deleting the local copy is a separate step after verification, on the Director's
    go.
- **Per org standards:** the Atlas map and `atlas check` if it runs workflows; the coverage bar for its code (the
  ingest code lives in rnd, so rnd-data may have no code at all); the repo-first rule before any coding.

## 7. Migration, in phases (each one small, reversible and checked)

| Phase | What | Paid? | Irreversible? |
|---|---|---|---|
| **P0 inventory** | A script classifies every file in rnd, rnd-local and the receipts by tier, size, licence and copies. It writes `inventory.csv` locally. | free | no |
| **P1 conventions** | The `experiment.json` schema, the size rule with a grandfather list, `rnd new-experiment`, and the handbook page. No files move. | free | no |
| **P2 index** | The five new tables and `rnd runs`, `rnd ledger`, `rnd where`. Backfill `experiment.json` for live experiments first (critic-signal, stage1-regeneration), then the rest as they're touched (the coverage bar's gradual rule). | free | no |
| **P3 backups first** | Copy rnd-local and the receipts to D: with hash verification. The single-copy risk is the most urgent thing here, and it needs no new repository. | free | no |
| **P4 rnd-data** | Create the repo, ingest the receipts window by window, deduplicate the binaries. | free (GitHub private) | creating a repo |
| **P5 T3 moves** | Move `verifier-gold`'s bulk JSONL into a data pack; the files in git are replaced by the manifest. Git history keeps the old bytes, with no rewrite. | free | upload |
| **P6 T5** | The private store: `rnd-private`, or a folder of `rnd-data` (Q2). | free | creating a repo |
| **P7 namespace** | Move the data packs from `mcp-tool-shop/` to the org namespace on Hugging Face, if the Director wants it (Q4). | free | rename |

- **P3 comes before the rest** because it closes the only risk that can lose data. P0–P3 can run this week with no
  go beyond the plan's approval.

## 8. Compensators (irreversible steps)

| Step | Undo | State after the undo | Owner |
|---|---|---|---|
| Create `rnd-data` (or `rnd-private`) | archive or delete the repo (`gh repo delete`, Director's go) | as before; local copies untouched | Publisher |
| Upload a data pack or raw files to Hugging Face | delete the revision or the repo (private, so nothing has leaked) | manifest in rnd reverted by PR | Publisher |
| Replace T3 files in rnd with a manifest | revert the PR; the bytes are in git history | as before | R&D |
| Delete a local copy after ingest | none once the bin is emptied, so it's done only after two verified copies, on the Director's go | the two copies remain | Publisher |
| Rename the HF namespace | rename back; old URLs in `hosted.json` are kept as aliases | as before | Publisher |

## 9. Questions for Argon

1. **Tier boundaries.** Is 256 KB a file and 2 MB an experiment the right T2 line? Should a hard cap be by type
   (JSONL always T3) rather than by size?
2. **T5's home.** Is a separate private repo better than a private folder of rnd-data, for access, accident risk
   and backup?
3. **The off-site copy** for 20 GB and growing. What should the choice be judged on: cost, limits, integrity checks,
   and how a restore is tested?
4. **The namespace.** Should the existing packs move to the org on Hugging Face, given that their URLs are cited in
   published pages?
5. **Text as the source of truth.** Is rebuilding every database from text and manifests still right once there
   are hundreds of runs? Or should `runs` be written once by the tools that run them (the Publisher's windows) and
   read by R&D?
6. **What's missing.** Retention (how long raw window data is kept), licences on raw outputs, and how readouts
   reads from T3 when it promotes.

**Severity levels:** `blocking`, `before P4` (anything that must be settled before a repository is created),
`not blocking`.

## Licences

No model or new source is used. Any third-party data already carries its licence in the data-pack manifests, and
raw outputs keep their model's terms, recorded per file in the rnd-data manifest.
