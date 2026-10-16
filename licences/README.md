# Licences and terms: the studio's path to the proof

**The rule (the maintainer's decision, 2026-10-16):** a use of AI-generated content is allowed only when the
provider's own documentation proves it: the live URL, the exact clause, and its date. If it isn't proven, it isn't
used. This folder is where that proof lives, one entry per page the studio relies on.

**This is a reading of published terms, not legal advice.**

## What's here

- **[`registry.json`](registry.json):** one entry per licence, terms page, model card or policy. Each entry has:
  - `url`, `page_date` (the page's own date) and `read_date` (when R&D read it);
  - `clauses`: the exact words the verdict rests on;
  - `uses`: the verdict for each of the four uses (`assets`, `training`, `evaluation`, `code`). The verdicts are
    `proven`, `conditions` (proven with the `conditions` listed), `barred`, `not_proven` and `n/a`;
  - `covers`: the models or services it governs;
  - `snapshot_sha256`: the hash of the page text as fetched on the read date;
  - `archive_url`: the Wayback Machine's closest copy, where one exists.
- **[`snapshot.py`](snapshot.py):** fetches every page, checks each quoted clause still appears on it, hashes the
  text, keeps a full-text copy, and asks the Wayback Machine for its closest copy (a read; nothing is submitted).
  Run it to re-check:
  ```
  python -I licences/snapshot.py <snapshot-dir>            # report only
  python -I licences/snapshot.py <snapshot-dir> --write    # also record hashes in registry.json
  ```
  A clause that no longer appears is reported `MISSING`, and the script exits 1.

## Snapshots

The full page texts aren't committed. Provider terms are their authors' copyrighted text. They're kept on the
studio's machine under `E:/AI/licence-snapshots/<read-date>/<id>.txt`, and the hash in the registry ties each one
to the reading. Re-run `snapshot.py` into a new dated folder whenever a page's verdict is relied on again. A changed
hash means the page changed, and its entry is re-read.

## How to use it

- **Before a model writes, critiques or codes for the studio,** its licence has an entry here, and the use has a
  `proven` or `conditions` verdict. role-set's `writers.json` names the registry `id` in each proven model's entry.
- **When a verdict depends on a judgement** (for example that the Stage 1 verifier is a "specialized tool"), the
  entry says so in `conditions` and names who decided.
- **A new provider or model** gets its entry before first use, with its clauses quoted from the live page.

## Related records

- `experiments/generated-content-terms/`: the first terms check, and Argon's blanket check re-read.
- `experiments/stage1-regeneration/PLAN.md` §1: the open-weight model licences.
- `experiments/stage1-regeneration/PROVENANCE.md`: who wrote what in Stage 1, and the code readings.
