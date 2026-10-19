# rnd at scale: where each kind of data lives, and the database that finds it (plan v3.1, 2026-10-19)

**Status: v3.1, FINAL. Argon PASSED it at round 3b (bundle c64a9dfb, 2026-10-19), with no findings at any
severity. P0 (backups) began on the Director's go on 2026-10-19. P1–P3 wait on his go; P4 waits on a price.**
- **Round 1:** CONDITIONAL PASS on v1 (bundle 6ce3076e), with findings F1–F7. All seven are taken in.
- **Round 2:** CONDITIONAL PASS on v2 (bundle c8c4df2f): F1–F7 resolved, no blocking findings, and two new ones (F8
  before P4, F9 not blocking). Both are taken in, with the round-2 answers; §10 says where.
- **Round 3:** PASS on v3. F10 (a table count) and the Q2 answer (no raw hash list in public rnd) are taken in.
- **Kept private** until the Director approves it (brainstorms stay out of public rnd).
- **Nothing here has been done.** Creating a repository, uploading data or deleting a local copy needs the
  Director's go.
- **The ask:** the Director wants rnd built up so it scales without becoming a mess, with databases, and possibly
  another repository, outside readouts, for raw and bulk data.

## Standards compliance (workflow standards, 0–3)

- **PIN_PER_STEP — 2.**
  - Every move is made by a script at a pinned rnd commit, and every byte moved carries its SHA-256 in a manifest.
  - The datapack format already does this (`rnd-datapack/v1`).
- **ANDON_AUTHORITY — 2.**
  - `rnd check` gains the size, layout and private-file rules (§4) and exits 1 on a breach, so CI stops a bad
    commit.
  - A backup or ingest stops on the first hash mismatch.
- **NAMED_COMPENSATORS — 2.** See §8. Owner: R&D for the rnd side, the Publisher for uploads and repo settings.
- **DECOMPOSE_BY_SECRETS — 2.** Text, small public data, bulk public data, raw data and private data change for
  different reasons, and each has its own home.
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
- **Nothing limits what goes in.** Any size, any file in any folder.

**Outside rnd, on this rig:**

| Store | Size | Files | What | Copies |
|---|---|---|---|---|
| `E:/AI/rnd-local` | 22 MB | 363 | private: sealed gold keys, item text, blind files, private project notes | **one, on E:** |
| `E:/AI/Publisher/receipts` | 20 GB | 1,474 | Colab and RunPod window receipts: tars, generations, logs, builds | **one, on E:** |
| `E:/AI/rnd-watch` | 43 MB | 998 | the weekly watch's runs, reports and public-page drafts | **one, on E:** |
| `E:/AI/readouts` (readouts-internal) | 12 GB on disk, 102 MB git | 12,749 | the shelf; 10.8 GB is `model-knowledge/generated/`, untracked | the git part on GitHub |

- **E: is the USB workspace drive.** D: (AI-BACKUP, external, 3.7 TB) holds no copy of the first three stores (the
  Publisher's check and mine, 2026-10-19).
- **58 receipt files are tracked in the Publisher's git repo.** That repo has no remote, so they aren't off E:
  either.
- **The data packs** (`natural-errors`, `hymn-arrangements`) are on Hugging Face as `mcp-tool-shop/rnd-*`, the
  personal namespace, and published pages cite those URLs.
  - Whether D: holds a verified copy of them isn't known; the backup step (P0) checks it.
- **Duplicate builds in the receipts:** the same 122 MB `llama-server.gz` sits in four windows (10, 10b, 10c, 10d).

**The index (`rnd.db`):**
- A generated SQLite file, not in git, rebuilt from the text.
- It covers entries, fields, tags, sources, claims, links and catalogues, with two FTS5 tables (`store.py`).
- **It knows nothing about experiments, runs, costs, data packs or where bytes live.**
- Costs and ledgers are prose in each experiment's README.

## 2. The problems this solves

1. **Single copies on one USB drive.** The sealed gold keys, 20 GB of window receipts and the watch's history.
   A fault on E: loses the evidence behind published results. **This is the only problem here that can lose data,
   so it's solved first (P0).**
2. **Bulk data in the clone grows without bound.** Every run can add megabytes of verdict JSONL to git, forever.
3. **No map of where bytes live.** Finding a run's raw output means knowing which disk, folder and tar it's in.
4. **No machine-readable record of experiments.** A question like "which runs used Muse at Q8_0, and what did they
   cost?" means reading prose READMEs.
5. **Duplicated builds** in the receipts.

## 3. The design: five tiers, each with one home

Every file belongs to exactly one tier. The tier decides where it lives, how it's backed up, and who may see it.

| Tier | What | Home | Public? | Copies |
|---|---|---|---|---|
| **T1 text** | entries, instruments, designs, results write-ups, briefs, code | rnd git | yes | GitHub |
| **T2 small data** | data a reader needs to check a result: CSVs, trimmed collected records, prereg files, small structured inputs | rnd git | yes | GitHub |
| **T3 bulk data** | processed data a reader may want but rnd needn't carry: verdict dumps, diffs, screens | data packs on Hugging Face, manifest in rnd | private until a publish go | HF + D: |
| **T4 raw** | run outputs from any venue (rig, Colab, RunPod): tars, generations, logs, journals, receipts, custom builds | **new private repo `rnd-data`** (manifests + small files in git), bytes on D: and off-site | never | git (manifests) + D: + off-site |
| **T5 private** | sealed gold keys (held-out keys for blind tests), item text, blind files, private project notes, the watch's history | `rnd-data/private/` in git | never | GitHub (private) + D: |

**The content rule** (round 1 Q1): what a file is decides its tier first, and size second.
- **Per-item raw generations, raw verdict dumps and raw run logs** are T3 or T4, whatever their size.
- **Small structured files** stay in T2 under the size limits: a prompt list, a trimmed collected record, a prereg.
- **"Gold" in a public pack** (for example `data/gold.json`, a published benchmark's labels) is T3 and public. Only
  **sealed** gold keys, held out for a blind test, are T5.

**Not stored by us:** model weights already hosted upstream. Their pin and SHA-256 go in the manifest.

**Stored once, by content (round 1 F3):** builds we made ourselves, such as llama-server.
- They live once in `D:/rnd-data/blobs/<sha256>/` and off-site.
- Each window's manifest lists them by SHA-256.
- No window points inside another window's folder, so archiving one window can't break another.

**readouts is unchanged.** It stays the shelf of verified knowledge bases. Its 10.8 GB of generated media is
readouts' own matter, listed here only so nobody puts it in rnd-data by accident.

## 4. rnd itself: conventions that `rnd check` enforces

**The size rule (T2).**
- A tracked file over 256 KB under `experiments/` fails `rnd check`, unless it's on the grandfather list.
- An experiment over 2 MB in total fails the same way.
- **The grandfather list** is generated once from today's files, so nothing turns red on day one. It may shrink,
  never grow, without an R&D review line.

**The private-file rule (round 1 F5).** `rnd check` fails on any tracked file that:
- has a SHA-256 listed in `rnd-data/private/manifest.json`, when a local rnd-data checkout is present;
- or matches the private name patterns below;

- or carries the private tag `T5-PRIVATE-DO-NOT-PUBLISH`.
  - Every T5 text file carries the tag: as a `"tier": "T5-PRIVATE-DO-NOT-PUBLISH"` field in JSON, and as a first-line
    comment elsewhere.
  - This works in CI, where rnd-data isn't checked out.
  - **No list of private files' hashes is published** (round 3 Q2). A sealed key is a short label file, so its raw
    SHA-256 could be matched by guessing label sets.
- **The exact SHA-256 check** against `rnd-data/private/manifest.json` runs where rnd-data is checked out: in `rnd
  check` on the rig, and in a local pre-push hook.

**The name patterns,** matching hyphens and underscores alike (round 2 Q3): `*blind*`, `*sealed*`,
`*gold[-_]key*`, `*item[-_]?text*`, `*review[-_]items*`. They're the backstop for a file that can't carry the tag (a binary). A false hit goes on a short, reviewed allow-list.

**The experiment layout** (round 1 F5):
- `README.md`: the design, result and promotion line, as now;
- `experiment.json`: its machine-readable record (below);
- `data/` and `results/`: T2 only (`results/` is where `rnd collect` writes, and `collect.json` stays at the top);
- `scripts/`;
- `staging/`: gitignored, the `--source` for `rnd datapack build`, so bulk files can be built into a pack without
  ever being committed.

`rnd new-experiment <name>` scaffolds it from the handbook template.

**`experiment.json`** (schema `rnd-experiment/v1`):
- **Written by people:** name, status (`designing`, `running`, `parked`, `closed`), the design doc, the template
  used, budgets, the licences relied on.
- **Written by tools, never typed (round 1 Q5):** the runs.
  - The window runner writes `outcome.json` for each run.
  - `rnd runs record --from <outcome.json>` adds or updates the run in `experiment.json`: its id, venue, hardware,
    date, pins, measured cost, cost unit, projected cost, outcome and raw manifest id.
  - It writes no machine paths, the same public-safe rule `rnd collect` already enforces.
- **Budgets:** one per cost unit (`colab_units`, `usd`, `rig_hours`), each with its cap and who set it. Spending is
  computed from the runs in that unit, never typed, and never summed across units (round 1 F2).

## 5. The database

The text stays the source of truth, and the database is rebuilt from it. That's how `rnd.db` works today, and at
thousands of rows a rebuild still takes well under a second.

**`rnd.db` gains six tables:**
- `experiments` (name PK, status, template, design path);
- `runs` (experiment, id, venue, hardware, date, cost, cost_unit, projected_cost, outcome, raw_manifest_id, pins
  JSON; PK experiment and id);
- `budgets` (experiment, cost_unit, cap, set_by; spent is computed in the query; PK experiment and cost_unit);
- `files` (sha256 PK, bytes, tier, licence);
- `manifest_files` (manifest_id, path, sha256; PK manifest_id and path): a file's logical path inside a run
  manifest or data pack, so `rnd where` finds it by path as well as by hash (round 2 F9);
- `copies` (sha256, store, location; one row per copy).

**Where the rows come from:**
- `experiment.json` files and data-pack manifests, always;
- `rnd-data`'s window and run manifests, when a local rnd-data checkout is present.

**Machine locations stay out of public rnd.** The `copies` rows for D: and off-site come only from rnd-data's
private manifests, never from anything committed to rnd.

**It gains these commands:**
- `rnd runs [--model …] [--venue …]`;
- `rnd ledger <experiment>`: per cost unit;
- `rnd where <sha256 or manifest path>`: every copy.

`rnd sql` already gives read-only SQL. There is one database, not two (round 1 F7).

## 6. rnd-data, the new repository

- **Name and owner:** `mcp-tool-shop-org/rnd-data`, private.
- **What's in git:**
  - `runs/<id>/manifest.json` for every run from any venue. It lists every file's path, SHA-256, size, tier and
    licence, and where each copy is. A `models` list at the top gives every generating model with its pin, licence
    and required notice, and each raw file inherits from it (round 1 Q6).
  - Raw files under 256 KB that matter: logs, journals, receipts JSON, `outcome.json`.
  - `private/`: the T5 files and their manifest.
  - A README.
- **What's not in git:**
  - large raw files, on D: under `D:/rnd-data/runs/<id>/`;
  - custom builds, under `D:/rnd-data/blobs/<sha256>/`;
  - and the off-site copy of both.
- **The off-site copy:** chosen and filled at P4 (§7) on four criteria, from the vendor's own pages read at the time (round 1
  Q3):
  - its file-size and total limits: files reach 159 MB, and the total is 20 GB and growing;
  - its monthly cost at 20–100 GB, and the egress cost of a full restore;
  - whether upload and restore can be checked against the manifest's SHA-256s;
  - a scripted restore test.
- **Tooling, in rnd:**
  - `rnd raw ingest <dir> --run <id>`: it hashes every file, writes the manifest, places each file on D: and verifies
    it by hash, and puts custom builds in the blob store. It never deletes the source.
    - **When the source is P0's verified backup on D:,** it hardlinks the files into `D:/rnd-data/` instead of
      copying them. D: is NTFS, with 3.37 TB free (measured 2026-10-19), so the 20 GB isn't copied over USB again
      (round 2 Q2).
    - A hardlink is the same bytes under a second name, not a second copy. D: still counts as one copy in P6's
      rule.
  - `rnd raw verify --run <id> [--remote]`: it re-hashes every copy, and with `--remote` it restores one run from
    off-site into a temporary folder and checks every SHA-256.
- **Per org standards:** the repo-first rule before any coding. rnd-data holds no code, so the Atlas map and the
  coverage bar apply only if it ever gains workflows or code.

## 7. The phases, backups first

| Phase | What | Paid? | Irreversible? |
|---|---|---|---|
| **P0 backups** | Copy `rnd-local`, `Publisher/receipts` and `rnd-watch` to `D:/backup-2026-10/`, verify every file by SHA-256, and write the hash list beside it. Check whether D: holds the two data packs, and copy them from HF if not. No new repo, no code beyond a copy-and-hash script. | free | no |
| **P1 conventions** | The size, layout and private-file rules with the grandfather list, the `experiment.json` schema, `rnd new-experiment`, and a handbook page. No files move. | free | no |
| **P2 database** | The six tables, `rnd runs record`, `rnd runs`, `rnd ledger`, `rnd where`. Backfill the live experiments first (critic-signal, stage1-regeneration); the rest as they're touched. | free | no |
| **P3 rnd-data** | Create the repo. Ingest from P0's backup on D:, run by run, by hardlink: the receipts and the rig's raw outputs. Move `rnd-local` into `private/` and check every private text file carries the tag. Builds go into the blob store, once each. | free | creating a repo |
| **P4 off-site** | Choose the off-site store on §6's criteria, upload `D:/rnd-data/` (the deduplicated layout, once), and pass `rnd raw verify --run <id> --remote` on at least one run. | **needs a price, and the Director's go** | no (deletable) |
| **P5 tidy** | After P3 and P4 are verified, remove the 58 receipts from the Publisher's git (`git rm`, with a pointer to rnd-data) and point rnd-watch's archive at rnd-data. | free | no (git history keeps them) |
| **P6 local deletion** | Delete an E: copy only when three things hold: D: and off-site both verify by hash, a restore test has passed, and the Director gives the go. | free | **yes** |

**Cut from v1 (round 1 F7):**
- the separate `rnd-private` repo, since T5 lives in `rnd-data/private/`;
- the second database, `rnd-data.db`;
- the standalone inventory script, since §1 is measured and ingest hashes as it goes;
- moving `verifier-gold`'s bulk out of rnd: without a history rewrite it shrinks the clone by 0 bytes, so it stays.
  The size rule stops new growth.
- moving the existing packs to the org namespace (round 1 F6): they stay at `mcp-tool-shop/rnd-*` because
  published pages cite them. New packs go under the org.

## 8. Compensators (irreversible and outward-facing steps)

| Step | Undo | State after the undo | Owner |
|---|---|---|---|
| Create `rnd-data` | archive or delete the repo (Director's go) | as before; local copies untouched | Publisher |
| Set up the off-site store and upload | delete the bucket or repo (private, so nothing has leaked) | D: and E: copies remain | Publisher |
| Upload a T3 pack to HF (private) | delete the revision or repo; revert the manifest PR | as before | Publisher |
| **Flip a T3 pack from private to public** | **none once it's public: copies may exist.** Gated on `rnd datapack verify`, a licence check, a check that no file is in the T5 manifest, and the Director's go. | the pack can be made private again; outside copies remain | Publisher |
| **A T5 file pushed to public rnd** | **none once pushed: forks and scrapes may hold it.** Prevented by the private-file rule in `rnd check` and the identity scan before every push. If it happens: remove it, rotate anything secret, and tell the Director. | the file is gone from the tip; history and copies may hold it | R&D |
| `git rm` the Publisher's 58 receipts | `git revert` | as before | Publisher |
| Delete a local E: copy (P6) | restore from D: or off-site, tested first | as before | Publisher |

## 9. Questions for Argon (round 3b, a short confirmation)

1. **Round 3's F10 and Q2.** Are both resolved as §10 lists?

**Severity levels:** `blocking`, `before P3` (before the repository is created), `not blocking`.

## 10. What changed from v1, v2 and v3

| Argon round 1 | Where v2 takes it |
|---|---|
| F1: backups behind the coding; rnd-watch dropped | P0 is now backups, including rnd-watch; rnd-watch's history is T5 (§3) |
| F2: costs in mixed units; no raw manifest id | §4 budgets per unit; §5 `runs` has cost_unit and raw_manifest_id; `budgets` keyed by unit |
| F3: builds "not stored" yet kept once | §3: hosted weights not stored; our builds stored once by SHA-256 in a blob store |
| F4: no off-site phase; the Publisher's 58 tracked receipts | off-site with a restore test (P4 since v3); P5 `git rm` with a pointer; P6 deletion gated on both |
| F5: rig runs, staging, collect's results/, gold vs sealed gold | §3 runs from any venue; §4 `staging/`, `results/`, the private-file rule; §3 public gold against sealed keys |
| F6: public flips and cited URLs | §8 rows for the public flip and a T5 leak; existing packs stay at their cited URLs |
| F7: over-built pieces | cut: rnd-private, rnd-data.db, the inventory script, the verifier-gold move; artifacts/uses replaced by files and copies |
| **Round 2** F8: off-site upload before ingest | §7: P3 is now rnd-data (ingest by hardlink from P0's backup), P4 the off-site upload of the deduplicated layout and the remote restore test |
| **Round 2** F9: no logical path for `rnd where` | §5: `manifest_files` (manifest_id, path, sha256) |
| **Round 2** Q2: P0 stays a plain copy | kept; ingest hardlinks from it (§6) |
| **Round 2** Q3: CI can't see rnd-data | §4: wider name patterns (the hash list it led to was withdrawn in v3.1) |
| **Round 3** F10: "five tables" in P2 | §7: six |
| **Round 3** Q2: a raw hash list is an oracle for short files | §4: the private tag in every T5 text file, checked in CI; the exact hash check only where rnd-data is checked out, and in a pre-push hook; no hash list published |

## Licences

No model or new source is used. Raw outputs keep their model's terms, recorded once per run in the manifest's
`models` list and inherited by each file.
