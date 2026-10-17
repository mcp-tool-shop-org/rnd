# Licences and terms: the studio's path to the proof

**The rule (the maintainer's decision, 2026-10-16, revised the same day):**

- **A use is allowed unless the provider's contract or licence restricts it.** The restriction search is
  documented: the pages, clauses and dates checked (`licences/registry.json`).
- **Commonly banned uses get the explicit clause check before they're relied on:** training on outputs,
  distillation, competing models.
- **A model's say-so isn't proof,** including Argon's, R&D's or any model's.
- **R&D re-reads every cited clause at its source** before anything relies on it.

*Revised the same day.* The first wording ("allowed only when the provider's documentation proves it; a missing
restriction proves nothing") counted silence as a bar. The maintainer judged that too strict. Only a contract the
studio agreed to, or copyright in the output, can restrict a use. A licence that makes no claim on outputs, or a
signed contract that is silent, leaves the use free. The verdicts below that rested on silence were revised
(`licences/registry.json`). The ones that rest on explicit clauses (Google's ML clause, xAI's distillation ban,
Anthropic's training-target rule, the Kimi app's non-commercial clause) stand.

This folder is the documented search: one entry per page the studio relies on.

**This is a reading of published terms, not legal advice.**

## What's here

- **[`registry.json`](registry.json):** one entry per licence, terms page, model card or policy. Each entry has:
  - `url`, `page_date` (the page's own date) and `read_date` (when R&D read it);
  - `clauses`: the exact words the verdict rests on;
  - `uses`: the verdict for each of the four uses (`assets`, `training`, `evaluation`, `code`). The verdicts are
    `allowed` (no clause restricts it), `conditions` (allowed with the `conditions` listed), `barred` (a quoted
    clause forbids it), and `n/a`. A use is barred only by a clause (2026-10-17); the earlier `proven` and
    `not_proven` labels belonged to the withdrawn proof rule;
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
to the reading. The hash identifies the copy we hold; it isn't a sign the terms changed. Pages with live counters
(model cards, some help pages) hash differently on every fetch. **The clause check is the signal:** a quoted clause
that no longer appears is reported `MISSING`, and its entry is re-read. Re-run `snapshot.py` into a new dated folder
whenever a verdict is relied on again.

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
